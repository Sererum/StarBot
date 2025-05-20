from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import CallbackContext
from lesson_managers.lesson import Lesson, LessonType
from senders.user_sender import UserSender
import os

class AdminSender(UserSender):

    def __init__(self, update: Update, context: CallbackContext):
        super().__init__(update, context)

    @staticmethod
    def _get_admin_actions_keyboard():
        return [
            [InlineKeyboardButton("Добавить админа", callback_data="add_admin")],
            [InlineKeyboardButton("Удалить админа", callback_data="remove_admin")]
        ]

    async def add_admin(self):
        admin_list = []  # Логика получения списка админов
        message = "Список администраторов:\n" + "\n".join(admin_list)
        await self._send_message(message)

    async def delete_admin(self):
        admin_list = []  # Логика получения списка админов
        message = "Список администраторов:\n" + "\n".join(admin_list)
        await self._send_message(message)

    async def add_longterm_hw(self):
        admin_list = []  # Логика получения списка админов
        message = "Список администраторов:\n" + "\n".join(admin_list)
        await self._send_message(message)

    async def show_homework(self, lesson: Lesson):
        keyboard = [[
                    InlineKeyboardButton(
                        text="✍️ Добавить ДЗ",
                        callback_data=f"add_hw_{lesson.id}"
        )]]
        markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        if not lesson or not lesson.has_hw:
            await self.update.effective_chat.send_message(
                text="Домашнее задание не найдено",
                reply_markup=markup
            )
            return

        text = f"📚 ДЗ по {lesson.title}\n\n"
        if len(lesson.hw_text) != 0:
            text += f"📃 Текст задания:\n{lesson.hw_text}\n\n"
        text += f"📅 Дедлайн: {lesson.date} {lesson.time}"

        keyboard = [[
                    InlineKeyboardButton(
                        text="✍️ Изменить ДЗ",
                        callback_data=f"add_hw_{lesson.id}"
        )]]
        markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        if lesson.has_file and lesson.file_path:
            ext = lesson.file_path.split('.')[-1].lower()
            try:
                with open(lesson.file_path, 'rb') as f:
                    filename = lesson.title + "." + lesson.date + "." + ext
                    file = InputFile(f, filename)
                    if ext in self.available_ext['photo']:
                        await self.update.effective_chat.send_photo(photo=file, caption=text, reply_markup=markup)
                    elif ext in self.available_ext['file']:
                        await self.update.effective_chat.send_document(document=file, caption=text, reply_markup=markup)
                    else:
                        await self.update.effective_chat.send_message(f"{text}\n\n⚠️ Неподдерживаемый формат файла")
            except FileNotFoundError:
                await self.update.effective_chat.send_message(f"{text}\n\n⚠️ Файл не найден", reply_markup=markup)
        else:
            await self.update.effective_chat.send_message(text, reply_markup=markup)
