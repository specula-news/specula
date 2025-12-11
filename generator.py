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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- INSTÄLLNINGAR ---
MAX_ARTICLES_DEFAULT = 10
MAX_ARTICLES_AFTONBLADET = 3
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90
MAX_SUMMARY_LENGTH = 280
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR ---")
except ImportError:
    SOURCES = []

print(f"--- STARTAR GENERATORN (V20.5.38 - STABLE & STRICT) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

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
    return time.time() - random.randint(3600, 86400) # Fallback för webb

def is_too_old(timestamp):
    limit = time.time() - (MAX_AGE_DAYS * 24 * 60 * 60)
    return timestamp < limit

def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def clean_image_url_generic(url):
    if not url: return None
    if 'aftonbladet' in url: return url
    if 'phys.org' in url or 'scx' in url: return url
    if 'fz.se' in url: return url
    if 'wp.com' in url or 'electrek' in url or '9to5' in url:
        if 'w=' in url: return re.sub(r'w=\d+', 'w=1600', url)
    return url

# --- BILDSTRATEGIER ---
def strategy_fz_se(link):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=10, verify=False)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.content, 'html.parser')
        og = soup.find("meta", property="og:image")
        if og and og.get("content"): return og["content"]
        img = soup.select_one('figure.image img')
        if img and img.get('src'): return urljoin(link, img.get('src'))
    except: pass
    return None

def strategy_phys_org(entry):
    img_url = None
    if 'media_thumbnail' in entry: img_url = entry.media_thumbnail[0]['url']
    elif 'media_content' in entry: img_url = entry.media_content[0]['url']
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            type_str = getattr(enc, 'type', '') or enc.get('type', '')
            if type_str.startswith('image/'):
                img_url = getattr(enc, 'href', '') or enc.get('href', '')
                break
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
    except: pass
    return None

def strategy_default(entry):
    img_url = None
    if 'media_content' in entry:
        try: img_url = entry.media_content[0]['url']
        except: pass
    elif 'enclosures' in entry:
        for enc in entry.enclosures:
            type_str = getattr(enc, 'type', '') or enc.get('type', '')
            if type_str.startswith('image/'):
                img_url = getattr(enc, 'href', '') or enc.get('href', '')
                break
    if not img_url:
        try:
            r = get_session().get(entry.link, timeout=5, verify=False)
            soup = BeautifulSoup(r.content, 'html.parser')
            og = soup.find("meta", property="og:image")
            if og: img_url = og['content']
        except: pass
    return img_url

def get_image_for_article(entry, source_url):
    if 'fz.se' in source_url: return strategy_fz_se(entry.link)
    if 'phys.org' in source_url or 'techxplore' in source_url: return strategy_phys_org(entry)
    if 'aftonbladet' in source_url: return strategy_aftonbladet(entry.link)
    deep_list = ['dagensps', 'electrek', 'feber', 'nasa.gov', 'sweclockers', 'indiatimes']
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
        if 'archdaily' in source['url']:
            resp = requests.get(source['url'], headers=HEADERS, timeout=15, verify=True)
        else:
            resp = get_session().get(source['url'], timeout=10, verify=False)

        if resp.status_code != 200: return []

        feed = feedparser.parse(resp.content)
        if not feed.entries: return []

        for entry in feed.entries[:limit]:
            timestamp = parse_date_to_timestamp(entry)
            if is_too_old(timestamp): continue
            if not entry.get('title'): continue

            img_url = get_image_for_article(entry, source['url'])
            img_url = clean_image_url_generic(img_url)
            if not img_url: img_url = DEFAULT_IMAGE

            summary = clean_text(entry.get('summary', '') or entry.get('description', ''))
            title = entry.title
            lang_note = ""
            if source.get('lang') == 'sv':
                title = translate_text(title, 'sv')
                summary = translate_text(summary, 'sv')
                lang_note = " (Translated from Swedish)"

            found_articles.append({
                "title": title,
                "link": entry.link,
                "images": [img_url],
                "summary": summary,
                "category": source['cat'],
                "filter_tag": source.get('filter_tag', ''), 
                "source": source.get('source_name', 'News'),
                "lang_note": lang_note,
                "time_str": "",
                "timestamp": timestamp,
                "is_video": False
            })
    except: pass
    return found_articles

def get_video_info(source):
    videos = []
    try:
        ydl_opts = {
            'quiet': True, 
            'ignoreerrors': True, 
            'extract_flat': True, 
            'playlistend': 8, # Hämtar 8 st
            'no_warnings': True,
            'http_headers': HEADERS
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if not info: return videos
            entries = info.get('entries', [info])

            for entry in entries:
                if not entry: continue
                
                img_url = ''
                thumbnails = entry.get('thumbnails', [])
                if thumbnails and isinstance(thumbnails, list):
                    try: img_url = thumbnails[-1].get('url', '')
                    except: pass
                
                if not img_url and entry.get('id'):
                    img_url = f"https://img.youtube.com/vi/{entry['id']}/hqdefault.jpg"
                if not img_url: img_url = DEFAULT_IMAGE

                ts = 0
                try:
                    date_str = entry.get('upload_date') or entry.get('release_date')
                    if date_str:
                        ts = datetime.strptime(date_str, '%Y%m%d').timestamp()
                    elif entry.get('timestamp'):
                        ts = entry['timestamp']
                except: pass

                # HÄR ÄR "RÄDDNINGEN" FRÅN DIN FUNGERANDE KOD:
                if ts == 0: ts = time.time()

                if is_too_old(ts): continue

                title = entry.get('title', 'Video')
                summary = clean_text(entry.get('description', ''))
                
                lang_note = ""
                if source.get('lang') == 'sv':
                    title = translate_text(title, 'sv')
                    summary = translate_text(summary, 'sv')
                    lang_note = " (Translated from Swedish)"

                videos.append({
                    "title": title,
                    "link": entry.get('webpage_url') or entry.get('url') or f"https://www.youtube.com/watch?v={entry['id']}",
                    "images": [img_url],
                    "summary": summary,
                    "category": source.get('cat', 'video'),
                    "filter_tag": source.get('filter_tag', ''),
                    "source": source.get('source_name', 'YouTube'),
                    "lang_note": lang_note,
                    "time_str": "",
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

unique_map = {}
for art in new_articles:
    if not art['title'] or art['title'] == 'Video': continue
    if art['link'] not in unique_map: unique_map[art['link']] = art
final_list = list(unique_map.values())

# --- VIKTIG ÄNDRING: STRIKT SORTERING (INGET JITTER) ---
# Nu sorteras allt strikt efter tid. Nyaste först.
final_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

now = time.time()
for art in final_list:
    diff = now - art['timestamp']
    
    if diff < 3600:
        art['time_str'] = f"{int(diff/60)}m ago"
    elif diff < 86400: 
        art['time_str'] = f"{int(diff/3600)}h ago"
    elif diff < 604800: 
        art['time_str'] = f"{int(diff/86400)}d ago"
    elif diff < 2592000:
        art['time_str'] = f"{int(diff/604800)}w ago"
    else:
        art['time_str'] = f"{int(diff/2592000)}mo ago"

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