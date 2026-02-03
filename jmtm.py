from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

URL = "https://eproc.jmtm.co.id/home/cari_paket"

def scrape_jmtm():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    # ⏳ Tunggu sampai tabel pertama muncul
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )

    # 🔁 Scroll biar semua data ter-render
    last_count = 0
    for _ in range(100):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if len(rows) == last_count:
            break
        last_count = len(rows)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    results = []
    for card in soup.select("div.card"):
        header = card.select_one("div.card-header")
        kategori = header.get_text(" ", strip=True) if header else "TANPA KATEGORI"

        for row in card.select("tbody tr"):
            nama_el = row.select_one("label.text-info")
            hps_el = row.select_one("td.table-hps")

            if not nama_el or not hps_el:
                continue

            results.append({
                "kategori": kategori,
                "nama_paket": nama_el.get_text(strip=True),
                "hps": hps_el.get_text(strip=True),
            })

    driver.quit()

    df = pd.DataFrame(results)
    df.to_excel("jasa-marga-pengadaan.xlsx", index=False)
    print("Selesai, total:", len(df))

    return df


if __name__ == "__main__":
    scrape_jmtm()
