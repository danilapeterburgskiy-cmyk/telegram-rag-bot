import os
import requests
from app.config import Config

class SpeechRecognizer:
    def __init__(self):
        self.api_key = Config.YANDEX_SPEECHKIT_API_KEY
        self.url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    def recognize(self, audio_bytes: bytes) -> str:
        """Распознаёт голосовое сообщение"""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "audio/ogg;codecs=opus"
        }
        
        try:
            response = requests.post(
                self.url,
                headers=headers,
                data=audio_bytes,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", "Не удалось распознать речь")
            else:
                return f"❌ Ошибка распознавания: {response.status_code}"
        except Exception as e:
            return f"❌ Ошибка: {e}"
