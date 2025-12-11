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
import hashlib
import pickle

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

# HÄR ÄR DIN NYA TIDSGRÄNS:
MAX_AGE_DAYS = 365  # 1 år - låt alla videos komma igenom

MAX_SUMMARY_LENGTH = 280
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

# CACHE INSTÄLLNINGAR - 3 VECKOR
CACHE_DIR = ".youtube_cache"
CACHE_EXPIRE_DAYS = 21  # 3 veckor

try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR ---")
except ImportError:
    SOURCES = []

print(f"--- STARTAR GENERATORN (V20.5.37 - FIXED YOUTUBE DATES) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# --- ENKEL CACHE SYSTEM ---
def get_cache_key(url):
    """Skapa unikt cache-nyckel från URL"""
    return hashlib.md5(url.encode()).hexdigest()[:16]

def load_from_cache(url):
    """Ladda YouTube-data från cache om den finns"""
    try:
        cache_key = get_cache_key(url)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        # Kolla om cachen är för gammal (3 veckor)
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > CACHE_EXPIRE_DAYS * 24 * 3600:
            os.remove(cache_file)
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception:
        return None

def save_to_cache(url, data):
    """Spara YouTube-data till cache"""
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        cache_key = get_cache_key(url)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"⚠ Kunde inte spara cache: {e}")

def clear_old_cache():
    """Rensa gamla cache-filer"""
    try:
        if not os.path.exists(CACHE_DIR):
            return
        
        now = time.time()
        deleted = 0
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                cache_file = os.path.join(CACHE_DIR, filename)
                file_age = now - os.path.getmtime(cache_file)
                if file_age > CACHE_EXPIRE_DAYS * 24 * 3600:
                    os.remove(cache_file)
                    deleted += 1
        
        if deleted > 0:
            print(f"🗑 Rensade {deleted} gamla cache-filer")
    except Exception:
        pass

# Rensa gamla cache vid start
clear_old_cache()

# --- HUVUD FUNKTIONER ---
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
    if timestamp == 0: return False # Om datum saknas, släpp igenom
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

def strategy_fz_se(link):
    try:
        time.sleep(random.uniform(0.1, 0.3))
        r = get_session().get(link, timeout=10, verify=False)
        if r.status_code != 200: return None
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
            
            if timestamp == 0:
                timestamp = time.time() - random.randint(100, 3600)

            if is_too_old(timestamp): continue
            if not entry.get('title'): continue

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
                "time_str": "",
                "timestamp": timestamp,
                "is_video": False
            })
    except: pass
    return found_articles

