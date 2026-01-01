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
delay_detik = random.randint(30, 180) # Delay agak lama biar aman 5x post
print(f"⏳ Menunggu {delay_detik} detik agar aktivitas natural...")
time.sleep(delay_detik)

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- SUMBER 1: GOOGLE TRENDS (Berita Viral) ---
def get_google_trends():
    print("🔍 Mengecek Google Trends...")
    try:
        url = "https://trends.google.co.id/trends/trendingsearches/daily/rss?geo=ID"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            if items:
                return [item.find('title').text for item in items[:7]]
    except Exception as e:
        print(f"⚠️ Gagal Google Trends: {e}")
    return []

# --- SUMBER 2: CNN / SUMBER BERITA LAIN ---
def get_cnn_news():
    print("🔍 Mengecek Portal Berita...")
    try:
        url = "https://www.cnnindonesia.com/teknologi/rss"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            titles = []
            for item in items[:5]:
                titles.append(item.find('title').text)
            return titles
    except Exception as e:
        print(f"⚠️ Gagal CNN News: {e}")
    return []

# --- SUMBER 3: AI TUTORIAL GENERATOR (KHUSUS TUTORIAL) ---
def generate_tutorial_idea():
    print("🧠 Meminta AI mencari ide Tutorial Baru...")
    try:
        # Kita minta Gemini cari ide tutorial spesifik
        prompt = "Berikan 1 saja Judul Tutorial Teknologi/Coding/Android/AI yang sangat dicari pemula di tahun 2026. Judul harus spesifik. Contoh: 'Cara Install Python di Android', 'Cara Membuat Bot WhatsApp Gratis'. Hanya berikan Judulnya saja tanpa tanda kutip."
        response = model.generate_content(prompt)
        judul_tutorial = response.text.strip().replace('"', '')
        print(f"💡 Ide Tutorial AI: {judul_tutorial}")
        return [judul_tutorial]
    except Exception as e:
        print(f"⚠️ Gagal Generate Ide Tutorial: {e}")
        return []

def get_mixed_topic():
    """
    Logika Pemilihan Topik:
    Kita perbesar peluang munculnya TUTORIAL.
    """
    # Kita buat 'tiket undian'. Tutorial kita kasih tiket lebih banyak.
    # 40% Tutorial AI, 30% Google Trends, 30% Berita Tekno
    sources = [
        generate_tutorial_idea, generate_tutorial_idea, # Tutorial ada 2 tiket (Peluang lebih besar)
        get_google_trends,
        get_cnn_news,
        get_google_trends # Tambah trends lagi biar imbang
    ]
    
    random.shuffle(sources) # Acak urutan
    
    for source_func in sources:
        topics = source_func() # Jalankan fungsi pencari topik
        if topics:
            chosen = random.choice(topics)
            chosen = chosen.replace('"', '').replace("'", "")
            print(f"✅ TOPIK TERPILIH: {chosen}")
            return chosen
            
    return "Tutorial Cara Menggunakan ChatGPT untuk Pemula" # Fallback terakhir

def generate_content_package(topik):
    print(f"🤖 Gemini sedang menulis artikel untuk: {topik}...")
    
    prompt = f"""
    Bertindaklah sebagai Ahli IT dan Blogger Tekno Profesional.
    Topik Utama: "{topik}"
    
    Tugasmu:
    1. Buat Judul Clickbait yang Edukatif (Hindari kata: Terbongkar/Wow). Gunakan kata seperti "Cara", "Panduan", "Tutorial", "Trik".
    2. Buat Keyword Gambar (Inggris, Max 4 kata, Visual Jelas).
    3. Buat Isi Artikel Tutorial/Berita Lengkap (Bahasa Indonesia).
    
    INSTRUKSI ISI ARTIKEL:
    - Jika ini Tutorial: Wajib ada "Langkah-langkah" (Step by Step) yang jelas memakai numbering.
    - Gaya bahasa: Seperti mengajari teman sendiri (akrab tapi jelas).
    - Panjang: Minimal 700 kata (Mendalam).
    - Struktur HTML: Gunakan <h2>, <h3>, <ul> atau <ol> untuk langkah-langkah, dan <p>.
    
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
            return f"Panduan: {topik}", "tech tutorial illustration", raw_text
    except Exception as e:
        print(f"❌ Error AI: {e}")
        return None, None, None

def upload_to_imgbb(image_url, name_slug):
    api_key = os.environ.get('IMGBB_API_KEY')
    if not api_key: return image_url

    print(f"☁️ Proses Download & Upload Gambar...")
    for attempt in range(1, 4):
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
    raw_thumb = f"https://image.pollinations.ai/prompt/realistic%20tech%20photo%20{encoded_prompt}?width=1000&height=448&model=flux&nologo=true&seed={seed1}"
    raw_body = f"https://image.pollinations.ai/prompt/tutorial%20illustration%20{encoded_prompt}?width=1000&height=600&model=flux&nologo=true&seed={seed2}"
    
    print("1️⃣ Proses Thumbnail...")
    final_thumb = upload_to_imgbb(raw_thumb, f"thumb-{file_slug}")
    time.sleep(15)
    print("2️⃣ Proses Gambar Body...")
    final_body = upload_to_imgbb(raw_body, f"body-{file_slug}")
    
    # HTML Structure
    html_thumb = f'<div class="separator" style="display: none;"><img src="{final_thumb}" alt="{title}" /></div>'
    html_body_img = f'<div class="separator" style="clear: both; text-align: center; margin: 30px 0;"><img src="{final_body}" width="640" height="384" style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" /></div><br/>'
    
    # Insert Logic (Setelah Paragraf 1)
    pos = content.find('</p>')
    final_content = html_thumb + (content[:pos+4] + html_body_img + content[pos+4:] if pos != -1 else html_body_img + content)

    # Blogger API
    creds = Credentials(None, refresh_token=os.environ['BLOGGER_REFRESH_TOKEN'], token_uri="https://oauth2.googleapis.com/token", client_id=os.environ['BLOGGER_CLIENT_ID'], client_secret=os.environ['BLOGGER_CLIENT_SECRET'])
    if not creds.valid: creds.refresh(Request())
    service = build('blogger', 'v3', credentials=creds)
    
    label_list = ['Tutorial', 'Teknologi', 'Tips & Trik'] # Label khusus Tutorial
    
    try:
        service.posts().insert(blogId=os.environ['BLOGGER_ID'], body={'kind': 'blogger#post', 'title': title, 'content': final_content, 'labels': label_list}).execute()
        print(f"✅ BERHASIL TAYANG!")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik = get_mixed_topic()
    judul, prompt_img, isi = generate_content_package(topik)
    if judul: post_to_blogger(judul, prompt_img, isi)
