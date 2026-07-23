import os
import time
from app.yandex.assistant import YandexAssistant

def main():
    assistant = YandexAssistant()
    
    # Собираем все части
    parts = []
    docs_dir = "docs"
    for i in range(1, 20):
        part_file = f"{docs_dir}/bitrix_part_{i}.txt"
        if os.path.exists(part_file):
            parts.append(part_file)
            print(f"📄 Найдена часть {i}: {part_file} ({os.path.getsize(part_file) / 1024 / 1024:.1f} МБ)")
    
    if not parts:
        print("❌ Части не найдены")
        return
    
    print(f"\n📚 Всего найдено частей: {len(parts)}")
    print("🔄 Загрузка частей в Yandex Cloud...")
    
    # Загружаем каждую часть по отдельности
    for i, part in enumerate(parts):
        print(f"  📤 Загрузка части {i+1}/{len(parts)}: {os.path.basename(part)}")
        try:
            assistant.create_search_index([part])
            print(f"    ✅ Часть {i+1} загружена")
            time.sleep(2)
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            break
    
    print("\n✅ Загрузка завершена!")
    print(f"📌 ID индекса: {assistant.search_index.id if assistant.search_index else 'не создан'}")

if __name__ == "__main__":
    main()