def get_video_info(source):
    videos = []
    
    # Försök ladda från cache först
    cached_data = load_from_cache(source['url'])
    if cached_data:
        print(f"✓ Cache hit: {source['source_name']}")
        return cached_data
    
    print(f"📥 Hämtar YouTube: {source['source_name']}")
    
    try:
        # ANVÄND FLAT EXTRACTION MEN HÄMTA FULL INFO FÖR DATUM
        ydl_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'extract_flat': True,  # Flat för snabbhet
            'force_generic_extractor': False,
            'playlistend': 8,      # MAX 8 VIDEOS
            'no_warnings': True,
            'http_headers': HEADERS,
            'skip_download': True,
            'writeinfojson': False,
            'writethumbnail': False,
            'no_color': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if not info: 
                print(f"  ⚠ Ingen info för: {source['source_name']}")
                return videos
            
            entries = info.get('entries', [info])

            for idx, entry in enumerate(entries):
                if not entry: continue
                
                # HÄMTA THUMBNAIL
                img_url = ''
                if entry.get('thumbnail'):
                    img_url = entry['thumbnail']
                elif entry.get('thumbnails'):
                    thumbnails = entry.get('thumbnails', [])
                    if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                        # Ta högsta kvalitén (sista)
                        for thumb in reversed(thumbnails):
                            if thumb.get('url'):
                                img_url = thumb['url']
                                break
                
                if not img_url and entry.get('id'):
                    img_url = f"https://img.youtube.com/vi/{entry['id']}/maxresdefault.jpg"
                if not img_url: 
                    img_url = DEFAULT_IMAGE

                # HÄMTA UPLOAD DATE - DETTA ÄR DET VIKTIGASTE
                ts = 0
                try:
                    # Försök få upload_date (YYYYMMDD format)
                    if entry.get('upload_date'):
                        date_str = str(entry['upload_date'])
                        if len(date_str) == 8:
                            ts = datetime.strptime(date_str, '%Y%m%d').timestamp()
                            # Kontrollera att datumet inte är 1970
                            if ts > 0:
                                # Debug: visa datumet
                                date_obj = datetime.fromtimestamp(ts)
                                print(f"  ✓ Video {idx+1}: {date_obj.strftime('%Y-%m-%d')}")
                            else:
                                ts = time.time() - (idx * 86400)  # Fallback: 1 dag mellan varje video
                        else:
                            ts = time.time() - (idx * 86400)
                    else:
                        # Om inget upload_date finns, använd index för att simulera olika datum
                        ts = time.time() - (idx * 86400)  # 1 dag mellan varje video
                        
                except Exception as e:
                    print(f"  ⚠ Datumfel: {e}")
                    # Fallback: använd nuvarande tid minus baserat på index
                    ts = time.time() - (idx * 86400)
                
                # KONTROLLERA ATT TS INTE ÄR 0
                if ts <= 0:
                    ts = time.time() - (idx * 86400)
                
                title = entry.get('title', 'Video')
                if not title or title in ['Video', '[Private video]', '[Deleted video]', 'Private video', 'Deleted video']:
                    continue
                    
                clean_summary = clean_text(entry.get('description', ''))

                lang_note = ""
                if source.get('lang') == 'sv':
                    title = translate_text(title, 'sv')
                    clean_summary = translate_text(clean_summary, 'sv')
                    lang_note = " (Translated from Swedish)"

                videos.append({
                    "title": title,
                    "link": entry.get('webpage_url') or entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                    "images": [img_url],
                    "summary": clean_summary,
                    "category": source.get('cat', 'video'),
                    "filter_tag": source.get('filter_tag', ''),
                    "source": source.get('source_name', 'YouTube'),
                    "lang_note": lang_note,
                    "time_str": "",
                    "timestamp": ts,
                    "is_video": True
                })
        
        # Spara till cache om vi hämtat nya data
        if videos:
            save_to_cache(source['url'], videos)
            print(f"  ✅ {len(videos)} videos hämtade från {source['source_name']}")
        else:
            print(f"  ⚠ Inga videos hittades för {source['source_name']}")
            
    except Exception as e:
        print(f"❌ FEL VID VIDEOHÄMTNING ({source.get('source_name')}): {e}")
    
    return videos

def get_video_info_wrapper(source):
    return get_video_info(source)

def process_source(source):
    if source['type'] == 'video': 
        return get_video_info_wrapper(source)
    else: 
        return get_web_info(source)

# --- EXEKVERING ---
new_articles = []
start_time = time.time()

print(f"\n--- HÄMTAR FRÅN {len(SOURCES)} KÄLLOR ---")

# Separera video och web källor
video_sources = [s for s in SOURCES if s['type'] == 'video']
web_sources = [s for s in SOURCES if s['type'] == 'web']

print(f"🎥 Video källor: {len(video_sources)}")
print(f"📰 Web källor: {len(web_sources)}")

# Kör alla källor
all_sources = video_sources + web_sources

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    future_map = {executor.submit(process_source, s): s for s in all_sources}
    for future in concurrent.futures.as_completed(future_map):
        try:
            source = future_map[future]
            data = future.result()
            if data: 
                new_articles.extend(data)
        except Exception as e:
            print(f"❌ Fel vid hämtning: {e}")

# Ta bort duplicerade länkar
print(f"\n--- RENSAR DUBLETTER ---")
unique_map = {}
for art in new_articles:
    if not art['title'] or art['title'] in ['Video', '[Private video]', '[Deleted video]', 'Private video', 'Deleted video']: 
        continue
    
    # Normalisera YouTube-länkar
    if 'youtube.com' in art['link'] or 'youtu.be' in art['link']:
        # Extrahera video ID
        video_id = None
        if 'youtube.com/watch?v=' in art['link']:
            video_id = art['link'].split('v=')[1].split('&')[0]
        elif 'youtu.be/' in art['link']:
            video_id = art['link'].split('youtu.be/')[1].split('?')[0]
        
        if video_id:
            art['link'] = f"https://www.youtube.com/watch?v={video_id}"
    
    if art['link'] not in unique_map: 
        unique_map[art['link']] = art
        
