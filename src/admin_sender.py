from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from lesson import Lesson, LessonType
from user_sender import UserSender
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

    async def get_admin(self):
        admin_list = []  # Логика получения списка админов
        message = "Список администраторов:\n" + "\n".join(admin_list)
        await self._send_message(message)

    async def get_hw_week(self):
        hw_list = []  # Логика получения ДЗ на неделю
        message = "ДЗ на текущую неделю:\n" + "\n".join(hw_list)
        await self._send_message(message)

    async def get_hw_next_week(self):
        hw_list = []  # Логика получения ДЗ на след. неделю
        message = "ДЗ на следующую неделю:\n" + "\n".join(hw_list)
        await self._send_message(message)

    async def get_hw_by_id(self, hw_id: int):
        lesson = None 
        if lesson and lesson.has_hw:
            await self.show_homework(lesson)
        else:
            await self._send_message("ДЗ не найдено")

    async def edit_hw_by_id(self, hw_id: int):
        keyboard = [
            [InlineKeyboardButton("Изменить текст", callback_data=f"edit_text_{hw_id}")],
            [InlineKeyboardButton("Изменить файл", callback_data=f"edit_file_{hw_id}")]
        ]
        await self._send_message("Выберите действие:", keyboard)

    async def replace_hw_by_id(self, hw_id: int):
        # Логика замены ДЗ
        await self._send_message(f"ДЗ #{hw_id} успешно заменено")

    async def show_admin_panel(self):
        message = "⚙️ Панель администратора:"
        await self._send_message(message, self._get_admin_actions_keyboard())
