import os

banned_words = ["@", "http", ".com", "казино", "выигр"]
thank_words = ["пасиб", "посиб", "спс", "благодар", "сэнкс", "сенкс", "дякую", "thanx", "thank"]
interest_words = os.environ.get("INTEREST", "рамиз").split(" ")

super_admin_ids = (76114490, 251521119)
info_kanal = "diobage"
log_chat_second = -268646012
