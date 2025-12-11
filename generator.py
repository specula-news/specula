import json
import os
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
import concurrent.futures
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlparse
import urllib3
import re

# --- INSTÄLLNINGAR ---
YOUTUBE_API_KEY = "DIN_API_NYCKEL_HÄR" # <--- Jag lägger in din nyckel automatiskt nedan i koden
CACHE_FILE = "youtube_cache.json"
CACHE_DURATION_HOURS = 3  # Hur många timmar vi sparar resultatet innan vi hämtar nytt

MAX_ARTICLES_DEFAULT = 10
MAX_ARTICLES_AFTONBLADET = 3
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90
MAX_SUMMARY_LENGTH = 280
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

# Din nyckel (Hårdkodad för enkelhetens skull, men dela inte denna fil offentligt)
API_KEY = "AIzaSyBGNGzJb2b9R1S7ur7x7Xt-d1ze6TfIOFM"

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_ACTIVE = True
except ImportError:
    TRANSLATOR_ACTIVE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR ---")
except ImportError:
    SOURCES = []

print(f"--- STARTAR GENERATORN (V20.5.35 - YOUTUBE API & SMART CACHE) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

# --- CACHE SYSTEM ---
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    except: pass

# Global Cache Variable
DATA_CACHE = load_cache()

# --- HJÄLPFUNKTIONER ---

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

# --- YOUTUBE API LOGIC (SMART & CHEAP) ---

def get_channel_id_from_handle(handle):
    """Konverterar @ChannelName till Channel ID via API (Cost: 100)."""
    # Ta bort @ och URL delar
    handle_clean = handle.replace("https://www.youtube.com/", "").replace("/videos", "").replace("/", "")
    
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&q={handle_clean}&key={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["id"]["channelId"]
    except: pass
    return None

def get_uploads_playlist_id(channel_id):
    """Hämtar 'Uploads' spellistan för en kanal (Cost: 1)."""
    url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except: pass
    return None

def get_videos_from_playlist(playlist_id):
    """Hämtar videos från en spellista (Cost: 1)."""
    url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults=8&key={API_KEY}"
    videos = []
    try:
        r = requests.get(url)
        data = r.json()
        if "items" in data:
            for item in data["items"]:
                snippet = item["snippet"]
                
                # Hämta bästa bilden
                thumbs = snippet.get("thumbnails", {})
                img_url = thumbs.get("maxres", thumbs.get("high", thumbs.get("medium", {}))).get("url", "")
                
                # Hämta tid (ISO 8601)
                pub_str = snippet.get("publishedAt") # ex: 2025-12-09T10:00:00Z
                ts = 0
                if pub_str:
                    try:
                        # Parsa ISO format
                        dt = datetime.strptime(pub_str, "%Y-%m-%dT%H:%M:%SZ")
                        ts = dt.timestamp()
                    except: pass
                
                videos.append({
                    "title": snippet["title"],
                    "link": f"https://www.youtube.com/watch?v={snippet['resourceId']['videoId']}",
                    "image": img_url,
                    "summary": snippet.get("description", ""),
                    "timestamp": ts
                })
    except Exception as e:
        print(f"API Error: {e}")
    return videos

def get_video_info_api(source):
    """Huvudfunktion för YouTube via API med Caching."""
    url = source['url']
    
    # 1. KOLLA CACHE
    cached_data = DATA_CACHE.get(url)
    if cached_data:
        last_fetched = cached_data.get("last_fetched", 0)
        # Om cachen är nyare än X timmar, använd den
        if (time.time() - last_fetched) < (CACHE_DURATION_HOURS * 3600):
            # print(f"Using cache for {source['source_name']}")
            return process_cached_videos(cached_data.get("videos", []), source)

    # 2. HÄMTA NY DATA (Om cache saknas eller är gammal)
    channel_id = cached_data.get("channel_id") if cached_data else None
    
    # Steg A: Hitta Channel ID (Spara detta permanent för att spara pengar)
    if not channel_id:
        print(f"Fetching ID for {source['source_name']}...")
        channel_id = get_channel_id_from_handle(url)
    
    if not channel_id:
        print(f"❌ Kunde inte hitta ID för {source['source_name']}")
        return []

    # Steg B: Hitta Uploads Playlist ID
    uploads_id = get_uploads_playlist_id(channel_id)
    if not uploads_id: return []

    # Steg C: Hämta videor (Billigt!)
    raw_videos = get_videos_from_playlist(uploads_id)
    
    # 3. UPPDATERA CACHE
    DATA_CACHE[url] = {
        "last_fetched": time.time(),
        "channel_id": channel_id, # Vi sparar ID så vi slipper söka nästa gång
        "videos": raw_videos
    }
    save_cache(DATA_CACHE) # Spara till fil direkt

    return process_cached_videos(raw_videos, source)

def process_cached_videos(raw_videos, source):
    """Omvandlar rå API-data till vårt format."""
    final_videos = []
    for vid in raw_videos:
        if is_too_old(vid['timestamp']): continue

        summary = clean_text(vid['summary'])
        title = vid['title']
        lang_note = ""

        # Översättning (om det behövs, men oftast är YT på engelska)
        if source.get('lang') == 'sv':
            title = translate_text(title, 'sv')
            summary = translate_text(summary, 'sv')
            lang_note = " (Translated)"

        final_videos.append({
            "title": title,
            "link": vid['link'],
            "images": [vid['image']] if vid['image'] else [DEFAULT_IMAGE],
            "summary": summary,
            "category": source.get('cat', 'video'),
            "filter_tag": source.get('filter_tag', ''),
            "source": source.get('source_name', 'YouTube'),
            "lang_note": lang_note,
            "time_str": "", # Räknas ut senare
            "timestamp": vid['timestamp'],
            "is_video": True
        })
    return final_videos

# --- WEB SCRAPING STRATEGIES (BEHÅLLS) ---
def strategy_fz_se(link):
    try:
        r = get_session().get(link, timeout=10, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        og = soup.find("meta", property="og:image")
        if og and og.get("content"): return og["content"]
    except: pass
    return None

def strategy_phys_org(entry):
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url'].replace('/tmb/', '/800/')
    return None

def strategy_aftonbladet(link):
    try:
        r = get_session().get(link, timeout=8, verify=False)
        matches = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+[^"\s]*)', r.text)
        if matches: return matches[0].replace('&amp;', '&')
    except: pass
    return None

def strategy_deep_scrape(link):
    try:
        r = get_session().get(link, timeout=8, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        og = soup.find("meta", property="og:image")
        if og: return urljoin(link, og["content"])
    except: pass
    return None

def strategy_default(entry):
    if 'media_content' in entry: return entry.media_content[0]['url']
    for enc in entry.get('enclosures', []):
        if enc.get('type', '').startswith('image/'): return enc['href']
    return None

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
            if timestamp == 0: timestamp = time.time() - random.randint(100, 3600)
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

def process_source(source):
    # HÄR ÄR SWITCHN: OM VIDEO -> ANVÄND API. ANNARS WEB.
    if source['type'] == 'video': 
        return get_video_info_api(source)
    else: 
        return get_web_info(source)

# --- EXEKVERING ---
new_articles = []
start_time = time.time()

# Vi kör API-anropen sekventiellt (en och en) eller i små batchar för att inte överbelasta om vi inte har cache
# Men ThreadPool funkar bra för web scraping. För API kan det vara bra att vara varsam första gången.
# Vi kör på som vanligt, cachen skyddar oss.

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    future_map = {executor.submit(process_source, s): s for s in SOURCES}
    for future in concurrent.futures.as_completed(future_map):
        try:
            data = future.result()
            if data: new_articles.extend(data)
        except Exception as e:
            print(f"Error processing source: {e}")

unique_map = {}
for art in new_articles:
    if not art['title']: continue
    if art['link'] not in unique_map: unique_map[art['link']] = art
final_list = list(unique_map.values())

# Jitter för webbnyheter (inte lika viktigt för YT nu när vi har exakt tid, men bra för mixen)
for art in final_list:
    jitter = random.randint(-300, 300) 
    art['sort_score'] = art['timestamp'] + jitter

final_list.sort(key=lambda x: x.get('sort_score', 0), reverse=True)

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

    art.pop('sort_score', None)

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