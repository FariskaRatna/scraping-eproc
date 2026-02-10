import re
import requests
import time
import pandas as pd
from datetime import datetime

FILTER_NAMA_PAKET = ["Informasi", "Information", "Sistem", "System", "Teknologi", "Technology"]
FILTER_SATUAN_KERJA = ["Deputi Bidang Pencegahan", "Deputi Bidang Pemberantasan", "Pusat Penelitian Data dan Informasi", "Pusat Laboratorium"]
DELAY = 5

headers= {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json"
}

base_url = "https://sirup.inaproc.id/sirup/datatablectr/dataruppenyediakldi"

session = requests.Session()
session.headers.update(headers)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_available_years():
    return list(range(2026, datetime.now().year + 1))

def scrape_year(tahun, keyword):
    start = 0
    length = 100
    rows = []

    while True:
        params = {
            "idKldi": "L8",
            "tahun": tahun,
            "iDisplayStart": start,
            "iDisplayLength": length,
            "sEcho": 1,
            "sSearch": keyword
        }

        r = session.get(base_url, params=params, timeout=120)
        r.raise_for_status()
        data = r.json()

        aa = data.get("aaData", [])
        if not aa:
            break

        rows.extend(aa)
        start += length
        time.sleep(DELAY)
    
    return rows

def scrape_bnn():
    all_data = []
    years = get_available_years()

    for nama_paket in FILTER_NAMA_PAKET:
        print(f"\nScraping Nama Paket: {nama_paket}")
        for year in years:
            print(f"  Tahun {year} ...")
            try:
                data = scrape_year(year, nama_paket)
                for r in data:
                    all_data.append(r + [year, "NAMA_PAKET", nama_paket])
            except Exception as e:
                print(f"  Gagal tahun {year}: {e}")

    for satuan in FILTER_SATUAN_KERJA:
        print(f"\nScraping Satuan Kerja: {satuan}")
        for year in years:
            print(f"  Tahun {year} ...")
            try:
                data = scrape_year(year, satuan)
                for r in data:
                    all_data.append(r + [year, "SATUAN_KERJA", satuan])
            except Exception as e:
                print(f"  Gagal tahun {year}: {e}")


    columns = [
        "no",
        "satuan_kerja",
        "nama_paket",
        "pagu", 
        "metode_pemilihan",
        "sumber_dana",
        "kode_rup",
        "waktu_pemilihan",
        "tahun",
        "tipe_filter",
        "nilai_filter"
    ]

    df = pd.DataFrame(all_data, columns=columns)

    # pattern_nama = "|".join(map(re.escape, FILTER_NAMA_PAKET))
    # pattern_satuan = "|".join(map(re.escape, FILTER_SATUAN_KERJA))

    # df = df[
    #     df["nama_paket"].str.contains(pattern_nama, case=False, na=False) |
    #     df["satuan_kerja"].str.contains(pattern_satuan, case=False, na=False)
    # ]

    df.drop_duplicates(subset=["kode_rup"], inplace=True)

    OUTPUT_FILE = "sirup_scrape_nama_dan_satuan.xlsx"

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        sheet = "DATA"
        df.to_excel(writer, sheet_name=sheet, index=False, startrow=6)

        ws = writer.book[sheet]
        ws["A1"] = "Filter Nama Paket"
        ws["B1"] = ", ".join(FILTER_NAMA_PAKET)
        ws["A2"] = "Filter Satuan Kerja"
        ws["B2"] = ", ".join(FILTER_SATUAN_KERJA)
        ws["A3"] = "Sumber Data"
        ws["B3"] = "https://sirup.inaproc.id"
        ws["A4"] = "Waktu Scraping"
        ws["B4"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\nSELESAI")
    print(f"Total data unik: {len(df)}")
    print(f"File: {OUTPUT_FILE}")

    return df

if __name__ == "__main__":
    scrape_bnn()