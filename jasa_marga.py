import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import time

BASE_URL = "https://eproc.jmtm.co.id"
MAIN_URL = f"{BASE_URL}/home/cari_paket"  # Sesuaikan dengan URL yang benar

def parse_currency(text):
    """Convert 'Rp 37.740.000,00' to 37740000"""
    angka = re.sub(r'[^\d]', '', text)
    return int(angka) if angka else 0

def extract_year_from_package(nama_paket, akhir_pendaftaran):
    """Extract year from package name or date"""
    try:
        date_obj = datetime.strptime(akhir_pendaftaran, "%d-%B-%Y %H:%M")
        return date_obj.year
    except:
        pass
    
    match = re.search(r'\b(20\d{2})\b', nama_paket)
    if match:
        return int(match.group(1))
    
    return None

def get_page_with_retry(session, url, max_retries=5, initial_timeout=30):
    """Fetch page with progressive retry mechanism"""
    for attempt in range(max_retries):
        # Increase timeout progressively: 30s, 60s, 90s, 120s, 180s
        timeout = initial_timeout * (attempt + 1)
        
        try:
            print(f"   🔄 Percobaan {attempt + 1}/{max_retries} (timeout: {timeout}s)...", end=" ", flush=True)
            
            res = session.get(url, timeout=timeout, stream=True)
            res.raise_for_status()
            
            # Read content in chunks for large pages
            content = b''
            for chunk in res.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
            
            res._content = content
            
            print(f"✅ Berhasil ({len(content):,} bytes)")
            return res
            
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout setelah {timeout}s")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"      Menunggu {wait_time} detik sebelum retry...", flush=True)
                time.sleep(wait_time)
            else:
                print("      ❌ Gagal setelah semua percobaan")
                raise
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"      Menunggu {wait_time} detik sebelum retry...", flush=True)
                time.sleep(wait_time)
            else:
                raise
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"      Menunggu {wait_time} detik sebelum retry...", flush=True)
                time.sleep(wait_time)
            else:
                raise
    
    return None

