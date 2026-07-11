import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

class BitrixParser:
    def __init__(self, docs_dir="docs"):
        self.docs_dir = docs_dir
        os.makedirs(docs_dir, exist_ok=True)
        self.driver = None

    def _setup_driver(self):
        print("🚀 Запуск Chrome...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        print("✅ Chrome запущен")

    def parse_page(self, url):
        print(f"🔍 Парсим: {url}")
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            body = self.driver.find_element(By.TAG_NAME, "body")
            text = body.text
            print(f"  ✅ Получено {len(text)} символов")
            return text
        except TimeoutException:
            print(f"  ⏰ Таймаут")
            return ""
        except Exception as e:
            print(f"  ❌ {e}")
            return ""

    def parse_bitrix_docs(self):
        try:
            self._setup_driver()
        except Exception as e:
            print(f"❌ Ошибка запуска Chrome: {e}")
            return
        
        # Расширенный список URL
        urls = [
            "https://apidocs.bitrix24.ru/",
            "https://apidocs.bitrix24.ru/api-reference/",
            "https://apidocs.bitrix24.ru/api-reference/tasks/",
            "https://apidocs.bitrix24.ru/api-reference/crm/",
            "https://apidocs.bitrix24.ru/api-reference/user/",
            "https://apidocs.bitrix24.ru/api-reference/rest/",
            "https://apidocs.bitrix24.ru/api-reference/rest/scope/",
            "https://apidocs.bitrix24.ru/api-reference/rest/methods/",
        ]
        
        all_text = ""
        for url in urls:
            text = self.parse_page(url)
            if text:
                all_text += f"\n\n=== {url} ===\n\n{text}\n\n"
            time.sleep(1)
        
        self.driver.quit()
        
        if all_text:
            with open(f"{self.docs_dir}/bitrix_api.txt", "w", encoding="utf-8") as f:
                f.write(all_text)
            print(f"✅ Документация сохранена: {self.docs_dir}/bitrix_api.txt")
            print(f"   Размер: {len(all_text)} символов")
        else:
            print("❌ Не удалось получить документацию")