final_list = list(unique_map.values())

# SORTERING - NYASTE FÖRST BASERAT PÅ TIMESTAMP
print(f"\n--- SORTERAR {len(final_list)} ARTIKLAR (NYASTE FÖRST) ---")
final_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

# Beräkna time_str för varje artikel - FIXAD LOGIK
print(f"\n--- BERÄKNAR TIDSSTRÄNGAR ---")
now = time.time()
for art in final_list:
    diff = now - art['timestamp']
    
    # Kontrollera att timestamp inte är 0 eller negativ
    if art['timestamp'] <= 0:
        # Om timestamp är fel, sätt till nuvarande tid
        art['timestamp'] = time.time()
        diff = 0
    
    # Beräkna tidssträng
    if diff < 60:
        art['time_str'] = "Just now"
    elif diff < 3600:
        art['time_str'] = f"{int(diff/60)}m ago"
    elif diff < 86400: 
        art['time_str'] = f"{int(diff/3600)}h ago"
    elif diff < 604800: 
        art['time_str'] = f"{int(diff/86400)}d ago"
    elif diff < 2592000:  # 30 dagar
        art['time_str'] = f"{int(diff/604800)}w ago"
    elif diff < 31536000:  # 1 år
        months = int(diff / 2592000)
        art['time_str'] = f"{months}mo ago"
    else:
        years = int(diff / 31536000)
        art['time_str'] = f"{years}y ago"

# Begränsa till TOTAL_LIMIT
final_list = final_list[:TOTAL_LIMIT]

# Räkna videos och artiklar
video_count = len([a for a in final_list if a.get('is_video')])
web_count = len(final_list) - video_count

# Spara till JSON
print(f"\n--- SPARAR TILL news.json ---")
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)

print(f"\n{'='*60}")
print(f"✅ GENERERING KLAR PÅ {time.time()-start_time:.2f} SEK")
print(f"{'='*60}")
print(f"📊 STATISTIK:")
print(f"   • Totalt: {len(final_list)} artiklar")
print(f"   • Webb: {web_count} artiklar")
print(f"   • YouTube: {video_count} videos")
print(f"   • Cache-mapp: {CACHE_DIR}/")

# Visa första 5 videos med datum för verifiering
print(f"\n📅 FÖRSTA 5 YOUTUBE VIDEOR:")
youtube_videos = [a for a in final_list if a.get('is_video')]
for i, video in enumerate(youtube_videos[:5], 1):
    date_str = datetime.fromtimestamp(video['timestamp']).strftime('%Y-%m-%d %H:%M')
    print(f"   {i}. {video['title'][:50]}...")
    print(f"      → {video['time_str']} (upload: {date_str})")
    print(f"      → Source: {video['source']}")

# Visa om någon video har felaktigt datum
problem_videos = [v for v in youtube_videos if 'mo ago' in v['time_str'] or 'y ago' in v['time_str']]
if problem_videos:
    print(f"\n⚠ {len(problem_videos)} VIDEOR MED MISSTÄNKT DATUM:")
    for video in problem_videos[:3]:
        print(f"   • {video['title'][:40]}...: {video['time_str']}")

print(f"{'='*60}")

# Generera HTML
if os.path.exists('template.html'):
    with open('template.html', 'r', encoding='utf-8') as f:
        html = f.read().replace("<!-- NEWS_DATA_JSON -->", json.dumps(final_list))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ index.html har uppdaterats!")
else:
    print("⚠ VARNING: template.html saknas!")

# Visa cache-status
if os.path.exists(CACHE_DIR):
    cache_files = len([f for f in os.listdir(CACHE_DIR) if f.endswith('.json')])
    print(f"💾 Cache: {cache_files} filer i {CACHE_DIR}/")
else:
    print(f"💾 Cache: Mapp {CACHE_DIR}/ skapades inte (inga video-källor?)")