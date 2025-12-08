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
MAX_ARTICLES_DEFAULT = 20
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90

# --- 1. IMPORTERA KÄLLOR ---
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py!")
    SOURCES = []

print(f"--- STARTAR GENERATORN (SEPARERAD LOGIK PER SAJT) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# --- 2. HJÄLPFUNKTIONER (DATUM & VIDEO) ---

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

def get_video_info(source):
    found_videos = []
    ydl_opts = {'quiet': True, 'extract_flat': True, 'playlistend': MAX_ARTICLES_DEFAULT, 'ignoreerrors': True}
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
                    img_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" # Safe bet

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

# --- 3. SPECIFIKA BILD-STRATEGIER ---

def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def strategy_phys_org(entry):
    """
    STRATEGI: Lita på RSS, gå ALDRIG in på sajten (blockrisk).
    Byt ut /tmb/ mot /800/ i URL.
    """
    img_url = None
    # 1. Hitta bild i RSS
    if 'media_thumbnail' in entry: img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry: img_url = entry.media_content[0]['url']
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): img_url = enc.href; break
    
    # 2. Hacka URLen
    if img_url:
        if '/tmb/' in img_url: return img_url.replace('/tmb/', '/800/')
        if 'thumbnails' in img_url: return img_url.replace('thumbnails', '800')
    
    return img_url

def strategy_aftonbladet(entry_url):
    """
    STRATEGI: Gå in på sajten. Hitta signerad länk via Regex/JSON.
    Justera parametrar men behåll signaturen.
    """
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(entry_url, timeout=8, verify=False)
        if r.status_code != 200: return None
        
        # Metod A: Regex (Oftast bäst för CDN-länkar)
        matches = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+[^"\s]*)', r.text)
        best_match = None
        
        if matches:
            best_match = matches[0].replace('&amp;', '&')
        
        # Metod B: JSON-LD (Om regex missar)
        if not best_match:
            soup = BeautifulSoup(r.content, 'html.parser')
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list): data = data[0]
                    if 'image' in data:
                        img = data['image']
                        if isinstance(img, list): best_match = img[0]
                        elif isinstance(img, dict): best_match = img.get('url')
                        elif isinstance(img, str): best_match = img
                        if best_match: break
                except: pass

        if best_match:
            # Optimera parametrar
            if 'w=' in best_match: best_match = re.sub(r'w=\d+', 'w=1200', best_match)
            else: best_match += '&w=1200'
            if 'q=' in best_match: best_match = re.sub(r'q=\d+', 'q=80', best_match)
            else: best_match += '&q=80'
            return best_match

    except: pass
    return None

def strategy_deep_scrape(entry_url):
    """
    STRATEGI: Gå in på sajten. Analysera DOM/Srcset.
    Rensa URL helt från parametrar (Wordpress/Electrek).
    """
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(entry_url, timeout=8, verify=False)
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 1. OpenGraph (Oftast bäst för Electrek/Feber)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            url = urljoin(entry_url, og["content"])
            return url.split('?')[0] # Rensa ?w=...

        # 2. Hitta största bilden i DOM (Fallback)
        # Detta behövs om OG-bilden saknas
        best_img = None
        max_w = 0
        
        for img in soup.find_all('img'):
            candidates = []
            if img.get('src'): candidates.append(img.get('src'))
            if img.get('data-src'): candidates.append(img.get('data-src'))
            
            # Srcset analys
            srcset = img.get('srcset') or img.get('data-srcset')
            if srcset:
                for p in srcset.split(','):
                    parts = p.strip().split(' ')
                    if len(parts) >= 1: candidates.append(parts[0])

            for c in candidates:
                if not c or 'base64' in c: continue
                full = urljoin(entry_url, c)
                
                # Ge poäng
                score = 0
                if 'w=' in full: 
                    try: score = int(re.search(r'w=(\d+)', full).group(1))
                    except: pass
                elif img.get('width'):
                    try: score = int(img['width'])
                    except: pass
                elif 'feat' in str(img.attrs) or 'hero' in str(img.attrs):
                    score = 800 # Gissning
                
                if any(x in full.lower() for x in ['logo', 'icon', 'avatar']): score = 0
                
                if score > max_w:
                    max_w = score
                    best_img = full

        if best_img:
            return best_img.split('?')[0] # Rensa ?w=...

    except: pass
    return None

def strategy_default(entry):
    """
    STRATEGI: Försök RSS. Om tomt -> Skrapa OG tag.
    """
    # 1. RSS
    img_url = None
    if 'media_content' in entry:
        try: img_url = entry.media_content[0]['url']
        except: pass
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): img_url = enc.href; break
    
    # 2. Om ingen bild, skrapa lätt
    if not img_url:
        try:
            r = get_session().get(entry.link, timeout=5, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            og = soup.find("meta", property="og:image")
            if og: img_url = og['content']
        except: pass
        
    return img_url

# --- 4. HUVUDLOGIK FÖR ATT VÄLJA STRATEGI ---

def get_image_for_article(entry, source_url):
    """Väljer rätt strategi baserat på domän."""
    
    # 1. PHYS.ORG / SCIENCE X
    if 'phys.org' in source_url or 'techxplore' in source_url:
        return strategy_phys_org(entry)
    
    # 2. AFTONBLADET
    if 'aftonbladet' in source_url:
        return strategy_aftonbladet(entry.link)
    
    # 3. DEEP SCRAPE (Electrek, Dagens PS, Feber, NASA)
    # Dessa kräver att vi går in på sidan och analyserar/rensar URL
    deep_scrape_domains = ['electrek', 'dagensps', 'feber', 'nasa.gov', 'sweclockers']
    if any(d in source_url for d in deep_scrape_domains):
        return strategy_deep_scrape(entry.link)
        
    # 4. DEFAULT
    return strategy_default(entry)

def get_web_info(source):
    found_articles = []
    
    # Begränsa antalet artiklar
    limit = MAX_ARTICLES_DEFAULT
    if 'aftonbladet' in source['url']:
        limit = 3 # Endast 3 från Aftonbladet
        
    try:
        resp = get_session().get(source['url'], timeout=10, verify=False)
        feed = feedparser.parse(resp.content)
        
        for entry in feed.entries[:limit]:
            timestamp = parse_date_to_timestamp(entry)
            if is_too_old(timestamp): continue

            # --- HÄMTA BILD MED RÄTT STRATEGI ---
            img_url = get_image_for_article(entry, source['url'])

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

# --- 5. EXEKVERING ---
new_articles = []
start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    future_map = {executor.submit(process_source, s): s for s in SOURCES}
    for future in concurrent.futures.as_completed(future_map):
        try:
            data = future.result()
            if data: new_articles.extend(data)
        except: pass

# --- 6. CLEANUP & SPARANDE ---
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