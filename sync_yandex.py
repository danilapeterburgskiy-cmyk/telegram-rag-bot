from app.yandex.assistant import YandexAssistant

def main():
    assistant = YandexAssistant()
    assistant.sync_pages_to_yandex()
    assistant.create_search_index_from_pages()
    print("✅ Синхронизация завершена!")

if __name__ == "__main__":
    main()
