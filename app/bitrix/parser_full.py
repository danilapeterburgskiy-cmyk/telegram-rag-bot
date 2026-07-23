import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse

class BitrixParserFull:
    def __init__(self, docs_dir="docs"):
        self.docs_dir = docs_dir
        os.makedirs(docs_dir, exist_ok=True)
        self.visited = set()
        self.all_text = ""
        self.base_url = "https://apidocs.bitrix24.ru/"

    def get_links(self, url):
        """Извлекает все ссылки со страницы"""
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Преобразуем относительные ссылки в абсолютные
                full_url = urljoin(self.base_url, href)
                
                # Только ссылки на apidocs.bitrix24.ru
                if 'apidocs.bitrix24.ru' in full_url:
                    # Убираем якоря
                    full_url = full_url.split('#')[0]
                    if full_url not in self.visited and full_url != url:
                        links.append(full_url)
            
            return links
        except Exception as e:
            print(f"  ❌ Ошибка получения ссылок: {e}")
            return []

    def parse_page(self, url):
        """Парсит страницу и добавляет текст"""
        if url in self.visited:
            return
        
        self.visited.add(url)
        
        try:
            print(f"📄 Парсим: {url}")
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Убираем скрипты, стили, навигацию
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            
            # Получаем текст
            text = soup.get_text(separator="\n")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            page_text = "\n".join(lines)
            
            if page_text:
                self.all_text += f"\n\n=== {url} ===\n\n"
                self.all_text += page_text
                self.all_text += "\n\n" + "=" * 80 + "\n"
                print(f"  ✅ Получено {len(page_text)} символов")
            
            # Получаем новые ссылки и рекурсивно обходим
            links = self.get_links(url)
            print(f"  🔗 Найдено ссылок: {len(links)}")
            
            time.sleep(0.5)  # Задержка
            
            for link in links:
                self.parse_page(link)
                
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

    def parse_all(self):
        """Запускает рекурсивный парсинг"""
        print("🚀 Начинаем рекурсивный парсинг всего сайта...")
        print(f"📍 Старт: {self.base_url}")
        
        self.parse_page(self.base_url)
        
        # Сохраняем всё
        if self.all_text:
            output_file = f"{self.docs_dir}/bitrix_api_full.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(self.all_text)
            print(f"\n✅ Документация сохранена: {output_file}")
            print(f"   Всего страниц: {len(self.visited)}")
            print(f"   Размер: {len(self.all_text)} символов")
        else:
            print("❌ Не удалось получить документацию")
