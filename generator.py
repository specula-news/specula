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
MAX_ARTICLES_AFTONBLADET = 3
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90

# --- 1. IMPORTERA KÄLLOR ---
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR FRÅN sources.py ---")
except ImportError:
    print("VARNING: Kunde inte hitta sources.py!")
    SOURCES = []

print(f"--- STARTAR GENERATORN (SEPARATED LOGIC STRATEGY) ---")

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

def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def clean_image_url_generic(url):
    """Generell städning för Wordpress/Jetpack (Electrek etc), men rör EJ Aftonbladet/Phys."""
    if not url: return None
    
    # RÖR INTE AFTONBLADET (Signaturen pajar)
    if 'aftonbladet' in url:
        return url
        
    # RÖR INTE PHYS.ORG (Hanteras i sin strategi)
    if 'phys.org' in url or 'scx' in url:
        return url

    # WORDPRESS / ELECTREK: Maxa storlek
    if 'wp.com' in url or 'electrek' in url or '9to5' in url:
        if 'w=' in url:
            return re.sub(r'w=\d+', 'w=1600', url)
            
    return url

# --- 3. BILDSTRATEGIER ---

def strategy_phys_org(entry):
    """
    STRATEGI 1: PHYS.ORG / SCIENCE X
    Gå inte in på sidan (block-risk). Hacka RSS-bilden.
    """
    img_url = None
    if 'media_thumbnail' in entry: img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry: img_url = entry.media_content[0]['url']
    
    if img_url:
        if '/tmb/' in img_url: return img_url.replace('/tmb/', '/800/')
        if 'thumbnails' in img_url: return img_url.replace('thumbnails', '800')
    return img_url

def strategy_aftonbladet(link):
    """
    STRATEGI 2: AFTONBLADET
    Hitta den signerade länken i källkoden via Regex eller JSON-LD.
    RÖR INTE parametrarna.
    """
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=8, verify=False)
        if r.status_code != 200: return None
        
        # Metod A: Regex (Mest pålitlig för CDN-länkar)
        # Letar efter: https://images.aftonbladet-cdn.se/... följt av parametrar
        matches = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+[^"\s]*)', r.text)
        if matches:
            # Ta den första som ser ut att vara en artikelbild (oftast w=800 eller liknande i koden)
            return matches[0].replace('&amp;', '&')

        # Metod B: JSON-LD
        soup = BeautifulSoup(r.content, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list): data = data[0]
                if 'image' in data:
                    img = data['image']
                    if isinstance(img, list): return img[0]
                    if isinstance(img, dict): return img.get('url')
                    if isinstance(img, str): return img
            except: pass
    except: pass
    return None

def strategy_deep_scrape(link):
    """
    STRATEGI 3: DAGENS PS / ELECTREK / FEBER
    Gå in på sidan. Analysera DOM för att hitta största bilden.
    Prioritera OpenGraph.
    """
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=8, verify=False)
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 1. OpenGraph (Oftast bäst för Dagens PS / Electrek)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return urljoin(link, og["content"])

        # 2. Hitta största bilden i 'figure' eller 'img'
        # Dagens PS har ofta bilder i <figure class="wp-block-post-featured-image">
        best_img = None
        max_w = 0
        
        images = soup.select('figure img, .entry-content img, article img, img')
        
        for img in images:
            candidates = []
            if img.get('src'): candidates.append(img.get('src'))
            if img.get('data-src'): candidates.append(img.get('data-src'))
            
            # Kolla srcset
            srcset = img.get('srcset') or img.get('data-srcset')
            if srcset:
                for p in srcset.split(','):
                    parts = p.strip().split(' ')
                    if len(parts) >= 1: candidates.append(parts[0])

            for c in candidates:
                if not c or 'base64' in c: continue
                full = urljoin(link, c)
                
                # Poängsättning
                score = 0
                if 'w=' in full: 
                    try: score = int(re.search(r'w=(\d+)', full).group(1))
                    except: pass
                elif img.get('width'):
                    try: score = int(img['width'])
                    except: pass
                
                # Ge bonus till featured image classes
                parent_cls = str(img.parent.get('class', []))
                if 'featured' in parent_cls or 'hero' in parent_cls:
                    score += 500
                
                if any(x in full.lower() for x in ['logo', 'icon', 'avatar']): score = 0
                
                if score > max_w:
                    max_w = score
                    best_img = full

        return best_img
    except: pass
    return None

def strategy_default(entry):
    """
    STRATEGI 4: ÖVRIGA
    Försök med RSS. Om tomt -> snabb skrapning av OG-tagg.
    """
    # 1. RSS
    img_url = None
    if 'media_content' in entry:
        try: img_url = entry.media_content[0]['url']
        except: pass
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): img_url = enc.href; break
    
    # 2. Skrapa OG om tomt
    if not img_url:
        try:
            r = get_session().get(entry.link, timeout=5, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            og = soup.find("meta", property="og:image")
            if og: img_url = og['content']
        except: pass
        
    return img_url

# --- 4. HUVUDLOGIK (ROUTING) ---

def get_image_for_article(entry, source_url):
    """Väljer strategi baserat på URL."""
    
    # 1. Phys.org
    if 'phys.org' in source_url or 'techxplore' in source_url:
        return strategy_phys_org(entry)
    
    # 2. Aftonbladet
    if 'aftonbladet' in source_url:
        return strategy_aftonbladet(entry.link)
    
    # 3. Deep Scrape (Dagens PS, Electrek, Feber, NASA)
    deep_list = ['dagensps', 'electrek', 'feber', 'nasa.gov', 'sweclockers']
    if any(d in source_url for d in deep_list):
        url = strategy_deep_scrape(entry.link)
        # Fallback till RSS om skrapning misslyckas
        if not url: return strategy_default(entry)
        return url
        
    # 4. Default
    return strategy_default(entry)

def get_web_info(source):
    found_articles = []
    limit = MAX_ARTICLES_DEFAULT
    
    # Specialregel för Aftonbladet: Max 3
    if 'aftonbladet' in source['url']:
        limit = MAX_ARTICLES_AFTONBLADET

    try:
        resp = get_session().get(source['url'], timeout=10, verify=False)
        feed = feedparser.parse(resp.content)
        
        for entry in feed.entries[:limit]:
            timestamp = parse_date_to_timestamp(entry)
            if is_too_old(timestamp): continue

            # HÄMTA BILD VIA ROUTING
            img_url = get_image_for_article(entry, source['url'])
            
            # STÄDA URL (Men rör inte Aftonbladet/Phys)
            img_url = clean_image_url_generic(img_url)

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

def get_video_info(source):
    return get_video_info(source) # (Använder funktionen definierad högst upp)

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