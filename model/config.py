import os
from peewee import *

embedded_database = False
init_bot_tables = True

banned_words = ["@", "http", ".com", "казино", "выигр"]
# Web hook
URL = os.environ.get("URL")
PORT = int(os.environ.get('PORT', '5000'))

# telegram
TOKEN = os.getenv("token")
ENV = os.environ.get("ENV", "dev")
_admin_id = 76114490
# Database

db_proxy = Proxy()
bot_database = None

if not embedded_database:
    print("Trying to use heroku-postgresql database")
    # bot_token = os.environ["token"]
    import urllib.parse
    import psycopg2

    urllib.parse.uses_netloc.append('postgres')
    url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
    bot_database = PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password, host=url.hostname,
                                      port=url.port, autocommit=True,
                                      autorollback=True)
else:
    print("Using local stored sqlite")
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    DATABASE = os.path.join(PROJECT_ROOT, 'db', 'people.sqlite')
    bot_database = SqliteDatabase(DATABASE)
    db_proxy.initialize(bot_database)
