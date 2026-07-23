import os
import requests
import json
import time
import re
from app.config import Config

class YandexGPT:
    def __init__(self):
        self.folder_id = Config.YANDEX_FOLDER_ID
        self.api_key = Config.YANDEX_API_KEY
        self.history = {}
        # Инициализируем SDK для _ask_gpt
        from yandex_ai_studio_sdk import AIStudio
        self.sdk = AIStudio(
            folder_id=self.folder_id,
            auth=self.api_key
        )

    def _call_gpt(self, prompt: str, retries: int = 3) -> str:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 1000
            },
            "messages": [{"role": "user", "text": prompt}]
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    return response.json()["result"]["alternatives"][0]["message"]["text"]
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
            except requests.exceptions.ConnectionError:
                print(f"⚠️ Ошибка подключения (попытка {attempt+1}/{retries})")
                time.sleep(2 ** attempt)
            except Exception as e:
                print(f"⚠️ Ошибка: {e}")
                time.sleep(2 ** attempt)
        
        return None

    def _is_bitrix_question(self, question: str) -> bool:
        keywords = [
            'bitrix', 'задач', 'task', 'crm', 'сделка', 'лид', 'контакт',
            'api', 'rest', 'метод', 'параметр', 'токен', 'авторизаци',
            'webhook', 'хук', 'событие', 'поле', 'фильтр', 'сортировка'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in keywords)

    def _load_docs(self):
        doc_path = "docs/bitrix_api_full.txt"
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                return f.read()
        doc_path = "docs/bitrix_api.txt"
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def _chunk_text(self, text: str, chunk_size: int = 3000) -> list:
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def _search_relevant_chunks(self, question: str, chunks: list, top_k: int = 3) -> list:
        question_words = set(question.lower().split())
        scored_chunks = []
        
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            score = len(question_words.intersection(chunk_words))
            if score > 0:
                scored_chunks.append((score, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:top_k]]

    def ask(self, question: str, user_id: str = None) -> str:
        docs_text = self._load_docs()
        
        context = ""
        if user_id and user_id in self.history:
            last_q, last_a = self.history[user_id]
            context = f"Предыдущий вопрос: {last_q}\nПредыдущий ответ: {last_a}\n\n"
        
        if not self._is_bitrix_question(question) and docs_text:
            prompt = f"""
Ты — дружелюбный ассистент. Отвечай на вопрос человека.

{context}

Вопрос: {question}

Ответ:"""
            answer = self._call_gpt(prompt)
            if answer:
                if user_id:
                    self.history[user_id] = (question, answer)
                return answer
            return "🤔 Не удалось сформулировать ответ."

        if docs_text:
            chunks = self._chunk_text(docs_text, chunk_size=3000)
            relevant_chunks = self._search_relevant_chunks(question, chunks, top_k=3)
            
            if relevant_chunks:
                context_docs = "\n\n---\n\n".join(relevant_chunks)
                
                prompt = f"""
Ты — эксперт по документации Bitrix24 REST API.

Инструкция:
1. Используй ТОЛЬКО информацию из контекста для ответа.
2. Если в контексте нет ответа — скажи: "В документации нет информации".
3. Отвечай чётко, указывай названия методов и параметры.

Контекст из документации:
{context_docs}

{context}

Вопрос: {question}

Ответ:"""
            else:
                return self._ask_gpt(question)
        else:
            return self._ask_gpt(question)
        
        answer = self._call_gpt(prompt)
        
        if not answer:
            answer = self._ask_gpt(question)
        
        if user_id and answer:
            self.history[user_id] = (question, answer)
        
        return answer

    def _ask_gpt(self, question: str) -> str:
        try:
            model = self.sdk.models.completions('yandexgpt-lite')
            response = model.run(question)
            return response.text
        except Exception as e:
            return f"❌ Ошибка: {e}"
