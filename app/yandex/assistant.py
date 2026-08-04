import os
import re
from yandex_ai_studio_sdk import AIStudio
from app.config import Config
from app.db.db import get_db
from app.db.models import Chunk

class YandexAssistant:
    def __init__(self):
        self.sdk = AIStudio(
            folder_id=Config.YANDEX_FOLDER_ID,
            auth=Config.YANDEX_API_KEY
        )
        self.docs_path = "docs/bitrix_api_full.txt"
        self._load_chunks_from_db()

    def _load_chunks_from_db(self):
        """Загружает чанки из БД"""
        db = next(get_db())
        self.chunks = [chunk.text for chunk in db.query(Chunk).all()]
        if self.chunks:
            print(f"✅ Загружено {len(self.chunks)} чанков из БД")

    def _chunk_text(self, text: str, chunk_size: int = 3000) -> list:
        words = text.split()
        chunks, current, size = [], [], 0
        for word in words:
            current.append(word)
            size += len(word) + 1
            if size >= chunk_size:
                chunks.append(" ".join(current))
                current, size = [], 0
        if current:
            chunks.append(" ".join(current))
        return chunks

    def _search_relevant_chunks(self, question: str, top_k: int = 5) -> list:
        """Ищет релевантные чанки по ключевым словам"""
        if not self.chunks:
            return []
        
        question_words = set(re.sub(r'[^\w\s]', '', question.lower()).split())
        scored = []
        for chunk in self.chunks:
            chunk_words = set(re.sub(r'[^\w\s]', '', chunk.lower()).split())
            score = len(question_words.intersection(chunk_words))
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def ask(self, question: str) -> str:
        """RAG с локальным поиском и генерацией через LLM"""
        # Если чанков нет в БД — загружаем из файла
        if not self.chunks:
            if not os.path.exists(self.docs_path):
                return "❌ Документация не найдена"
            with open(self.docs_path, "r", encoding="utf-8") as f:
                text = f.read()
            self.chunks = self._chunk_text(text, 3000)
            print(f"📚 Загружено {len(self.chunks)} чанков из файла")
        
        relevant = self._search_relevant_chunks(question, 5)
        
        if not relevant:
            return "❌ Не нашёл информации по вашему вопросу."
        
        context = "\n\n---\n\n".join(relevant)
        
        prompt = f"""
Ты — эксперт по документации Bitrix24 API.
Ответь на вопрос, используя ТОЛЬКО информацию из контекста.
Если в контексте нет ответа — скажи: "В документации нет информации".

Контекст:
{context}

Вопрос: {question}

Ответ:"""
        
        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(prompt)
            return response.text
        except Exception as e:
            return f"❌ Ошибка LLM: {e}"
