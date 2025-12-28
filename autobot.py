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
from datetime import datetime

# --- KONFIGURASI ---
# Delay acak agar tidak terdeteksi spam
delay_detik = random.randint(30, 300)
print(f"⏳ Menunggu {delay_detik} detik...")
time.sleep(delay_detik)

# Setup AI (Menggunakan Gemini 3 Flash sesuai request)
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-3-flash-preview')

def get_hot_trend():
    """Mencari Berita Paling Panas di Indonesia Saat Ini"""
    print("🔥 Mencari topik yang lagi viral...")
    try:
        # Mengambil RSS Google Trends Indonesia
        url = "https://trends.google.co.id/trends/trendingsearches/daily/rss?geo=ID"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            # AMBIL 3 TERATAS SAJA (Yang paling panas/baru)
            # Kita acak sedikit dari 3 besar biar variatif
            top_3 = items[:3]
            if top_3:
                chosen = random.choice(top_3)
                judul = chosen.find('title').text
                trafik = chosen.find('ht:approx_traffic', namespaces={'ht': 'https://trends.google.co.id/trends/trendingsearches/daily'}).text
                print(f"✅ Topik Panas Ditemukan: {judul} ({trafik}+ pencarian)")
                return judul
    except Exception as e:
        print(f"⚠️ Gagal ambil Trends: {e}")
    
    return None

def get_backup_topic():
    # Cadangan kalau Google Trends error
    return random.choice([
        "Cara Menggunakan AI untuk Pemula",
        "Review Gadget Terbaru 2025",
        "Tips Keamanan Cyber untuk HP Android",
        "Tutorial Coding Python Dasar"
    ])

def generate_content(topik):
    print(f"🤖 Gemini-3 sedang menulis tentang: {topik}...")
    
    img_keyword = urllib.parse.quote(topik)
    img_thumb = f"https://image.pollinations.ai/prompt/realistic%20news%20headline%20{img_keyword}?width=1000&height=448&nologo=true"
    
    prompt = f"""
    Kamu adalah jurnalis berita online yang cepat dan akurat.
    Buatkan ARTIKEL BERITA VIRAL tentang "{topik}" untuk audiens Indonesia.
    
    INSTRUKSI KHUSUS:
    1. Judul: Harus HEBOH tapi tetap faktual (Clickbait yang bertanggung jawab).
    2. Intro: Langsung bahas "Kenapa ini viral HARI INI?".
    3. Gaya Bahasa: Ringkas, Padat, Informatif (seperti portal berita detik/kompas).
    4. Panjang: Minimal 500 kata.
    
    STRUKTUR HTML (Body Only):
    1. <div class="separator" style="display: none; text-align: center;"><img src="{img_thumb}" /></div>
    2. Paragraf Pembuka (Breaking News).
    3. <h2>Kronologi / Fakta Utama</h2>
    4. Penjelasan detail 5W+1H.
    5. <h2>Reaksi Netizen & Dampaknya</h2>
    6. Kesimpulan.
    
    Output: Hanya kode HTML isi artikel.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"❌ Error AI: {e}")
        return "<p>Maaf, konten gagal dibuat.</p>"

def post_to_blogger(title, content):
    print("🚀 Posting ke Blogger...")
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
    
    # Tambahkan Timestamp di judul agar unik jika topik sama
    waktu = datetime.now().strftime("%H:%M")
    
    body = {
        'kind': 'blogger#post',
        'title': f"{title} (Update {waktu})",
        'content': content,
        'labels': ['Berita Viral', 'Trending Topic', 'News']
    }
    
    try:
        post = service.posts().insert(blogId=os.environ['BLOGGER_ID'], body=body).execute()
        print(f"✅ SUKSES TAYANG: {post['url']}")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik = get_hot_trend()
    if not topik:
        topik = get_backup_topic()
        
    isi = generate_content(topik)
    post_to_blogger(topik, isi)
