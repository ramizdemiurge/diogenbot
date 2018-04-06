import datetime

from model.database_model import User, db
from model.lists import log_chat_second


class UserDAO:
    @staticmethod
    def get_all_users():
        return User.select()

    @staticmethod
    def get_by_uid_and_chit(uid, chid):
        user_query = User.select().where(User.chat_id == uid, User.user_id == chid).limit(1)
        if user_query.exists():
            return user_query.first()

    @staticmethod
    def increment_msg_count(user: User, bot):
        user_id = user.user_id
        chat_id = user.chat_id
        import time
        dt = datetime.datetime.now()
        timestamp = int((time.mktime(dt.timetuple()) + dt.microsecond / 1000000.0) * 1000)

        query = "UPDATE \"user\" SET messages_count = messages_count + 1, last_activity = now()  WHERE user_id = {} AND chat_id = {}" \
            .format(user_id, chat_id)
        try:
            db.execute_sql(query)
            db.close()
        except Exception as e:
            bot.send_message(log_chat_second, "Error: " + str(e)+"\nQuery: "+query)
