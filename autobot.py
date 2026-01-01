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
# Delay acak (30-120 detik) agar aktivitas terlihat natural di mata Google
delay_detik = random.randint(30, 120)
print(f"⏳ Menunggu {delay_detik} detik...")
time.sleep(delay_detik)

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-2.5-flash')

def get_hot_trend():
    """Mencari Berita Trending di Google Trends Indonesia (RSS Feed)"""
    print("🔥 Mencari topik panas di Google Trends...")
    try:
        url = "https://trends.google.co.id/trends/trendingsearches/daily/rss?geo=ID"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            # Ambil 7 topik teratas untuk variasi
            top_items = items[:7]
            if top_items:
                chosen = random.choice(top_items)
                judul = chosen.find('title').text
                # Bersihkan tanda kutip agar tidak mengganggu prompt
                judul = judul.replace('"', '').replace("'", "")
                print(f"✅ Topik Ditemukan: {judul}")
                return judul
    except Exception as e:
        print(f"⚠️ Gagal ambil Trends: {e}")
    return None

def get_backup_topic():
    """Topik cadangan jika Google Trends tidak bisa diakses"""
    return random.choice([
        "Tutorial Python untuk Pemula Lengkap",
        "Cara Menghasilkan Uang dari Blog di Tahun 2026",
        "Rekomendasi HP Gaming Murah Spek Dewa",
        "Tips Menjaga Keamanan Data Pribadi di Internet",
        "Masa Depan AI dan Dampaknya bagi Lapangan Pekerjaan"
    ])

def generate_content_package(topik):
    """Meminta AI membuat Judul, Prompt Gambar (Inggris), dan Isi Artikel"""
    print(f"🤖 Gemini sedang meracik konten dan prompt gambar untuk: {topik}...")
    
    prompt = f"""
    Bertindaklah sebagai Ahli SEO dan Jurnalis Senior.
    Tugasmu ada 3 hal:
    1. Buat Judul Clickbait yang Menarik (Bahasa Indonesia).
    2. Buat Keyword untuk Gambar (BAHASA INGGRIS, MAX 4 KATA, Visual Deskriptif, Jangan pakai nama orang spesifik).
    3. Buat Isi Artikel Lengkap (Bahasa Indonesia).
    
    Topik Utama: "{topik}"
    
    ATURAN ISI ARTIKEL (HTML Body Only):
    - Gunakan tag <h2> dan <h3> untuk struktur SEO.
    - Paragraf pertama WAJIB mengandung keyword "{topik}".
    - Gaya bahasa: Santai, Mengalir, Mudah dibaca (Human-friendly).
    - Panjang: Minimal 600 kata agar dianggap konten mendalam oleh Google.
    
    WAJIB GUNAKAN FORMAT OUTPUT PEMISAH INI (|||):
    JUDUL_SEO_INDONESIA ||| KEYWORD_GAMBAR_INGGRIS ||| KODE_HTML_ISI_ARTIKEL
    """
    
    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # Memisahkan output AI berdasarkan pemisah |||
        parts = raw_text.split("|||")
        if len(parts) >= 3:
            judul = parts[0].strip()
            img_prompt = parts[1].strip()
            # Menggabungkan sisa bagian jika ada ||| berlebih di dalam isi artikel
            isi = "|||".join(parts[2:]).strip()
            return judul, img_prompt, isi
        else:
            # Fallback darurat jika format AI ngaco
            print("⚠️ Format output AI tidak sesuai, menggunakan fallback.")
            return f"Berita Viral: {topik}", "technology news illustration", raw_text
            
    except Exception as e:
        print(f"❌ Error AI Gemini: {e}")
        return None, None, None

def upload_to_imgbb(image_url, name_slug):
    """
    FUNGSI PENTING: Mendownload gambar AI lalu upload ke ImgBB.
    Ini membuat loading blog jauh lebih cepat.
    """
    api_key = os.environ.get('IMGBB_API_KEY')
    if not api_key:
        print("⚠️ IMGBB_API_KEY tidak ditemukan di Secrets. Menggunakan link asli (agak lambat).")
        return image_url

    print(f"☁️ Sedang memproses upload gambar ke server cepat (ImgBB)...")
    try:
        # 1. Download gambar mentah dari Pollinations
        img_response = requests.get(image_url, timeout=25)
        if img_response.status_code == 200:
            # 2. Convert gambar ke format Base64 untuk upload
            img_b64 = base64.b64encode(img_response.content)
            
            # 3. Kirim ke API ImgBB
            upload_url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": api_key,
                "image": img_b64,
                "name": name_slug[:30] # Batasi panjang nama file
            }
            # Timeout agak lama karena proses upload butuh waktu
            res = requests.post(upload_url, data=payload, timeout=30)
            
            if res.status_code == 200:
                data = res.json()
                # Ambil URL gambar langsung (direct link)
                hosted_url = data['data']['url']
                print(f"✅ Gambar berhasil di-host: {hosted_url}")
                return hosted_url
            else:
                print(f"⚠️ Gagal Upload ke ImgBB (API Error): {res.text}")
        else:
             print(f"⚠️ Gagal download gambar sumber dari AI.")

    except Exception as e:
        print(f"⚠️ Error dalam proses upload gambar: {e}")
    
    # FALLBACK PENTING: Kalau upload gagal, tetap pakai link asli biar bot gak error
    print("⚠️ Menggunakan link gambar asli sebagai cadangan.")
    return image_url

