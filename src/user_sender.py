from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lesson import Lesson, LessonType
import os

class UserSender:
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        self.WEEKDAYS_RU = {
            0: "понедельник",
            1: "вторник",
            2: "среда",
            3: "четверг",
            4: "пятница",
            5: "суббота",
            6: "воскресенье"
        }

    async def _send_message(self, text: str, keyboard: list = None):
        """Универсальный метод для отправки сообщений"""
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await self.update.message.reply_text(
            text=text,
            reply_markup=reply_markup
        )

    async def _send_photo(self, text: str, photo_path: str, keyboard: list = None):
        """Отправка сообщения с фотографией"""
        if not os.path.exists(photo_path):
            await self._send_message(f"⚠️ Файл не найден!\n{text}", keyboard)
            return

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        with open(photo_path, 'rb') as photo:
            await self.update.message.reply_photo(
                photo=photo,
                caption=text,
                reply_markup=reply_markup
            )

    async def show_schedule(self, lessons: list[Lesson], header: str):
        if not lessons:
            await self._send_message(f"{header}Нет занятий")  # Добавлен await
            return

        # Форматирование сообщения
        message = header
        keyboard = []
        lessons_by_date = {}

        # Группировка по датам
        for lesson in sorted(lessons, key=lambda l: (l.date, l.time)):
            date_obj = datetime.strptime(lesson.date, "%Y.%m.%d")
            date_str = date_obj.strftime("%d.%m")
            weekday = self.WEEKDAYS_RU[date_obj.weekday()]
            
            if date_str not in lessons_by_date:
                lessons_by_date[date_str] = {
                    'weekday': weekday,
                    'lessons': []
                }
            lessons_by_date[date_str]['lessons'].append(lesson)

        # Построение сообщения
        for date_str in sorted(lessons_by_date.keys()):
            date_info = lessons_by_date[date_str]
            sep = "―" * 14 
            message += f"\n{sep}\n{date_str} ({date_info['weekday']})\n{sep}\n"
            
            for lesson in date_info['lessons']:
                message += (
                    f"{lesson.time} \t{lesson.title}\n"
                    f"\t\t\t\t\t\t\t\t\t\t\t\t{lesson.lesson_type.value}\n\n"
                )
                
                if lesson.has_hw:
                    keyboard.append([InlineKeyboardButton(
                        text=f"ДЗ: {lesson.title}",
                        callback_data=f"hw_{lesson.id}"
                    )])

        await self._send_message(message, keyboard)

    async def show_homework(self, lesson: Lesson):
        """Показ домашнего задания с прикрепленным файлом"""
        if not lesson or not lesson.has_hw:
            await self._send_message("Домашнее задание не найдено")
            return

        # Формирование текста сообщения
        text = (
            f"📚 ДЗ по {lesson.title}\n\n"
            f"📃 Текст задания:\n{lesson.hw_text}\n\n"
            f"📅 Дедлайн: {lesson.date} {lesson.time}"
        )

        # Проверка наличия файла
        if lesson.has_file and lesson.file_path:
            file_ext = lesson.file_path.split('.')[-1].lower()
            
            try:
                with open(lesson.file_path, 'rb') as file:
                    # Отправка в зависимости от типа файла
                    if file_ext in ('jpg', 'jpeg', 'png'):
                        await self.update.message.reply_photo(
                            photo=file,
                            caption=text
                        )
                    elif file_ext in ('pdf', 'docx'):
                        await self.update.message.reply_document(
                            document=file,
                            caption=text
                        )
                    else:
                        await self._send_message(f"{text}\n\n⚠️ Неподдерживаемый формат файла")
            except FileNotFoundError:
                await self._send_message(f"{text}\n\n⚠️ Файл не найден")
        else:
            await self._send_message(text)

    # Методы для разных типов расписания
    async def show_schedule_today(self):
        today = datetime.today()
        lessons = [
            Lesson("Теория графов", LessonType.LECT, today.strftime("%Y.%m.%d"), "14:00", True),
            Lesson("Дискретная математика", LessonType.PRACT, today.strftime("%Y.%m.%d"), "12:00")
        ]
        await self.show_schedule(lessons, "📅 Расписание на сегодня:\n")

    async def show_schedule_tomorrow(self):
        tomorrow = datetime.today() + timedelta(days=1)
        lessons = [
            Lesson("Математический анализ", LessonType.LAB, tomorrow.strftime("%Y.%m.%d"), "10:00"),
            Lesson("Теория вероятностей", LessonType.LECT, tomorrow.strftime("%Y.%m.%d"), "16:00", True)
        ]
        await self.show_schedule(lessons, "📅 Расписание на завтра:\n")

    async def show_schedule_week(self):
        today = datetime.today()
        start_week = today - timedelta(days=today.weekday())
        lessons = [
            Lesson("Алгебра", LessonType.LECT, (start_week + timedelta(days=0)).strftime("%Y.%m.%d"), "10:00", True),
            Lesson("Математический анализ", LessonType.LAB, tomorrow.strftime("%Y.%m.%d"), "10:00"),
            Lesson("Теория вероятностей", LessonType.LECT, tomorrow.strftime("%Y.%m.%d"), "16:00", True)
        ]
        start_str, end_str = self._get_week_range(start_week)
        await self.show_schedule(lessons, f"📅 Текущая неделя ({start_str} - {end_str}):\n")

    async def show_schedule_next_week(self):
        """Показать расписание на следующую неделю"""
        today = datetime.today()
        start_week = today - timedelta(days=today.weekday())
        start_next_week = start_week + timedelta(weeks=1)
        
        lessons = [
            Lesson("Программирование", LessonType.LECT, 
                  (start_next_week + timedelta(days=1)).strftime("%Y.%m.%d"), "12:00", True),
            Lesson("Базы данных", LessonType.PRACT, 
                  (start_next_week + timedelta(days=1)).strftime("%Y.%m.%d"), "14:00"),
            Lesson("Искусственный интеллект", LessonType.LECT, 
                  (start_next_week + timedelta(days=3)).strftime("%Y.%m.%d"), "10:00", True),
            Lesson("Сетевые технологии", LessonType.LAB, 
                  (start_next_week + timedelta(days=4)).strftime("%Y.%m.%d"), "13:00")
        ]
        
        start_str, end_str = self._get_week_range(start_next_week)
        await self.show_schedule(lessons, f"📅 Следующая неделя ({start_str} - {end_str}):\n")

    async def show_hw_week(self):
        lessons = [
            Lesson(
                title="Теория графов",
                lesson_type=LessonType.LECT,
                date=(start_week + timedelta(days=0)).strftime("%Y.%m.%d"),
                time_str="14:00",
                has_hw=True,
                hw_text="Решить задачи 1-5 из учебника, стр. 45",
                has_file=True,
                file_path="files/graph_theory_hw.pdf"
            ),
            Lesson(
                title="Программирование",
                lesson_type=LessonType.PRACT,
                date=(start_week + timedelta(days=2)).strftime("%Y.%m.%d"),
                time_str="12:00",
                has_hw=True,
                hw_text="Написать программу для сортировки слиянием",
                has_file=False
            )
        ]

    async def show_hw_week(self):
        """ДЗ на текущую неделю (примеры)"""
        today = datetime.today()
        start_week = today - timedelta(days=today.weekday())
        
        lessons = [
            Lesson(
                title="Теория графов",
                lesson_type=LessonType.LECT,
                date=(start_week + timedelta(days=0)).strftime("%Y.%m.%d"),
                time_str="14:00",
                has_hw=True,
                hw_text="Решить задачи 1-5 из учебника, стр. 45",
                has_file=True,
                file_path="files/2.pdf"
            ),
            Lesson(
                title="Программирование",
                lesson_type=LessonType.PRACT,
                date=(start_week + timedelta(days=2)).strftime("%Y.%m.%d"),
                time_str="12:00",
                has_hw=True,
                hw_text="Написать программу для сортировки слиянием",
                has_file=False
            )
        ]
        
        hw_lessons = [lesson for lesson in lessons if lesson.has_hw]
        
        if not hw_lessons:
            await self._send_message("📚 На текущей неделе нет домашних заданий")
            return

        await self._send_message("📚 Домашние задания на текущую неделю:")
        for lesson in hw_lessons:
            await self.show_homework(lesson)

    async def show_hw_next_week(self):
        """ДЗ на следующую неделю (примеры)"""
        next_week_start = datetime.today() + timedelta(weeks=1)
        next_week_start -= timedelta(days=next_week_start.weekday())
        
        lessons = [
            Lesson(
                title="Базы данных",
                lesson_type=LessonType.LAB,
                date=(next_week_start + timedelta(days=1)).strftime("%Y.%m.%d"),
                time_str="10:00",
                has_hw=True,
                hw_text="Спроектировать схему БД для интернет-магазина",
                has_file=True,
                file_path="files/1.jpg"
            ),
            Lesson(
                title="Математический анализ",
                lesson_type=LessonType.LECT,
                date=(next_week_start + timedelta(days=3)).strftime("%Y.%m.%d"),
                time_str="09:00",
                has_hw=True,
                hw_text="Решить пределы: № 15.3, 15.7, 15.9",
                has_file=False
            )
        ]
        
        hw_lessons = [lesson for lesson in lessons if lesson.has_hw]
        
        if not hw_lessons:
            await self._send_message("📚 На следующей неделе нет домашних заданий")
            return

        await self._send_message("📚 Домашние задания на следующую неделю:")
        for lesson in hw_lessons:
            await self.show_homework(lesson)

    # Вспомогательные методы
    @staticmethod
    def _get_week_range(start_date: datetime) -> (str, str):
        end_date = start_date + timedelta(days=6)
        return (
            start_date.strftime("%d.%m"),
            end_date.strftime("%d.%m")
        )
