import asyncio
from bsi import scrape_bsi
from app import build_sirup_message, send_telegram_messages

def main():
    df_bsi = scrape_bsi()
    bsi_msgs = build_sirup_message(df_bsi)

    asyncio.run(send_telegram_messages(bsi_msgs))

if __name__ == "__main__":
    main()