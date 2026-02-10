import schedule
import time
import random
import subprocess
from datetime import datetime

SCRAPERS = [
    'telegram/app-bnn.py',
    'telegram/app-bri.py',
    'telegram/app-jmtm.py',
    'telegram/app-bsi.py'
]

current_index = 0

def run_scraper(script_name):
    print("="*70)
    print(f"Menjalankan scraper {script_name}- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    try:
        result = subprocess.run(
            ['python', script_name],
            capture_output=True,
            text=True,
            timeout=3600
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print(f"Scraper {script_name} telah dijalankan dengan sukses!")
        else:
            print(f"Scraper {script_name} gagal dijalankan, {result.returncode}")

    except subprocess.TimeoutExpired:
        print("Scraper timeout (lebih dari 1 jam)")
    except Exception as e:
        print(f"Error: {e}")

    print("="*70 + "\n")


def schedule_random_time():
    global current_index

    script = SCRAPERS[current_index]

    random_hour = random.randint(10, 17)
    random_minute = random.randint(0, 59)

    schedule_time = f"{random_hour:02d}:{random_minute:02d}"
    
    print(f"Jadwal berikutnya: Senin, {schedule_time} -> {script}")

    schedule.clear()
    schedule.every().tuesday.at(schedule_time).do(run_and_rescheduler)

    return schedule_time

def run_and_rescheduler():
    global current_index

    script = SCRAPERS[current_index]

    run_scraper(script)
    current_index = (current_index + 1) % len(SCRAPERS)

    schedule_random_time()

if __name__ == "__main__":
    print("Scheduler scraper dimulai...")
    print("="*70)
    print("Akan berjalan setiap harus Senin (jam 10:00-17:00)")
    print("Tekan Ctrl+C untuk berhenti")
    print("="*70)

    next_time = schedule_random_time()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("Scheduler dihentikan oleh user!")