def scrape_all_tables(url, tahun_filter=2026):
    """Scrape all tables from the page"""
    print(f"🌐 Mengakses: {url}")
    print(f"⏱️  Website berat, mohon bersabar...\n")
    
    # Create session with optimized settings for slow websites
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",  # Enable compression
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    })
    
    # Set connection pool size
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1,
        pool_maxsize=1,
        max_retries=0
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    try:
        # Fetch page with progressive retry
        print("📥 Mengunduh halaman...")
        res = get_page_with_retry(session, url, max_retries=5, initial_timeout=30)
        
        if not res:
            print("❌ Tidak bisa mengakses halaman")
            return []
        
        print(f"✅ Halaman berhasil diunduh\n")
        
        # Parse HTML
        print("🔍 Parsing HTML...", end=" ", flush=True)
        try:
            soup = BeautifulSoup(res.text, 'lxml')
            print("✅ (menggunakan lxml)")
        except:
            soup = BeautifulSoup(res.text, 'html.parser')
            print("✅ (menggunakan html.parser)")
        
        # Find all card sections
        cards = soup.find_all('div', class_='card-header')
        
        if not cards:
            print("⚠️  Tidak ditemukan card-header")
            # Fallback: find all tables
            tables = soup.find_all('table')
            if not tables:
                print("❌ Tidak ada tabel ditemukan")
                
                # Debug: save HTML to file
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(res.text)
                print("💾 HTML disimpan ke 'debug_page.html' untuk debugging")
                
                return []
            
            print(f"✅ Ditemukan {len(tables)} tabel (tanpa card-header)\n")
            all_results = []
            
            for table_idx, table in enumerate(tables, 1):
                print(f"\n{'='*80}")
                print(f"📊 TABEL #{table_idx}")
                print(f"{'='*80}")
                
                results = process_table(table, f"Tabel {table_idx}", tahun_filter)
                all_results.extend(results)
                
                time.sleep(0.5)  # Small delay between tables
            
            return all_results
        
        print(f"✅ Ditemukan {len(cards)} section pengadaan\n")
        print("=" * 80)
        
        all_results = []
        
        # Process each card section
        for card_idx, card in enumerate(cards, 1):
            jenis_pengadaan = card.get_text(strip=True)
            jenis_pengadaan = re.sub(r'\s+', ' ', jenis_pengadaan)
            
            # Find the table
            card_parent = card.find_parent('div', class_='card')
            if card_parent:
                table = card_parent.find('table')
            else:
                table = card.find_next('table')
            
            if not table:
                print(f"⚠️  Tidak ada tabel untuk: {jenis_pengadaan}")
                continue
            
            print(f"\n{'='*80}")
            print(f"📊 SECTION #{card_idx}/{len(cards)}")
            print(f"{'='*80}")
            print(f"📦 Jenis: {jenis_pengadaan}")
            
            results = process_table(table, jenis_pengadaan, tahun_filter)
            all_results.extend(results)
            
            # Progress update
            print(f"\n📈 Progress: {card_idx}/{len(cards)} sections | Total data: {len(all_results)} paket")
            
            time.sleep(0.5)  # Small delay between sections
        
        print("\n" + "=" * 80)
        print(f"✅ SELESAI SCRAPING!")
        print(f"📦 Total: {len(all_results)} paket dari {len(cards)} section")
        print("=" * 80 + "\n")
        
        return all_results
        
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT ERROR!")
        print("\n💡 Website terlalu lambat. Solusi:")
        print("   1. Coba lagi saat traffic rendah (malam hari)")
        print("   2. Gunakan koneksi internet yang lebih stabil")
        print("   3. Jika masih gagal, website mungkin sedang overload")
        print("   4. Alternatif: scrape langsung dari browser dengan Save As HTML")
        return []
        
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR!")
        print("\n💡 Solusi:")
        print("   1. Cek koneksi internet")
        print("   2. Website mungkin sedang down")
        print("   3. Coba gunakan VPN")
        return []
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_table(table, jenis_pengadaan, tahun_filter):
    """Process a single table and return results"""
    results = []
    
    rows = table.find_all('tr')
    
    if not rows:
        print("⚠️  Tabel kosong")
        return results
    
    # Header
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    print(f"📋 Kolom: {', '.join(headers[:4])}...")
    
    # Data rows
    data_rows = rows[1:]
    total_rows = len(data_rows)
    
    print(f"📊 Total rows: {total_rows}")
    print("🔄 Processing...", end="", flush=True)
    
    for row_idx, row in enumerate(data_rows, 1):
        cols = row.find_all('td')
        
        if len(cols) < 4:
            continue
        
        try:
            no = cols[0].get_text(strip=True)
            
            # Nama paket
            nama_label = cols[1].find('label', class_='text-info')
            if nama_label:
                nama_paket = nama_label.get_text(strip=True)
            else:
                nama_paket = cols[1].get_text(strip=True)
            
            hps_raw = cols[2].get_text(strip=True)
            akhir_pendaftaran = cols[3].get_text(strip=True)
            
            if not nama_paket or nama_paket == '-' or nama_paket.lower() == 'nama paket':
                continue
            
            # Link
            link = ''
            if len(cols) > 4:
                link_tag = cols[4].find('a')
                if link_tag:
                    onclick = link_tag.get('onclick', '')
                    match = re.search(r'lihat_persyartaan\((\d+)\)', onclick)
                    if match:
                        paket_id = match.group(1)
                        link = f"{BASE_URL}/home/detail_paket/{paket_id}"
            
            # Year
            tahun = extract_year_from_package(nama_paket, akhir_pendaftaran)
            
            if tahun_filter and tahun != tahun_filter:
                continue
            
            results.append({
                'jenis_pengadaan': jenis_pengadaan,
                'no': no,
                'nama_paket': nama_paket,
                'hps': parse_currency(hps_raw),
                'hps_formatted': hps_raw,
                'akhir_pendaftaran': akhir_pendaftaran,
                'tahun': tahun,
                'link': link
            })
            
            # Progress bar
            if row_idx % 10 == 0 or row_idx == total_rows:
                progress = int(50 * row_idx / total_rows)
                bar = '█' * progress + '░' * (50 - progress)
                print(f"\r🔄 Processing... [{bar}] {row_idx}/{total_rows}", end="", flush=True)
        
        except Exception as e:
            continue
    
    print()  # New line after progress bar
    print(f"✅ Berhasil memproses: {len(results)} paket (filter tahun {tahun_filter})")
    
    if results:
        total_hps = sum(r['hps'] for r in results)
        print(f"💰 Total HPS: Rp {total_hps:,.0f}")
    
    return results

