import datetime
from time import sleep

import pendulum
import telegram

from functions.djaler_utils import get_username_or_name_sb, get_username_or_name, choice_variant_from_file
from functions.raiting import check_rate_flood
from model.config import _log_chat_id
from model.dao.GroupDAO import GroupDAO
from model.database_model import UserLogs, User, AdminList, Groups, Settings
from model.lists import banned_words, thank_words, interest_words, log_chat_second


def inbox(update):
    _user_id = update.message.from_user.id
    _chat_id = update.message.chat.id
    if _user_id == _chat_id:
        return True
    else:
        return False


def spam_cheker(text):
    text = text.lower()
    return any(b_word in text for b_word in banned_words)


def thanks_checkers(message):
    message = message.lower()
    for x in thank_words:
        if x in message:
            return True
    return False


def left_chat_detector(bot, update):
    if update.message.left_chat_member:
        print("Someone left chat.")
        name = update.message.left_chat_member.first_name
        id = update.message.left_chat_member.id
        print("LCDET: {} left the group.".format(name))
        name = name.strip()
        if name == "":
            name = get_username_or_name(id)

        answer = "[{}](tg://user?id={}) покинул чат.".format(name, str(id))
        bot.send_message(chat_id=update.message.chat.id, text=answer, parse_mode=telegram.ParseMode.MARKDOWN)
        return True



def thanks_detector(update):
    _message = update.message
    _chat_id = _message.chat.id
    _user = _message.from_user
    _reply_user = _message.reply_to_message.from_user
    _text = _message.text
    if thanks_checkers(_text):
        if _reply_user.id == _user.id:
            return
        user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id).limit(1)
        if user_query.exists():
            user_object = user_query.first()
            user_object.rating_plus += 1
            user_object.save()


def interest_detector(bot, update, group_settings):
    _msg = update.message

    if group_settings.spylevel < 1:
        return

    if update.message.text:
        text = update.message.text.lower()
        if any(b_word in text for b_word in interest_words):
            bot.forward_message(_log_chat_id, update.message.chat.id, update.message.message_id)
            return
    if group_settings.spylevel > 1:
        if _msg.document or _msg.voice or _msg.photo or _msg.contact or _msg.video:
            bot.forward_message(_log_chat_id, update.message.chat.id, update.message.message_id)


def get_user(bot, update):
    _chat_id = update.message.chat.id
    _user = update.message.from_user
    _username = None
    _first_name = None
    _last_name = None

    if update.message.from_user.username:
        _username = update.message.from_user.username
    if update.message.from_user.first_name:
        _first_name = update.message.from_user.first_name
    if update.message.from_user.last_name:
        _last_name = update.message.from_user.last_name

    user_query = User.select().where(User.chat_id == _chat_id, User.user_id == _user.id)
    user_object = user_query.first()
    if user_object:
        # user_object = user_query.first()
        try:
            changes_detector(user_object, update, bot)
        except Exception as e:
            bot.send_message(log_chat_second, "Error: " + str(e) + "\nWhile: Detecting changes")
        return user_object

    else:
        user_object = User.create(user_id=update.message.from_user.id, first_name=_first_name,
                                  last_name=_last_name, chat_id=_chat_id, t_username=_username,
                                  last_activity=datetime.datetime.now(), start_time=datetime.datetime.now())
        # user_object = user_query.first()
        return user_object


