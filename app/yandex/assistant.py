import os
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

    def ask(self, question: str) -> str:
        if not self.search_index:
            return self._ask_gpt(question)
        
        try:
            doc_path = "docs/bitrix_api.txt"
            if os.path.exists(doc_path):
                with open(doc_path, "r", encoding="utf-8") as f:
                    docs_text = f.read()
            else:
                return self._ask_gpt(question)
            
            # Улучшенный промпт
            prompt = f"""
Ты — эксперт по документации Bitrix24 REST API.
Твоя задача — отвечать на вопросы разработчиков, используя ТОЛЬКО информацию из документации.

Правила:
1. Отвечай чётко и по делу
2. Если вопрос про метод API — укажи название метода, параметры и пример
3. Если в документации нет ответа — скажи: "В документации нет информации по этому вопросу"
4. Не добавляй информацию, которой нет в документации
5. Если спрашивают про сайт — дай ссылку

Документация:
{docs_text[:20000]}

Вопрос: {question}

Ответ:"""
            
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(prompt)
            return response.text
            
        except Exception as e:
            print(f"⚠️ Ошибка RAG: {e}")
            return self._ask_gpt(question)

    def _ask_gpt(self, question: str) -> str:
        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(question)
            return response.text
        except Exception as e:
            return f"❌ Ошибка: {e}"

    # Кэш для ответов
    _cache = {}

    def ask_with_cache(self, question: str) -> str:
        """Кэширует ответы на повторяющиеся вопросы"""
        key = question.lower().strip()
        if key in self._cache:
            print("📦 Ответ из кэша")
            return self._cache[key]
        
        answer = self.ask(question)
        self._cache[key] = answer
        return answer
