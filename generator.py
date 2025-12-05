# generator.py – SPECULA v10.10.0 – Unsplash + No Duplicates
import feedparser, time, random, json, os, re, requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from yt_dlp import YoutubeDL

try: import sys; sys.stdout.reconfigure(encoding='utf-8')
except: pass

# ─────────────────────── KONFIG ───────────────────────
MAX_ARTICLES_PER_SOURCE = 50
MAX_DAYS_OLD = 5
MAX_VIDEO_DAYS_OLD = 3
TIMEOUT_SECONDS = 5
SITE_URL = "https://specula-news.netlify.app"

# ─────────────────────── YOUTUBE KÄLLOR ───────────────────────
YOUTUBE_CHANNELS = [
    ("https://www.youtube.com/@electricviking", "ev"),
    ("https://www.youtube.com/@Asianometry", "geopolitics"),
    ("https://www.youtube.com/@DWDocumentary", "geopolitics"),
    ("https://www.youtube.com/@inside_china_business", "geopolitics"),
    ("https://www.youtube.com/@johnnyharris", "geopolitics"),
    ("https://www.youtube.com/@TheDiaryOfACEO", "geopolitics"),
    ("https://www.youtube.com/@ShanghaiEyeMagic", "geopolitics"),
    ("https://www.youtube.com/@cgtnamerica", "geopolitics"),
    ("https://www.youtube.com/@CCTVVideoNewsAgency", "geopolitics"),
    ("https://www.youtube.com/@CGTNEurope", "geopolitics"),
    ("https://www.youtube.com/@cgtn", "geopolitics"),
    ("https://www.youtube.com/channel/UCWP1FO6PhA-LildwUO70lsA", "geopolitics"),
    ("https://www.youtube.com/@channelnewsasia", "geopolitics"),
    ("https://www.youtube.com/@GeopoliticalEconomyReport", "geopolitics"),
    ("https://www.youtube.com/@chinaviewtv", "geopolitics"),
    ("https://www.youtube.com/@eudebateslive", "geopolitics"),
    ("https://www.youtube.com/@wocomodocs", "geopolitics"),
    ("https://www.youtube.com/@elithecomputerguy", "tech"),
    ("https://www.youtube.com/@undecidedmf", "ev"),
    ("https://www.youtube.com/@elektromanija", "ev"),
    ("https://www.youtube.com/@fullychargedshow", "ev"),
    ("https://www.youtube.com/@ScienceChannel", "science"),
    ("https://www.youtube.com/@veritasium", "science"),
    ("https://www.youtube.com/@smartereveryday", "science"),
    ("https://www.youtube.com/@PracticalEngineeringChannel", "science"),
    ("https://www.youtube.com/@fii_institute", "science"),
    ("https://www.youtube.com/@spaceeyetech", "science"),
    ("https://www.youtube.com/@kzjut", "science"),
    ("https://www.youtube.com/@pbsspacetime", "science"),
    ("https://www.youtube.com/@FD_Engineering", "construction"),
    ("https://www.youtube.com/@TheB1M", "construction"),
    ("https://www.youtube.com/@TomorrowsBuild", "construction"),
]

# ─────────────────────── RSS KÄLLOR ───────────────────────
RSS_SOURCES = [
    ("https://www.dagensps.se/feed/", "geopolitics"),
    ("https://www.nyteknik.se/rss", "tech"),
    ("https://feber.se/rss/", "tech"),
    ("https://www.scmp.com/rss/91/feed", "geopolitics"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "geopolitics"),
    ("https://anastasiintech.substack.com/feed", "tech"),
    ("https://techcrunch.com/feed/", "tech"),
    ("https://www.theverge.com/rss/index.xml", "tech"),
    ("https://arstechnica.com/feed/", "tech"),
    ("https://cleantechnica.com/feed/", "ev"),
    ("https://electrek.co/feed/", "ev"),
    ("https://insideevs.com/rss/articles/all/", "ev"),
    ("https://www.greencarreports.com/rss/news", "ev"),
    ("https://oilprice.com/rss/main", "ev"),
    ("https://www.renewableenergyworld.com/feed/", "ev"),
    ("https://www.autoblog.com/category/green/rss.xml", "ev"),
    ("https://www.space.com/feeds/all", "science"),
    ("https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss", "science"),
    ("http://rss.sciam.com/ScientificAmerican-Global", "science"),
    ("https://www.newscientist.com/feed/home/", "science"),
    ("https://www.constructiondive.com/feeds/news/", "construction"),
    ("http://feeds.feedburner.com/ArchDaily", "construction"),
    ("https://www.building.co.uk/rss/news", "construction"),
    ("https://www.constructionenquirer.com/feed/", "construction"),
]