def get_group(bot, update):
    _chat = update.message.chat
    _chat_id = update.message.chat.id

    group_query = Groups.select().where(Groups.chat_id == _chat_id)
    group = group_query.first()
    if not group:
        group = GroupDAO.create_group(name=None, id=_chat_id)
        bot.send_message(_chat_id,
                         "Чат был автоматически зарегистрирован в системе. Однако не верифицирован. Напишите боту.")
        answer = "⚡️Registered new {}⚡️\n".format(_chat.type)
        _users_count = None

        try:
            _users_count = bot.getChatMembersCount(_chat_id)
        except Exception as e:
            print(str(e))

        try:
            _chat = bot.getChat(_chat_id)
        except Exception as e:
            bot.send_message(log_chat_second, "Error: " + str(e) + "\nWhile: Trying to get chat")

        if _chat.title:
            answer += "\nTtle: " + _chat.title
        if _chat.invite_link:
            answer += "\nLink: " + _chat.invite_link
        if _chat.username:
            answer += "\nUsrn: " + _chat.username
        if _chat.description:
            answer += "\nDesc: " + _chat.description
        answer += "\nChat: " + group.group_name
        if _users_count:
            answer += "\nUsrs: " + str(_users_count)

        try:
            _chat_admins = bot.getChatAdministrators(_chat_id)
            answer += "\n\n⚡️Admins⚡️"
            for member in _chat_admins:
                name = "Admin"
                if member.user.first_name:
                    name = member.user.first_name
                answer += "\n[{}](tg://user?id={})".format(name, str(member.user.id))
                if member.status:
                    answer += " (" + member.status + ")"
        except Exception as e:
            print(str(e))

        bot.send_message(chat_id=log_chat_second, text=answer, parse_mode=telegram.ParseMode.MARKDOWN)
    return group


def changes_detector(user_from_db, update, bot):
    _user = update.message.from_user
    _chat_id = update.message.chat.id
    status = False
    log_string = ""

    if _user.username:
        if user_from_db.t_username != _user.username:
            status = True
            log_string += "uname: " + user_from_db.t_username + " → " + _user.username + ","
            user_from_db.t_username = _user.username
    if _user.first_name:
        if user_from_db.first_name != _user.first_name:
            status = True
            log_string += " fname: " + user_from_db.first_name + " → " + _user.first_name + ","
            user_from_db.first_name = _user.first_name
    if _user.last_name:
        if user_from_db.last_name != _user.last_name:
            status = True
            log_string += " lname: " + user_from_db.last_name + " → " + _user.last_name + ","
            user_from_db.last_name = _user.last_name

    if status:
        log_string = log_string.strip()[:-1]
        user_from_db.changes_count += 1
        user_from_db.save()
        UserLogs.create(user_id=_user.id, chat_id=_chat_id, text=log_string, date=datetime.datetime.now())
        if update.message:
            # update.message.reply_text("Изменения:\n" + log_string)
            update.message.reply_text(choice_variant_from_file('changes.txt'))


