import asyncio
from telegram import Bot
from telegram.error import TimedOut
from bnn import scrape_bnn
from bri import scrape_bri

BOT_TOKEN = "8511928874:AAHKAdT1pn6K00vH0PVPewi9kuzkkI0ZrXw"
CHAT_ID = "-5280853082"

def format_rupiah(angka):
    return f"Rp{int(angka):,}".replace(",", ".")

def build_sirup_message(df, max_char=3500):
    messages = []
    header_global = "🏦 Hasil Scraping SIRUP BNN\n\n"

    grouped = df.groupby("satuan_kerja")

    for satuan, group in grouped:
        header_divisi = f"{satuan}:\n"
        current = header_global + header_divisi
        counter = 1

        for _, row in group.iterrows():
            line = (
                f"{counter}. {row['nama_paket']} "
                f"({format_rupiah(row['pagu'])})\n\n"
            )

            if len(current) + len(line) > max_char:
                messages.append(current)
                current = header_global + header_divisi

            current += line
            counter += 1

        if current.strip() != (header_global + header_divisi).strip():
            messages.append(current)

    return messages

def build_bri_messages(df, max_char=3500):
    messages = []
    header = "🏦 Hasil Scrapping BRI\n\n"

    current = header

    for _, row in df.iterrows():
        line = (
            f"• {row['judul']}\n"
            f"  {row['periode']}\n"
            f"  {row['download_link']}\n\n"
        )

        if len(current) + len(line) > max_char:
            messages.append(current)
            current = header

        current += line

    if current.strip() != header.strip():
        messages.append(current)

    return messages

async def send_telegram_messages(messages):
    bot = Bot(BOT_TOKEN)

    for msg in messages:
        for attempt in range(3):
            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=msg,
                    connect_timeout=30,
                    read_timeout=30
                )
                await asyncio.sleep(1.5)
                break
            except TimedOut:
                print("⚠️ Timeout kirim Telegram, retry...")
                await asyncio.sleep(3)

def main():
    print("🚀 Mulai scraping data...")

    df_sirup = scrape_bnn()
    df_bri = scrape_bri()

    print(f"SIRUP: {len(df_sirup)} data")
    print(f"BRI  : {len(df_bri)} data")

    sirup_msgs = build_sirup_message(df_sirup)
    bri_msgs = build_bri_messages(df_bri)

    asyncio.run(send_telegram_messages(sirup_msgs))
    asyncio.run(send_telegram_messages(bri_msgs))

if __name__ == "__main__":
    main()