from app.yandex.assistant import YandexAssistant

a = YandexAssistant()

if not a.search_index:
    print("❌ Индекс не загружен!")
    exit()

print(f"✅ Индекс загружен: {a.search_index.id}")

# Пробуем поискать
question = "crm"
print(f"\n🔍 Ищем: {question}")

try:
    # Пробуем разные методы
    if hasattr(a.search_index, 'query'):
        results = a.search_index.query(question, limit=3)
        print(f"✅ Метод query работает! Найдено: {len(results)}")
    elif hasattr(a.search_index, 'search'):
        results = a.search_index.search(question, limit=3)
        print(f"✅ Метод search работает! Найдено: {len(results)}")
    else:
        print("❌ Нет методов поиска!")
        print(f"Доступные методы: {[m for m in dir(a.search_index) if not m.startswith('_')]}")
except Exception as e:
    print(f"❌ Ошибка: {e}")
