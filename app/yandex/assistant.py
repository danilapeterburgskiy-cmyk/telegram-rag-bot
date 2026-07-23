import os
import json
from yandex_ai_studio_sdk import AIStudio
from app.config import Config

class YandexAssistant:
    def __init__(self):
        self.sdk = AIStudio(
            folder_id=Config.YANDEX_FOLDER_ID,
            auth=Config.YANDEX_API_KEY
        )
        self.search_index = None
        self._load_existing_index()

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
                print(f"⚠️ Ошибка загрузки индекса: {e}")

    def create_search_index(self, file_paths):
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
            *files,
            index_type=index_type
        )
        self.search_index = operation.wait()
        
        with open("index_id.txt", "w") as f:
            f.write(self.search_index.id)
        print(f"✅ Индекс создан: {self.search_index.id}")

    def search(self, question: str, limit: int = 5):
        """Поиск по индексу"""
        if not self.search_index:
            return []
        
        try:
            if hasattr(self.search_index, 'query'):
                return self.search_index.query(question, limit=limit)
            elif hasattr(self.search_index, 'search'):
                return self.search_index.search(question, limit=limit)
            elif hasattr(self.search_index, 'find'):
                return self.search_index.find(question, limit=limit)
            else:
                return []
        except Exception as e:
            print(f"⚠️ Ошибка поиска: {e}")
            return []

    def ask_with_index(self, question: str) -> str:
        """Поиск по индексу + генерация ответа через Yandex GPT"""
        if not self.search_index:
            return None
        
        results = self.search(question)
        if not results:
            return None
        
        context = "\n\n---\n\n".join([r.text for r in results])
        
        prompt = f"""
Ты — эксперт по документации Bitrix24 API.
Ответь на вопрос, используя ТОЛЬКО контекст.

Контекст:
{context}

Вопрос: {question}

Ответ:"""
        
        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(prompt)
            return response.text
        except Exception as e:
            print(f"⚠️ Ошибка генерации: {e}")
            return None
