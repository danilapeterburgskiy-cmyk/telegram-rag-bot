from app.yandex.assistant import YandexAssistant

a = YandexAssistant()
answer = a.ask_with_index("Какие методы есть в CRM?")
print(f"🤖 Ответ:\n{answer}")
