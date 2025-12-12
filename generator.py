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

# --- ALLA LOGIKER ---
def strat_og(soup, url):
    m = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_twitter(soup, url):
    m = soup.find("meta", attrs={"name": "twitter:image"}) or soup.find("meta", property="twitter:image")
    return urljoin(url, m["content"]) if m and m.get("content") else None

def strat_json(soup, url):
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string); d = d[0] if isinstance(d, list) else d
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

def strat_srcset(soup, url):
    img = soup.find('img', srcset=True)
    if img:
        return urljoin(url, img['srcset'].split(',')[-1].strip().split(' ')[0])
    return None

def strat_lazy(soup, url):
    img = soup.find('img', attrs={"data-src": True}) or soup.find('img', attrs={"data-lazy-src": True})
    return urljoin(url, img.get('data-src') or img.get('data-lazy-src')) if img else None

def strat_hero(soup, url):
    for cls in ['hero', 'featured', 'main-image', 'article-image', 'post-thumbnail']:
        div = soup.find(class_=re.compile(cls, re.I))
        if div:
            img = div.find('img')
            if img: return urljoin(url, img.get('src') or img.get('data-src'))
    return None

STRATEGY_MAP = {
    'og': strat_og, 'twitter': strat_twitter, 'json': strat_json,
    'swec': strat_swec, 'afton': strat_afton, 'hero': strat_hero, 
    'srcset': strat_srcset, 'lazy': strat_lazy
}

def get_image(entry, source):
    # 1. TVINGAD STRATEGI FRÅN ADMIN
    strat_name = source.get('image_strategy')
    if strat_name and strat_name in STRATEGY_MAP:
        try:
            r = get_session().get(entry.link, timeout=10, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            func = STRATEGY_MAP[strat_name]
            res = func(r.text if strat_name in ['swec', 'afton'] else soup, entry.link)
            if res: return res
        except: pass

    # 2. RSS FLÖDE
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'): return enc.get('href')

    # 3. AUTO DEEP SCRAPE (Standard)
    try:
        r = get_session().get(entry.link, timeout=8, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        for func in [strat_og, strat_twitter, strat_json, strat_hero]:
            res = func(soup, entry.link)
            if res: return res
    except: pass
    return DEFAULT_IMAGE

def process_feed(source):
    articles = []
    try:
        r = get_session().get(source['url'], timeout=10, verify=False)
        feed = feedparser.parse(r.content)
        for entry in feed.entries[:MAX_ARTICLES]:
            try:
                ts = time.mktime(entry.published_parsed) if hasattr(entry, 'published_parsed') else time.time()
            except: ts = time.time()
            if (time.time() - ts) > (MAX_AGE_DAYS * 86400): continue

            img = get_image(entry, source)
            raw_desc = entry.get('summary', '') or entry.get('description', '')
            desc = BeautifulSoup(raw_desc, 'html.parser').get_text(separator=' ').strip()
            desc = (desc[:250] + '...') if len(desc) > 250 else desc

            articles.append({
                "title": entry.title, "link": entry.link, "images": [img],
                "summary": desc, "category": source['cat'], "filter_tag": source.get('filter_tag', ''),
                "source": source.get('source_name', 'News'), "timestamp": ts, "is_video": False, "feed_url": source['url']
            })
    except: pass
    return articles

# --- YOUTUBE & MAIN LOOP (Samma som förut) ---
def get_video_info(source):
    videos = []
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True, 'playlistend': 5}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source['url'], download=False)
            for entry in info.get('entries', []):
                videos.append({
                    "title": entry['title'], "link": entry['url'], "images": [entry['thumbnails'][-1]['url']],
                    "summary": entry.get('description', 'Video Update')[:250], "category": source['cat'],
                    "source": source['source_name'], "timestamp": time.time(), "is_video": True, "feed_url": source['url']
                })
    except: pass
    return videos

if __name__ == "__main__":
    from sources import SOURCES
    all_data = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(get_video_info if s['type'] == 'video' else process_feed, s) for s in SOURCES]
        for f in concurrent.futures.as_completed(futures):
            all_data.extend(f.result())

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