def admin_method(bot, update, settings, user_object):
    _chat_id = update.message.chat.id
    _user = update.message.from_user
    text = update.message.text
    text_array = text.split()

    try:
        if update.message.text:
            if update.message.reply_to_message is None:
                pass
            else:
                _reply_user = update.message.reply_to_message.from_user
                if len(text_array) >= 2:
                    if text_array[0] == "/wipe":
                        if int(text_array[1]) > 60:
                            text_array[1] = 60
                        user_query = User.select().where(User.chat_id == _chat_id, User.user_id == _reply_user.id)
                        if user_query.exists():
                            user_object = user_query.first()
                            user_object.autowipe_sec = int(text_array[1])
                            user_object.save()
                            if int(text_array[1]) > 0:
                                update.message.reply_text(
                                    "Включено автоудаление сообщений " + get_username_or_name_sb(_reply_user)
                                    + " c задержкой: " + str(text_array[1]) + " сек.")
                            else:
                                update.message.reply_text("Автоудаление выключено.")
                            return
                else:
                    if text == "/warn":
                        user_query = User.select().where(User.chat_id == _chat_id, User.user_id == _reply_user.id)
                        if user_query.exists():
                            user_object = user_query.first()
                            user_object.warns += 1
                            user_object.save()
                            bot.send_message(_chat_id, get_username_or_name_sb(_reply_user) +
                                             " выполнено предупреждение. (" + str(user_object.warns) + "/" + "5)")

        if update.message.text:
            if len(text_array) >= 2:
                if text_array[0] == "/setcount":
                    old_value = settings.antibot_count
                    settings.antibot_count = int(text_array[1])
                    settings.save()
                    update.message.reply_text("Изменено с " + str(old_value) + " на " + text_array[1])
                elif text_array[0] == "/stickercount":
                    old_value = settings.stickers_count
                    settings.stickers_count = int(text_array[1])
                    settings.save()
                    update.message.reply_text("Изменено с " + str(old_value) + " на " + text_array[1])
                elif text_array[0] == "/wipe":
                    if int(text_array[1]) > 60:
                        text_array[1] = 60
                    user_object.autowipe_sec = int(text_array[1])
                    user_object.save()
                    if int(text_array[1]) > 0:
                        update.message.reply_text(
                            "Включено автоудаление ваших сообщений c задержкой: " + str(text_array[1]) + " сек.")
                    else:
                        update.message.reply_text("Автоудаление выключено.")

            else:
                if text == "/stickers_off":
                    settings.delete_stickers = True
                    settings.save()
                    bot.send_message(_chat_id, "Стикеры выключены")
                if text == "/stickers_on":
                    settings.delete_stickers = False
                    settings.save()
                    bot.send_message(_chat_id, "Стикеры включены")
                if text == "/text_off":
                    settings.delete_messages = True
                    settings.save()
                    bot.send_message(_chat_id, get_username_or_name(_user) + " объявил тишину...")
                if text == "/text_on":
                    settings.delete_messages = False
                    settings.save()
                    bot.send_message(_chat_id, get_username_or_name(_user) + " отменил тишину...")

    except Exception as e:
        update.message.reply_text("Exception: " + str(e))


