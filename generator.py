import json
import os
import requests
import feedparser
from bs4 import BeautifulSoup
import time
import random
import concurrent.futures
from urllib.parse import urljoin
import urllib3
import re
import yt_dlp
from datetime import datetime

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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.google.com/"
}

def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

# --- STRATEGIES ---
def strat_og(soup, html, url):
    m = soup.find("meta", property="og:image")
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_twitter(soup, html, url):
    m = soup.find("meta", attrs={"name": "twitter:image"})
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_swec(soup, html, url):
    m = re.findall(r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[^"\'\s>]+)', html)
    return max(m, key=len).replace("&amp;", "&") if m else None

def strat_afton(soup, html, url):
    m = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)', html)
    return m[0] if m else None

def strat_wordpress(soup, html, url):
    img = soup.find('img', class_=re.compile('wp-post-image'))
    return urljoin(url, img.get('src')) if img else None

def strat_lazy(soup, html, url):
    img = soup.find('img', attrs={"data-src": True})
    return urljoin(url, img['data-src']) if img else None

def strat_hero(soup, html, url):
    for cls in ['hero', 'featured', 'main-image', 'article-image', 'post-thumbnail']:
        div = soup.find(class_=re.compile(cls, re.I))
        if div:
            img = div.find('img')
            if img: return urljoin(url, img.get('src'))
    return None

def strat_largest(soup, html, url):
    imgs = soup.find_all('img', src=True)
    if not imgs: return None
    target = soup.find('article')
    if target:
        img = target.find('img', src=True)
        if img: return urljoin(url, img['src'])
    return urljoin(url, imgs[0]['src'])

STRATEGY_MAP = {
    'og': strat_og, 'twitter': strat_twitter, 
    'swec': strat_swec, 'afton': strat_afton, 
    'wordpress': strat_wordpress, 'lazy': strat_lazy, 
    'hero': strat_hero, 'largest': strat_largest
}

def get_image(entry, source):
    # 1. TVINGAD STRATEGI
    strat_name = source.get('image_strategy')
    if strat_name and strat_name in STRATEGY_MAP:
        try:
            r = get_session().get(entry.link, timeout=10, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            func = STRATEGY_MAP[strat_name]
            img = func(soup, r.text, entry.link)
            if img: return img
        except: pass

    # 2. RSS (Prioritera)
    if 'media_content' in entry:
        try: return entry.media_content[0]['url']
        except: pass
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'): return enc.get('href')

    # 3. CONTENT (WP Fix)
    if 'content' in entry:
        for c in entry.content:
            try:
                soup = BeautifulSoup(c.value, 'html.parser')
                img = soup.find('img')
                if img: return img.get('src')
            except: pass

    # 4. DEEP SCRAPE (Fallback)
    try:
        r = get_session().get(entry.link, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        for func in [strat_og, strat_twitter, strat_wordpress, strat_hero, strat_lazy]:
            res = func(soup, r.text, entry.link)
            if res: return res
    except: pass

    return DEFAULT_IMAGE

def process_feed(source):
    articles = []
    try:
        r = get_session().get(source['url'], timeout=15, verify=False)
        if r.status_code != 200:
            print(f"FAILED: {source['url']} (Status {r.status_code})")
            return []
            
        feed = feedparser.parse(r.content)
        if not feed.entries:
            print(f"EMPTY: {source['url']} (Inga artiklar hittades)")
            return []

        for entry in feed.entries[:MAX_ARTICLES]:
            # Datumhantering
            ts = time.time()
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    ts = time.mktime(entry.published_parsed)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    ts = time.mktime(entry.updated_parsed)
            except: pass 

            if (time.time() - ts) > (MAX_AGE_DAYS * 86400): continue

            img = get_image(entry, source)
            
            desc = ""
            if 'summary' in entry: desc = entry.summary
            elif 'description' in entry: desc = entry.description
            
            clean_desc = BeautifulSoup(desc, 'html.parser').get_text(separator=' ').strip()
            clean_desc = " ".join(clean_desc.split())[:280] + "..." if len(clean_desc) > 280 else clean_desc

            title = entry.title
            if TRANSLATOR_ACTIVE and source.get('lang') == 'sv':
                try: title = GoogleTranslator(source='sv', target='en').translate(title)
                except: pass

            articles.append({
                "title": title, "link": entry.link, "images": [img or DEFAULT_IMAGE],
                "summary": clean_desc, "category": source['cat'], "filter_tag": source.get('filter_tag', ''),
                "source": source.get('source_name', 'News'), "timestamp": ts, "is_video": False,
                "feed_url": source['url']
            })
    except Exception as e: print(f"CRASH: {source['url']} - {e}")
    return articles

def get_video_info(source):
    videos = []
    try:
        # extract_flat=True ger oss 'upload_date' (YYYYMMDD) men inte exakt klockslag
        ydl_opts = {'quiet': True, 'ignoreerrors': True, 'extract_flat': True, 'playlistend': 5}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            for entry in info.get('entries', []):
                if not entry: continue
                desc = entry.get('description') or entry.get('title') or "Video Update"
                thumb = entry.get('thumbnails', [{}])[-1].get('url', DEFAULT_IMAGE)
                
                # --- FIX: PARSE YOUTUBE DATE ---
                ts = time.time()
                date_str = entry.get('upload_date')
                if date_str:
                    try:
                        dt = datetime.strptime(date_str, '%Y%m%d')
                        ts = dt.timestamp()
                    except: pass
                
                videos.append({
                    "title": entry['title'], "link": entry['url'], "images": [thumb],
                    "summary": desc[:280], "category": source['cat'], "filter_tag": source.get('filter_tag', ''),
                    "source": source['source_name'], "timestamp": ts, "is_video": True,
                    "feed_url": source['url']
                })
    except Exception as e: print(f"YT Error {source['url']}: {e}")
    return videos

if __name__ == "__main__":
    try:
        from sources import SOURCES
    except: SOURCES = []

    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
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
            final.append(a); seen.add(a['link'])
            
    # TIDSFORMATERING FÖR JSON
    now = time.time()
    for art in final:
        diff = now - art['timestamp']
        if diff < 3600: art['time_str'] = "Just Now"
        elif diff < 86400: art['time_str'] = f"{int(diff/3600)}h ago"
        elif diff < 604800: art['time_str'] = f"{int(diff/86400)}d ago"
        else: art['time_str'] = f"{int(diff/604800)}w ago"

    with open('news.json', 'w', encoding='utf-8') as f: json.dump(final[:TOTAL_LIMIT], f, ensure_ascii=False, indent=2)
    
    if os.path.exists('template.html'):
        with open('template.html', 'r', encoding='utf-8') as f: html = f.read()
        html = html.replace("<!-- NEWS_DATA_JSON -->", json.dumps(final[:TOTAL_LIMIT]))
        if '<head>' in html and 'no-referrer' not in html:
            html = html.replace('<head>', '<head><meta name="referrer" content="no-referrer">')
        with open("index.html", "w", encoding="utf-8") as f: f.write(html)