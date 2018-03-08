import os

from peewee import *

from methods.configs import bot_static_token

heroku = False
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
DATABASE = os.path.join(PROJECT_ROOT, 'db', 'people.sqlite')
db3 = SqliteDatabase(DATABASE)
db_proxy = Proxy()

# import logging
# logger = logging.getLogger('peewee')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

bot_token = None
if heroku:
    bot_token = os.environ["token"]
    print("Trying to use heroku-postgresql database")
    import urllib.parse, psycopg2

    urllib.parse.uses_netloc.append('postgres')
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    db = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname,
                            port=url.port, autocommit=True,
                            autorollback=True)
else:
    bot_token = bot_static_token
    print("Using local stored sqlite")
    db = db3
    db_proxy.initialize(db)


class UserLogs(Model):
    # id = IntegerField(primary_key=True)
    user_id = BigIntegerField(unique=False)
    chat_id = BigIntegerField(unique=False)
    text = TextField(null=True)
    date = DateTimeField()

    class Meta:
        database = db


class User(Model):
    # id = IntegerField(primary_key=True, unique=True)
    user_id = BigIntegerField(unique=False)
    messages_count = IntegerField(default=0)
    t_username = TextField(null=True)
    first_name = TextField(null=False)
    last_name = TextField(null=True)
    chat_id = BigIntegerField(unique=False)
    changes_count = IntegerField(default=0)
    rating_plus = IntegerField(default=1)
    rating_minus = IntegerField(default=1)
    warns = IntegerField(default=0)
    last_activity = DateTimeField()

    class Meta:
        database = db


class Settings(Model):
    # id = IntegerField(primary_key=True)
    delete_messages = BooleanField(default=False)
    delete_messages_seconds = IntegerField(default=2)
    delete_stickers = BooleanField(default=False)
    delete_stickers_seconds = IntegerField(default=2)
    antibot_count = IntegerField(default=5)
    stickers_count = IntegerField(default=0)

    class Meta:
        database = db


class Groups(Model):
    # id = BigIntegerField(primary_key=True)
    chat_id = BigIntegerField(unique=True)
    settings = ForeignKeyField(Settings, related_name='settings')
    group_name = TextField(null=True)

    class Meta:
        database = db


class AdminList(Model):
    # id = IntegerField(primary_key=True)
    user_id = BigIntegerField()
    group_id = BigIntegerField()

    class Meta:
        database = db


def init_tables():
    try:
        UserLogs.create_table()
        User.create_table()
        Settings.create_table()
        Groups.create_table()
        AdminList.create_table()
    except Exception:
        pass


init_tables()