def super_admin_method(bot, update):
    if update.message.text:
        _chat_id = update.message.chat.id
        _user = update.message.from_user
        _text = update.message.text
        _text_array = _text.split(" ")

        try:
            if len(_text_array) >= 2:
                if _text_array[0] == "/add_admin":
                    admin_query = AdminList.select().where(AdminList.user_id == int(_text_array[1]),
                                                           AdminList.group_id == _chat_id)
                    if not admin_query.exists():
                        AdminList.create(user_id=int(_text_array[1]), group_id=_chat_id)
                        update.message.reply_text("Добавлен админ с id: " + _text_array[1])
                    else:
                        update.message.reply_text("Админ с id: " + _text_array[1] + " в данном чате уже есть.")
                elif _text_array[0] == "/del_admin":
                    admin_query = AdminList.select().where(AdminList.group_id == _chat_id,
                                                           AdminList.user_id == int(_text_array[1]))
                    if admin_query.exists():
                        admin = admin_query.first()
                        admin.delete_instance()
                        update.message.reply_text("Админ удален")
                    else:
                        update.message.reply_text("Такой админ не зарегистрирован в данном чате")
                elif _text_array[0] == "/verify":
                    _settings = Settings.create()
                    Groups.create(group_name=_text_array[1], chat_id=_chat_id, settings=_settings, force_insert=True)
                elif _text_array[0] == "/say":
                    chat_name = _text_array[1]
                    group_query = Groups.select().where(Groups.group_name == chat_name).limit(1)
                    if group_query.exists():
                        group = group_query.first()
                        _text_array[0] = _text_array[1] = ""
                        send_text = "".join([str(x + " ") for x in _text_array])
                        bot.send_message(group.chat_id, send_text)
                    else:
                        _text_array[0] = _text_array[1] = ""
                        send_text = "".join([str(x + " ") for x in _text_array])
                        bot.send_message(str(chat_name), send_text)
                        # update.message.reply_text("Чат не найден.")
                    return True
            # if len(_text_array) >= 3:
            #     pass
            else:
                if _text == "/chats":
                    groups = Groups.select()
                    answer = ""
                    counter = 1
                    for group in groups:
                        name = group.group_name
                        if not name:
                            continue
                            # name = "chat_" + str(counter)
                        users_count = User.select().where(User.chat_id == group.chat_id).count()
                        answer += str(counter) + ". " + name + " [users: " + str(users_count) + "]\n"
                        counter += 1
                    if answer != "":
                        update.message.reply_text(answer)
                    else:
                        update.message.reply_text("Журнал пуст.")
                    return True
                if _text == "/verify":
                    update.message.reply_text("Задай чату имя.")
                    # group_query = Groups.select().where(Groups.chat_id == _chat_id)
                    # if not group_query.exists():
                    #     _settings = Settings.create()
                    #     Groups.create(chat_id=_chat_id, settings=_settings, force_insert=True)
                    #     update.message.reply_text("Чат был зарегистрирован.")
                    # else:
                    #     update.message.reply_text("Чат уже зарегистрирован.")
                    # return True

                if _text == "/del_chat":
                    group_query = Groups.select().where(Groups.chat_id == _chat_id)
                    if group_query.exists():
                        group = group_query.first()
                        group.delete_instance()
                        deleted_users = User.delete().where(User.chat_id == group.chat_id)
                        deleted_logs = UserLogs.delete().where(UserLogs.chat_id == group.chat_id)

                        deleted_user_count = deleted_users.execute()
                        deleted_logs_count = deleted_logs.execute()
                        update.message.reply_text("Чат был удален."
                                                  "\nУдалено пользователей: " + str(deleted_user_count) +
                                                  "\nЖурнал: " + str(deleted_logs_count))
                    else:
                        update.message.reply_text("Этот чат не зарегистрирован.")
                    return True
                if _text == "/bot":

                    # update.message.reply_text("Комманды бота:\n/setcount <int> - количество написанных " +
                    #                               "сообщений после которого пользователю позволяется отправлять ссылки\n" +
                    #                               "/stickercount - количество написанных сообщений после которого пользователю"
                    #                               " позволяется отправлять стикеры в чат\n" +
                    #                               "/sticker_on (/sticker_off) - включение/выключение стикеров в группе\n" +
                    #                               "/text_on (/text_off) - включение/выключение сообщений в группе\n" +
                    #                               "/warn - предупредить пользователя\n" +
                    #                               "/log посмотреть историю изменений профильной информации пользователя\n" +
                    #                               "/stats - ваша статистика\n" +
                    #                               "(комманды работают в чате группы)")
                    logs_count = UserLogs.select().count()
                    users_count = User.select().count()
                    groups_count = Groups.select().count()
                    update.message.reply_text("База данных:" +
                                                "\nЛоги: " + str(logs_count) +
                                                "\nПользователи: " + str(users_count) +
                                                "\nГруппы: " + str(groups_count))
        except Exception as e:
            update.message.reply_text("Exception: " + str(e))
            return True


