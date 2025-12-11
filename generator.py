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
from urllib.parse import urljoin, urlparse, parse_qs
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
MAX_AGE_DAYS = 25 

MAX_SUMMARY_LENGTH = 280
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

# CACHE INSTÄLLNINGAR - 3 VECKOR
CACHE_DIR = ".youtube_cache"
CACHE_EXPIRE_DAYS = 21  # 3 veckor

# YOUTUBE API NYCKEL
YOUTUBE_API_KEY = "AIzaSyBGNGzJb2b9R1S7ur7x7Xt-d1ze6TfIOFM"

try:
    from sources import SOURCES
    print(f"--- LADDADE {len(SOURCES)} KÄLLOR ---")
except ImportError:
    SOURCES = []

print(f"--- STARTAR GENERATORN (V20.5.36 - YOUTUBE API & CACHE) ---")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

# --- HJÄLPFUNKTIONER FÖR YOUTUBE ---
def extract_video_id(url):
    """Extrahera YouTube video ID från URL"""
    if not url:
        return None
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&]+)',
        r'(?:youtu\.be\/)([^?]+)',
        r'(?:youtube\.com\/embed\/)([^\/]+)',
        r'(?:youtube\.com\/v\/)([^\/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_video_details(video_id):
    """Hämta videoinfo från YouTube API"""
    if not video_id or not YOUTUBE_API_KEY:
        return None
    
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id,
            'key': YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('items') and len(data['items']) > 0:
                return data['items'][0]
    except Exception as e:
        print(f"⚠ YouTube API error: {e}")
    
    return None

def get_channel_videos(channel_id):
    """Hämta senaste videos från en kanal via YouTube API"""
    if not channel_id or not YOUTUBE_API_KEY:
        return []
    
    try:
        url = f"https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'channelId': channel_id,
            'maxResults': 8,
            'order': 'date',
            'type': 'video',
            'key': YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json().get('items', [])
    except Exception as e:
        print(f"⚠ YouTube API search error: {e}")
    
    return []

def extract_channel_id(url):
    """Extrahera channel ID från YouTube URL"""
    try:
        if '/@' in url:
            # För @username länkar
            username = url.split('/@')[-1].split('/')[0]
            # Vi behöver konvertera username till channelId via API
            return None
        elif '/channel/' in url:
            return url.split('/channel/')[-1].split('/')[0]
        elif '/c/' in url:
            return url.split('/c/')[-1].split('/')[0]
        elif '/user/' in url:
            return url.split('/user/')[-1].split('/')[0]
    except:
        pass
    return None

