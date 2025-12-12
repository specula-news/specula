import json
import os
import requests
import feedparser
from bs4 import BeautifulSoup
import time
import random
import concurrent.futures
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
import urllib3
import re
import yt_dlp

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_ACTIVE = True
except ImportError:
    TRANSLATOR_ACTIVE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
MAX_ARTICLES = 10
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

# --- STRATEGIES (MATCHING ADMIN JS) ---
def strat_og(soup, url):
    m = soup.find("meta", property="og:image")
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_twitter(soup, url):
    m = soup.find("meta", attrs={"name": "twitter:image"})
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_json(soup, url):
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string)
            if isinstance(d, list): d = d[0]
            if 'image' in d:
                img = d['image']
                res = img['url'] if isinstance(img, dict) else img
                return urljoin(url, res)
        except: continue
    return None

def strat_swec(html, url):
    m = re.findall(r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[^"\'\s>]+)', html)
    return max(m, key=len).replace("&amp;", "&") if m else None

def strat_afton(html, url):
    m = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)', html)
    return m[0] if m else None

def strat_wordpress(soup, url):
    img = soup.find('img', class_=re.compile('wp-post-image'))
    return urljoin(url, img.get('src')) if img else None

def strat_lazy(soup, url):
    img = soup.find('img', attrs={"data-src": True})
    return urljoin(url, img['data-src']) if img else None

def strat_hero(soup, url):
    for cls in ['hero', 'featured', 'main-image', 'article-image', 'post-thumbnail']:
        div = soup.find(class_=re.compile(cls, re.I))
        if div:
            img = div.find('img')
            if img: return urljoin(url, img.get('src'))
    return None

def strat_largest(soup, url):
    imgs = soup.find_all('img', src=True)
    if not imgs: return None
    target = soup.find('article')
    if target:
        img = target.find('img', src=True)
        if img: return urljoin(url, img['src'])
    return urljoin(url, imgs[0]['src'])

STRATEGY_MAP = {
    'og': strat_og, 'twitter': strat_twitter, 'json': strat_json,
    'swec': strat_swec, 'afton': strat_afton, 'hero': strat_hero, 
    'largest': strat_largest, 'wordpress': strat_wordpress, 'lazy': strat_lazy
}

def get_image(entry, source):
    # 1. SPECIFIK STRATEGI
    strat_name = source.get('image_strategy')
    if strat_name and strat_name in STRATEGY_MAP:
        try:
            r = get_session().get(entry.link, timeout=10, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            func = STRATEGY_MAP[strat_name]
            if strat_name in ['swec', 'afton']: res = func(r.text, entry.link)
            else: res = func(soup, entry.link)
            if res: return res
        except: pass

    # 2. RSS FLÖDE
    if 'media_content' in entry:
        try: return entry.media_content[0]['url']
        except: pass
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'): return enc.get('href')
            
    # 3. CONTENT SCAN (WP FIX)
    if 'content' in entry:
        for c in entry.content:
            try:
                soup = BeautifulSoup(c.value, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'): return img['src']
            except: pass

    # 4. FALLBACK DEEP SCRAPE
    try:
        r = get_session().get(entry.link, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        for func in [strat_og, strat_twitter, strat_wordpress, strat_hero, strat_lazy]:
            res = func(soup, entry.link)
            if res: return res
    except: pass

    return DEFAULT_IMAGE

def process_feed(source):
    articles = []
    try:
        r = get_session().get(source['url'], timeout=10, verify=False)
        feed = feedparser.parse(r.content)
        if not feed.entries: return []

        for entry in feed.entries[:MAX_ARTICLES]:
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    ts = time.mktime(entry.published_parsed)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    ts = time.mktime(entry.updated_parsed)
                else: ts = time.time()
            except: ts = time.time()

            if (time.time() - ts) > (MAX_AGE_DAYS * 86400): continue

            img = get_image(entry, source)
            
            raw_desc = entry.get('summary', '') or entry.get('description', '')
            desc = BeautifulSoup(raw_desc, 'html.parser').get_text(separator=' ').strip()
            desc = " ".join(desc.split())[:280] + "..." if len(desc) > 280 else desc

            title = entry.title
            if TRANSLATOR_ACTIVE and source.get('lang') == 'sv':
                try:
                    title = GoogleTranslator(source='sv', target='en').translate(title)
                    desc = GoogleTranslator(source='sv', target='en').translate(desc)
                except: pass

            articles.append({
                "title": title, 
                "link": entry.link, 
                "images": [img or DEFAULT_IMAGE],
                "summary": desc, 
                "category": source['cat'], 
                "filter_tag": source.get('filter_tag', ''),
                "source": source.get('source_name', 'News'), 
                "timestamp": ts, 
                "is_video": False,
                "feed_url": source['url']  # KEY FOR ADMIN MATCHING
            })
    except Exception as e: print(f"Error {source['url']}: {e}")
    return articles

def get_video_info(source):
    videos = []
    try:
        ydl_opts = {'quiet': True, 'ignoreerrors': True, 'extract_flat': True, 'playlistend': 5}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            if not info: return []
            entries = info.get('entries', [])
            
            for entry in entries:
                if not entry: continue
                desc = entry.get('description') or entry.get('title') or "Video Update"
                desc = desc[:280] + "..." if len(desc) > 280 else desc
                thumb = entry.get('thumbnails', [{}])[-1].get('url', DEFAULT_IMAGE)
                
                videos.append({
                    "title": entry['title'], 
                    "link": entry['url'], 
                    "images": [thumb],
                    "summary": desc, 
                    "category": source['cat'], 
                    "filter_tag": source.get('filter_tag', ''),
                    "source": source['source_name'], 
                    "timestamp": time.time(), 
                    "is_video": True,
                    "feed_url": source['url'] # KEY FOR ADMIN MATCHING
                })
    except Exception as e: print(f"YT Error {source['url']}: {e}")
    return videos

if __name__ == "__main__":
    try:
        from sources import SOURCES
    except ImportError:
        print("Error: sources.py not found.")
        SOURCES = []

    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for s in SOURCES:
            if s['type'] == 'video': futures.append(executor.submit(get_video_info, s))
            else: futures.append(executor.submit(process_feed, s))
            
        for f in concurrent.futures.as_completed(futures):
            try:
                res = f.result()
                if res: all_data.extend(res)
            except: pass

    all_data.sort(key=lambda x: x['timestamp'], reverse=True)
    seen = set()
    final = []
    for a in all_data:
        if a['link'] not in seen:
            final.append(a)
            seen.add(a['link'])
            
    final = final[:TOTAL_LIMIT]

    now = time.time()
    for art in final:
        diff = now - art['timestamp']
        if diff < 3600: art['time_str'] = "Just Now"
        elif diff < 86400: art['time_str'] = f"{int(diff/3600)}h ago"
        else: art['time_str'] = f"{int(diff/86400)}d ago"

    with open('news.json', 'w', encoding='utf-8') as f: json.dump(final, f, ensure_ascii=False, indent=2)
    
    if os.path.exists('template.html'):
        with open('template.html', 'r', encoding='utf-8') as f: html = f.read()
        html = html.replace("<!-- NEWS_DATA_JSON -->", json.dumps(final))
        with open("index.html", "w", encoding="utf-8") as f: f.write(html)
        print("SUCCESS: index.html updated.")