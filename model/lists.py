import os

banned_words = ["@", "http", ".com", "казино", "выигр"]
thank_words = ["пасиб", "посиб", "спс", "благодар", "сэнкс", "сенкс", "дякую", "thanx", "thank"]
interest_words = os.environ.get("INTEREST", "рамиз").split(" ")


