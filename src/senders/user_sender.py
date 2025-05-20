from config.config import MYSQL_CONFIG
from datetime import datetime, timedelta
from lesson_managers.compositor import Compositor
from lesson_managers.database import Database 
from lesson_managers.lesson import Lesson, LessonType
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging
import os

logger = logging.getLogger(__name__)

class UserSender:
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context
        self.compositor = Compositor()
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
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await self.update.message.reply_text(
            text=text,
            reply_markup=reply_markup
        )

    async def show_schedule(self, lessons: list[Lesson], header: str):
        if not lessons:
            await self._send_message(f"{header}Нет занятий")
            return

        message = header
        keyboard = []
        lessons_by_date = {}

        logger.info(lessons)
        for lesson in sorted(lessons, key=lambda l: (l.date, l.time)):
            logger.info(str(lesson))
            try:
                date_obj = datetime.strptime(lesson.date, "%Y-%m-%d")
            except ValueError:
                continue
            date_str = date_obj.strftime("%d.%m")
            weekday = self.WEEKDAYS_RU[date_obj.weekday()]
            lessons_by_date.setdefault(date_str, { 'weekday': weekday, 'lessons': [] })['lessons'].append(lesson)
            logger.info(f"lessons_by_date: {lessons_by_date}")

        for date_str in sorted(lessons_by_date.keys()):
            info = lessons_by_date[date_str]
            sep = "―" * 14
            message += f"\n{sep}\n{date_str} ({info['weekday']})\n{sep}\n\n"
            for lesson in info['lessons']:
                message += (
                    f"{lesson.time}\t{lesson.title}\n"
                    f"{'\t' * 11}{lesson.lesson_type.value}\n\n"
                )
                if lesson.lesson_type in [LessonType.PRACT, LessonType.LAB]:
                    keyboard.append([
                        InlineKeyboardButton(
                            text=f"ДЗ: {lesson.title}",
                            callback_data=f"hw_{lesson.id}"
                        )
                    ])
        await self._send_message(message, keyboard)

    async def show_homework(self, lesson: Lesson):
        if not lesson or not lesson.has_hw:
            await self.update.effective_chat.send_message("Домашнее задание не найдено")
            return

        text = (
            f"📚 ДЗ по {lesson.title}\n\n"
            f"📃 Текст задания:\n{lesson.hw_text}\n\n"
            f"📅 Дедлайн: {lesson.date} {lesson.time}"
        )

        if lesson.has_file and lesson.file_path:
            ext = lesson.file_path.split('.')[-1].lower()
            try:
                with open(lesson.file_path, 'rb') as f:
                    if ext in ('jpg', 'jpeg', 'png'):
                        await self.update.effective_chat.send_photo(photo=f, caption=text)
                    elif ext in ('pdf', 'docx', 'txt'):
                        await self.update.effective_chat.send_document(document=f, caption=text)
                    else:
                        await self.update.effective_chat.send_message(f"{text}\n\n⚠️ Неподдерживаемый формат файла")
            except FileNotFoundError:
                await self.update.effective_chat.send_message(f"{text}\n\n⚠️ Файл не найден")
        else:
            await self.update.effective_chat.send_message(text)

    # Методы с логикой Compositor
    async def show_longterm_hw(self):
        lessons = self.compositor.getLongtermHW()
        hw_lessons = [l for l in lessons if l.has_hw]
        if not hw_lessons:
            await self._send_message("📚 На текущей неделе нет домашних заданий")
            return
        await self._send_message("📚 Домашние задания на текущую неделю:")
        for lesson in hw_lessons:
            await self.show_homework(lesson)

    async def show_schedule_today(self):
        lessons = self.compositor.mergeListsScheduleHWToday()
        logger.info(lessons)
        logger.info(str(lessons[0]))
        await self.show_schedule(lessons, "📅 Расписание на сегодня:\n")

    async def show_schedule_tomorrow(self):
        lessons = self.compositor.mergeListsScheduleHWTomorrow()
        await self.show_schedule(lessons, "📅 Расписание на завтра:\n")

    async def show_schedule_week(self):
        lessons = self.compositor.mergeListsScheduleHWWeek()
        start, end = self._get_week_range(datetime.today() - timedelta(days=datetime.today().weekday()))
        header = f"📅 Текущая неделя ({start} - {end}):\n"
        await self.show_schedule(lessons, header)

    async def show_schedule_next_week(self):
        lessons = self.compositor.mergeListsScheduleHWNextWeek()
        today = datetime.today()
        start_next = today + timedelta(days=(7 - today.weekday()))
        start, end = self._get_week_range(start_next)
        header = f"📅 Следующая неделя ({start} - {end}):\n"
        await self.show_schedule(lessons, header)

    async def show_hw_by_id(self, hw_id: int):
        lesson = self.compositor.getHWbyID(hw_id)
        logger.info(f"user_sender: {str(lesson)}")
        await self.show_homework(lesson)

    async def show_hw_week(self):
        lessons = self.compositor.mergeListsScheduleHWWeek()
        hw_lessons = [l for l in lessons if l.has_hw]
        if not hw_lessons:
            await self._send_message("📚 На текущей неделе нет домашних заданий")
            return
        await self._send_message("📚 Домашние задания на текущую неделю:")
        for lesson in hw_lessons:
            await self.show_homework(lesson)

    async def show_hw_next_week(self):
        lessons = self.compositor.mergeListsScheduleHWNextWeek()
        hw_lessons = [l for l in lessons if l.has_hw]
        if not hw_lessons:
            await self._send_message("📚 На следующей неделе нет домашних заданий")
            return
        await self._send_message("📚 Домашние задания на следующую неделю:")
        for lesson in hw_lessons:
            await self.show_homework(lesson)

    @staticmethod
    def _get_week_range(start_date: datetime) -> (str, str):
        end_date = start_date + timedelta(days=6)
        return (start_date.strftime("%d.%m"), end_date.strftime("%d.%m"))
