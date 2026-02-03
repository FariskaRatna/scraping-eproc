from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

URL = "https://eproc.jmtm.co.id/home/cari_paket"

def scrape_jmtm():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.card"))
    )
    time.sleep(3)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.card")
    results = []

    for card in cards:
        try:
            kategori = driver.execute_script("""
                var h = arguments[0].querySelector('.card-header');
                return h.childNodes[0].textContent.trim();
            """, card)


            table = card.find_element(By.CSS_SELECTOR, "table")
            rows = driver.execute_script("""
                var dt = $(arguments[0]).DataTable();
                var data = [];
                dt.rows().every(function(){
                    var row = [];
                    $(this.node()).find("td").each(function(){
                        row.push(this.innerText.trim());
                    });
                    data.push(row);
                });
                return data;
            """, table)

            print(f"📦 {kategori} → {len(rows)} rows")

            for r in rows:
                results.append({
                    "nama_pengadaan": kategori,
                    "no": r[0],
                    "nama_paket": r[1],  
                    "hps": r[2],
                    "akhir_pendaftaran": r[3],
                })

        except Exception as e:
            print("⚠️ Skip card:", e)

    driver.quit()

    df = pd.DataFrame(results)
    
    df["akhir_pendaftaran_dt"] = pd.to_datetime(
        df["akhir_pendaftaran"],
        errors="coerce"
    )

    df = df[df["akhir_pendaftaran_dt"].dt.year == 2026]

    df = df.drop(columns=["akhir_pendaftaran_dt"])

    df.to_excel("jmtm-full-with-kategori.xlsx", index=False)
    print("✅ Total row:", len(df))
    return df

if __name__ == "__main__":
    scrape_jmtm()