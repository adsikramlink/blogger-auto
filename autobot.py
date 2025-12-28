import os
import random
import time
import urllib.parse
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- KONFIGURASI ---
delay_detik = random.randint(30, 300)
print(f"⏳ Menunggu {delay_detik} detik...")
time.sleep(delay_detik)

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-3-flash-preview')

def get_hot_trend():
    """Mencari Berita Paling Panas di Indonesia"""
    print("🔥 Mencari topik viral...")
    try:
        url = "https://trends.google.co.id/trends/trendingsearches/daily/rss?geo=ID"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            # Ambil acak dari 5 besar agar makin variatif
            top_5 = items[:5]
            if top_5:
                chosen = random.choice(top_5)
                judul = chosen.find('title').text
                judul = judul.replace('"', '').replace("'", "")
                print(f"✅ Topik Ditemukan: {judul}")
                return judul
    except Exception as e:
        print(f"⚠️ Gagal ambil Trends: {e}")
    return None

def get_backup_topic():
    return random.choice([
        "Cara Menggunakan AI Gratis 2026",
        "Rekomendasi HP Murah Spek Dewa",
        "Tips Menghasilkan Uang dari Internet",
        "Tutorial Python untuk Pemula",
        "Bahaya Kejahatan Siber di Android"
    ])

def generate_content_package(topik):
    print(f"🤖 Gemini sedang meracik Judul & Konten untuk: {topik}...")
    
    img_keyword = urllib.parse.quote(topik)
    img_thumb = f"https://image.pollinations.ai/prompt/realistic%20news%20headline%20photo%20{img_keyword}?width=1000&height=448&nologo=true"
    
    # KITA MINTA FORMAT KHUSUS: JUDUL ||| ISI
    prompt = f"""
    Kamu adalah jurnalis berita online profesional.
    Tugasmu: Buatkan JUDUL CLICKBAIT yang unik dan ISI ARTIKEL untuk topik "{topik}".
    
    ATURAN JUDUL:
    - Harus beda dari yang lain, viral, dan memancing klik.
    - JANGAN pakai tanda kutip.
    - Maksimal 10 kata.
    
    ATURAN ISI (HTML Body Only):
    1. <div class="separator" style="display: none; text-align: center;"><img src="{img_thumb}" /></div>
    2. Paragraf pembuka yang heboh (Breaking News).
    3. <h2>Fakta Utama</h2> (Jelaskan 5W+1H).
    4. <h2>Kenapa Viral?</h2> (Analisa penyebab trending).
    5. Kesimpulan.
    
    WAJIB GUNAKAN FORMAT OUTPUT INI (Pemisah |||):
    JUDUL_VIRAL_KAMU ||| KODE_HTML_ISI_ARTIKEL
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # Pisahkan Judul dan Isi berdasarkan tanda |||
        if "|||" in raw_text:
            judul_jadi, isi_jadi = raw_text.split("|||", 1)
            return judul_jadi.strip(), isi_jadi.strip()
        else:
            # Fallback jika AI lupa format
            return f"Berita Viral: {topik}", raw_text
            
    except Exception as e:
        print(f"❌ Error AI: {e}")
        return None, None

def post_to_blogger(title, content):
    print(f"🚀 Posting: {title}")
    
    creds = Credentials(
        None,
        refresh_token=os.environ['BLOGGER_REFRESH_TOKEN'],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ['BLOGGER_CLIENT_ID'],
        client_secret=os.environ['BLOGGER_CLIENT_SECRET']
    )
    
    if not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        
    service = build('blogger', 'v3', credentials=creds)
    
    body = {
        'kind': 'blogger#post',
        'title': title, # Judul ini hasil buatan AI, pasti unik!
        'content': content,
        'labels': ['Berita Viral', 'Trending', 'News']
    }
    
    try:
        post = service.posts().insert(blogId=os.environ['BLOGGER_ID'], body=body).execute()
        print(f"✅ SUKSES TAYANG: {post['url']}")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik_awal = get_hot_trend()
    if not topik_awal:
        topik_awal = get_backup_topic()
        
    # Fungsi baru mengembalikan 2 variabel: Judul & Isi
    judul_final, isi_final = generate_content_package(topik_awal)
    
    if judul_final and isi_final:
        post_to_blogger(judul_final, isi_final)
    else:
        print("❌ Gagal generate konten.")
