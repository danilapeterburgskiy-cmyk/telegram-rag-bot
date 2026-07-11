import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.config import Config
from app.db.db import get_db
from app.db.crud import get_or_create_user, save_message, get_user_history, clear_user_history
from app.yandex.gpt_rest import YandexGPT
from app.yandex.speech import SpeechRecognizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        self.gpt = YandexGPT()
        self.speech = SpeechRecognizer()
        self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("history", self.history))
        self.app.add_handler(CommandHandler("clear", self.clear))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        self.app.add_error_handler(self.error_handler)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Ошибка: {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db = next(get_db())
        get_or_create_user(db, user.id, user.username)
        await update.message.reply_text(
            "👋 Привет! Я бот по документации Bitrix24 API.\n\n"
            "📌 Отправь вопрос текстом или голосом.\n"
            "📌 /history — последние вопросы\n"
            "📌 /clear — очистить историю"
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🆘 Команды:\n\n"
            "/start — приветствие\n"
            "/help — справка\n"
            "/history — последние вопросы\n"
            "/clear — очистить историю"
        )

    async def history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        db = next(get_db())
        messages = get_user_history(db, user.id, limit=5)
        if not messages:
            await update.message.reply_text("📭 История пуста")
            return
        text = "📜 Последние вопросы:\n\n"
        for msg in messages:
            text += f"❓ {msg.question[:50]}...\n"
        await update.message.reply_text(text)

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = str(user.id)
        
        # Очищаем историю в памяти бота
        if user_id in self.gpt.history:
            del self.gpt.history[user_id]
        
        # Очищаем историю в БД
        db = next(get_db())
        clear_user_history(db, user.id)
        
        await update.message.reply_text("🧹 История полностью очищена!")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        status_msg = await update.message.reply_text("🎤 Распознаю...")
        try:
            voice = await update.message.voice.get_file()
            voice_bytes = await voice.download_as_bytearray()
            text = self.speech.recognize(voice_bytes)
            if "❌" in text:
                await status_msg.delete()
                await update.message.reply_text(text)
                return
            await status_msg.delete()
            await update.message.reply_text(f"🎤 Вы сказали: {text}")
            user = update.effective_user
            user_id = str(user.id)
            answer = self.gpt.ask(text, user_id)
            db = next(get_db())
            db_user = get_or_create_user(db, user.id, user.username)
            save_message(db, db_user.id, text, answer)
            await update.message.reply_text(answer)
        except Exception as e:
            logger.error(f"❌ Ошибка голоса: {e}")
            await status_msg.delete()
            await update.message.reply_text("❌ Не удалось обработать голосовое.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        question = update.message.text
        user = update.effective_user
        user_id = str(user.id)
        logger.info(f"📩 Вопрос от {user.id}: {question[:50]}...")
        try:
            status_msg = await update.message.reply_text("🔍 Ищу ответ...")
            answer = self.gpt.ask(question, user_id)
            if not answer or len(answer.strip()) < 5:
                answer = "🤔 Не удалось сформулировать ответ."
            db = next(get_db())
            db_user = get_or_create_user(db, user.id, user.username)
            save_message(db, db_user.id, question, answer)
            await status_msg.delete()
            await update.message.reply_text(answer)
            logger.info("✅ Ответ отправлен")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")

    def run(self):
        print("🤖 Бот запущен!")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