def post_to_blogger(title, img_prompt_en, content):
    print(f"🚀 Memulai proses posting: {title}")
    
    # Bersihkan prompt gambar (hanya huruf angka spasi) agar URL valid
    clean_prompt = re.sub(r'[^a-zA-Z0-9\s]', '', img_prompt_en)
    encoded_prompt = urllib.parse.quote(clean_prompt)
    
    # Seed acak agar gambar selalu unik tiap hari
    seed1 = random.randint(1, 9999)
    seed2 = random.randint(1, 9999)
    
    # Buat slug nama file dari judul untuk ImgBB
    file_slug = re.sub(r'[^a-zA-Z0-9]', '-', title.lower())

    # --- TAHAP 1: Siapkan URL Asli AI ---
    # Thumbnail Wajib 1000x448 (Model Flux agar stabil)
    raw_thumb_url = f"https://image.pollinations.ai/prompt/realistic%20photo%20{encoded_prompt}?width=1000&height=448&model=flux&nologo=true&seed={seed1}"
    # Gambar Body Wajib 1000x600 (Model Flux)
    raw_body_url = f"https://image.pollinations.ai/prompt/illustration%20art%20{encoded_prompt}?width=1000&height=600&model=flux&nologo=true&seed={seed2}"
    
    # --- TAHAP 2: Upload ke Hosting Cepat (ImgBB) ---
    print("1️⃣ Memproses Gambar Thumbnail (Hidden)...")
    final_thumb_url = upload_to_imgbb(raw_thumb_url, f"thumb-{file_slug}")
    
    print("2️⃣ Memproses Gambar Ilustrasi (Body)...")
    final_body_url = upload_to_imgbb(raw_body_url, f"body-{file_slug}")
    
    # --- TAHAP 3: Menyusun HTML Postingan ---
    
    # A. HTML Thumbnail (Disembunyikan dengan display: none)
    html_thumbnail = f"""
    <div class="separator" style="display: none;">
        <img src="{final_thumb_url}" alt="{title}" />
    </div>
    """
    
    # B. HTML Gambar Body (Ditampilkan jelas, ada shadow biar cantik)
    html_body_image = f"""
    <div class="separator" style="clear: both; text-align: center; margin: 30px 0;">
        <a href="{final_body_url}" style="margin-left: 1em; margin-right: 1em;">
            <img border="0" src="{final_body_url}" width="640" height="384" style="width: 100%; height: auto; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" alt="Ilustrasi {title}" />
        </a>
    </div>
    """
    
    # C. Logika Penyisipan di Tengah Artikel (Smart Injection)
    # Cari titik tengah jumlah karakter
    titik_tengah = len(content) // 2
    # Cari akhir paragraf </p> terdekat setelah titik tengah
    posisi_sisip = content.find('</p>', titik_tengah)
    
    if posisi_sisip != -1:
        posisi_sisip += 4 # Geser setelah tag penutup </p>
        # Sisipkan gambar di antara paragraf tersebut
        isi_final_body = content[:posisi_sisip] + html_body_image + content[posisi_sisip:]
    else:
        # Fallback: Jika tidak ketemu </p> di tengah, cari Heading <h2> kedua
        posisi_sisip = content.find('<h2>', 100)
        if posisi_sisip != -1:
             isi_final_body = content[:posisi_sisip] + html_body_image + content[posisi_sisip:]
        else:
             # Fallback terakhir: Taruh di paling atas body text jika struktur aneh
             isi_final_body = html_body_image + content

    # Gabungkan Thumbnail Hidden + Isi Body yang sudah disisipi gambar
    final_content = html_thumbnail + isi_final_body

    # --- TAHAP 4: Kirim ke Blogger ---
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
        'labels': ['News', 'Viral', 'Update'] # Label otomatis
    }
    
    try:
        post = service.posts().insert(blogId=os.environ['BLOGGER_ID'], body=body).execute()
        print(f"✅ SUKSES! Postingan telah terbit: {post['url']}")
    except Exception as e:
        print(f"❌ Gagal Posting ke Blogger: {e}")

if __name__ == "__main__":
    # 1. Cari Topik
    topik = get_hot_trend()
    if not topik:
        topik = get_backup_topic()
        
    # 2. Generate Konten & Prompt Gambar via AI
    judul, prompt_gambar, isi = generate_content_package(topik)
    
    # 3. Proses Gambar & Posting
    if judul and prompt_gambar and isi:
        post_to_blogger(judul, prompt_gambar, isi)
    else:
        print("❌ Gagal dalam tahap generasi konten AI.")
