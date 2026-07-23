from app.yandex.assistant import YandexAssistant
from app.config import Config

a = YandexAssistant()

if not a.search_index:
    print("❌ Индекс не загружен")
    exit()

print(f"✅ Индекс: {a.search_index.id}")

# Пробуем создать ассистента с этим индексом
try:
    from yandex_ai_studio_sdk import AIStudio
    sdk = AIStudio(
        folder_id=Config.YANDEX_FOLDER_ID,
        auth=Config.YANDEX_API_KEY
    )
    
    tool = sdk.tools.search_index(a.search_index)
    assistant = sdk.assistants.create(
        'yandexgpt-lite',
        tools=[tool],
        temperature=0.3
    )
    print("✅ Ассистент создан!")
    
    thread = sdk.threads.create()
    thread.write("Что такое crm в Bitrix24?")
    run = assistant.run(thread)
    result = run.wait()
    print(f"🤖 Ответ: {result.text}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
