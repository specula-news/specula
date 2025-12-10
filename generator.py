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

# NY IMPORT: Översättning
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_ACTIVE = True
except ImportError:
    print("VARNING: 'deep-translator' saknas. Kör 'pip install deep-translator'.")
    TRANSLATOR_ACTIVE = False

# Stäng av SSL-varningar
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- INSTÄLLNINGAR ---
MAX_ARTICLES_DEFAULT = 10
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

print(f"--- STARTAR GENERATORN (V20.5.1 - Translation & GeoFilters) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# --- 2. HJÄLPFUNKTIONER ---

def translate_text(text, source_lang):
    """Översätter text till engelska om TRANSLATOR_ACTIVE är True."""
    if not TRANSLATOR_ACTIVE or not text:
        return text
    try:
        # Begränsa textlängd för att undvika timeouts vid långa texter
        if len(text) > 4000: text = text[:4000]
        return GoogleTranslator(source=source_lang, target='en').translate(text)
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

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
    if 'aftonbladet' in url: return url
    if 'phys.org' in url or 'scx' in url: return url
    if 'wp.com' in url or 'electrek' in url or '9to5' in url:
        if 'w=' in url:
            return re.sub(r'w=\d+', 'w=1600', url)
    return url

# --- 3. BILDSTRATEGIER ---

def strategy_phys_org(entry):
    img_url = None
    if 'media_thumbnail' in entry: img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry: img_url = entry.media_content[0]['url']
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): img_url = enc.href; break
    if img_url:
        if '/tmb/' in img_url: return img_url.replace('/tmb/', '/800/')
        if 'thumbnails' in img_url: return img_url.replace('thumbnails', '800')
    return img_url

def strategy_aftonbladet(link):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=8, verify=False)
        if r.status_code != 200: return None
        matches = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+[^"\s]*)', r.text)
        if matches: return matches[0].replace('&amp;', '&')
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
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=8, verify=False)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.content, 'html.parser')
        og = soup.find("meta", property="og:image")
        if og and og.get("content"): return urljoin(link, og["content"])
        best_img = None
        max_w = 0
        images = soup.select('figure img, .entry-content img, article img, img')
        for img in images:
            candidates = []
            if img.get('src'): candidates.append(img.get('src'))
            if img.get('data-src'): candidates.append(img.get('data-src'))
            srcset = img.get('srcset') or img.get('data-srcset')
            if srcset:
                for p in srcset.split(','):
                    parts = p.strip().split(' ')
                    if len(parts) >= 1: candidates.append(parts[0])
            for c in candidates:
                if not c or 'base64' in c: continue
                full = urljoin(link, c)
                score = 0
                if 'w=' in full: 
                    try: score = int(re.search(r'w=(\d+)', full).group(1))
                    except: pass
                elif img.get('width'):
                    try: score = int(img['width'])
                    except: pass
                parent_cls = str(img.parent.get('class', []))
                if 'featured' in parent_cls or 'hero' in parent_cls: score += 500
                if any(x in full.lower() for x in ['logo', 'icon', 'avatar']): score = 0
                if score > max_w:
                    max_w = score
                    best_img = full
        return best_img
    except: pass
    return None

