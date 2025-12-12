import json
import os
import requests
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
import yt_dlp

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_ACTIVE = True
except ImportError:
    TRANSLATOR_ACTIVE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIG ---
MAX_ARTICLES = 10
TOTAL_LIMIT = 2000
MAX_AGE_DAYS = 90
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def get_session():
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    return s

# --- STRATEGIES ---
def strat_og(soup, url):
    m = soup.find("meta", property="og:image")
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_twitter(soup, url):
    m = soup.find("meta", attrs={"name": "twitter:image"})
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_json(soup):
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string)
            if isinstance(d, list): d = d[0]
            if 'image' in d:
                img = d['image']
                return img['url'] if isinstance(img, dict) else img
        except: continue
    return None

def strat_swec(html):
    m = re.findall(r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[^"\'\s>]+)', html)
    return max(m, key=len).replace("&amp;", "&") if m else None

def strat_afton(html):
    m = re.findall(r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)', html)
    return m[0] if m else None

def strat_largest(soup, url):
    # Find image with largest srcset or just generic heuristic
    imgs = soup.find_all('img', src=True)
    if not imgs: return None
    # Simple heuristic: pick first image inside an article tag if exists, else first likely content image
    target = soup.find('article')
    if target: 
        img = target.find('img', src=True)
        if img: return urljoin(url, img['src'])
    return urljoin(url, imgs[0]['src'])

# --- MAIN LOGIC ---
def get_image(entry, source):
    # 1. CHECK EXPLICIT STRATEGY FROM SOURCES.PY
    strat = source.get('image_strategy')
    if strat:
        try:
            r = get_session().get(entry.link, timeout=10, verify=False)
            html = r.text
            soup = BeautifulSoup(html, 'html.parser')
            
            if strat == 'og': return strat_og(soup, entry.link)
            if strat == 'twitter': return strat_twitter(soup, entry.link)
            if strat == 'json': return strat_json(soup)
            if strat == 'swec': return strat_swec(html)
            if strat == 'afton': return strat_afton(html)
            if strat == 'largest': return strat_largest(soup, entry.link)
        except: pass

    # 2. DEFAULT FALLBACKS (RSS Content)
    if 'media_content' in entry:
        try: return entry.media_content[0]['url']
        except: pass
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'): return enc.get('href')
            
    # 3. AUTO-DETECT (Deep Scrape if needed)
    # Don't deep scrape generic sites to save time, unless specified above
    return DEFAULT_IMAGE

def process_feed(source):
    articles = []
    try:
        r = get_session().get(source['url'], timeout=10, verify=False)
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:MAX_ARTICLES]:
            # Date Parsing
            ts = time.time()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                ts = time.mktime(entry.published_parsed)
            
            if (time.time() - ts) > (MAX_AGE_DAYS * 86400): continue

            img = get_image(entry, source)
            
            # Text Cleaning
            desc = BeautifulSoup(entry.get('summary', ''), 'html.parser').get_text()[:MAX_SUMMARY_LENGTH] + "..."
            
            # Translation
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
                "is_video": source['type'] == 'video'
            })
    except Exception as e: print(f"Error {source['url']}: {e}")
    return articles

def get_video_info(source):
    # Simplified YouTube logic
    videos = []
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True, 'playlistend': 5}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            for entry in info['entries']:
                videos.append({
                    "title": entry['title'],
                    "link": entry['url'],
                    "images": [entry.get('thumbnails', [{}])[-1].get('url', DEFAULT_IMAGE)],
                    "summary": "Video Update",
                    "category": source['cat'],
                    "filter_tag": source.get('filter_tag', ''),
                    "source": source['source_name'],
                    "timestamp": time.time(), # Placeholder if no date
                    "is_video": True
                })
    except: pass
    return videos

# --- EXECUTION ---
if __name__ == "__main__":
    try:
        from sources import SOURCES
    except:
        SOURCES = []
        
    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for s in SOURCES:
            if s['type'] == 'video': futures.append(executor.submit(get_video_info, s))
            else: futures.append(executor.submit(process_feed, s))
            
        for f in concurrent.futures.as_completed(futures):
            all_data.extend(f.result())

    all_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Simple Dedup
    seen = set()
    final = []
    for a in all_data:
        if a['link'] not in seen:
            final.append(a)
            seen.add(a['link'])
            
    final = final[:TOTAL_LIMIT]

    # Export
    with open('news.json', 'w') as f: json.dump(final, f, indent=2)
    
    # Template Update
    if os.path.exists('template.html'):
        with open('template.html', 'r') as f: html = f.read()
        html = html.replace("<!-- NEWS_DATA_JSON -->", json.dumps(final))
        with open("index.html", "w") as f: f.write(html)
        print("Done.")