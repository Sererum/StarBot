import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.config import BOT_TOKEN
from handlers import Handler 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

def main():
    handler = Handler()
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .post_init(handler.register_default_commands)  # :contentReference[oaicite:0]{index=0}
        .build()
    )
    
    # Регистрация обработчиков
    app.add_handler(MessageHandler(filters.COMMAND, handler.commands_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.text_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handler.handle_hw_files))
    app.add_handler(CallbackQueryHandler(handler.callbacks_handler))
    
    # Запуск бота
    app.run_polling()

if __name__ == '__main__':
    main()
