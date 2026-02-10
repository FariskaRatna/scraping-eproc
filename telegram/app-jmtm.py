import asyncio
from jmtm import scrape_jmtm
from app import build_sirup_message, send_telegram_messages

def main():
    df_jmtm = scrape_jmtm()
    jmtm_msgs = build_sirup_message(df_jmtm)

    asyncio.run(send_telegram_messages(jmtm_msgs))

if __name__ == "__main__":
    main()