import json
import os
import requests
import yt_dlp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import time

# --- 1. IMPORTERA KÄLLOR FRÅN SOURCES.PY ---
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py! Inga NYA nyheter kommer hämtas.")
    SOURCES = []

print("--- STARTAR GENERATORN (MED SMART SCRAPING) ---")

# "Fake" headers för att se ut som en riktig webbläsare (undviker blockering)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# --- 2. HJÄLPFUNKTIONER ---

def scrape_article_image(url):
    """Går in på hemsidan och letar efter huvudbilden (og:image)"""
    try:
        # 3 sekunders timeout så vi inte fastnar
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # 1. Leta efter Open Graph image (standard för delning)
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]
            
            # 2. Reservplan: Twitter image
            tw_image = soup.find("meta", name="twitter:image")
            if tw_image and tw_image.get("content"):
                return tw_image["content"]
                
            # 3. Sista utväg: Hitta första bästa <img> tagg som ser stor ut
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if src and src.startswith('http') and ('jpg' in src or 'png' in src):
                    return src
    except Exception:
        pass
    return None

def get_video_info(source):
    """Hämtar videoinfo och väljer en lagom stor tumnagel (inte 4K)"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 2,
        'ignoreerrors': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry: continue
                    
                    # Logik för att välja bild: 
                    # Vi vill ha 'hqdefault' (480p) eller 'sddefault' (640p).
                    # 'maxresdefault' är ofta för tung (flera MB).
                    thumbnails = entry.get('thumbnails', [])
                    img_url = ""
                    
                    if thumbnails:
                        # Hitta en bild som är närmast 640px bred (lagom kvalitet för webben)
                        # Detta sorterar listan och tar den som är närmast 640px
                        best_thumb = min(thumbnails, key=lambda x: abs(x.get('width', 0) - 640))
                        img_url = best_thumb.get('url')
                    
                    # Fallback om yt-dlp inte gav thumbnails struktur
                    if not img_url:
                        video_id = entry.get('id')
                        # Använder hqdefault.jpg som är standard 480x360 (säkert kort)
                        img_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    return {
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "images": [img_url],
                        "summary": "Watch this video on YouTube.",
                        "category": source['cat'],
                        "source": info.get('uploader', 'YouTube'),
                        "time_str": "New Video",
                        "is_video": True
                    }
    except Exception as e:
        print(f"YouTube-fel ({source['url']}): {e}")
    return None

def get_web_info(source):
    """Hämtar RSS och skrapar fram bild om den saknas"""
    try:
        # Använd headers även för RSS om möjligt (vissa flöden kräver det)
        # Vi hämtar rådatan först med requests för att kunna fejka headers
        response = requests.get(source['url'], headers=HEADERS, timeout=10)
        feed = feedparser.parse(response.content)
        
        if feed.entries:
            entry = feed.entries[0]
            img_url = ""
            
            # 1. Kolla om bild finns direkt i RSS (enclosures/media_content)
            if 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if link.type.startswith('image/'):
                        img_url = link.href
                        break
            elif 'enclosures' in entry and len(entry.enclosures) > 0:
                 img_url = entry.enclosures[0].href

            # 2. Om ingen bild hittades i RSS, gå in på sidan och "skrapa" den
            # Detta fixar Aftonbladet, SCMP, etc som ofta inte skickar bild i RSS
            if not img_url:
                print(f"   -> Saknar bild, skrapar: {entry.title[:30]}...")
                img_url = scrape_article_image(entry.link)

            # Rensa sammanfattning från HTML-taggar
            summary_text = entry.get('summary', '')
            if '<' in summary_text:
                soup = BeautifulSoup(summary_text, 'html.parser')
                summary_text = soup.get_text()
            
            return {
                "title": entry.title,
                "link": entry.link,
                "images": [img_url] if img_url else [],
                "summary": summary_text[:160] + "..." if len(summary_text) > 160 else summary_text,
                "category": source['cat'],
                "source": source.get('source_name', 'News'),
                "time_str": "Just Now",
                "is_video": False
            }
    except Exception as e:
        print(f"Webb-fel ({source['url']}): {e}")
    return None

# --- 3. KÖR LOOPEN ---
new_articles = []
print("Börjar hämta nyheter...")

for source in SOURCES:
    # Liten paus för att vara snäll mot servrarna och inte bli blockad
    time.sleep(0.5) 
    
    item = None
    if source['type'] == 'video':
        item = get_video_info(source)
    else:
        item = get_web_info(source)
    
    if item:
        new_articles.append(item)
        print(f"OK: {item['title'][:40]}")
    else:
        print(f"FAIL: {source['url']}")

# --- 4. UPPDATERA NEWS.JSON ---
existing_data = []
try:
    if os.path.exists('news.json'):
        with open('news.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
except Exception:
    existing_data = []

# Lägg nya nyheter först
all_news = new_articles + existing_data
unique_news = []
seen_links = set()

for article in all_news:
    # Använd länken som unikt ID för att undvika dubbletter
    if article['link'] not in seen_links:
        unique_news.append(article)
        seen_links.add(article['link'])

# Spara max 200 artiklar så filen inte blir för stor
final_news = unique_news[:200]

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"Databas uppdaterad. Totalt {len(final_news)} artiklar.")

# --- 5. BYGG HTML ---
json_data = json.dumps(final_news)

try:
    # Vi läser in din template.html (se till att den filen finns i repot)
    with open('template.html', 'r', encoding='utf-8') as f:
        template_code = f.read()
    
    final_html = template_code.replace("<!-- NEWS_DATA_JSON -->", json_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("SUCCESS: index.html har uppdaterats!")
except Exception as e:
    print(f"FEL vid HTML-generering: {e}")