def user_cmds(bot, update, user):
    _chat_id = update.message.chat.id
    _user = update.message.from_user
    _text = update.message.text.lower()
    _text_array = _text.split()
    try:
        if len(_text_array) >= 2:
            pass
        else:
            if _text == "/stats":
                rating_value = float(user.rating_plus / user.rating_minus)
                answer = "Сообщений: " + str(user.messages_count) + ", изменений в профиле: " + str(
                    user.changes_count) + ", идентификатор: " + str(_user.id) + ", чат: " + str(
                    _chat_id) + ", рейтинг: " + str("%.1f" % rating_value)
                update.message.reply_text(answer)
                return True
            if "/info" in _text:
                bot.send_chat_action(chat_id=_chat_id, action=telegram.ChatAction.TYPING)
                user_query = User.select().where(User.user_id == _user.id, User.chat_id == _chat_id)
                if user_query.exists():
                    user_object = user_query.first()
                    rating_value = float(user_object.rating_plus / user_object.rating_minus)
                    update.message.reply_text("Ваш рейтинг: " + str("%.1f" % rating_value))
                return True
            if "/vsem_ban" in _text:
                bot.send_chat_action(chat_id=_chat_id, action=telegram.ChatAction.TYPING)
                sleep(0.5)
                bot.send_message(chat_id=update.message.chat.id, text="`Все зобанени`", parse_mode=telegram.ParseMode.MARKDOWN)
                return True
            # if "/clicktobecomeautist" in _text:
            #     bot.send_chat_action(chat_id=_chat_id, action=telegram.ChatAction.TYPING)
            #     sleep(0.5)
            #     update.message.reply_text(text="`Ви аутист.`", parse_mode=telegram.ParseMode.MARKDOWN)
            #     return True
            # if "/checkdown" in _text:
            #     choices = ["даун", "не даун"]
            #     import random
            #     print(random.choice(choices))
            #     bot.send_chat_action(chat_id=_chat_id, action=telegram.ChatAction.TYPING)
            #     sleep(0.5)
            #     update.message.reply_text(text="Вы {}.".format(random.choice(choices)), parse_mode=telegram.ParseMode.MARKDOWN)
            #     return True
            if "/log" in _text:
                bot.send_chat_action(chat_id=_chat_id, action=telegram.ChatAction.TYPING)
                sleep(1)
                update.message.reply_text(text="Скоро будет ;)", parse_mode=telegram.ParseMode.MARKDOWN)
                return True
        pass
    except Exception as e:
        update.message.reply_text("Exception: " + str(e))
    pass


def reply_cmds(update, bot):
    _message = update.message
    _chat_id = _message.chat.id
    _user = _message.from_user
    _reply_user = _message.reply_to_message.from_user
    _text = _message.text
    _text_array = _text.split()
    try:
        if len(_text_array) >= 2:
            pass
        else:
            if _text == "/log":
                answer = ""

                users = UserLogs.select().where(UserLogs.user_id == _reply_user.id,
                                                UserLogs.chat_id == _chat_id).order_by(UserLogs.date.desc()).limit(5)
                counter = 1
                for log in users:
                    date = pendulum.instance(log.date)
                    answer += "" + str(date.diff_for_humans()) + ":\n" + str(log.text) + "\n\n"
                    counter += 1
                if answer != "":
                    update.message.reply_text(answer)
                else:
                    update.message.reply_text("Журнал пуст.")
                return True
            elif "/info" in _text:
                user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id).limit(1)
                if user_query.exists():
                    user_object = user_query.first()
                    rating_value = float(user_object.rating_plus / user_object.rating_minus)
                    bot.send_message(_chat_id, "Рейтинг " + get_username_or_name_sb(
                        _reply_user) + ": " + str("%.1f" % rating_value))
                return True
            elif _text in ("/sps", "/like"):
                if check_rate_flood(_user.id, _reply_user.id):
                    return True
                user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id).limit(1)
                if user_query.exists():
                    user_object = user_query.first()
                    user_object.rating_plus += 1
                    user_object.save()
                    bot.send_message(_chat_id, get_username_or_name(_user) + " → 🙂 → " + get_username_or_name(
                        _reply_user))
                try:
                    bot.delete_message(chat_id=_chat_id, message_id=_message.message_id)
                except Exception as e:
                    print("Permission: " + str(e))
                return True
            elif _text in ("/ban", "/dis"):
                if check_rate_flood(_user.id, _reply_user.id):
                    return True
                user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id).limit(1)
                if user_query.exists():
                    user_object = user_query.first()
                    user_object.rating_minus += 1
                    user_object.save()
                    bot.send_message(_chat_id, get_username_or_name(_user) + " → 😡 → " + get_username_or_name(
                        _reply_user))
                try:
                    bot.delete_message(chat_id=_chat_id, message_id=_message.message_id)
                except Exception as e:
                    print("Permission: " + str(e))
                return True

    except Exception as e:
        update.message.reply_text("Exception: " + str(e))
