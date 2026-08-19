import os
import re
import tempfile
from yandex_ai_studio_sdk import AIStudio
from yandex_ai_studio_sdk.search_indexes import TextSearchIndexType
from app.config import Config
from app.db.db import get_db
from app.db.models import Page, Chunk

class YandexAssistant:
    def __init__(self):
        self.sdk = AIStudio(
            folder_id=Config.YANDEX_FOLDER_ID,
            auth=Config.YANDEX_API_KEY
        )
        self.search_index = None
        self.chunks = []
        self._load_existing_index()
        self._load_chunks_from_db()

    def _load_existing_index(self):
        index_file = "index_id.txt"
        if os.path.exists(index_file):
            try:
                with open(index_file, "r") as f:
                    index_id = f.read().strip()
                if index_id:
                    self.search_index = self.sdk.search_indexes.get(index_id)
                    print(f"✅ Загружен индекс: {index_id}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки: {e}")

    def _load_chunks_from_db(self):
        db = next(get_db())
        chunks = db.query(Chunk).all()
        self.chunks = [chunk.text for chunk in chunks if chunk.text]
        if self.chunks:
            print(f"✅ Загружено {len(self.chunks)} чанков из БД")

    def ask(self, question: str, user_id: int = None) -> str:
        """RAG: передаём чанки в Yandex GPT, чтобы он сам нашёл ответ"""
        if not self.chunks:
            return self._ask_gpt(question)

        # Собираем все чанки в один большой текст
        full_docs = "\n\n---\n\n".join(self.chunks[:50])  # Ограничиваем, чтобы не перегружать

        prompt = f"""
Ты — эксперт по документации Bitrix24 REST API.
Ниже приведена документация Bitrix24. Найди в ней ответ на вопрос пользователя.
Если в документации нет ответа — скажи: "В документации нет информации".
В конце ответа укажи источники (URL страниц).

Документация:
{full_docs}

Вопрос: {question}

Ответ:"""

        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(prompt)
            return response.text
        except Exception as e:
            return f"❌ Ошибка LLM: {e}"

    def _ask_gpt(self, question: str) -> str:
        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(question)
            return response.text
        except Exception as e:
            return f"❌ Ошибка: {e}"
