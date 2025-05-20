"""
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database import Database
from config import MYSQL_CONFIG
from src.compositor import Compositor

async def start_command(update: Update, context: CallbackContext):
    user = update.effective_user
    with Database(MYSQL_CONFIG) as db:
        db.initialize_database()
        user_data = db.get_user(user.id)

    if user_data:
        status = 'админ' if user_data['is_admin'] else 'не админ'
        await update.message.reply_text(f'Привет! Ты {status}')
    else:
        keyboard = [['Да', 'Нет']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            'Вы администратор?',
            reply_markup=reply_markup
        )


async def handle_admin_response(update: Update, context: CallbackContext):
    text = update.message.text.lower()

    if text not in ['да', 'нет']:
        await update.message.reply_text('Пожалуйста, выберите "Да" или "Нет"')
        return

    is_admin = text == 'да'
    with Database(MYSQL_CONFIG) as db:
        user = update.effective_user
        db.set_admin_status(user.id, is_admin)

    await update.message.reply_text(
        f'Статус сохранён: Вы {"админ" if is_admin else "не админ"}',
        reply_markup=ReplyKeyboardRemove()
    )


async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    with Database(MYSQL_CONFIG) as db:
        user_data = db.get_user(user.id)
    text = update.message.text.lower()
    if text == 'дз':
        with Database(MYSQL_CONFIG) as db:
            response = db.fillListHWForToday()
        await update.message.reply_text(response, parse_mode='HTML')
        return
    if text == 'дз1':
        with Database(MYSQL_CONFIG) as db:
            response = db.fillListHWForTomorrow()
        await update.message.reply_text(response, parse_mode='HTML')
        return
    if text == 'дз2':
        with Database(MYSQL_CONFIG) as db:
            response = db.fillListHWForWeek()
        await update.message.reply_text(response, parse_mode='HTML')
        return
    if text == 'удалить':
        with Database(MYSQL_CONFIG) as db:
            db.removeHWLastWeek()
        return
    if text == 'чтото':
        with Compositor() as comp:  # Создаем экземпляр Compositor
            comp.mergeListsScheduleHWToday()  # Вызываем метод
        return
    if text == 'чтото1':
        with Compositor() as comp:
            comp.mergeListsScheduleHWTomorrow()
        return
    if text == 'чтото2':
        with Compositor() as comp:
            comp.mergeListsScheduleHWWeek()
        return
    if user_data:
        status = 'админ' if user_data['is_admin'] else 'не админ'
        await update.message.reply_text(f'Ты {status}')
    else:
        await start_command(update, context)
"""
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

