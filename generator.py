import json
import os
import requests
import yt_dlp
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import concurrent.futures
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
import urllib3
import re

# Stäng av SSL-varningar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- INSTÄLLNINGAR ---
MAX_ARTICLES_PER_SOURCE = 20
MAX_AGE_DAYS = 90
TOTAL_LIMIT = 2000

# --- 1. IMPORTERA KÄLLOR ---
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py!")
    SOURCES = []

print(f"--- STARTAR GENERATORN (AFTONBLADET JSON-LD FIX) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# --- 2. HJÄLPFUNKTIONER ---

def parse_date_to_timestamp(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return time.mktime(entry.published_parsed)
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return time.mktime(entry.updated_parsed)
        date_str = entry.get('published', entry.get('updated', ''))
        if date_str:
            return parsedate_to_datetime(date_str).timestamp()
    except: pass
    return time.time() - random.randint(3600, 86400)

def is_too_old(timestamp):
    limit = time.time() - (MAX_AGE_DAYS * 24 * 60 * 60)
    return timestamp < limit

def get_width_from_url(url):
    try:
        match = re.search(r'[?&]w=(\d+)', url)
        if match: return int(match.group(1))
    except: pass
    return 0

def clean_image_url(url):
    """ Fixar upplösning på bilderna. """
    if not url: return None
    
    # 1. PHYS.ORG
    if 'scx' in url or 'phys.org' in url or 'b-cdn.net' in url:
        if '/tmb/' in url:
            return url.replace('/tmb/', '/800/')
    
    # 2. AFTONBLADET (Måste ha parametrar, men vi maxar dem)
    if 'aftonbladet-cdn' in url:
        # Ersätt befintliga parametrar med maxade värden
        if 'w=' in url: url = re.sub(r'w=\d+', 'w=1200', url)
        else: url += '&w=1200'
        
        if 'q=' in url: url = re.sub(r'q=\d+', 'q=80', url)
        else: url += '&q=80'
        
        return url

    # 3. WORDPRESS / ELECTREK
    if 'wp.com' in url or 'electrek' in url or '9to5' in url:
        if 'w=' in url:
            return re.sub(r'w=\d+', 'w=1600', url)
            
    return url

def find_largest_image_on_page(soup, base_url):
    best_image = None
    max_score = 0
    images = soup.find_all('img')
    
    for img in images:
        candidates = []
        src = img.get('src')
        data_src = img.get('data-src') or img.get('data-original')
        if src: candidates.append(src)
        if data_src: candidates.append(data_src)
        
        srcset = img.get('srcset') or img.get('data-srcset')
        if srcset:
            parts = srcset.split(',')
            for p in parts:
                p = p.strip().split(' ')[0]
                if p: candidates.append(p)

        for url in candidates:
            if not url or 'base64' in url: continue
            full_url = urljoin(base_url, url)
            score = 0
            
            w_param = get_width_from_url(full_url)
            if w_param > 0: score = w_param
            elif img.get('width'):
                try: score = int(img['width'])
                except: pass
            elif 'data' in str(img.attrs) and score == 0:
                score = 600
            elif src and score == 0:
                score = 100

            lower = full_url.lower()
            if any(x in lower for x in ['logo', 'icon', 'avatar', 'tracker', 'pixel', 'footer']):
                score = 0
            
            if score > max_score:
                max_score = score
                best_image = full_url
    return best_image

def scrape_article_image(url):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        session = requests.Session()
        r = session.get(url, headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # --- METOD 1: JSON-LD (Guldstandarden för Aftonbladet) ---
            # Aftonbladet lägger huvudbilden i en dold JSON-struktur för Google
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Ibland är det en lista
                    if isinstance(data, list):
                        data = data[0]
                    
                    if 'image' in data:
                        img_data = data['image']
                        # Ibland är image en lista av URL:er
                        if isinstance(img_data, list):
                            return img_data[0] # Ta första
                        # Ibland är det ett objekt med url
                        elif isinstance(img_data, dict) and 'url' in img_data:
                            return img_data['url']
                        # Ibland är det bara en sträng
                        elif isinstance(img_data, str):
                            return img_data
                except: pass

            # --- METOD 2: OpenGraph ---
            og = soup.find("meta", property="og:image")
            if og and og.get("content"): return urljoin(url, og["content"])
            
            # --- METOD 3: Twitter ---
            tw = soup.find("meta", name="twitter:image")
            if tw and tw.get("content"): return urljoin(url, tw["content"])

            # --- METOD 4: DOM-analys ---
            largest = find_largest_image_on_page(soup, url)
            if largest: return largest
    except: pass
    return None

def get_video_info(source):
    found_videos = []
    ydl_opts = {'quiet': True, 'extract_flat': True, 'playlistend': MAX_ARTICLES_PER_SOURCE, 'ignoreerrors': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if not entry: continue
                    timestamp = time.time()
                    upload_date = entry.get('upload_date')
                    if upload_date:
                        try:
                            dt = datetime.strptime(upload_date, "%Y%m%d")
                            timestamp = dt.timestamp()
                        except: pass
                    
                    if is_too_old(timestamp): continue
                    
                    video_id = entry.get('id')
                    img_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    found_videos.append({
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "images": [img_url],
                        "summary": "Watch this video on YouTube.",
                        "category": source['cat'],
                        "source": source.get('source_name', 'YouTube'),
                        "time_str": "Recent",
                        "timestamp": timestamp,
                        "is_video": True
                    })
    except: pass
    return found_videos

def get_web_info(source):
    found_articles = []
    try:
        session = requests.Session()
        resp = session.get(source['url'], headers=HEADERS, timeout=10, verify=False)
        feed = feedparser.parse(resp.content)
        
        for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
            timestamp = parse_date_to_timestamp(entry)
            if is_too_old(timestamp): continue

            img_url = None
            
            # --- SKRAP-LISTA ---
            # Lägg till 'aftonbladet' här för att tvinga fram JSON-LD analysen
            force_scrape = any(x in source['url'] for x in [
                'dagensps', 'electrek', 'feber', 'nasa.gov', 'sweclockers', 'nyteknik', 'aftonbladet'
            ])
            
            if not force_scrape:
                # Kolla RSS
                if 'media_content' in entry:
                    try:
                        imgs = sorted(entry.media_content, key=lambda x: int(x.get('width', 0)), reverse=True)
                        imgs = [i for i in imgs if 'image' in i.get('type', 'image')]
                        if imgs: img_url = imgs[0]['url']
                    except: pass
                
                if not img_url and 'enclosures' in entry:
                    for enc in entry.enclosures:
                        if enc.type.startswith('image/'):
                            img_url = enc.href; break
                
                if not img_url:
                    content = entry.get('content', [{'value': ''}])[0]['value'] or entry.get('description', '') or entry.get('summary', '')
                    if content and '<img' in content:
                        try:
                            soup = BeautifulSoup(content, 'html.parser')
                            img = soup.find('img')
                            if img:
                                src = img.get('src')
                                if src and 'pixel' not in src: img_url = src
                        except: pass

            # Om force_scrape är sant, eller om ingen bild hittades
            # (Undantag för phys.org i molnet)
            if (not img_url and 'phys.org' not in source['url']) or force_scrape:
                scraped = scrape_article_image(entry.link)
                if scraped: img_url = scraped

            img_url = clean_image_url(img_url)

            summary = entry.get('summary', '') or entry.get('description', '')
            if '<' in summary:
                summary = BeautifulSoup(summary, 'html.parser').get_text()
            
            found_articles.append({
                "title": entry.title,
                "link": entry.link,
                "images": [img_url] if img_url else [],
                "summary": summary[:180] + "..." if len(summary) > 180 else summary,
                "category": source['cat'],
                "source": source.get('source_name', 'News'),
                "time_str": "Just Now",
                "timestamp": timestamp,
                "is_video": False
            })
    except: pass
    return found_articles

def process_source(source):
    if source['type'] == 'video': return get_video_info(source)
    else: return get_web_info(source)

# --- 3. EXEKVERING ---
new_articles = []
start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    future_map = {executor.submit(process_source, s): s for s in SOURCES}
    for future in concurrent.futures.as_completed(future_map):
        try:
            data = future.result()
            if data: new_articles.extend(data)
        except: pass

# --- 4. CLEANUP ---
unique_map = {}
for art in new_articles:
    if art['link'] not in unique_map:
        unique_map[art['link']] = art
final_list = list(unique_map.values())

final_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

now = time.time()
for art in final_list:
    diff = now - art['timestamp']
    if diff < 3600: art['time_str'] = f"{int(diff/60)}m ago"
    elif diff < 86400: art['time_str'] = f"{int(diff/3600)}h ago"
    else: art['time_str'] = f"{int(diff/86400)}d ago"

final_list = final_list[:TOTAL_LIMIT]

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)

print(f"--- KLAR PÅ {time.time()-start_time:.2f} SEK ---")
print(f"Totalt antal artiklar: {len(final_list)}")

if os.path.exists('template.html'):
    with open('template.html', 'r', encoding='utf-8') as f:
        html = f.read().replace("<!-- NEWS_DATA_JSON -->", json.dumps(final_list))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("SUCCESS: index.html har uppdaterats!")
else:
    print("VARNING: template.html saknas!")