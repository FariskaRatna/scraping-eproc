import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

URL = "https://www.bankbsi.co.id/news-update/info-nasabah"

def scrape_bsi(max_page=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

    for page in range(1, max_page + 1):
        url = f"{URL}?page={page}"
        print("Scraping:", url)

        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        blocks = soup.select("p.info-card-date")

        for p in blocks:
            text = p.get_text(" ", strip=True)

            if "2026" not in text:
                continue

            a = p.find_next("a")
            if not a:
                continue

            title = a.select_one("h5.info-card-title")
            if not title:
                continue

            title = title.get_text(strip=True)

            results.append({"judul": title})
        
        if not blocks:
            break

    df = pd.DataFrame(results)

    return df

if __name__ == "__main__":
    scrape_bsi(max_page=10)
    
