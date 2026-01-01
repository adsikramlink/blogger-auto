import os
import random
import time
import urllib.parse
import re
import requests
import base64
import xml.etree.ElementTree as ET
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- KONFIGURASI ---
delay_detik = random.randint(30, 120)
print(f"⏳ Menunggu {delay_detik} detik agar aktivitas natural...")
time.sleep(delay_detik)

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- SUMBER 1: GOOGLE TRENDS ---
def get_google_trends():
    print("🔍 Mengecek Google Trends...")
    try:
        url = "https://trends.google.co.id/trends/trendingsearches/daily/rss?geo=ID"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            if items:
                return [item.find('title').text for item in items[:7]] # Ambil 7 teratas
    except Exception as e:
        print(f"⚠️ Gagal Google Trends: {e}")
    return []

# --- SUMBER 2: CNN INDONESIA (Tekno & Hiburan) ---
def get_cnn_news():
    print("🔍 Mengecek CNN Indonesia (Siapa tau ada viral TikTok)...")
    try:
        # Menggabungkan RSS Tekno dan Hiburan
        urls = [
            "https://www.cnnindonesia.com/teknologi/rss",
            "https://www.cnnindonesia.com/hiburan/rss"
        ]
        collected_titles = []
        for url in urls:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                for item in items[:3]: # Ambil 3 dari tiap kategori
                    collected_titles.append(item.find('title').text)
        return collected_titles
    except Exception as e:
        print(f"⚠️ Gagal CNN News: {e}")
    return []

# --- SUMBER 3: YOUTUBE TRENDING INDONESIA ---
# (Kita pakai RSS feed tersembunyi YouTube, aman dari blokir)
def get_youtube_trending():
    print("🔍 Mengecek YouTube Trending...")
    try:
        # ID untuk Indonesia (Banyak video viral medsos masuk sini)
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCEgdi0XIXXZ-qJOFPf4JSKw" 
        # Note: URL di atas adalah feed 'YouTube Spotlight' atau bisa pakai scraping ringan jika perlu
        # TAPI, cara paling stabil tanpa API key adalah lewat Google Trends 'YouTube' mode, 
        # atau kita pakai RSS feed berita saja yang lebih aman.
        # Mari kita ganti ke ANTARA NEWS agar lebih variatif beritanya
        url_antara = "https://www.antaranews.com/rss/tekno.xml"
        response = requests.get(url_antara, timeout=10)
        if response.status_code == 200:
             root = ET.fromstring(response.content)
             items = root.findall('.//item')
             if items:
                 return [item.find('title').text for item in items[:5]]
    except Exception as e:
        print(f"⚠️ Gagal Source Tambahan: {e}")
    return []

def get_mixed_topic():
    """Mengambil topik dari salah satu sumber secara acak"""
    sources = [get_google_trends, get_cnn_news, get_youtube_trending]
    random.shuffle(sources) # Acak urutan pengecekan
    
    for source_func in sources:
        topics = source_func()
        if topics:
            chosen = random.choice(topics)
            # Bersihkan karakter aneh
            chosen = chosen.replace('"', '').replace("'", "")
            print(f"✅ Topik Terpilih: {chosen} (Dari {source_func.__name__})")
            return chosen
            
    # Backup jika semua gagal
    return random.choice([
        "Tutorial Python untuk Pemula",
        "Rekomendasi HP Gaming Murah",
        "Cara Menghasilkan Uang dari Internet",
        "Berita Viral Hari Ini"
    ])

