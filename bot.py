import datetime
from time import sleep

import pendulum
import requests
from telegram.ext import RegexHandler, Updater, MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

from functions.djaler_utils import get_username_or_name_sb, is_user_group_admin
from functions.handlers import help_command_handler
from functions.methods import get_user, admin_method, get_group, super_admin_method, spam_cheker, reply_cmds, user_cmds, \
    thanks_detector, interest_detector, left_chat_detector
from model.config import URL, PORT, ENV, TOKEN, _admin_id, _elkhan_id
from model.dao.UserDao import UserDAO
from model.lists import super_admin_ids


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
        self._updater.dispatcher.add_handler(MessageHandler(Filters.all, self._message_handler))

    @staticmethod
    @run_async
    def _cmd_handler_group(bot, update, groups):
        _user_id = update.message.from_user.id
        _chat_id = update.message.chat.id
        if update.message.text:
            print("Комманда: " + update.message.text)
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
                    admin_method(bot, update, settings_object, user_object=user_object)
        else:
            if update.message.text:
                if update.message.text == "/start":
                    update.message.reply_text("Человек! Где человек?")

    # @run_async
    def _group_message_handler(self, bot, update):

        _chat_id = update.message.chat.id
        _message_id = update.message.message_id
        if left_chat_detector(bot, update):
            return
        if update.message.sticker:
            self._group_sticker_handler(bot, update)
            return
        group = get_group(bot, update)
        user_object = get_user(bot, update)
        settings_object = group.settings
        interest_detector(bot, update, settings_object)
        if update.message.text:
            print("Сообщение: " + update.message.text)
        if settings_object.delete_messages:
            if settings_object.delete_messages_seconds > 0:
                sleep(settings_object.delete_messages_seconds)
            try:
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
            except Exception as e:
                print("Exception: " + str(e))
            return
        elif user_object.autowipe_sec > 0:
            sleep(user_object.autowipe_sec)
            try:
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
            except Exception as e:
                update.message.reply_text("Не могу удалить: " + str(e))
        elif user_object.messages_count < settings_object.antibot_count and update.message.text:
            if spam_cheker(update.message.text):
                try:
                    bot.delete_message(chat_id=_chat_id, message_id=_message_id)
                    bot.send_message(_chat_id,
                                     "Удалена попытка спама " + get_username_or_name_sb(update.message.from_user))
                except Exception as e:
                    update.message.reply_text("Не могу удалить спам: " + str(e))
                return
        else:

            user_cmds(user_object, update, update.message.text)
            if update.message.reply_to_message is None:
                pass
            else:
                thanks_detector(update)

        # user_object.messages_count += 1
        # user_object.last_activity = datetime.datetime.now()
        # user_object.save()
        UserDAO.increment_msg_count(user_object, bot)

    # @run_async
    def _message_handler(self, bot, update):

        _user_id = update.message.from_user.id
        # admin_query = AdminList.select().where(AdminList.user_id == _user_id)
        is_admin = bool(_user_id in super_admin_ids)

        if update.message.reply_to_message is None:
            pass
            # update.message.reply_text("Вы администратор одной из зарегистрированных групп 😉")
            if is_admin:
                pass
            else:
                bot.forward_message(super_admin_ids[0], update.message.chat.id, update.message.message_id)
        else:
            if is_admin:
                try:
                    if update.message.text:
                        bot.send_message(update.message.reply_to_message.forward_from.id, update.message.text)
                    elif update.message.sticker:
                        bot.sendSticker(update.message.reply_to_message.forward_from.id, update.message.sticker.file_id)
                except Exception as e:
                    update.message.reply_text("Exception: " + str(e))
            else:
                bot.forward_message(super_admin_ids[0], update.message.chat.id, update.message.message_id)

    # @run_async
    def _group_sticker_handler(self, bot, update):
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
            elif user_object.autowipe_sec > 0:
                sleep(user_object.autowipe_sec)
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
            elif user_object.messages_count < settings_object.stickers_count:
                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