SWEDISH_SOURCES = ["feber.se","sweclockers.com","elektromanija","dagensps.se","nyteknik.se"]
BANNED_SOURCES = ["cleantechnica","oilprice","dagens ps","dagensps","al jazeera","scmp","south china morning post"]

# ─────────────────────── STATISKA FALLBACKBILDER ───────────────────────
STATIC_FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1504639725590-34d0984388bd?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1566093097221-8563d80d2d31?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1464817739973-0128fe77aaa1?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1501854140884-074cf272492b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1518005052351-53b29640dd26?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1496442226666-8d4a0e62e6e9?auto=format&fit=crop&w=800&q=80",
]

# ─────────────────────── IMAGE MANAGER (inga dubletter) ───────────────────────
class ImageManager:
    def __init__(self):
        self.available = list(STATIC_FALLBACK_IMAGES)
        random.shuffle(self.available)
        self.used = set()
    def get_unique_fallback(self):
        if not self.available: return "https://images.unsplash.com/photo-1614850523060-8da1d56ae167?q=80&w=1000&auto=format&fit=crop"
        img = self.available.pop(0)
        self.used.add(img)
        return img
    def is_used(self, url): return url in self.used
    def mark_used(self, url): 
        if url: self.used.add(url)

image_manager = None

# ─────────────────────── UNSPLASH SÖK (din nyckel inbakad) ───────────────────────
def search_unsplash_image(query):
    try:
        q = re.sub(r'[^a-zA-Z0-9 ]', '', query).strip()[:60]
        if not q: return None
        url = f"https://api.unsplash.com/search/photos?query={requests.utils.quote(q)}&per_page=1&orientation=landscape"
        headers = {"Authorization": "Client-ID NjC7cLC58hqhxaG7WQi4Ro2ghNdV5ZVI2VxXBQPidW8"}
        r = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if r.status_code == 200:
            data = r.json()
            if data.get('results'):
                img = data['results'][0]['urls']['regular']
                if not image_manager.is_used(img):
                    image_manager.mark_used(img)
                    return img
    except Exception as e:
        print(f"Unsplash error: {e}")
    return None

# ─────────────────────── BÄSTA BILDEN PER ARTIKEL ───────────────────────
def fetch_og_image(url):
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=TIMEOUT_SECONDS)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            og = soup.find("meta", property="og:image")
            if og and og.get("content"): return og["content"]
    except: pass
    return None

def get_best_image(entry, category, article_url, source_name, title):
    source_lower = source_name.lower()
    if any(b in source_lower for b in BANNED_SOURCES):
        img = search_unsplash_image(title)
        return img or image_manager.get_unique_fallback()

    # RSS-bild
    rss_img = None
    try:
        if hasattr(entry,'media_content') and entry.media_content: rss_img = entry.media_content[0].get('url')
        elif hasattr(entry,'media_thumbnail') and entry.media_thumbnail: rss_img = entry.media_thumbnail[0].get('url')
        elif hasattr(entry,'links'):
            for l in entry.links:
                if l.get('type','').startswith('image/'): rss_img = l.get('href')
    except: pass
    if rss_img and not image_manager.is_used(rss_img):
        if not any(k in rss_img.lower() for k in ["placeholder","pixel","default","icon","feedburner"]):
            image_manager.mark_used(rss_img)
            return rss_img

    # og:image
    real = fetch_og_image(article_url)
    if real and not image_manager.is_used(real):
        image_manager.mark_used(real)
        return real

    # Unsplash som backup
    unsplash = search_unsplash_image(title)
    if unsplash: return unsplash

    return image_manager.get_unique_fallback()

