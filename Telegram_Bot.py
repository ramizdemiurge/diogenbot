# -*- coding: utf-8 -*-
import datetime
from time import sleep

import telegram
from telegram.error import NetworkError, Unauthorized

from Model import *
from methods.djaler_utils import is_user_group_admin, get_username_or_name_sb
from methods.methods import spam_cheker, admin_method, changes_detector, super_admin_method, user_cmds, reply_cmds

update_id = None

_admin_id = 76114490


def main():
    print("Bot started")
    global update_id
    start_time = datetime.datetime.now()
    bot = telegram.Bot(bot_token)

    # try:
    #     update_id = bot.get_updates()[0].update_id
    # except IndexError:
    #     update_id = None

    while True:
        try:
            echo(bot, start_time)
        except NetworkError:
            # print("[Exception] NetworkError")
            sleep(1)
        except Unauthorized:
            update_id += 1
            print("[Exception] Unauthorized")
        except AttributeError:
            print("[Exception] AttributeError")
        except IndexError:
            print("[Exception] IndexError")


def echo(bot, start_time):
    global update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        try:
            _user_id = None
            _username = None
            _first_name = None
            _last_name = None

            if not update.message:
                print("There is no message in update")
                return

            _chat_id = update.message.chat.id

            if update.message.from_user.id:
                _user_id = update.message.from_user.id
            if update.message.from_user.username:
                _username = update.message.from_user.username
            if update.message.from_user.first_name:
                _first_name = update.message.from_user.first_name
            if update.message.from_user.last_name:
                _last_name = update.message.from_user.last_name

            if _chat_id == _user_id:
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
                                              "Пользователей: " + str(users_count)+
                                              "\nГрупп: "+str(groups_count))
                    try:
                        answer = get_username_or_name_sb(update.message.from_user)+" получил данные."
                        print(answer)
                        bot.send_message(_admin_id, answer)
                    except Exception:
                        pass

                else:
                    answer = get_username_or_name_sb(update.message.from_user) + " обратился к боту."
                    print(answer)
                    bot.send_message(_admin_id, answer)
                    update.message.reply_text("Человек! Где человек?")
                return
            else:
                user_query = User.select().where(User.chat_id == _chat_id, User.user_id == _user_id)
                group_query = Groups.select().where(Groups.chat_id == _chat_id)

                if _user_id == _admin_id:
                    super_admin_method(bot, update)

                if not group_query.exists():
                    bot.send_message(_chat_id, "Чат не зарегистрирован в базе бота. Обратитесь к @abdullaeff"
                                               "\nchatid: " + str(_chat_id))
                    return

                group_object = group_query.first()

                try:
                    settings_object = group_object.settings
                except Exception:
                    return

                # Admin commands
                if _user_id != _admin_id and not is_user_group_admin(bot, _user_id, _chat_id, _admin_id):
                    pass
                else:
                    admin_method(bot, update, settings_object)

                if user_query.exists():
                    user_object = user_query.first()
                    changes_detector(user_object, update, bot)

                else:
                    user_object = User.create(user_id=update.message.from_user.id, first_name=_first_name,
                                              last_name=_last_name, chat_id=_chat_id, t_username=_username,
                                              last_activity=datetime.datetime.now())
                    user_object = user_query.first()

                # Working with messages
                if update.message:
                    _message_id = update.message.message_id
                    _message = update.message

                    if _message.reply_to_message is None:
                        pass
                    else:
                        if reply_cmds(update, bot):
                            return

                    if update.message.sticker:
                        if settings_object.delete_stickers:
                            # sleep(settings_object.delete_stickers_seconds)
                            bot.delete_message(chat_id=_chat_id, message_id=_message_id)
                        elif user_object.messages_count < settings_object.stickers_count:
                            bot.delete_message(chat_id=_chat_id, message_id=_message_id)
                            return
                    elif update.message.text:
                        if settings_object.delete_messages:
                            # sleep(settings_object.delete_messages_seconds)
                            bot.delete_message(chat_id=_chat_id, message_id=_message_id)
                            return
                        elif user_object.messages_count < settings_object.antibot_count:
                            if spam_cheker(update.message.text):
                                bot.delete_message(chat_id=_chat_id, message_id=_message_id)
                                return
                        else:
                            user_cmds(user_object, update, update.message.text)

                        user_object.messages_count += 1
                        user_object.last_activity = datetime.datetime.now()
                        user_object.save()
        except Exception:
            print("Exception while working with update")
            return

if __name__ == '__main__':
    main()