# --- CACHE SYSTEM ---
def get_cache_key(url):
    """Skapa unikt cache-nyckel från URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def load_from_cache(url):
    """Ladda YouTube-data från cache om den finns och inte är utgången"""
    try:
        cache_key = get_cache_key(url)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
        
        if not os.path.exists(cache_file):
            return None
        
        # Kolla om cachen är för gammal (3 veckor)
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age > CACHE_EXPIRE_DAYS * 24 * 3600:
            return None
        
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)
        
        return cached_data
    except Exception:
        return None

def save_to_cache(url, data):
    """Spara YouTube-data till cache"""
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        cache_key = get_cache_key(url)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
        
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except Exception:
        pass

def clear_old_cache():
    """Rensa gamla cache-filer (äldre än 3 veckor)"""
    try:
        if not os.path.exists(CACHE_DIR):
            return
        
        now = time.time()
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.pkl'):
                cache_file = os.path.join(CACHE_DIR, filename)
                file_age = now - os.path.getmtime(cache_file)
                if file_age > CACHE_EXPIRE_DAYS * 24 * 3600:
                    os.remove(cache_file)
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

# --- BILDSTRATEGIER ---
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
        return cached_data
    
    try:
        print(f"📥 Hämtar YouTube: {source['source_name']}...")
        
        # Försök hämta via YouTube API först
        channel_id = extract_channel_id(source['url'])
        
        if channel_id and YOUTUBE_API_KEY:
            # Hämta via YouTube API
            api_videos = get_channel_videos(channel_id)
            
            for item in api_videos:
                try:
                    snippet = item.get('snippet', {})
                    video_id = item.get('id', {}).get('videoId')
                    
                    if not video_id:
                        continue
                    
                    # Hämta detaljerad info med publish datum
                    details = get_youtube_video_details(video_id)
                    
                    # Hämta datum - använd publishedAt från API
                    published_at = snippet.get('publishedAt')
                    if published_at:
                        try:
                            # Konvertera ISO 8601 datum till timestamp
                            dt = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                            ts = dt.timestamp()
                        except:
                            ts = time.time()
                    else:
                        ts = time.time()
                    
                    # Hämta thumbnail
                    thumbnails = snippet.get('thumbnails', {})
                    img_url = ''
                    if thumbnails.get('maxres'):
                        img_url = thumbnails['maxres']['url']
                    elif thumbnails.get('standard'):
                        img_url = thumbnails['standard']['url']
                    elif thumbnails.get('high'):
                        img_url = thumbnails['high']['url']
                    elif thumbnails.get('medium'):
                        img_url = thumbnails['medium']['url']
                    else:
                        img_url = DEFAULT_IMAGE
                    
                    title = snippet.get('title', 'Video')
                    description = snippet.get('description', '')
                    
                    if not title or title in ['[Private video]', '[Deleted video]']:
                        continue
                    
                    # 25-dagars regel
                    if ts > 0 and is_too_old(ts):
                        continue
                    
                    clean_summary = clean_text(description)
                    
                    lang_note = ""
                    if source.get('lang') == 'sv':
                        title = translate_text(title, 'sv')
                        clean_summary = translate_text(clean_summary, 'sv')
                        lang_note = " (Translated from Swedish)"
                    
                    videos.append({
                        "title": title,
                        "link": f"https://www.youtube.com/watch?v={video_id}",
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
                    
                except Exception as e:
                    print(f"  ⚠ Fel vid API video: {e}")
                    continue
        
        # Om API inte gav några videos, använd yt-dlp som fallback
        if not videos:
            print(f"  ⚠ API gav inga videos, använder yt-dlp...")
            
            ydl_opts = {
                'quiet': True,
                'ignoreerrors': True,
                'extract_flat': True,
                'playlistend': 8,
                'no_warnings': True,
                'http_headers': HEADERS,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source['url'], download=False)
                if not info:
                    return videos
                
                entries = info.get('entries', [info])

                for idx, entry in enumerate(entries):
                    if not entry:
                        continue
                    
                    # Hämta thumbnail
                    img_url = ''
                    if entry.get('thumbnail'):
                        img_url = entry['thumbnail']
                    elif entry.get('id'):
                        img_url = f"https://img.youtube.com/vi/{entry['id']}/maxresdefault.jpg"
                    
                    if not img_url:
                        img_url = DEFAULT_IMAGE
                    
                    # Hämta datum från yt-dlp
                    ts = 0
                    try:
                        if entry.get('upload_date'):
                            date_str = str(entry['upload_date'])
                            if len(date_str) == 8:
                                ts = datetime.strptime(date_str, '%Y%m%d').timestamp()
                        elif entry.get('timestamp'):
                            ts = entry['timestamp']
                    except:
                        ts = time.time() - random.randint(1, 7) * 86400
                    
                    # Om vi har video ID, försök hämta korrekt datum via API
                    video_id = entry.get('id')
                    if video_id and YOUTUBE_API_KEY and (ts == 0 or ts > time.time() - 3600):
                        details = get_youtube_video_details(video_id)
                        if details and details.get('snippet', {}).get('publishedAt'):
                            try:
                                published_at = details['snippet']['publishedAt']
                                dt = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')
                                ts = dt.timestamp()
                            except:
                                pass
                    
                    # 25-dagars regel
                    if ts > 0 and is_too_old(ts):
                        continue
                    
                    title = entry.get('title', 'Video')
                    if not title or title in ['Video', '[Private video]', '[Deleted video]']:
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

# Kör alla källor
all_sources = video_sources + web_sources

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    future_map = {executor.submit(process_source, s): s for s in all_sources}
    for future in concurrent.futures.as_completed(future_map):
        try:
            source = future_map[future]
            data = future.result()
            if data: 
                new_articles.extend(data)
                source_type = "🎥" if source['type'] == 'video' else "📰"
                print(f"{source_type} {source['source_name']}: {len(data)}")
        except Exception as e:
            print(f"❌ Fel vid hämtning: {e}")

# Ta bort duplicerade länkar
print(f"\n--- RENSAR DUBLETTER ---")
unique_map = {}
for art in new_articles:
    if not art['title'] or art['title'] in ['Video', '[Private video]', '[Deleted video]']: 
        continue
    
    # Normalisera YouTube-länkar
    if 'youtube.com' in art['link'] or 'youtu.be' in art['link']:
        video_id = extract_video_id(art['link'])
        if video_id:
            art['link'] = f"https://www.youtube.com/watch?v={video_id}"
    
    if art['link'] not in unique_map: 
        unique_map[art['link']] = art
        
final_list = list(unique_map.values())

# SORTERING - NYASTE FÖRST BASERAT PÅ TIMESTAMP
print(f"\n--- SORTERAR {len(final_list)} ARTIKLAR (NYASTE FÖRST) ---")
final_list.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

# Beräkna time_str för varje artikel
print(f"\n--- BERÄKNAR TIDSSTRÄNGAR ---")
now = time.time()
for art in final_list:
    diff = now - art['timestamp']
    
    if diff < 60:
        art['time_str'] = f"Just now"
    elif diff < 3600:
        art['time_str'] = f"{int(diff/60)}m ago"
    elif diff < 86400: 
        art['time_str'] = f"{int(diff/3600)}h ago"
    elif diff < 604800: 
        art['time_str'] = f"{int(diff/86400)}d ago"
    elif diff < 2592000:
        art['time_str'] = f"{int(diff/604800)}w ago"
    else:
        months = int(diff / 2592000)
        art['time_str'] = f"{months}mo ago"

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
print(f"   • Cache: {CACHE_DIR}/ (3 veckor)")
print(f"   • YouTube API: {'AKTIVERAD' if YOUTUBE_API_KEY else 'INAKTIV'}")
print(f"{'='*60}")

# Visa första 5 videos med datum för verifiering
print(f"\n📅 FÖRSTA 5 YOUTUBE VIDEOR:")
youtube_videos = [a for a in final_list if a.get('is_video')][:5]
for i, video in enumerate(youtube_videos, 1):
    date_str = datetime.fromtimestamp(video['timestamp']).strftime('%Y-%m-%d')
    print(f"   {i}. {video['title'][:50]}...")
    print(f"      → {video['time_str']} ({date_str})")

# Generera HTML
if os.path.exists('template.html'):
    with open('template.html', 'r', encoding='utf-8') as f:
        html = f.read().replace("<!-- NEWS_DATA_JSON -->", json.dumps(final_list))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✅ index.html har uppdaterats!")
else:
    print("⚠ VARNING: template.html saknas!")