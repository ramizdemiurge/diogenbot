import datetime
from time import sleep

import pendulum
import requests
from telegram.ext import RegexHandler, Updater, MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

from functions.djaler_utils import get_username_or_name_sb, is_user_group_admin
from functions.handlers import help_command_handler
from functions.methods import get_user, admin_method, get_group, super_admin_method, spam_cheker, reply_cmds, user_cmds, \
    thanks_detector
from model.config import URL, PORT, ENV, TOKEN, _admin_id, _elkhan_id
from model.database_model import AdminList, UserLogs, User, Groups


class Bot:
    def __init__(self, token, debug=False):
        self._token = token
        self._updater = Updater(token)
        self._debug = debug

        self._session = requests.Session()

        self._init_handlers()
        pendulum.set_locale('ru')

    def run(self):
        if ENV == "prod":
            print("Using webhooks")
            self._updater.start_webhook(listen='0.0.0.0', port=PORT,
                                        url_path=TOKEN)
            self._updater.bot.set_webhook(URL + TOKEN)
            self._updater.idle()
        else:
            print("Using polling")
            self._updater.start_polling(poll_interval=1)

    def _init_handlers(self):
        self._updater.dispatcher.add_handler(CommandHandler('help', help_command_handler))
        self._updater.dispatcher.add_handler(RegexHandler("\/.*", self._cmd_handler_group, pass_groups=True))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.group, self._group_message_handler))
        self._updater.dispatcher.add_handler(MessageHandler(Filters.text, self._message_handler))

    @run_async
    def _cmd_handler_group(bot, update):
        _user_id = update.message.from_user.id
        _chat_id = update.message.chat.id
        if _user_id == _admin_id or _user_id == _elkhan_id:
            if super_admin_method(bot, update):
                return

        if _user_id != _chat_id:
            group = get_group(bot, update)
            if group:
                user_object = get_user(bot, update)
                if update.message.reply_to_message is None:
                    if user_cmds(user_object, update, update.message.text):
                        return
                elif reply_cmds(update, bot):
                    return

                if _user_id != _admin_id and not is_user_group_admin(bot, _user_id, _chat_id, _admin_id):
                    pass
                else:
                    settings_object = group.settings
                    admin_method(bot, update, settings_object)

    def _group_message_handler(self, bot, update):
        _chat_id = update.message.chat.id
        _message_id = update.message.message_id
        if update.message.sticker:
            self._group_sticker_handler(bot, update)
            return
        group = get_group(bot, update)
        if not group:
            return
        user_object = get_user(bot, update)
        settings_object = group.settings
        if settings_object.delete_messages:
            if settings_object.delete_messages_seconds > 0:
                sleep(settings_object.delete_messages_seconds)
            bot.delete_message(chat_id=_chat_id, message_id=_message_id)
            return
        elif user_object.messages_count < settings_object.antibot_count:
            if spam_cheker(update.message.text):
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
                return
        else:

            user_cmds(user_object, update, update.message.text)
            if update.message.reply_to_message is None:
                pass
            else:
                thanks_detector(update)

        user_object.messages_count += 1
        user_object.last_activity = datetime.datetime.now()
        user_object.save()

    @staticmethod
    @run_async
    def _message_handler(bot, update):
        _user_id = update.message.from_user.id
        admin_query = AdminList.select().where(AdminList.user_id == _user_id)
        if admin_query.exists() or _user_id == _admin_id:
            update.message.reply_text("Вы администратор одной из зарегистрированных групп 😉")
            update.message.reply_text("Комманды бота:\n/setcount <int> - количество написанных " +
                                      "сообщений после которого пользователю позволяется отправлять ссылки\n" +
                                      "/stickercount - количество написанных сообщений после которого пользователю"
                                      " позволяется отправлять стикеры в чат\n" +
                                      "/sticker_on (/sticker_off) - включение/выключение стикеров в группе\n" +
                                      "/text_on (/text_off) - включение/выключение сообщений в группе\n" +
                                      "/warn - предупредить пользователя\n" +
                                      "/log посмотреть историю изменений профильной информации пользователя\n" +
                                      "/stats - ваша статистика\n" +
                                      "(комманды работают в чате группы)")
            logs_count = UserLogs.select().count()
            users_count = User.select().count()
            groups_count = Groups.select().count()
            update.message.reply_text("База данных:\n" +
                                      "Логов: " + str(logs_count) + "\n" +
                                      "Пользователей: " + str(users_count) +
                                      "\nГрупп: " + str(groups_count))
            try:
                answer = get_username_or_name_sb(update.message.from_user) + " получил данные."
                print(answer)
                bot.send_message(_admin_id, answer)
            except Exception:
                pass
        else:
            answer = get_username_or_name_sb(update.message.from_user) + " обратился к боту."
            print(answer)
            bot.send_message(_admin_id, answer)
            update.message.reply_text("Человек! Где человек?")

    @staticmethod
    @run_async
    def _group_sticker_handler(bot, update):
        group = get_group(bot, update)
        if not group:
            return
        user_object = get_user(bot, update)
        settings_object = group.settings

        _user_id = update.message.from_user.id
        _chat_id = update.message.chat.id
        _message_id = update.message.message_id

        if _user_id != _chat_id:
            if settings_object.delete_stickers:
                if settings_object.delete_stickers_seconds:
                    sleep(settings_object.delete_stickers_seconds)
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
            elif user_object.messages_count < settings_object.stickers_count:
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
