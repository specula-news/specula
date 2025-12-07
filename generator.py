import json
import os
import requests
import yt_dlp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import time
import concurrent.futures

# --- 1. IMPORTERA KÄLLOR ---
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py! Inga NYA nyheter kommer hämtas.")
    SOURCES = []

print(f"--- STARTAR GENERATORN (HÄMTAR 10 PER KÄLLA) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# --- 2. FUNKTIONER (UPPDATERADE FÖR FLERA ARTIKLAR) ---

def scrape_article_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"): return og_image["content"]
            tw_image = soup.find("meta", name="twitter:image")
            if tw_image and tw_image.get("content"): return tw_image["content"]
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if src and src.startswith('http') and ('jpg' in src or 'png' in src): return src
    except Exception:
        pass
    return None

def get_video_info(source):
    """Hämtar de 10 senaste videorna från en kanal"""
    found_videos = []
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 10,  # ÖKAD FRÅN 5 TILL 10
        'ignoreerrors': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry: continue
                    
                    thumbnails = entry.get('thumbnails', [])
                    img_url = ""
                    if thumbnails:
                        best_thumb = min(thumbnails, key=lambda x: abs(x.get('width', 0) - 640))
                        img_url = best_thumb.get('url')
                    
                    if not img_url:
                        video_id = entry.get('id')
                        img_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    found_videos.append({
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "images": [img_url],
                        "summary": "Watch this video on YouTube.",
                        "category": source['cat'],
                        "source": info.get('uploader', 'YouTube'),
                        "time_str": "Recent",
                        "is_video": True
                    })
    except Exception:
        pass
    return found_videos

def get_web_info(source):
    """Hämtar de 10 senaste artiklarna från RSS"""
    found_articles = []
    try:
        response = requests.get(source['url'], headers=HEADERS, timeout=10)
        feed = feedparser.parse(response.content)
        
        # Loopar igenom de 10 första inläggen (ÖKAD FRÅN 5)
        for entry in feed.entries[:10]:
            img_url = ""
            if 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if link.type.startswith('image/'):
                        img_url = link.href
                        break
            elif 'enclosures' in entry and len(entry.enclosures) > 0:
                 img_url = entry.enclosures[0].href

            if not img_url:
                img_url = scrape_article_image(entry.link)

            summary_text = entry.get('summary', '')
            if '<' in summary_text:
                soup = BeautifulSoup(summary_text, 'html.parser')
                summary_text = soup.get_text()
            
            found_articles.append({
                "title": entry.title,
                "link": entry.link,
                "images": [img_url] if img_url else [],
                "summary": summary_text[:160] + "..." if len(summary_text) > 160 else summary_text,
                "category": source['cat'],
                "source": source.get('source_name', 'News'),
                "time_str": "Just Now",
                "is_video": False
            })
    except Exception:
        pass
    return found_articles

def process_source(source):
    if source['type'] == 'video':
        return get_video_info(source)
    else:
        return get_web_info(source)

# --- 3. KÖR PARALLELLT ---
new_articles = []
print(f"Startar hämtning...")

start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_to_source = {executor.submit(process_source, source): source for source in SOURCES}
    
    for future in concurrent.futures.as_completed(future_to_source):
        source = future_to_source[future]
        try:
            data_list = future.result() # Detta är nu en LISTA med artiklar
            if data_list:
                new_articles.extend(data_list) # Lägg till alla hittade
                print(f"Hämtade {len(data_list)} st från {source.get('source_name', 'YouTube')}")
        except Exception:
            pass

duration = time.time() - start_time
print(f"--- HÄMTNING KLAR PÅ {duration:.2f} SEKUNDER ---")

# --- 4. UPPDATERA NEWS.JSON ---
existing_data = []
try:
    if os.path.exists('news.json'):
        with open('news.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
except Exception:
    existing_data = []

# Slå ihop nytt och gammalt
all_news = new_articles + existing_data
unique_news = []
seen_links = set()

# Rensa dubbletter
for article in all_news:
    if article['link'] not in seen_links:
        unique_news.append(article)
        seen_links.add(article['link'])

# ÖKA GRÄNSEN TILL 400 ARTIKLAR (För att få fler sidor)
final_news = unique_news[:400]

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"Databas uppdaterad. Totalt {len(final_news)} artiklar.")

# --- 5. BYGG HTML ---
json_data = json.dumps(final_news)

try:
    with open('template_fixed.html', 'r', encoding='utf-8') as f:
        template_code = f.read()
    
    final_html = template_code.replace("<!-- NEWS_DATA_JSON -->", json_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("SUCCESS: index.html har uppdaterats med den nya mallen!")

except Exception as e:
    print(f"KRITISKT FEL: {e}")