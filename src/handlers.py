from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext
from database import Database
from config import MYSQL_CONFIG

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
        db.set_admin_status(user.id, is_admin)
    
    await update.message.reply_text(
        f'Статус сохранён: Вы {"админ" if is_admin else "не админ"}',
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    with Database(MYSQL_CONFIG) as db:
        user_data = db.get_user(user.id)
    
    if user_data:
        status = 'админ' if user_data['is_admin'] else 'не админ'
        await update.message.reply_text(f'Ты {status}')
    else:
        await start_command(update, context)
