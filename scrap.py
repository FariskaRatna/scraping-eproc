import re
from datetime import datetime

def parse_hps(text):
    angka = re.sub(r"[^\d]", "", text)
    return int(angka) if angka else 0

def extract_year(nama_paket, akhir_pendaftaran):
    # 1. Dari tanggal
    try:
        return datetime.strptime(
            akhir_pendaftaran, "%d-%B-%Y %H:%M"
        ).year
    except Exception:
        pass

    # 2. Fallback dari nama paket
    m = re.search(r"(20\d{2})", nama_paket)
    return int(m.group(1)) if m else None

import requests
from bs4 import BeautifulSoup

URL = "https://eproc.jmtm.co.id/home/cari_paket"

def scrape_pengadaan_2026():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "id-ID,id;q=0.9"
    })

    res = session.get(URL, timeout=30)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table")

    rows = table.find_all("tr")[1:]  # skip header
    results = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        nama_paket = cols[1].get_text(strip=True)
        hps_raw = cols[2].get_text(strip=True)
        akhir_pendaftaran = cols[3].get_text(strip=True)

        tahun = extract_year(nama_paket, akhir_pendaftaran)

        if tahun != 2026:
            continue

        results.append({
            "nama_paket": nama_paket,
            "hps": parse_hps(hps_raw),
            "akhir_pendaftaran": akhir_pendaftaran
        })

    return results

import pandas as pd

def save_to_excel(data, filename="pengadaan_2026.xlsx"):
    df = pd.DataFrame(data)

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pengadaan 2026")

    print(f"Excel berhasil dibuat: {filename}")


if __name__ == "__main__":
    data = scrape_pengadaan_2026()
    print(f"Total paket 2026: {len(data)}")

    save_to_excel(data)

