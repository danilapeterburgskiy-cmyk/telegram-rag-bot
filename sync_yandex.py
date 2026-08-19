from app.yandex.assistant import YandexAssistant

def main():
    assistant = YandexAssistant()
    
    # 1. Синхронизация страниц
    print("🔄 Синхронизация страниц с Yandex File Storage...")
    assistant.sync_pages_to_yandex()
    
    # 2. Создание индекса из страниц
    print("\n🔍 Создание поискового индекса из страниц...")
    assistant.create_search_index_from_pages()
    
    print("\n✅ Синхронизация завершена!")

if __name__ == "__main__":
    main()
