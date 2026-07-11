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
                "temperature": 0.5,
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
        """Определяет, относится ли вопрос к Bitrix24 API"""
        keywords = [
            'bitrix', 'задач', 'task', 'crm', 'сделка', 'лид', 'контакт',
            'api', 'rest', 'метод', 'параметр', 'токен', 'авторизаци',
            'webhook', 'хук', 'событие', 'поле', 'фильтр', 'сортировка'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in keywords)

    def ask(self, question: str, user_id: str = None) -> str:
        docs_text = ""
        doc_path = "docs/bitrix_api.txt"
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                docs_text = f.read()
        
        context = ""
        if user_id and user_id in self.history:
            last_q, last_a = self.history[user_id]
            context = f"Предыдущий вопрос: {last_q}\nПредыдущий ответ: {last_a}\n\n"
        
        # Если вопрос НЕ про Bitrix24 — сразу отвечаем как нейросеть
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

        # Если вопрос про Bitrix24 — ищем в документации
        if docs_text:
            prompt = f"""
Ты — эксперт по документации Bitrix24 REST API.

Инструкция:
1. Проверь, есть ли в документации ответ на вопрос.
2. Если есть — используй ТОЛЬКО информацию из документации.
3. Если нет — ответь как нейросеть, но скажи, что в документации этого нет.

{context}

Документация:
{docs_text[:20000]}

Вопрос: {question}

Ответ:"""
        else:
            prompt = f"""
Ты — ассистент. Отвечай на вопрос.

{context}

Вопрос: {question}

Ответ:"""
        
        answer = self._call_gpt(prompt)
        
        if not answer:
            # Если не удалось получить ответ — нейросеть
            fallback_prompt = f"""
Ты — дружелюбный ассистент. Отвечай на вопрос.

Вопрос: {question}

Ответ:"""
            answer = self._call_gpt(fallback_prompt) or "❌ Не удалось получить ответ."
        
        if user_id and answer:
            self.history[user_id] = (question, answer)
        
        return answer
