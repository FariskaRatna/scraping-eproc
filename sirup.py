import re
import requests
import time
import pandas as pd
from datetime import datetime
import asyncio
from telegram import Bot

FILTER_NAMA_PAKET = ["Informasi", "Information", "Sistem", "System", "Teknologi", "Technology"]
FILTER_SATUAN_KERJA = ["Deputi Bidang Pencegahan", "Deputi Bidang Pemberantasan", "Pusat Penelitian Data dan Informasi", "Pusat Laboratorium"]
DELAY = 4

BOT_TOKEN = "8511928874:AAHKAdT1pn6K00vH0PVPewi9kuzkkI0ZrXw"
CHAT_ID = "-1003869116211"

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

def format_rupiah(angka):
    return f"Rp{int(angka):,}".replace(",", ".")

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

        r = session.get(base_url, params=params, timeout=90)
        r.raise_for_status()
        data = r.json()

        aa = data.get("aaData", [])
        if not aa:
            break

        rows.extend(aa)
        start += length
        time.sleep(DELAY)
    
    return rows

def build_grouped_messages(df, max_char=3500):
    messages = []
    header_global = "📊 Hasil Scraping SIRUP BNN\n\n"

    grouped = df.groupby("satuan_kerja")

    for satuan, group in grouped:
        header_dvisi = f"{satuan}:\n"
        current = header_global + header_dvisi
        counter = 1

        for _, row in group.iterrows():
            line = (
                f"{counter}. {row['nama_paket']} "
                f"({format_rupiah(row['pagu'])})\n\n"
            )

            if len(current) + len(line) > max_char:
                messages.append(current)
                current = header_global + header_dvisi

            current += line
            counter += 1

        if current.strip() != (header_global + header_dvisi).strip():
            messages.append(current)

    return messages

async def send_messages(df):
    bot = Bot(BOT_TOKEN)

    try:
        messages = build_grouped_messages(df)

        for msg in messages:
            await bot.send_message(
                chat_id=CHAT_ID,
                text=msg
            )

    except Exception as e:
        print("❌ ERROR KIRIM TELEGRAM")
        print(e)

def main():
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

    print(f"\nSELESAI ✅")
    print(f"Total data unik: {len(df)}")
    print(f"File: {OUTPUT_FILE}")

    if not df.empty:
        asyncio.run(send_messages(df))
    else:
        log("Tidak ada data yang dikirim ke Telegram")



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
