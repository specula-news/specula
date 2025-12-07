import json
import os
import requests
import yt_dlp
import feedparser
from datetime import datetime

# --- 1. IMPORTERA KÄLLOR FRÅN SOURCES.PY ---
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py! Inga NYA nyheter kommer hämtas.")
    SOURCES = []

print("--- STARTAR HÄMTNING AV NYHETER ---")

# --- 2. HÄMTA DATA (SCRAPING) ---
new_articles = []

def get_video_info(source):
    """Hämtar senaste videon från YouTube"""
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
                    return {
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "images": [entry.get('thumbnails')[-1]['url']] if entry.get('thumbnails') else [],
                        "summary": "YouTube Video",
                        "category": source['cat'],
                        "source": info.get('uploader', 'YouTube'),
                        "time_str": "New Video",
                        "is_video": True
                    }
    except Exception as e:
        print(f"Fel vid YouTube ({source['url']}): {e}")
    return None

def get_web_info(source):
    """Hämtar nyheter från Webb/RSS"""
    try:
        feed = feedparser.parse(source['url'])
        if feed.entries:
            entry = feed.entries[0]
            img_url = ""
            if 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if link.type.startswith('image/'):
                        img_url = link.href
                        break
            
            return {
                "title": entry.title,
                "link": entry.link,
                "images": [img_url] if img_url else [],
                "summary":  entry.get('summary', '')[:150] + "...",
                "category": source['cat'],
                "source": source.get('source_name', 'Web News'),
                "time_str": "Just now",
                "is_video": False
            }
    except Exception as e:
        print(f"Fel vid Webb ({source['url']}): {e}")
    return None

# Kör loopen genom alla källor
for source in SOURCES:
    item = None
    if source['type'] == 'video':
        item = get_video_info(source)
    else:
        item = get_web_info(source)
    
    if item:
        new_articles.append(item)
        print(f"Hittade: {item['title']}")

# --- 3. UPPDATERA NEWS.JSON ---
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
    if article['link'] not in seen_links:
        unique_news.append(article)
        seen_links.add(article['link'])

# Spara max 200 artiklar
final_news = unique_news[:200]

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_news, f, ensure_ascii=False, indent=2)

print(f"Databas uppdaterad. Totalt {len(final_news)} artiklar.")

# Förbered data för HTML
json_data = json.dumps(final_news)

# --- 4. BYGG HEMSIDAN (INDEX.HTML) ---
# Läser in din design från template.html och stoppar in nyheterna
try:
    with open('template.html', 'r', encoding='utf-8') as f:
        template_code = f.read()
    
    final_html = template_code.replace("<!-- NEWS_DATA_JSON -->", json_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("SUCCESS: Hemsidan (index.html) är uppdaterad!")
except Exception as e:
    print(f"FEL vid skapandet av HTML: {e}")