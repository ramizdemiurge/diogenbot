# from telegram import User
import datetime

from Model import AdminList, Groups, Settings, UserLogs, User
from methods.djaler_utils import get_username_or_name, get_username_or_name_sb

banned_words = ["@", "http", ".com", "казино", "выигр"]


def spam_cheker(message):
    for x in banned_words:
        if x in message:
            return True
    return False


# user_from_db - peewee class | user_new - telegram class
def changes_detector(user_from_db, update, bot):
    _user = update.message.from_user
    _chat_id = update.message.chat.id
    status = False
    log_string = ""

    if _user.username:
        if user_from_db.t_username != _user.username:
            status = True
            log_string += "Username: " + user_from_db.t_username + " => " + _user.username + ","
            user_from_db.t_username = _user.username
    if _user.first_name:
        if user_from_db.first_name != _user.first_name:
            status = True
            log_string += " First name: " + user_from_db.first_name + " => " + _user.first_name + ","
            user_from_db.first_name = _user.first_name
    if _user.last_name:
        if user_from_db.last_name != _user.last_name:
            status = True
            log_string += " Last name: " + user_from_db.last_name + " => " + _user.last_name + ","
            user_from_db.last_name = _user.last_name

    if status:
        log_string = log_string.strip()[:-1]
        user_from_db.changes_count += 1
        user_from_db.save()
        UserLogs.create(user_id=_user.id, chat_id=_chat_id, text=log_string, date=datetime.datetime.now())
        if update.message:
            update.message.reply_text("Изменения:\n" + log_string)


def admin_method(bot, update, settings):
    _chat_id = update.message.chat.id
    _user = update.message.from_user

    try:
        if update.message.text:
            if update.message.reply_to_message is None:
                pass
            else:
                text = update.message.text
                _reply_user = update.message.reply_to_message.from_user
                if text == "/warn":
                    user_query = User.select().where(User.chat_id == _chat_id, User.user_id == _reply_user.id)
                    if user_query.exists():
                        user_object = user_query.first()
                        user_object.warns += 1
                        user_object.save()
                        bot.send_message(_chat_id, get_username_or_name_sb(_reply_user) + " выполнено предупреждение."
                                                                                          " (" + str(
                            user_object.warns) + "/" + "5)")

        if update.message.text:
            text = update.message.text
            text_array = text.split()
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
    except Exception:
        update.message.reply_text("Exception. Do your best.")


def super_admin_method(bot, update):
    if update.message.text:
        _chat_id = update.message.chat.id
        _user = update.message.from_user
        _text = update.message.text
        _text_array = _text.split()

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
                elif _text_array[0] == "/reg_chat":
                    _settings = Settings.create()
                    Groups.create(group_name=_text_array[1], chat_id=_chat_id, settings=_settings, force_insert=True)
            # if len(_text_array) >= 3:
            #     pass
            else:
                if _text == "/chats":
                    pass
                if _text == "/reg_chat":
                    group_query = Groups.select().where(Groups.chat_id == _chat_id)
                    if not group_query.exists():
                        _settings = Settings.create()
                        Groups.create(chat_id=_chat_id, settings=_settings, force_insert=True)
                        update.message.reply_text("Чат был зарегистрирован.")
                    else:
                        update.message.reply_text("Чат уже зарегистрирован.")
                if _text == "/del_chat":
                    group_query = Groups.select().where(Groups.chat_id == _chat_id)
                    if group_query.exists():
                        group = group_query.first()
                        group.delete_instance()
                        update.message.reply_text("Чат был удален.")
                    else:
                        update.message.reply_text("Этот чат не зарегистрирован.")


        except FileExistsError:
            update.message.reply_text("Exception. Do your best.")


def user_cmds(user, update, text):
    _chat_id = update.message.chat.id
    _user = update.message.from_user
    _text = update.message.text
    _text_array = _text.split()
    try:
        if len(_text_array) >= 2:
            pass
        else:
            if _text == "/stats":
                rating_value = float(user.rating_plus / user.rating_minus)
                answer = "Сообщений: " + str(user.messages_count) + ", изменений в профиле: " + str(
                    user.changes_count) + ", идентификатор: " + str(_user.id) + ", чат: " + str(
                    _chat_id) + ", рейтинг: " + \
                         str("%.2f" % rating_value)
                update.message.reply_text(answer)
        pass
    except Exception:
        update.message.reply_text("Exception. Do your best.")
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
                counter = 1
                for log in UserLogs.select().order_by(UserLogs.date.desc()).dicts() \
                        .where(UserLogs.user_id == _reply_user.id, UserLogs.chat_id == _chat_id):
                    if counter > 5:
                        break
                    date = datetime.datetime.fromtimestamp(log['date'] / 1e3)
                    answer += str(counter) + ") " + str(log['text']) + " [" + str(date) + "]" + "\n"
                    counter += 1
                if answer != "":
                    update.message.reply_text(answer)
                else:
                    update.message.reply_text("Журнал пуст.")
                return True
            elif _text == "/info":
                user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id)
                if user_query.exists():
                    user_object = user_query.first()
                    rating_value = float(user_object.rating_plus / user_object.rating_minus)
                    bot.send_message(_chat_id, "Рейтинг " + get_username_or_name_sb(
                        _reply_user) + ": " + str("%.2f" % rating_value))
                return True
            elif _text == "/sps":
                if _reply_user.id == _user.id:
                    return True
                user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id)
                if user_query.exists():
                    user_object = user_query.first()
                    user_object.rating_plus += 1
                    user_object.save()
                    try:
                        bot.delete_message(chat_id=_chat_id, message_id=_message.message_id)
                    except Exception:
                        pass
                    bot.send_message(_chat_id,
                                     get_username_or_name(_user) + " поблагодарил " + get_username_or_name(
                                         _reply_user))
                return True
            elif _text == "/ban":
                if _reply_user.id == _user.id:
                    return True
                user_query = User.select().where(User.user_id == _reply_user.id, User.chat_id == _chat_id)
                if user_query.exists():
                    user_object = user_query.first()
                    user_object.rating_minus += 1
                    user_object.save()
                    try:
                        bot.delete_message(chat_id=_chat_id, message_id=_message.message_id)
                    except Exception:
                        pass
                    bot.send_message(_chat_id,
                                     get_username_or_name(_user) + " поругал " + get_username_or_name(
                                         _reply_user))
                return True

    except FileExistsError:
        update.message.reply_text("Exception. Do your best.")
