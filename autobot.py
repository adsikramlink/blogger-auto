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

def get_hot_trend():
    """Mencari Berita Trending di Google Trends Indonesia"""
    print("🔥 Mencari topik panas di Google Trends...")
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
        "Tutorial Python untuk Pemula Lengkap",
        "Cara Menghasilkan Uang dari Blog di Tahun 2025",
        "Rekomendasi HP Gaming Murah Spek Dewa",
        "Tips Menjaga Keamanan Data Pribadi di Internet",
        "Masa Depan AI dan Dampaknya bagi Lapangan Pekerjaan"
    ])

def generate_content_package(topik):
    print(f"🤖 Gemini sedang meracik konten kreatif untuk: {topik}...")
    
    # PROMPT BARU: ANTI-TERBONGKAR & LEBIH VARIASI
    prompt = f"""
    Bertindaklah sebagai Ahli SEO dan Jurnalis Senior.
    Tugasmu:
    1. Buat Judul Clickbait yang UNIK dan BERVARIASI (Bahasa Indonesia).
    2. Buat Keyword Gambar (BAHASA INGGRIS, MAX 4 KATA, Visual Deskriptif).
    3. Buat Isi Artikel (Bahasa Indonesia).
    
    Topik: "{topik}"
    
    ATURAN KHUSUS JUDUL (PENTING!):
    - DILARANG MEMULAI JUDUL DENGAN KATA: "TERBONGKAR", "RAHASIA", "WOW", "HEBOH", "GEGER".
    - Gunakan variasi gaya judul seperti:
      a. Pertanyaan (Contoh: "Benarkah...?", "Kenapa...?")
      b. Angka/Listicle (Contoh: "5 Alasan...", "7 Fakta...")
      c. Solusi/Benefit (Contoh: "Cara Mudah...", "Tips Ampuh...")
      d. Peringatan (Contoh: "Hati-hati...", "Jangan Lakukan...")
    - Maksimal 60 karakter.
    
    ATURAN ISI (HTML Body Only):
    - Gunakan tag <h2> dan <h3>.
    - Paragraf pertama mengandung keyword "{topik}".
    - Panjang: Minimal 600 kata.
    - Gunakan tag <p> untuk setiap paragraf.
    
    WAJIB GUNAKAN FORMAT OUTPUT PEMISAH INI (|||):
    JUDUL_SEO_INDONESIA ||| KEYWORD_GAMBAR_INGGRIS ||| KODE_HTML_ISI_ARTIKEL
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        parts = raw_text.split("|||")
        if len(parts) >= 3:
            judul = parts[0].strip()
            img_prompt = parts[1].strip()
            isi = "|||".join(parts[2:]).strip()
            return judul, img_prompt, isi
        else:
            return f"Berita Update: {topik}", "technology news illustration", raw_text
            
    except Exception as e:
        print(f"❌ Error AI Gemini: {e}")
        return None, None, None

def upload_to_imgbb(image_url, name_slug):
    """
    Upload ke ImgBB dengan Logika RETRY (Cuba Lagi) jika gagal.
    """
    api_key = os.environ.get('IMGBB_API_KEY')
    if not api_key:
        print("⚠️ IMGBB_API_KEY tidak ditemukan.")
        return image_url

    print(f"☁️ Memulai proses download & upload...")
    
    # SISTEM RETRY: Mencoba maksimal 3 kali
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"   -> Percobaan ke-{attempt} mendownload gambar...")
            
            # Timeout 120 detik (2 Menit) - Memberi masa AI melukis
            img_response = requests.get(image_url, timeout=120)
            
            if img_response.status_code == 200:
                print("   -> Download sukses! Mengirim ke ImgBB...")
                img_b64 = base64.b64encode(img_response.content)
                
                upload_url = "https://api.imgbb.com/1/upload"
                payload = {
                    "key": api_key,
                    "image": img_b64,
                    "name": name_slug[:30]
                }
                
                # Timeout upload 60 detik
                res = requests.post(upload_url, data=payload, timeout=60)
                
                if res.status_code == 200:
                    data = res.json()
                    hosted_url = data['data']['url']
                    print(f"✅ SUKSES UPLOAD: {hosted_url}")
                    return hosted_url 
                else:
                    print(f"⚠️ Gagal Upload API ImgBB: {res.text}")
            else:
                print(f"⚠️ Gagal download dari AI (Status: {img_response.status_code})")
                
        except Exception as e:
            print(f"⚠️ Error pada percobaan {attempt}: {e}")
        
        # Jika gagal, tunggu 15 detik sebelum cuba lagi
        if attempt < max_retries:
            print("⏳ Menunggu 15 detik sebelum mencuba lagi...")
            time.sleep(15)

    print("⚠️ Gagal total setelah 3x percubaan. Menggunakan link asal.")
    return image_url

def post_to_blogger(title, img_prompt_en, content):
    print(f"🚀 Memulai posting: {title}")
    
    clean_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', img_prompt_en)
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed1 = random.randint(1, 9999)
    seed2 = random.randint(1, 9999)
    file_slug = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())

    # --- SIAPKAN URL GAMBAR ---
    raw_thumb_url = f"https://image.pollinations.ai/prompt/realistic%20photo%20{encoded_prompt}?width=1000&height=448&model=flux&nologo=true&seed={seed1}"
    raw_body_url = f"https://image.pollinations.ai/prompt/illustration%20art%20{encoded_prompt}?width=1000&height=600&model=flux&nologo=true&seed={seed2}"
    
    # --- UPLOAD KE IMGBB (Urutan Sabar) ---
    
    print("1️⃣ [THUMBNAIL] Sedang diproses...")
    final_thumb_url = upload_to_imgbb(raw_thumb_url, f"thumb-{file_slug}")
    
    print("⏳ Rehat 15 saat agar server ImgBB tidak menolak...")
    time.sleep(15) 
    
    print("2️⃣ [GAMBAR BODY] Sedang diproses...")
    final_body_url = upload_to_imgbb(raw_body_url, f"body-{file_slug}")
    
    # --- SUSUN HTML ---
    
    # 1. THUMBNAIL (HIDDEN)
    html_thumbnail = f"""
    <div class="separator" style="display: none;">
        <img src="{final_thumb_url}" alt="{title}" />
    </div>
    """
    
    # 2. GAMBAR ILUSTRASI (VISIBLE)
    html_body_image = f"""
    <div class="separator" style="clear: both; text-align: center; margin: 30px 0;">
        <a href="{final_body_url}" style="margin-left: 1em; margin-right: 1em;">
            <img border="0" src="{final_body_url}" width="640" height="384" style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" alt="Ilustrasi {title}" />
        </a>
    </div>
    <br/>
    """
    
    # --- LOGIKA PENYISIPAN (SETELAH PARAGRAF PERTAMA) ---
    posisi_sisip = content.find('</p>')
    
    if posisi_sisip != -1:
        posisi_sisip += 4 
        isi_final_body = content[:posisi_sisip] + html_body_image + content[posisi_sisip:]
    else:
        isi_final_body = html_body_image + content

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
        print(f"✅ SUKSES: {post['url']}")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik = get_hot_trend()
    if not topik:
        topik = get_backup_topic()
        
    judul, prompt_gambar, isi = generate_content_package(topik)
    
    if judul and prompt_gambar and isi:
        post_to_blogger(judul, prompt_gambar, isi)
    else:
        print("❌ Gagal generate konten.")
