import os
import random
import time
import urllib.parse
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# --- KONFIGURASI ---
# 1. Delay acak (Anti-Deteksi)
delay_detik = random.randint(30, 300) # Tunggu 30 detik - 5 menit
print(f"⏳ Menunggu {delay_detik} detik agar terlihat natural...")
time.sleep(delay_detik)

# 2. Setup AI
genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-flash')

def get_random_topic():
    topik_list = [
        "Tutorial Termux Hacking Tools Pemula",
        "Cara Config Cisco Router Dasar",
        "Masa Depan AI Artificial Intelligence",
        "Trik Internet Gratis Termux",
        "Belajar Jaringan Komputer Dasar",
        "Cara Membuat Bot WhatsApp Python"
    ]
    return random.choice(topik_list)

def generate_content(topik):
    print(f"🤖 Sedang menulis artikel tentang: {topik}...")
    
    # Encode topik untuk URL gambar
    img_keyword = urllib.parse.quote(topik)
    
    # URL Gambar AI (Gratis via Pollinations)
    img_thumb = f"https://image.pollinations.ai/prompt/realistic%20tech%20blog%20thumbnail%20{img_keyword}?width=1000&height=448&nologo=true"
    img_body = f"https://image.pollinations.ai/prompt/coding%20hacking%20{img_keyword}?width=600&height=400&nologo=true"

    prompt = f"""
    Buatkan artikel blog seru tentang "{topik}" dalam Bahasa Indonesia.
    
    GAYA BAHASA (WAJIB):
    - Santai, gaul, seperti ngobrol sama teman (pake kata 'Gue/Aku', 'Lo/Kalian', 'Gaskeun', 'Worth it').
    - Jangan kaku kayak robot! Masukkan opini pribadi atau curhatan dikit.
    - Minimal 1000 karakter.
    
    STRUKTUR HTML (WAJIB):
    1. Awal postingan (Hidden Thumbnail): 
       <div class="separator" style="display: none; text-align: center;"><img src="{img_thumb}" /></div>
    2. Paragraf pembuka yang 'hook' (bikin penasaran).
    3. Penjelasan materi (Pake Heading <h2>).
    4. Gambar Tengah: <div class="separator" style="clear: both; text-align: center;"><img src="{img_body}" style="border-radius: 10px; margin: 20px auto; display: block;" /></div>
    5. Tutorial step-by-step (jika ada).
    6. Kesimpulan & Ajakan Share.
    
    OUTPUT: HANYA KODE HTML BAGIAN ISI ARTIKEL SAJA.
    """
    
    response = model.generate_content(prompt)
    return response.text

def post_to_blogger(title, content):
    print("🚀 Menghubungkan ke Blogger...")
    
    creds = Credentials(
        None,
        refresh_token=os.environ['BLOGGER_REFRESH_TOKEN'],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ['BLOGGER_CLIENT_ID'],
        client_secret=os.environ['BLOGGER_CLIENT_SECRET']
    )
    
    if not creds.valid:
        creds.refresh(Request())
        
    service = build('blogger', 'v3', credentials=creds)
    
    body = {
        'kind': 'blogger#post',
        'title': f"{title} - Edisi Belajar",
        'content': content,
        'labels': ['Tutorial', 'Teknologi', 'AutoPost']
    }
    
    try:
        post = service.posts().insert(blogId=os.environ['BLOGGER_ID'], body=body).execute()
        print(f"✅ SUKSES! Lihat di: {post['url']}")
    except Exception as e:
        print(f"❌ Gagal Posting: {e}")

if __name__ == "__main__":
    topik = get_random_topic()
    isi_html = generate_content(topik)
    post_to_blogger(topik, isi_html)
