import os
import time
from app.yandex.assistant import YandexAssistant

def main():
    assistant = YandexAssistant()
    
    # Собираем все части
    parts = []
    docs_dir = 'docs'
    
    # Все части от aa до ap
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
    print('🔄 Загрузка в Yandex Cloud...')
    print('⏳ Это может занять 5-10 минут...\n')
    
    # Загружаем все части в один индекс
    assistant.create_search_index(parts)
    
    print(f'\n✅ Индекс создан!')
    print(f'📌 ID индекса: {assistant.search_index.id}')

if __name__ == '__main__':
    main()
