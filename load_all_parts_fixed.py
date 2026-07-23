import os
import time
from yandex_ai_studio_sdk.search_indexes import TextSearchIndexType
from app.yandex.assistant import YandexAssistant

def main():
    assistant = YandexAssistant()
    
    # Собираем все части
    parts = []
    docs_dir = 'docs'
    
    for suffix in ['aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 
                   'ai', 'aj', 'ak', 'al', 'am', 'an', 'ao', 'ap']:
        part_file = f'{docs_dir}/bitrix_part_{suffix}.txt'
        if os.path.exists(part_file):
            parts.append(part_file)
            size_mb = os.path.getsize(part_file) / 1024 / 1024
            print(f'📄 Часть {suffix}: {size_mb:.1f} МБ')
    
    if not parts:
        print('❌ Части не найдены')
        return
    
    print(f'\n📚 Всего частей: {len(parts)}')
    print('🔄 Загрузка файлов в Yandex Cloud...\n')
    
    # Загружаем все файлы
    loaded_files = []
    for i, part_path in enumerate(parts):
        print(f'  📤 Загрузка части {i+1}/{len(parts)}: {os.path.basename(part_path)}')
        try:
            uploaded_file = assistant.sdk.files.upload(
                part_path,
                mime_type="text/plain",
                ttl_days=7,
                expiration_policy="static"
            )
            loaded_files.append(uploaded_file)
            print(f'    ✅ Часть {i+1} загружена')
        except Exception as e:
            print(f'    ❌ Ошибка: {e}')
    
    if not loaded_files:
        print('❌ Не удалось загрузить ни один файл.')
        return
    
    print(f'\n✅ Загружено {len(loaded_files)} файлов.')
    print('🔍 Создание поискового индекса...')
    
    # ✅ ПРАВИЛЬНО: передаём список файлов
    index_type = TextSearchIndexType()
    operation = assistant.sdk.search_indexes.create_deferred(
        loaded_files,  # ← список, а не отдельные аргументы
        index_type=index_type
    )
    assistant.search_index = operation.wait()
    
    # Сохраняем ID индекса
    with open("index_id.txt", "w") as f:
        f.write(assistant.search_index.id)
    
    print(f'\n✅ Индекс создан!')
    print(f'📌 ID индекса: {assistant.search_index.id}')

if __name__ == '__main__':
    main()
