import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import Handler 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    handler = Handler()
    
    # Регистрация обработчиков
    app.add_handler(MessageHandler(filters.COMMAND, handler.commands_handler))
    app.add_handler(MessageHandler(filters.TEXT, handler.text_handler))
    app.add_handler(CallbackQueryHandler(handler.callbacks_handler))
    
    # Запуск бота
    app.run_polling()

if __name__ == '__main__':
    main()