def generate_content_package(topik):
    print(f"🤖 Gemini sedang meracik konten untuk: {topik}...")
    
    prompt = f"""
    Bertindaklah sebagai Jurnalis Media Online & Ahli SEO.
    Topik Utama: "{topik}"
    
    Tugasmu:
    1. Buat Judul Clickbait yang UNIK (DILARANG pakai kata: Terbongkar, Wow, Heboh).
    2. Buat Keyword Gambar (Inggris, Max 4 kata).
    3. Buat Isi Artikel (Bahasa Indonesia).
    
    INSTRUKSI KHUSUS KONTEN:
    - Jika topik ini berpotensi viral di media sosial (TikTok/Instagram), sebutkan dalam artikel: "Topik ini sedang ramai diperbincangkan netizen di media sosial..."
    - Gaya bahasa: Santai tapi berbobot (seperti portal berita teknologi).
    - Panjang: Minimal 600 kata.
    - Wajib pakai tag <p>, <h2>, <h3>.
    
    FORMAT OUTPUT (|||):
    JUDUL_SEO ||| KEYWORD_GAMBAR ||| KODE_HTML_ISI
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        parts = raw_text.split("|||")
        if len(parts) >= 3:
            return parts[0].strip(), parts[1].strip(), "|||".join(parts[2:]).strip()
        else:
            return f"Update: {topik}", "news illustration", raw_text
    except Exception as e:
        print(f"❌ Error AI: {e}")
        return None, None, None

def upload_to_imgbb(image_url, name_slug):
    """Upload ImgBB dengan Retry System"""
    api_key = os.environ.get('IMGBB_API_KEY')
    if not api_key: return image_url

    print(f"☁️ Proses Download & Upload Gambar...")
    for attempt in range(1, 4): # 3x Percobaan
        try:
            img_response = requests.get(image_url, timeout=120)
            if img_response.status_code == 200:
                img_b64 = base64.b64encode(img_response.content)
                payload = { "key": api_key, "image": img_b64, "name": name_slug[:30] }
                res = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=60)
                if res.status_code == 200:
                    hosted = res.json()['data']['url']
                    print(f"✅ Sukses Upload: {hosted}")
                    return hosted
            else:
                print(f"⚠️ Gagal Download AI (Status {img_response.status_code})")
        except Exception as e:
            print(f"⚠️ Error {attempt}: {e}")
        time.sleep(10)
    return image_url

def post_to_blogger(title, img_prompt_en, content):
    print(f"🚀 Posting: {title}")
    
    clean_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', img_prompt_en)
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed1, seed2 = random.randint(1, 9999), random.randint(1, 9999)
    file_slug = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())

    # Generate & Upload Images
    raw_thumb = f"https://image.pollinations.ai/prompt/realistic%20photo%20{encoded_prompt}?width=1000&height=448&model=flux&nologo=true&seed={seed1}"
    raw_body = f"https://image.pollinations.ai/prompt/illustration%20art%20{encoded_prompt}?width=1000&height=600&model=flux&nologo=true&seed={seed2}"
    
    final_thumb = upload_to_imgbb(raw_thumb, f"thumb-{file_slug}")
    time.sleep(15) # Jeda nafas
    final_body = upload_to_imgbb(raw_body, f"body-{file_slug}")
    
    # HTML Structure
    html_thumb = f'<div class="separator" style="display: none;"><img src="{final_thumb}" alt="{title}" /></div>'
    html_body_img = f'<div class="separator" style="clear: both; text-align: center; margin: 30px 0;"><img src="{final_body}" width="640" height="384" style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" /></div><br/>'
    
    # Insert Logic (After Paragraph 1)
    pos = content.find('</p>')
    final_content = html_thumb + (content[:pos+4] + html_body_img + content[pos+4:] if pos != -1 else html_body_img + content)

    # Blogger API
    creds = Credentials(None, refresh_token=os.environ['BLOGGER_REFRESH_TOKEN'], token_uri="https://oauth2.googleapis.com/token", client_id=os.environ['BLOGGER_CLIENT_ID'], client_secret=os.environ['BLOGGER_CLIENT_SECRET'])
    if not creds.valid: creds.refresh(Request())
    service = build('blogger', 'v3', credentials=creds)
    
    try:
        service.posts().insert(blogId=os.environ['BLOGGER_ID'], body={'kind': 'blogger#post', 'title': title, 'content': final_content, 'labels': ['News', 'Viral', 'Update']}).execute()
        print(f"✅ BERHASIL TAYANG!")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik = get_mixed_topic() # Panggil fungsi pencari topik campuran
    judul, prompt_img, isi = generate_content_package(topik)
    if judul: post_to_blogger(judul, prompt_img, isi)
