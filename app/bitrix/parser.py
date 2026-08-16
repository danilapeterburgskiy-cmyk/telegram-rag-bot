import os
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app.db.db import get_db
from app.db.models import Page, Chunk

class BitrixParser:
    def __init__(self):
        self.driver = None

    def _setup_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)

    def parse_page(self, url):
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            body = self.driver.find_element(By.TAG_NAME, "body")
            text = body.text
            title = self.driver.title or url
            return title, text
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None, None

    def parse_and_save(self):
        self._setup_driver()
        urls = [
            "https://apidocs.bitrix24.ru/",
            "https://apidocs.bitrix24.ru/api-reference/",
            "https://apidocs.bitrix24.ru/api-reference/tasks/",
            "https://apidocs.bitrix24.ru/api-reference/crm/",
            "https://apidocs.bitrix24.ru/api-reference/user/",
        ]
        db = next(get_db())
        
        for url in urls:
            print(f"🔍 Парсим: {url}")
            title, content = self.parse_page(url)
            if content:
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                existing = db.query(Page).filter(Page.url == url).first()
                if existing:
                    existing.title = title
                    existing.content = content[:10000]
                    existing.content_hash = content_hash
                    existing.sync_status = 'pending'
                    db.commit()
                    page_id = existing.id
                    print(f"  🔄 Страница обновлена: {title[:50]}")
                else:
                    page = Page(
                        url=url,
                        title=title,
                        content=content[:10000],
                        content_hash=content_hash,
                        sync_status='pending'
                    )
                    db.add(page)
                    db.commit()
                    page_id = page.id
                    print(f"  ✅ Страница сохранена: {title[:50]}")
                
                # Сохраняем чанки
                chunk_size = 3000
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                for chunk_text in chunks:
                    chunk = Chunk(
                        page_id=page_id,
                        text=chunk_text,
                        file_id=None,
                        index_id=None
                    )
                    db.add(chunk)
                db.commit()
                print(f"  ✅ Сохранено {len(chunks)} чанков")
        
        self.driver.quit()
        print("✅ Парсинг завершён")
