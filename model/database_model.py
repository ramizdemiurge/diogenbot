import logging

from peewee import *

from model.config import bot_database, init_bot_tables

db = bot_database

logger = logging.getLogger('peewee')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


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
    start_time = DateTimeField(null=True)
    autowipe_sec = IntegerField(default=0, null=False)

    class Meta:
        database = db


class Settings(Model):
    # id = IntegerField(primary_key=True)
    delete_messages = BooleanField(default=False)
    delete_messages_seconds = IntegerField(default=0)
    delete_stickers = BooleanField(default=False)
    delete_stickers_seconds = IntegerField(default=0)
    antibot_count = IntegerField(default=5)
    stickers_count = IntegerField(default=0)
    spylevel = SmallIntegerField(default=1)

    class Meta:
        database = db


class Groups(Model):
    # id = BigIntegerField(primary_key=True)
    chat_id = BigIntegerField(unique=True)
    settings = ForeignKeyField(Settings, related_name='settings')
    group_name = TextField(null=True)
    confirmed = BooleanField(null=False, default=False)

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
        print("Error creating database. Maybe it exists?")
        pass


if init_bot_tables:
    init_tables()