def save_to_excel(data, filename="pengadaan_jasa_marga_2026.xlsx"):
    """Save data to Excel"""
    if not data:
        print("\n⚠️  Tidak ada data untuk disimpan")
        return
    
    print(f"\n💾 Menyimpan ke Excel: {filename}")
    
    df = pd.DataFrame(data)
    columns_order = ['jenis_pengadaan', 'no', 'nama_paket', 'hps_formatted', 'hps', 
                     'akhir_pendaftaran', 'tahun', 'link']
    df = df[[col for col in columns_order if col in df.columns]]
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # All data sorted by HPS
        df_sorted = df.sort_values('hps', ascending=False)
        df_sorted.to_excel(writer, index=False, sheet_name='Semua (Sorted by HPS)')
        print("   ✅ Sheet: Semua (Sorted by HPS)")
        
        # All data by jenis
        df_by_jenis = df.sort_values(['jenis_pengadaan', 'hps'], ascending=[True, False])
        df_by_jenis.to_excel(writer, index=False, sheet_name='Semua (By Jenis)')
        print("   ✅ Sheet: Semua (By Jenis)")
        
        # Per jenis
        for jenis in sorted(df['jenis_pengadaan'].unique()):
            df_filtered = df[df['jenis_pengadaan'] == jenis].sort_values('hps', ascending=False)
            sheet_name = re.sub(r'[\\/*?:\[\]]', '', jenis.strip())[:31]
            df_filtered.to_excel(writer, index=False, sheet_name=sheet_name)
            print(f"   ✅ Sheet: {sheet_name}")
        
        # Auto-width
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                try:
                    max_length = min(max(df[col].astype(str).apply(len).max(), len(col)) + 2, 70)
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length
                except:
                    worksheet.column_dimensions[chr(65 + idx)].width = 15
    
    print(f"\n✅ Excel berhasil dibuat: {filename}")

def display_summary(data):
    """Display summary"""
    df = pd.DataFrame(data)
    
    print("\n" + "=" * 80)
    print("📊 RINGKASAN DATA")
    print("=" * 80)
    
    for jenis in sorted(df['jenis_pengadaan'].unique()):
        filtered = df[df['jenis_pengadaan'] == jenis]
        print(f"\n📦 {jenis}")
        print(f"   • Jumlah: {len(filtered):,} paket")
        print(f"   • Total HPS: Rp {filtered['hps'].sum():,.0f}")
    
    print(f"\n{'='*80}")
    print(f"📈 TOTAL: {len(df):,} paket | HPS: Rp {df['hps'].sum():,.0f}")
    print("=" * 80)

def main():
    print("=" * 80)
    print("  🚀 SCRAPING PENGADAAN JASA MARGA 2026")
    print("  ⚠️  WEBSITE BERAT - MOHON BERSABAR")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        data = scrape_all_tables(MAIN_URL, tahun_filter=2026)
        
        if data:
            display_summary(data)
            save_to_excel(data)
            
            elapsed = time.time() - start_time
            print(f"\n✅ SELESAI! Waktu: {elapsed:.1f} detik ({elapsed/60:.1f} menit)")
        else:
            print("\n⚠️  TIDAK ADA DATA")
            print("\n💡 Alternatif jika website terlalu lambat:")
            print("   1. Buka website di browser")
            print("   2. Klik kanan → Save As → Complete HTML")
            print("   3. Jalankan script dengan file HTML lokal")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Dibatalkan")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")

if __name__ == "__main__":
    main()