# ─────────────────────── HJÄLPFUNKTIONER ───────────────────────
def clean_summary(s):
    if not s: return ""
    try: return BeautifulSoup(s,'html.parser').get_text()[:200] + ("..." if len(s)>200 else "")
    except: return str(s)[:200] + "..."

def translate_text(t):
    try: return GoogleTranslator(source='sv',target='en').translate(t)
    except: return t

def fetch_youtube_videos(channel_url, category):
    ydl_opts = {'quiet':True,'extract_flat':'in_playlist','playlistend':10,'ignoreerrors':True}
    videos = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            if "@" in channel_url and not channel_url.endswith("/videos"): channel_url += "/videos"
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                source = info.get('uploader','YouTube')
                for e in info['entries']:
                    if not e: continue
                    vid_id = e.get('id')
                    if not vid_id: continue
                    img = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    ts = datetime.strptime(e.get('upload_date'),"%Y%m%d").timestamp() if e.get('upload_date') else time.time()
                    if (time.time()-ts)/86400 > MAX_VIDEO_DAYS_OLD: continue
                    image_manager.mark_used(img)
                    videos.append({
                        "title": e.get('title','Video'),
                        "link": f"https://www.youtube.com/watch?v={vid_id}",
                        "summary": clean_summary(e.get('description','')),
                        "image": img,
                        "source": source,
                        "category": category,
                        "published": ts,
                        "time_str": "Recent",
                        "is_video": True
                    })
    except: pass
    return videos

# ─────────────────────── GENERERA SIDAN ───────────────────────
def generate_site():
    global image_manager
    image_manager = ImageManager()
    print("SPECULA v10.10.0 – Unsplash Integrated + No Duplicates")
    all_articles, seen_titles = [], set()

    # YouTube
    for url, cat in YOUTUBE_CHANNELS:
        all_articles.extend(fetch_youtube_videos(url, cat))

    # RSS
    headers = {'User-Agent':'Mozilla/5.0'}
    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.get('title','News')
            is_swedish = any(s in url for s in SWEDISH_SOURCES)

            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                title = entry.title
                if title in seen_titles: continue
                seen_titles.add(title)

                pub_ts = time.time()
                if hasattr(entry,'published_parsed') and entry.published_parsed:
                    pub_ts = time.mktime(entry.published_parsed)
                if (time.time()-pub_ts)/86400 > MAX_DAYS_OLD: continue
                time_str = "Just Now" if (time.time()-pub_ts)/86400 < 1 else f"{int((time.time()-pub_ts)/86400)}d Ago"

                summary = clean_summary(getattr(entry,'summary',''))
                note = ' <span class="lang-note">(Translated)</span>' if is_swedish else ""
                if is_swedish:
                    title = translate_text(title)
                    summary = translate_text(summary)

                img = get_best_image(entry, category, entry.link, source_name, title)

                all_articles.append({
                    "title": title,
                    "link": entry.link,
                    "summary": summary + note,
                    "image": img,
                    "source": source_name,
                    "category": category,
                    "published": pub_ts,
                    "time_str": time_str,
                    "is_video": False
                })
        except Exception as e:
            print(f"RSS error {url}: {e}")

    all_articles.sort(key=lambda x: x.get('published',0), reverse=True)
    json_data = json.dumps(all_articles, ensure_ascii=False)

    if os.path.exists("template.html"):
        with open("template.html","r",encoding="utf-8") as f: template = f.read()
        final_html = template.replace("<!-- NEWS_DATA_JSON -->", json_data)
        with open("index.html","w",encoding="utf-8") as f: f.write(final_html)

        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        with open("sitemap.xml","w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}/index.html</loc><lastmod>{now}</lastmod></url></urlset>')
        with open("robots.txt","w") as f:
            f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

        print("KLAR! index.html genererad – inga dubbla bilder, perfekta Unsplash-bilder")
    else:
        print("template.html saknas!")

if __name__ == "__main__":
    generate_site()
