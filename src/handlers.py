from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, Application
import re
from callbacks import ADMIN_YES, ADMIN_NO
from config.config import MYSQL_CONFIG
from lesson_managers.database import Database
from lesson_managers.compositor import Compositor
from senders.admin_sender import AdminSender
from senders.user_sender import UserSender
import os

class Handler:
    GROUP_PATTERN = re.compile(r'^\d{7}/\d{5}$')

    def __init__(self):
        self.db = Database(MYSQL_CONFIG)
        self.db.connect()
        self.compositor = Compositor()

    async def register_default_commands(self, application: Application):
        default_commands = [
            BotCommand("start", "Начать работу и регистрация"),
            BotCommand("schedule_today", "Расписание на сегодня"),
            BotCommand("schedule_tomorrow", "Расписание на завтра"),
            BotCommand("schedule_week", "Расписание на эту неделю"),
            BotCommand("schedule_next_week", "Расписание на следующую неделю"),
            BotCommand("hw_on_week", "ДЗ на эту неделю"),
            BotCommand("hw_next_week", "ДЗ на следующую неделю"),
        ]
        await application.bot.set_my_commands(default_commands, scope=BotCommandScopeDefault())

    async def commands_handler(self, update: Update, context: CallbackContext):
        cmd = update.message.text.split()[0].lower().lstrip('/')
        if cmd == "start":
            await self._start_command_handler(update, context)
        else:
            state = context.user_data.get('state')
            if state in ('ASK_GROUP', 'ASK_ADMIN'):
                await update.message.reply_text("Сначала нужно зарегистрироваться!")
                return
            await self._schedule_commands_handler(cmd, update, context)

    async def _start_command_handler(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        user_data = self.db.getUser(user_id)
        if user_data:
            # Пользователь уже в БД
            group = user_data['academ_group']
            is_admin = user_data['is_admin']
            role = 'староста' if is_admin else 'не староста'
            await update.message.reply_text(f"Привет! Ваша группа: {group}. Вы {role}.")
            return

        # Новая регистрация: спрашиваем группу
        context.user_data.clear()
        context.user_data['state'] = 'ASK_GROUP'
        await update.message.reply_text(
            "Пожалуйста, введите вашу академическую группу в формате xxxxxxx/xxxxx."
        )

    async def text_handler(self, update: Update, context: CallbackContext):
        state = context.user_data.get('state')
        text = update.message.text.strip()

        if state == 'ASK_GROUP':
            if not self.GROUP_PATTERN.fullmatch(text):
                await update.message.reply_text(
                    "Неверный формат. Группа должна быть вида xxxxxxx/xxxxx."
                )
                return
            context.user_data['group'] = text
            context.user_data['state'] = 'ASK_ADMIN'
            keyboard = [[
                InlineKeyboardButton("Да", callback_data=ADMIN_YES),
                InlineKeyboardButton("Нет", callback_data=ADMIN_NO)
            ]]
            await update.message.reply_text(
                "Вы являетесь старостой?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        if context.user_data.get('id_adding_hw') is not None:
            hw_id = context.user_data['id_adding_hw']
            with self.db:
                lesson = self.compositor.getHWbyID(hw_id)
                if lesson:
                    lesson.hw_text = text
                    self.db.addHW(lesson)
            await update.message.reply_text("Текст домашнего задания сохранён!")
            return

        # Если не в процессе регистрации, повторяем /start
        await self._start_command_handler(update, context)

    async def handle_hw_files(self, update: Update, context: CallbackContext):
        if context.user_data.get('id_adding_hw') is None:
            return

        hw_id = context.user_data['id_adding_hw']
        file_path = None

        if update.message.document:
            file = await update.message.document.get_file()
            ext = os.path.splitext(update.message.document.file_name)[-1]
            file_path = f"files/{hw_id}{ext}"
            await file.download_to_drive(file_path)

        elif update.message.photo:
            photo = update.message.photo[-1]
            file = await photo.get_file()
            file_path = f"files/{hw_id}.jpg"
            await file.download_to_drive(file_path)

        if file_path:
            lesson = self.compositor.getHWbyID(hw_id)
            if lesson:
                print(file_path)
                print(str(lesson))
                lesson.file_path = file_path
                print(str(lesson))
                self.db.addHW(lesson)

            await update.message.reply_text("Файл к домашнему заданию сохранён!")

    async def callbacks_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        state = context.user_data.get('state')

        if state == 'ASK_ADMIN':
            is_admin = (query.data == ADMIN_YES)
            user_id = query.from_user.id
            group = context.user_data.get('group')

            success = self.db.addUser(user_id, group, is_admin)
            if not success:
                await query.message.reply_text(
                    "Ошибка при сохранении в БД, попробуйте позже.",
                    reply_markup=ReplyKeyboardRemove()
                )
                context.user_data.clear()
                return

            # Подтверждаем регистрацию
            await query.message.reply_text(
                f"Регистрация завершена! Вы {'староста' if is_admin else 'не староста'}.",
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data.clear()

            # После успешной регистрации, добавляем админ-команды в меню этого пользователя
            admin_commands = [
                BotCommand("add_admin", "Добавить старосту"),
                BotCommand("delete_admin", "Удалить старосту"),
            ]
            await update.bot.set_my_commands(
                await update.bot.get_my_commands(scope=BotCommandScopeDefault()) + admin_commands,
                scope=BotCommandScopeChat(user_id)
            )
            return

        user = update.effective_user
        user_data = self.db.getUser(user.id)
        if (user_data is None):
            return

        is_admin = user_data.get('is_admin', False)
        sender = AdminSender(update, context) if is_admin else UserSender(update, context)
        if query.data.startswith("hw_"):
            await sender.show_hw_by_id(int(query.data[3:]))
        elif query.data.startswith("add_hw_"):
            hw_id = int(query.data[len("add_hw_"):])
            context.user_data['id_adding_hw'] = hw_id
            await query.message.reply_text(
                "Пожалуйста, отправьте текст домашнего задания и при необходимости прикрепите файл."
            )

    async def _schedule_commands_handler(self, command: str, update: Update, context: CallbackContext):
        user = update.effective_user
        user_data = self.db.getUser(user.id)
        if (user_data is None):
            await update.message.reply_text("Для начала пользования ботом вам необходимо зарегестрироваться -- введите /start")
            return

        is_admin = user_data.get('is_admin', False)
        sender = AdminSender(update, context) if is_admin else UserSender(update, context)

        routes = {
            "schedule_today": sender.show_schedule_today,
            "schedule_tomorrow": sender.show_schedule_tomorrow,
            "schedule_week": sender.show_schedule_week,
            "schedule_next_week": sender.show_schedule_next_week,
            "hw_on_week": sender.show_hw_week,
            "hw_next_week": sender.show_hw_next_week,
            "add_admin": sender.add_admin if is_admin else None,
            "delete_admin": sender.delete_admin if is_admin else None,
        }

        action = routes.get(command)
        if action:
            await action()
        else:
            await update.message.reply_text(f"Неизвестная команда: /{command}")
