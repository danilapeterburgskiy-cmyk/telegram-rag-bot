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
        self.chunks = [(chunk.text, chunk.page_id) for chunk in chunks if chunk.page_id]
        if self.chunks:
            print(f"✅ Загружено {len(self.chunks)} чанков из БД")

    def sync_pages_to_yandex(self):
        db = next(get_db())
        pages = db.query(Page).filter(Page.sync_status == 'pending').all()
        print(f"📚 Найдено {len(pages)} страниц для синхронизации")
        for page in pages:
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(page.content)
                    temp_path = f.name
                file = self.sdk.files.upload(
                    temp_path,
                    mime_type="text/plain",
                    ttl_days=7,
                    expiration_policy="static"
                )
                os.unlink(temp_path)
                page.file_id = file.id
                page.sync_status = 'synced'
                db.commit()
                print(f"  ✅ Синхронизировано: {page.title[:50]}")
            except Exception as e:
                page.sync_status = 'failed'
                db.commit()
                print(f"  ❌ Ошибка: {e}")

    def create_search_index_from_pages(self):
        db = next(get_db())
        pages = db.query(Page).filter(Page.file_id.isnot(None)).all()
        if not pages:
            print("⚠️ Нет страниц с file_id")
            return
        files = []
        for page in pages:
            try:
                file = self.sdk.files.get(page.file_id)
                files.append(file)
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
        if not files:
            print("❌ Нет доступных файлов")
            return
        index_type = TextSearchIndexType()
        operation = self.sdk.search_indexes.create_deferred(files, index_type=index_type)
        self.search_index = operation.wait()
        with open("index_id.txt", "w") as f:
            f.write(self.search_index.id)
        for page in pages:
            page.search_index_id = self.search_index.id
        db.commit()
        print(f"✅ Индекс создан: {self.search_index.id}")

    def ask(self, question: str, user_id: int = None) -> str:
        """Основной RAG — поиск по чанкам в БД + генерация через LLM"""
        if not self.chunks:
            return self._ask_gpt(question)
        
        # Поиск релевантных чанков
        question_words = set(re.sub(r'[^\w\s]', '', question.lower()).split())
        scored = []
        for text, page_id in self.chunks:
            chunk_words = set(re.sub(r'[^\w\s]', '', text.lower()).split())
            score = len(question_words.intersection(chunk_words))
            if score > 0:
                scored.append((score, text, page_id))
        scored.sort(key=lambda x: x[0], reverse=True)
        relevant = scored[:5]
        
        if not relevant:
            return self._ask_gpt(question)
        
        context = "\n\n---\n\n".join([text for _, text, _ in relevant])
        
        # Собираем источники
        db = next(get_db())
        sources = []
        for _, _, page_id in relevant:
            if page_id:
                page = db.query(Page).filter(Page.id == page_id).first()
                if page:
                    sources.append(page.url)
        
        prompt = f"""
Ты — эксперт по документации Bitrix24 API.
Ответь на вопрос, используя ТОЛЬКО информацию из контекста.
Если в контексте нет ответа — скажи: "В документации нет информации".
В конце ответа укажи источники: {', '.join(sources[:3]) if sources else 'документация Bitrix24'}

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

    def _ask_gpt(self, question: str) -> str:
        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(question)
            return response.text
        except Exception as e:
            return f"❌ Ошибка: {e}"
