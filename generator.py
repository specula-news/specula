import json, os, requests, feedparser, time, random, concurrent.futures, re, yt_dlp, urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from email.utils import parsedate_to_datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIG ---
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

# --- SPECIFIKA LOGIKER ---
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

def strat_first(soup, html, url):
    # Desperat metod: Ta första bästa bild i artikeln
    target = soup.find('article') or soup
    img = target.find('img', src=True)
    if img: return urljoin(url, img['src'])
    return None

STRATEGY_MAP = {
    'og': strat_og, 'twitter': strat_twitter, 
    'swec': strat_swec, 'afton': strat_afton, 
    'wordpress': strat_wordpress, 'lazy': strat_lazy, 
    'hero': strat_hero, 'first_img': strat_first
}

def get_image(entry, source):
    # 1. KONTROLLERA OM ADMIN HAR VALT EN STRATEGI
    forced_strat = source.get('image_strategy')
    
    if forced_strat and forced_strat in STRATEGY_MAP:
        try:
            # Gå direkt till källan och använd vald logik
            r = get_session().get(entry.link, timeout=10, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            func = STRATEGY_MAP[forced_strat]
            img = func(soup, r.text, entry.link)
            if img: return img
        except: pass # Om vald strategi misslyckas, fall tillbaka till standard

    # 2. STANDARD: RSS BILD (Snabbt & Säkert)
    if 'media_content' in entry:
        try: return entry.media_content[0]['url']
        except: pass
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'): return enc.get('href')

    # 3. FALLBACK: FÖRSÖK HITTA NÅGOT (Deep Scrape)
    try:
        r = get_session().get(entry.link, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Prioritetsordning
        for func in [strat_og, strat_twitter, strat_wordpress, strat_hero, strat_lazy]:
            img = func(soup, r.text, entry.link)
            if img: return img
    except: pass

    return DEFAULT_IMAGE

def process_feed(source):
    articles = []
    try:
        r = get_session().get(source['url'], timeout=15, verify=False)
        feed = feedparser.parse(r.content)
        if not feed.entries: return []

        for entry in feed.entries[:MAX_ARTICLES]:
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    ts = time.mktime(entry.published_parsed)
                else: ts = time.time()
            except: ts = time.time()

            if (time.time() - ts) > (MAX_AGE_DAYS * 86400): continue

            # HÄMTA BILD MED LOGIKEN OVAN
            img = get_image(entry, source)
            
            desc = entry.get('summary', '') or entry.get('description', '')
            desc = BeautifulSoup(desc, 'html.parser').get_text(separator=' ').strip()
            desc = (desc[:280] + '...') if len(desc) > 280 else desc

            title = entry.title
            if TRANSLATOR_ACTIVE and source.get('lang') == 'sv':
                try: title = GoogleTranslator(source='sv', target='en').translate(title)
                except: pass

            articles.append({
                "title": title, "link": entry.link, "images": [img or DEFAULT_IMAGE],
                "summary": desc, "category": source['cat'], "filter_tag": source.get('filter_tag', ''),
                "source": source.get('source_name', 'News'), "timestamp": ts, "is_video": False,
                "feed_url": source['url'] # Viktigt för admin-koppling
            })
    except Exception as e: print(f"Error {source['url']}: {e}")
    return articles

def get_video_info(source):
    videos = []
    try:
        ydl_opts = {'quiet': True, 'ignoreerrors': True, 'extract_flat': True, 'playlistend': 5}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            for entry in info.get('entries', []):
                if not entry: continue
                desc = entry.get('description') or entry.get('title') or "Video Update"
                videos.append({
                    "title": entry['title'], "link": entry['url'], "images": [entry['thumbnails'][-1]['url']],
                    "summary": desc[:280], "category": source['cat'], "filter_tag": source.get('filter_tag', ''),
                    "source": source['source_name'], "timestamp": time.time(), "is_video": True,
                    "feed_url": source['url']
                })
    except: pass
    return videos

if __name__ == "__main__":
    try:
        from sources import SOURCES
    except: SOURCES = []

    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for s in SOURCES:
            if s['type'] == 'video': futures.append(executor.submit(get_video_info, s))
            else: futures.append(executor.submit(process_feed, s))
        for f in concurrent.futures.as_completed(futures):
            try: all_data.extend(f.result())
            except: pass

    all_data.sort(key=lambda x: x['timestamp'], reverse=True)
    final = []
    seen = set()
    for a in all_data:
        if a['link'] not in seen:
            final.append(a); seen.add(a['link'])
            
    with open('news.json', 'w', encoding='utf-8') as f: json.dump(final[:TOTAL_LIMIT], f, ensure_ascii=False, indent=2)
    
    if os.path.exists('template.html'):
        with open('template.html', 'r', encoding='utf-8') as f: 
            html = f.read().replace("<!-- NEWS_DATA_JSON -->", json.dumps(final[:TOTAL_LIMIT]))
        with open("index.html", "w", encoding="utf-8") as f: f.write(html)