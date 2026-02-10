import asyncio
from bri import scrape_bri
from app import build_sirup_message, send_telegram_messages

def main():
    df_bri = scrape_bri()
    bri_msgs = build_sirup_message(df_bri)

    asyncio.run(send_telegram_messages(bri_msgs))

if __name__ == "__main__":
    main()