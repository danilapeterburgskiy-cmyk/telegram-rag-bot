import os
import re
from app.config import Config
from yandex_ai_studio_sdk import AIStudio

class YandexAssistant:
    def __init__(self):
        self.sdk = AIStudio(
            folder_id=Config.YANDEX_FOLDER_ID,
            auth=Config.YANDEX_API_KEY
        )
        self.search_index = None
        self._load_existing_index()

    def _load_existing_index(self):
        """Загружает индекс (для совместимости, но не используется)"""
        index_file = "index_id.txt"
        if os.path.exists(index_file):
            try:
                with open(index_file, "r") as f:
                    index_id = f.read().strip()
                if index_id:
                    self.search_index = self.sdk.search_indexes.get(index_id)
                    print(f"✅ Загружен индекс: {index_id}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки индекса: {e}")

    def create_search_index(self, file_paths):
        """Создание индекса (для совместимости)"""
        print("📚 Загрузка файлов в Yandex Cloud...")
        files = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                file = self.sdk.files.upload(
                    file_path,
                    ttl_days=7,
                    expiration_policy="static"
                )
                files.append(file)
                print(f"  ✅ Загружен: {os.path.basename(file_path)}")
        
        if not files:
            print("⚠️ Нет файлов для загрузки")
            return
        
        print("🔍 Создание поискового индекса...")
        from yandex_ai_studio_sdk.search_indexes import TextSearchIndexType
        index_type = TextSearchIndexType()
        operation = self.sdk.search_indexes.create_deferred(
            files,
            index_type=index_type
        )
        self.search_index = operation.wait()
        
        with open("index_id.txt", "w") as f:
            f.write(self.search_index.id)
        print(f"✅ Индекс создан: {self.search_index.id}")

    def _chunk_text(self, text: str, chunk_size: int = 3000) -> list:
        """Разбивает текст на чанки"""
        words = text.split()
        chunks = []
        current = []
        size = 0
        
        for word in words:
            current.append(word)
            size += len(word) + 1
            if size >= chunk_size:
                chunks.append(" ".join(current))
                current = []
                size = 0
        
        if current:
            chunks.append(" ".join(current))
        return chunks

    def _search_relevant_chunks(self, question: str, chunks: list, top_k: int = 5) -> list:
        """Ищет релевантные чанки по ключевым словам"""
        question_words = set(re.sub(r'[^\w\s]', '', question.lower()).split())
        scored = []
        
        for chunk in chunks:
            chunk_words = set(re.sub(r'[^\w\s]', '', chunk.lower()).split())
            score = len(question_words.intersection(chunk_words))
            if score > 0:
                scored.append((score, chunk))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def ask_with_index(self, question: str) -> str:
        """Локальный RAG: поиск по файлу + генерация через GPT"""
        doc_path = "docs/bitrix_api_full.txt"
        if not os.path.exists(doc_path):
            print("⚠️ Файл документации не найден")
            return None
        
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"⚠️ Ошибка чтения: {e}")
            return None
        
        # Разбиваем на чанки
        chunks = self._chunk_text(text, chunk_size=3000)
        print(f"📚 Создано {len(chunks)} чанков")
        
        # Ищем релевантные
        relevant = self._search_relevant_chunks(question, chunks, top_k=5)
        print(f"🔍 Найдено {len(relevant)} релевантных чанков")
        
        if not relevant:
            return None
        
        context = "\n\n---\n\n".join(relevant)
        
        prompt = f"""
Ты — эксперт по документации Bitrix24 REST API.
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
            print(f"⚠️ Ошибка GPT: {e}")
            return None
