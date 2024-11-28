import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "asjdnjsbfvsdhbsjfb")

DATABASE = os.getenv("DB_NAME", "example.db")
