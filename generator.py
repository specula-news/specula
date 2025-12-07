import json
import os
import requests
import yt_dlp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import time
import concurrent.futures # För att hämta 10 saker samtidigt

# --- 1. IMPORTERA KÄLLOR FRÅN SOURCES.PY ---
# Detta gör att koden håller sig ren. Du ändrar länkarna i sources.py istället.
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py! Se till att filen finns.")
    SOURCES = []

print(f"--- STARTAR GENERATORN (OPTIMERING: PÅ) ---")

# "Fake" headers för att se ut som en riktig webbläsare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# --- 2. OPTIMERADE FUNKTIONER ---

def scrape_article_image(url):
    """Går in på hemsidan och letar efter huvudbilden (og:image)"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Prioritera Open Graph (Facebook/Social media bild)
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]
            
            # Twitter bild
            tw_image = soup.find("meta", name="twitter:image")
            if tw_image and tw_image.get("content"):
                return tw_image["content"]
                
            # Första bästa bild
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if src and src.startswith('http') and ('jpg' in src or 'png' in src):
                    return src
    except Exception:
        pass
    return None

def get_video_info(source):
    """Hämtar videoinfo och väljer en lagom stor tumnagel (SNABB)"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True, # Hämtar bara info, laddar inte ner videon
        'playlistend': 2,     # Bara de 2 senaste
        'ignoreerrors': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry: continue
                    
                    # Hitta optimal bildstorlek (c:a 640px bred) istället för tung 4K
                    thumbnails = entry.get('thumbnails', [])
                    img_url = ""
                    
                    if thumbnails:
                        best_thumb = min(thumbnails, key=lambda x: abs(x.get('width', 0) - 640))
                        img_url = best_thumb.get('url')
                    
                    if not img_url:
                        video_id = entry.get('id')
                        img_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    return {
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "images": [img_url],
                        "summary": "Click to watch video.",
                        "category": source['cat'],
                        "source": info.get('uploader', 'YouTube'),
                        "time_str": "New Video",
                        "is_video": True
                    }
    except Exception as e:
        # Tyst felhantering för att inte spamma loggen
        pass
    return None

def get_web_info(source):
    """Hämtar RSS och skrapar fram bild om den saknas"""
    try:
        response = requests.get(source['url'], headers=HEADERS, timeout=10)
        feed = feedparser.parse(response.content)
        
        if feed.entries:
            entry = feed.entries[0]
            img_url = ""
            
            # Försök hitta bild i RSS-datan först
            if 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if link.type.startswith('image/'):
                        img_url = link.href
                        break
            elif 'enclosures' in entry and len(entry.enclosures) > 0:
                 img_url = entry.enclosures[0].href

            # Om ingen bild hittades, använd vår smarta scraper
            if not img_url:
                img_url = scrape_article_image(entry.link)

            # Städa upp texten
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
    except Exception:
        pass
    return None

# Wrapper-funktion för trådhanteraren
def process_source(source):
    if source['type'] == 'video':
        return get_video_info(source)
    else:
        return get_web_info(source)

# --- 3. KÖR PARALLELLT (TURBO MODE) ---
new_articles = []
print(f"Startar hämtning av {len(SOURCES)} källor med 10 trådar...")

start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Skicka alla jobb till poolen
    future_to_source = {executor.submit(process_source, source): source for source in SOURCES}
    
    # Ta emot resultaten allt eftersom de blir klara
    for future in concurrent.futures.as_completed(future_to_source):
        source = future_to_source[future]
        try:
            data = future.result()
            if data:
                new_articles.append(data)
                print(f"KLAR: {data['title'][:40]}...")
            else:
                print(f"INGEN NYHET: {source['url']}")
        except Exception as exc:
            print(f"FEL: {source['url']} genererade ett undantag: {exc}")

duration = time.time() - start_time
print(f"--- HÄMTNING KLAR PÅ {duration:.2f} SEKUNDER ---")

# --- 4. UPPDATERA DATABASEN (NEWS.JSON) ---
existing_data = []
try:
    if os.path.exists('news.json'):
        with open('news.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
except Exception:
    existing_data = []

# Lägg nya nyheter först i listan
all_news = new_articles + existing_data
unique_news = []
seen_links = set()

# Ta bort dubbletter
for article in all_news:
    if article['link'] not in seen_links:
        unique_news.append(article)
        seen_links.add(article['link'])

# Spara max 200 artiklar
final_news = unique_news[:200]

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"Sparade {len(final_news)} artiklar till news.json.")

# --- 5. SKAPA HTML-FILEN ---
json_data = json.dumps(final_news)

try:
    # Försök läsa in template.html (den snygga designen)
    with open('template.html', 'r', encoding='utf-8') as f:
        template_code = f.read()
    
    # Byt ut platshållaren mot riktig data
    final_html = template_code.replace("<!-- NEWS_DATA_JSON -->", json_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("SUCCESS: index.html har uppdaterats korrekt!")

except Exception as e:
    print(f"KRITISKT FEL: Kunde inte läsa template.html: {e}")
    print("Se till att 'template.html' finns i din mapp.")