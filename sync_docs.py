#!/usr/bin/env python3
"""Скрипт для синхронизации документации с Yandex Cloud"""
import os
import sys
from app.yandex.assistant import YandexAssistant

def main():
    # Проверяем, что файл документации существует
    doc_file = "docs/bitrix_api_full.txt"
    if not os.path.exists(doc_file):
        print(f"❌ Файл {doc_file} не найден!")
        sys.exit(1)
    
    print("🔄 Синхронизация документации с Yandex Cloud...")
    
    assistant = YandexAssistant()
    
    # Создаём индекс из полной документации
    assistant.create_search_index([doc_file])
    
    print("✅ Синхронизация завершена!")
    print(f"📄 Индекс: {assistant.search_index.id if assistant.search_index else 'не создан'}")

if __name__ == "__main__":
    main()
