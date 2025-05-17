from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import Database
from config import MYSQL_CONFIG
from callbacks import ADMIN_YES, ADMIN_NO
from user_sender import UserSender
from admin_sender import AdminSender

class Handler:
    def __init__(self):
        self.db = Database(MYSQL_CONFIG)
        self.db.connect()

    async def commands_handler(self, update: Update, context: CallbackContext):
        """Обработчик всех команд"""
        command = update.message.text.split()[0].lower().replace("/", "")

        if command == "start":
            await self._start_command_handler(update, context)  # Добавлен self и await
            return
        if command in ["schedule_today", "schedule_tomorrow", "schedule_week", 
                      "schedule_next_week", "hw_on_week", "hw_next_week", "add_admin", "delete_admin"]:
            await self._user_admin_commands_handler(command, update, context)  # Добавлен self и await
            return 

        await update.message.reply_text(f"Я не знаю такой команды: /{command}")

    async def _user_admin_commands_handler(self, command: str, update: Update, context: CallbackContext):
        """Обработчик команд для юзеров и админов"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        is_admin = user_data['is_admin']
        sender = AdminSender(update, context) if is_admin else UserSender(update, context)

        if command == "schedule_today":
            await sender.show_schedule_today()
        elif command == "schedule_tomorrow":
            await sender.show_schedule_tomorrow()
        elif command == "schedule_week":
            await sender.show_schedule_week()
        elif command == "schedule_next_week":
            await sender.show_schedule_next_week()
        elif command == "hw_on_week":
            await sender.show_hw_week()
        elif command == "hw_next_week":
            await sender.show_hw_next_week()
        elif is_admin and command == "add_admin":
            pass
        elif is_admin and command == "delete_admin":
            pass
        else:
            await update.message.reply_text(f"Я не знаю такой команды: /{command}")

    async def _start_command_handler(self, update: Update, context: CallbackContext):
        """Обработчик команды /start"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)  # Используем self.db
        
        if user_data:
            status = 'староста' if user_data['is_admin'] else 'не староста'
            await update.message.reply_text(f'Привет! Ты {status}')
        else:
            keyboard = [[
                InlineKeyboardButton("Да", callback_data=ADMIN_YES),
                InlineKeyboardButton("Нет", callback_data=ADMIN_NO)
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                'Вы староста?',
                reply_markup=reply_markup
            )

    async def text_handler(self, update: Update, context: CallbackContext):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)  # Используем self.db
        
        if user_data:
            status = 'староста' if user_data['is_admin'] else 'не староста'
            await update.message.reply_text(f'Ты {status}')
        else:
            await self._start_command_handler(update, context)  # Добавлен self

    async def callbacks_handler(self, update: Update, context: CallbackContext):
        """Обработчик колбэков"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        if callback_data in [ADMIN_YES, ADMIN_NO]:
            # Передаем все необходимые параметры
            await self.handle_admin_response(update, query.from_user.id, callback_data)

    async def handle_admin_response(self, update: Update, user_id: int, answer: str):
        """Обработка ответа на вопрос о статусе"""
        is_admin = (answer == ADMIN_YES)
        self.db.set_admin_status(user_id, is_admin)  # Используем self.db
        
        # Используем query.message для редактирования оригинального сообщения
        await update.callback_query.message.reply_text(
            f'Статус сохранён: Вы {"староста" if is_admin else "не староста"}',
            reply_markup=ReplyKeyboardRemove()
        )
