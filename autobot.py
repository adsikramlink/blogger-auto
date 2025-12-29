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
delay_detik = random.randint(30, 120)
print(f"⏳ Menunggu {delay_detik} detik agar natural...")
time.sleep(delay_detik)

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash')

def get_hot_trend():
    """Mencari Berita Trending di Google Trends Indonesia"""
    print("🔥 Mencari topik panas...")
    try:
        url = "https://trends.google.co.id/trends/trendingsearches/daily/rss?geo=ID"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            top_items = items[:7]
            if top_items:
                chosen = random.choice(top_items)
                judul = chosen.find('title').text
                judul = judul.replace('"', '').replace("'", "")
                print(f"✅ Topik Ditemukan: {judul}")
                return judul
    except Exception as e:
        print(f"⚠️ Gagal ambil Trends: {e}")
    return None

def get_backup_topic():
    return random.choice([
        "Tutorial Python untuk Pemula",
        "Cara Menghasilkan Uang dari Blog",
        "Rekomendasi HP Gaming Murah 2025",
        "Tips Menjaga Keamanan Data di Internet",
        "Masa Depan AI dan Dampaknya bagi Pekerjaan"
    ])

def generate_content_package(topik):
    print(f"🤖 Gemini sedang menulis artikel untuk: {topik}...")
    
    prompt = f"""
    Bertindaklah sebagai Ahli SEO dan Jurnalis Senior.
    Buatkan ARTIKEL BLOG LENGKAP tentang "{topik}".
    
    ATURAN JUDUL:
    - Clickbait, Viral, tapi Relevan (Max 60 karakter).
    - JANGAN pakai tanda kutip.
    
    ATURAN ISI (HTML Body Only):
    - Gunakan tag <h2> dan <h3>.
    - Paragraf pertama mengandung keyword "{topik}".
    - Gaya bahasa: Santai, Mengalir, Enak dibaca.
    - Panjang: Minimal 600 kata.
    
    STRUKTUR:
    1. Paragraf Pembuka (Hook).
    2. <h2>Apa itu {topik}?</h2>
    3. <h2>Fakta Utama / Kronologi</h2>
    4. <h2>Kenapa Viral?</h2>
    5. Kesimpulan.
    
    WAJIB GUNAKAN FORMAT OUTPUT PEMISAH (|||):
    JUDUL_SEO_KAMU ||| KODE_HTML_ISI_ARTIKEL
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        if "|||" in raw_text:
            judul, isi = raw_text.split("|||", 1)
            return judul.strip(), isi.strip()
        else:
            return f"Berita Viral: {topik}", raw_text
            
    except Exception as e:
        print(f"❌ Error AI: {e}")
        return None, None

def post_to_blogger(title, content, topik_asli):
    print(f"🚀 Memposting: {title}")
    
    img_keyword = urllib.parse.quote(topik_asli)
    seed1 = random.randint(1, 9999)
    seed2 = random.randint(1, 9999)
    
    # --- 1. THUMBNAIL (HIDDEN) ---
    # Wajib 1000x448 sesuai request
    # Di-hidden (display: none) agar tidak muncul ganda, tapi terdeteksi Google/Blogger
    thumb_url = f"https://image.pollinations.ai/prompt/realistic%20news%20thumbnail%20about%20{img_keyword}?width=1000&height=448&nologo=true&seed={seed1}"
    
    html_thumbnail = f"""
    <div class="separator" style="display: none;">
        <img src="{thumb_url}" alt="{title}" />
    </div>
    """
    
    # --- 2. GAMBAR ILUSTRASI (VISIBLE - TENGAH KONTEN) ---
    # Ukuran proporsional enak dilihat (1000x600)
    body_img_url = f"https://image.pollinations.ai/prompt/illustration%20blog%20image%20about%20{img_keyword}?width=1000&height=600&nologo=true&seed={seed2}"
    
    html_body_image = f"""
    <div class="separator" style="clear: both; text-align: center; margin: 30px 0;">
        <a href="{body_img_url}" style="margin-left: 1em; margin-right: 1em;">
            <img border="0" src="{body_img_url}" width="640" height="384" style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" alt="Ilustrasi {title}" />
        </a>
    </div>
    """
    
    # --- LOGIKA PENYISIPAN GAMBAR DI TENGAH (SMART INJECTION) ---
    # Kita cari posisi tengah artikel, lalu cari paragraf terdekat
    titik_tengah = len(content) // 2
    
    # Cari penutup paragraf </p> terdekat SETELAH titik tengah
    posisi_sisip = content.find('</p>', titik_tengah)
    
    if posisi_sisip != -1:
        # Sisipkan setelah paragraf tengah
        posisi_sisip += 4 # Panjang tag </p>
        isi_final_body = content[:posisi_sisip] + html_body_image + content[posisi_sisip:]
    else:
        # Fallback 1: Jika tidak ketemu, coba cari Heading kedua (<h2>)
        posisi_sisip = content.find('<h2>', 100) # Cari h2 tapi jangan yang paling awal
        if posisi_sisip != -1:
             isi_final_body = content[:posisi_sisip] + html_body_image + content[posisi_sisip:]
        else:
             # Fallback 2: Terpaksa taruh setelah paragraf pertama (biar tidak paling atas banget)
             posisi_sisip = content.find('</p>')
             if posisi_sisip != -1:
                 posisi_sisip += 4
                 isi_final_body = content[:posisi_sisip] + html_body_image + content[posisi_sisip:]
             else:
                 # Sangat jarang terjadi: Artikel tanpa paragraf
                 isi_final_body = html_body_image + content

    # GABUNGKAN SEMUA: Thumbnail Hidden + Isi Artikel Ber-Gambar
    final_content = html_thumbnail + isi_final_body

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
        'title': title,
        'content': final_content,
        'labels': ['News', 'Viral', 'Update']
    }
    
    try:
        post = service.posts().insert(blogId=os.environ['BLOGGER_ID'], body=body).execute()
        print(f"✅ SUKSES POSTING: {post['url']}")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik = get_hot_trend()
    if not topik:
        topik = get_backup_topic()
        
    judul, isi = generate_content_package(topik)
    
    if judul and isi:
        post_to_blogger(judul, isi, topik)
    else:
        print("❌ Gagal generate konten.")
