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

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_ACTIVE = True
except ImportError:
    TRANSLATOR_ACTIVE = False

# Stäng av varningar för osecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- INSTÄLLNINGAR ---
MAX_ARTICLES_DEFAULT = 10
MAX_ARTICLES_AFTONBLADET = 3
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90
MAX_SUMMARY_LENGTH = 280
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

# Ladda källor
try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR ---")
except ImportError:
    SOURCES = []
    print("VARNING: sources.py hittades inte.")

print(f"--- STARTAR GENERATORN (V5.2 - SWECLOCKERS OG PRIORITY) ---")

# --- FAKE BROWSER HEADERS ---
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# --- HJÄLPFUNKTIONER ---

def get_session():
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    return s

def clean_text(text):
    if not text: return ""
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")
    text = " ".join(text.split())
    if len(text) > MAX_SUMMARY_LENGTH:
        return text[:MAX_SUMMARY_LENGTH] + "..."
    return text

def translate_text(text, source_lang):
    if not TRANSLATOR_ACTIVE or not text: return text
    try:
        if len(text) > 1000: text = text[:1000]
        return GoogleTranslator(source=source_lang, target='en').translate(text)
    except Exception: return text

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
    return 0 

def is_too_old(timestamp):
    if timestamp == 0: return False 
    limit = time.time() - (MAX_AGE_DAYS * 24 * 60 * 60)
    return timestamp < limit

def clean_image_url_generic(url):
    if not url: return None
    if 'w=' in url: return re.sub(r'w=\d+', 'w=1200', url)
    return url

# --- BILDSTRATEGIER ---

def strategy_sweclockers(link):
    """
    Sweclockers Strategi V5.2:
    PRIO 1: OpenGraph (Efter ditt testresultat)
    PRIO 2: Regex för CDN-länkar (Fallback)
    PRIO 3: JSON-LD (Fallback)
    """
    try:
        time.sleep(random.uniform(0.5, 1.0))
        session = get_session()
        r = session.get(link, timeout=10, verify=False)
        if r.status_code != 200: return None
        html_content = r.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # PRIO 1: OPEN GRAPH (Detta fungerade bäst i ditt test)
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        # PRIO 2: Regex för dynamiska länkar (?l=...)
        pattern_dynamic = r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[a-zA-Z0-9%\-_]+)'
        matches = re.findall(pattern_dynamic, html_content)
        if matches:
            return max(matches, key=len).replace("&amp;", "&")

        # PRIO 3: JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list): data = data[0]
                if 'image' in data:
                    img_data = data['image']
                    if isinstance(img_data, dict) and 'url' in img_data: return img_data['url']
                    if isinstance(img_data, str): return img_data
            except: continue

    except Exception: pass
    return None

def strategy_aftonbladet(link):
    """
    Aftonbladet: Regex Brute Force.
    """
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=8, verify=False)
        matches = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)', r.text)
        if matches: return matches[0]
    except: pass
    return None

def strategy_fz_se(link):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=10, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        og = soup.find("meta", property="og:image")
        if og and og.get("content"): return og["content"]
    except: pass
    return None

def strategy_phys_org(entry):
    img_url = None
    if 'media_thumbnail' in entry: img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry: img_url = entry.media_content[0]['url']
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if getattr(enc, 'type', '').startswith('image/'):
                img_url = getattr(enc, 'href', '')
                break
    if img_url:
        if '/tmb/' in img_url: return img_url.replace('/tmb/', '/800/')
    return img_url