def strategy_default(entry):
    img_url = None
    if 'media_content' in entry:
        try: img_url = entry.media_content[0]['url']
        except: pass
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.type.startswith('image/'): img_url = enc.href; break
    if not img_url:
        try:
            r = get_session().get(entry.link, timeout=5, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            og = soup.find("meta", property="og:image")
            if og: img_url = og['content']
        except: pass
    return img_url

# --- 4. ROUTING LOGIK ---

def get_image_for_article(entry, source_url):
    if 'phys.org' in source_url or 'techxplore' in source_url:
        return strategy_phys_org(entry)
    if 'aftonbladet' in source_url:
        return strategy_aftonbladet(entry.link)
    deep_list = ['dagensps', 'electrek', 'feber', 'nasa.gov', 'sweclockers']
    if any(d in source_url for d in deep_list):
        url = strategy_deep_scrape(entry.link)
        if not url: return strategy_default(entry)
        return url
    return strategy_default(entry)

def get_web_info(source):
    found_articles = []
    limit = MAX_ARTICLES_DEFAULT
    if 'aftonbladet' in source['url']: limit = MAX_ARTICLES_AFTONBLADET

    try:
        # VIP-behandling för ArchDaily
        if 'archdaily' in source['url']:
            resp = requests.get(source['url'], headers=HEADERS, timeout=15, verify=True)
        else:
            resp = get_session().get(source['url'], timeout=10, verify=False)

        if resp.status_code != 200:
            print(f"⚠️ VARNING: {source['source_name']} status {resp.status_code}.")
            return []

        feed = feedparser.parse(resp.content)
        if not feed.entries:
            print(f"⚠️ TOMT FLÖDE: {source['source_name']}")

        for entry in feed.entries[:limit]:
            timestamp = parse_date_to_timestamp(entry)
            if is_too_old(timestamp): continue

            img_url = get_image_for_article(entry, source['url'])
            img_url = clean_image_url_generic(img_url)

            summary = entry.get('summary', '') or entry.get('description', '')
            if '<' in summary:
                summary = BeautifulSoup(summary, 'html.parser').get_text()

            # --- TRANSLATION LOGIC ---
            title = entry.title
            lang_note = ""
            if source.get('lang') == 'sv':
                title = translate_text(title, 'sv')
                summary = translate_text(summary, 'sv')
                lang_note = " (Translated from Swedish)"

            found_articles.append({
                "title": title,
                "link": entry.link,
                "images": [img_url] if img_url else [],
                "summary": (summary[:180] + "...") if len(summary) > 180 else summary,
                "category": source['cat'],
                "filter_tag": source.get('filter_tag', ''), # NYTT: För Geopolitics filter
                "source": source.get('source_name', 'News'),
                "lang_note": lang_note, # NYTT: Footer text
                "time_str": "Just Now",
                "timestamp": timestamp,
                "is_video": False
            })
    except Exception as e: 
        print(f"FEL ({source.get('source_name', 'Unknown')}): {e}")
        pass
    return found_articles

def get_video_info(source):
    videos = []
    try:
        ydl_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': True,
            'playlistend': 10,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if not info: return videos
            
            entries = info['entries'] if 'entries' in info else [info]

            for entry in entries:
                if not entry: continue
                
                img_url = ''
                thumbnails = entry.get('thumbnails', [])
                if thumbnails and isinstance(thumbnails, list):
                    try: img_url = thumbnails[-1].get('url', '')
                    except: pass
                
                if not img_url and entry.get('id'):
                    img_url = f"https://img.youtube.com/vi/{entry['id']}/hqdefault.jpg"

                ts = time.time()
                try:
                    if entry.get('upload_date'):
                        ts = datetime.strptime(entry['upload_date'], '%Y%m%d').timestamp()
                    elif entry.get('timestamp'):
                        ts = entry['timestamp']
                except: pass

                if is_too_old(ts): continue

                # Translate video title/desc if needed (rare, usually English videos)
                title = entry.get('title', 'Video')
                summary = entry.get('description', '')[:200] + "..."
                lang_note = ""
                
                if source.get('lang') == 'sv':
                    title = translate_text(title, 'sv')
                    summary = translate_text(summary, 'sv')
                    lang_note = " (Translated from Swedish)"

                videos.append({
                    "title": title,
                    "link": entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry['id']}",
                    "images": [img_url],
                    "summary": summary,
                    "category": source.get('cat', 'video'),
                    "filter_tag": source.get('filter_tag', ''), # NYTT
                    "source": source.get('source_name', 'YouTube'),
                    "lang_note": lang_note,
                    "time_str": "Just Now",
                    "timestamp": ts,
                    "is_video": True
                })
    except Exception as e:
        print(f"FEL VID VIDEOHÄMTNING ({source.get('source_name')}): {e}")
    
    return videos

def get_video_info_wrapper(source):
    return get_video_info(source)

def process_source(source):
    if source['type'] == 'video': return get_video_info_wrapper(source)
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

# --- 6. CLEANUP ---
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