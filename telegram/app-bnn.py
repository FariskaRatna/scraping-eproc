import asyncio
from bnn import scrape_bnn
from app import build_sirup_message, send_telegram_messages

def main():
    df_sirup = scrape_bnn()
    sirup_msgs = build_sirup_message(df_sirup)

    asyncio.run(send_telegram_messages(sirup_msgs))

if __name__ == "__main__":
    main()