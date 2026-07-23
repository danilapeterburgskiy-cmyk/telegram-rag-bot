from app.config import Config
from app.db.db import init_db
from app.handlers.handlers import TelegramBot

def main():
    Config.check()
    init_db()
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()
