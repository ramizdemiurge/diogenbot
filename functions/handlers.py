import telegram


# def info_command_handler(bot, update):
#     _message = update.message
#     _chat_id = _message.chat.id
#     _user = _message.from_user
#     _text = _message.text
#     _text_array = _text.split()
#     if inbox(update):
#         pass
#     else:
#         user_query = User.select().where(User.user_id == _user.id, User.chat_id == _chat_id)
#         if user_query.exists():
#             user_object = user_query.first()
#             rating_value = float(user_object.rating_plus / user_object.rating_minus)
#             update.message.reply_text("Ваш рейтинг: " + str("%.1f" % rating_value))
#         return


def help_command_handler(bot, update):
    update.message.reply_text("Комманды: \n*/sps* - добавить рейтинг\n"
                              "*/ban* - отнять рейтинг\n"
                              "*/log* - журнал изменений юзера\n"
                              " */info* - информация юзера\n_(Все комманды, кроме /info, работают лишь в reply-сообщении в чате группы)_", parse_mode=telegram.ParseMode.MARKDOWN)
