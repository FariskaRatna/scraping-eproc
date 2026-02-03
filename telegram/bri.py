from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import time

URL = "https://bri.co.id/auction-info"
BASE = "https://bri.co.id"

def scrape_bri():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    # driver.get(URL)
    try:
        driver.get(URL)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.box-list"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        results = []
        for item in soup.select("div.box-list"):
            h4 = item.select_one("div.box-name h4")
            small = item.select_one("div.box-name small")
            a = item.select_one("div.box-down a[href]")

            if not (h4 and small and a):
                continue
            
            span = h4.find("span")
            status = span.get_text(strip=True) if span else ""

            raw_title = h4.get_text(" ", strip=True)
            title = raw_title.replace(status, "").strip()

            date_range = small.get_text(strip=True)
            
            if "2026" not in date_range:
                continue

            link = urljoin(BASE, a["href"]) if a else None

            results.append({
                "judul": title,
                "periode": date_range,
                "download_link": link
            })

        df = pd.DataFrame(results)
        df.to_excel("bri-pengadaan.xlsx", index=False)
        print("Selesai, total:", len(results))

        return df
    
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_bri()