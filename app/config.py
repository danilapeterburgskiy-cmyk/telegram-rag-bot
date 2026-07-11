import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    YANDEX_SPEECHKIT_API_KEY = os.getenv("YANDEX_SPEECHKIT_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")

    @classmethod
    def check(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден")
        if not cls.YANDEX_FOLDER_ID:
            raise ValueError("❌ YANDEX_FOLDER_ID не найден")
        if not cls.YANDEX_API_KEY:
            raise ValueError("❌ YANDEX_API_KEY не найден")
        if not cls.YANDEX_SPEECHKIT_API_KEY:
            raise ValueError("❌ YANDEX_SPEECHKIT_API_KEY не найден")
        print("✅ Все переменные загружены")