def strategy_deep_scrape(link):
    """
    Generell "Deep Scrape". Prioriterar OpenGraph.
    """
    try:
        time.sleep(random.uniform(0.3, 0.7))
        session = get_session()
        r = session.get(link, timeout=8, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 1. Open Graph
        og = soup.find("meta", property="og:image")
        if og and og.get("content"): 
            return urljoin(link, og["content"])
            
        # 2. Twitter Card
        tw = soup.find("meta", name="twitter:image")
        if tw and tw.get("content"):
            return urljoin(link, tw["content"])
            
    except: pass
    return None

def strategy_default(entry):
    img_url = None
    if 'media_content' in entry:
        try: img_url = entry.media_content[0]['url']
        except: pass
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            if getattr(enc, 'type', '').startswith('image/'):
                img_url = getattr(enc, 'href', '')
                break
    
    if not img_url:
        return strategy_deep_scrape(entry.link)
        
    return img_url

def get_image_for_article(entry, source_url):
    # 1. KOPPLA KÄLLOR TILL RÄTT STRATEGI
    if 'sweclockers' in source_url: return strategy_sweclockers(entry.link)
    if 'aftonbladet' in source_url: return strategy_aftonbladet(entry.link)
    if 'fz.se' in source_url: return strategy_fz_se(entry.link)
    if 'phys.org' in source_url or 'techxplore' in source_url: return strategy_phys_org(entry)
    
    # 2. Sidor som behöver Deep Scrape (OG Image)
    deep_scrape_sites = [
        'dagensps', 
        'cnn', 
        'electrek', 
        'feber', 
        'nasa.gov', 
        'indiatimes', 
        'reuters', 
        'cnbc',
        'nyteknik',
        'di.se'
    ]
    
    if any(d in source_url for d in deep_scrape_sites):
        url = strategy_deep_scrape(entry.link)
        if url: return url
        
    return strategy_default(entry)

# --- INFO HÄMTNING ---

def get_web_info(source):
    found_articles = []
    limit = MAX_ARTICLES_DEFAULT
    if 'aftonbladet' in source['url']: limit = MAX_ARTICLES_AFTONBLADET

    try:
        session = get_session()
        resp = session.get(source['url'], timeout=10, verify=False)
        
        if resp.status_code != 200: return []

        feed = feedparser.parse(resp.content)
        if not feed.entries: return []

        for entry in feed.entries[:limit]:
            timestamp = parse_date_to_timestamp(entry)
            if timestamp == 0: timestamp = time.time()
            if is_too_old(timestamp): continue
            if not entry.get('title'): continue

            # Hämta bild
            img_url = get_image_for_article(entry, source['url'])
            img_url = clean_image_url_generic(img_url)
            if not img_url: img_url = DEFAULT_IMAGE

            raw_summary = entry.get('summary', '') or entry.get('description', '')
            clean_summary = clean_text(raw_summary)

            title = entry.title
            lang_note = ""
            if source.get('lang') == 'sv':
                title = translate_text(title, 'sv')
                clean_summary = translate_text(clean_summary, 'sv')
                lang_note = " (Translated from Swedish)"

            found_articles.append({
                "title": title,
                "link": entry.link,
                "images": [img_url],
                "summary": clean_summary,
                "category": source['cat'],
                "filter_tag": source.get('filter_tag', ''), 
                "source": source.get('source_name', 'News'),
                "lang_note": lang_note,
                "timestamp": timestamp,
                "is_video": False
            })
    except Exception as e:
        print(f"Error processing {source['url']}: {e}")
        
    return found_articles

def get_video_info(source):
    videos = []
    try:
        ydl_opts = {
            'quiet': True, 'ignoreerrors': True, 'extract_flat': True, 
            'playlistend': 5, 'no_warnings': True, 'http_headers': BROWSER_HEADERS 
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if not info: return videos
            entries = info.get('entries', [info])

            for entry in entries:
                if not entry: continue
                
                img_url = ''
                thumbnails = entry.get('thumbnails', [])
                if thumbnails: img_url = thumbnails[-1].get('url', '')
                if not img_url and entry.get('id'):
                    img_url = f"https://i.ytimg.com/vi/{entry['id']}/hqdefault.jpg"
                if not img_url: img_url = DEFAULT_IMAGE

                ts = 0
                try:
                    date_str = entry.get('upload_date')
                    if date_str: ts = datetime.strptime(date_str, '%Y%m%d').timestamp()
                    elif entry.get('timestamp'): ts = entry['timestamp']
                except: pass
                
                if ts == 0: ts = time.time()
                if is_too_old(ts): continue

                title = entry.get('title', 'Video')
                clean_summary = clean_text(entry.get('description', ''))
                
                lang_note = ""
                if source.get('lang') == 'sv':
                    title = translate_text(title, 'sv')
                    clean_summary = translate_text(clean_summary, 'sv')
                    lang_note = " (Translated from Swedish)"

                videos.append({
                    "title": title,
                    "link": entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    "images": [img_url],
                    "summary": clean_summary,
                    "category": source.get('cat', 'video'),
                    "filter_tag": source.get('filter_tag', ''),
                    "source": source.get('source_name', 'YouTube'),
                    "lang_note": lang_note,
                    "timestamp": ts,
                    "is_video": True
                })
    except: pass
    return videos

def process_source(source):
    if source['type'] == 'video': return get_video_info(source)
    else: return get_web_info(source)

# --- EXEKVERING ---
new_articles = []
start_time = time.time()

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    future_map = {executor.submit(process_source, s): s for s in SOURCES}
    for future in concurrent.futures.as_completed(future_map):
        try:
            data = future.result()
            if data: new_articles.extend(data)
        except: pass

# Ta bort dubbletter
unique_map = {}
for art in new_articles:
    if not art['title'] or art['title'] == 'Video': continue
    if art['link'] not in unique_map: unique_map[art['link']] = art
final_list = list(unique_map.values())

# =======================================================
# SORTERINGSLOGIK
# =======================================================

final_list.sort(key=lambda x: x['timestamp'], reverse=True)

mixed_list = []
last_source = None

while final_list:
    best_index = -1
    search_window = min(len(final_list), 6)
    
    for i in range(search_window):
        art = final_list[i]
        if art['source'] != last_source:
            best_index = i
            break
    
    if best_index == -1: best_index = 0
        
    selected_art = final_list.pop(best_index)
    mixed_list.append(selected_art)
    last_source = selected_art['source']

final_list = mixed_list

# Skapa tidssträngar
now = time.time()
for art in final_list:
    diff = now - art['timestamp']
    if diff < 3600: art['time_str'] = "Just Now"
    elif diff < 86400: art['time_str'] = f"{int(diff/3600)}h ago"
    elif diff < 604800: art['time_str'] = f"{int(diff/86400)}d ago"
    elif diff < 2592000: art['time_str'] = f"{int(diff/604800)}w ago"
    else: art['time_str'] = f"{int(diff/2592000)}mo ago"

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