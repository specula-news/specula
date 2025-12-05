import feedparser
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import random
import json
import sys
import os
import re
import requests
from deep_translator import GoogleTranslator
from yt_dlp import YoutubeDL

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# --- KONFIGURATION ---
MAX_ARTICLES_PER_SOURCE = 50
MAX_DAYS_OLD = 5
MAX_VIDEO_DAYS_OLD = 3
TIMEOUT_SECONDS = 4

SITE_URL = "https://specula-news.netlify.app"

# --- KÄLLOR ---
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

SWEDISH_SOURCES = ["feber.se", "sweclockers.com", "elektromanija", "dagensps.se", "nyteknik.se"]

# --- STATIC IMAGE LIBRARY (GARANTERAT UNIKA BILDER) ---
# En hårdkodad lista med bra bilder för att slippa strul med Unsplash IDn.
STATIC_FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80", # High rise
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=800&q=80", # City
    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=800&q=80", # Urban
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80", # Tech chip
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80", # Coding
    "https://images.unsplash.com/photo-1504639725590-34d0984388bd?auto=format&fit=crop&w=800&q=80", # Code screen
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80", # Globe/Network
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80", # Digital abstract
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80", # Matrix code
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=800&q=80", # Cyberpunk city
    "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80", # EV Charging
    "https://images.unsplash.com/photo-1566093097221-8563d80d2d31?auto=format&fit=crop&w=800&q=80", # Electric car
    "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?auto=format&fit=crop&w=800&q=80", # Nature road
    "https://images.unsplash.com/photo-1464817739973-0128fe77aaa1?auto=format&fit=crop&w=800&q=80", # Mountains
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80", # Sea
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=800&q=80", # Nature
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=800&q=80", # Forest
    "https://images.unsplash.com/photo-1501854140884-074cf272492b?auto=format&fit=crop&w=800&q=80", # Dark mountain
    "https://images.unsplash.com/photo-1518005052351-53b29640dd26?auto=format&fit=crop&w=800&q=80", # Abstract landscape
    "https://images.unsplash.com/photo-1496442226666-8d4a0e62e6e9?auto=format&fit=crop&w=800&q=80", # New York
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=800&q=80", # City night
    "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80", # City skyline
    "https://images.unsplash.com/photo-1444723121867-bddbc7113f43?auto=format&fit=crop&w=800&q=80", # Satellite
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80", # Earth network
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80", # Tech
    "https://images.unsplash.com/photo-1526304640152-d29241528c7d?auto=format&fit=crop&w=800&q=80", # Plants
    "https://images.unsplash.com/photo-1530210124550-912dc1381cb8?auto=format&fit=crop&w=800&q=80", # Rocks
    "https://images.unsplash.com/photo-1504384308090-c54be3855833?auto=format&fit=crop&w=800&q=80", # Abstract dark
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?auto=format&fit=crop&w=800&q=80", # Fluid
    "https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=800&q=80", # Solar panels
    "https://images.unsplash.com/photo-1566093097221-8563d80d2d31?auto=format&fit=crop&w=800&q=80", # Charging
    "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80", # Charger
    "https://images.unsplash.com/photo-1620882352329-a41764645229?auto=format&fit=crop&w=800&q=80", # EV car
    "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80", # Earth
    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80", # Chart
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80", # Data
    "https://images.unsplash.com/photo-1543286386-2e659306cd6c?auto=format&fit=crop&w=800&q=80", # Groceries
    "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=800&q=80", # Meeting
    "https://images.unsplash.com/photo-1521791136064-7986608178d4?auto=format&fit=crop&w=800&q=80", # Shakehand
    "https://images.unsplash.com/photo-1579532537598-459ecdaf39cc?auto=format&fit=crop&w=800&q=80", # Money
    "https://images.unsplash.com/photo-1611974765270-ca1258634369?auto=format&fit=crop&w=800&q=80", # Stock graph
    "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80", # Stock
    "https://images.unsplash.com/photo-1529400971008-f566de0e6dfc?auto=format&fit=crop&w=800&q=80", # Job
    "https://images.unsplash.com/photo-1535320903710-d9cf11df87b6?auto=format&fit=crop&w=800&q=80", # Papers
    "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80", # Business
    "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=800&q=80", # Typing
    "https://images.unsplash.com/photo-1531297461136-82lw9b283993?auto=format&fit=crop&w=800&q=80", # Keyboard
    "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80", # Industry
    "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=800&q=80", # Construction
    "https://images.unsplash.com/photo-1590644365607-1c5a38d07399?auto=format&fit=crop&w=800&q=80", # Building
    "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=800&q=80", # Construction
    "https://images.unsplash.com/photo-1535732759880-bbd5c7265e3f?auto=format&fit=crop&w=800&q=80", # Worker
    "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80", # Blueprint
]

# --- IMAGE MANAGER (SIMPLE & ROBUST) ---
class ImageManager:
    def __init__(self):
        self.used_urls = set()
        
        # Kopiera listan och blanda den
        self.deck = list(STATIC_FALLBACK_IMAGES)
        random.shuffle(self.deck)

    def is_url_used(self, url):
        return url in self.used_urls

    def mark_as_used(self, url):
        self.used_urls.add(url)

    def get_random_fallback(self):
        """Hämtar en bild från kortleken och tar bort den."""
        if not self.deck:
            # Om leken är slut, återställ och blanda om (nödfall)
            self.deck = list(STATIC_FALLBACK_IMAGES)
            random.shuffle(self.deck)
        
        # Ta översta bilden
        img = self.deck.pop(0)
        self.used_urls.add(img)
        return img

image_manager = ImageManager()

# --- REAL IMAGE SCRAPER ---
def fetch_og_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                return og_image["content"]
    except Exception:
        pass
    return None

def get_best_image(entry, category, article_url, source_name):
    # --- HARD BLOCK: DO NOT TRUST THESE SOURCES ---
    BANNED_SOURCES = [
        "cleantechnica", 
        "oilprice", 
        "dagens ps", 
        "dagensps",
        "al jazeera", 
        "scmp", 
        "south china morning post"
    ]
    
    source_lower = source_name.lower()
    
    # 1. Om källan är svartlistad -> GÅ DIREKT TILL KORTLEKEN
    if any(banned in source_lower for banned in BANNED_SOURCES):
        return image_manager.get_random_fallback()

    # 2. Om källan är OK, försök hitta bild i RSS
    rss_img = None
    try:
        if 'media_content' in entry: rss_img = entry.media_content[0]['url']
        elif 'media_thumbnail' in entry: rss_img = entry.media_thumbnail[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.type.startswith('image/'): rss_img = link.href
    except: pass
    
    if rss_img:
        # Extra koll: innehåller URL:en namnet på en bannad källa?
        if any(banned in rss_img.lower() for banned in BANNED_SOURCES):
            rss_img = None
        else:
            bad_keywords = ["placeholder", "pixel", "tracker", "feedburner", "default", "icon"]
            if any(bad in rss_img.lower() for bad in bad_keywords):
                rss_img = None
            elif image_manager.is_url_used(rss_img):
                rss_img = None
    
    if rss_img:
        image_manager.mark_as_used(rss_img)
        return rss_img

    # 3. Scraper (Om RSS misslyckades men källan är OK)
    real_img = fetch_og_image(article_url)
    if real_img:
        if any(banned in real_img.lower() for banned in BANNED_SOURCES):
            real_img = None
        elif image_manager.is_url_used(real_img):
            real_img = None
            
    if real_img:
        image_manager.mark_as_used(real_img)
        return real_img

    # 4. Sista utväg för alla: Kortleken
    return image_manager.get_random_fallback()


def clean_youtube_description(text):
    if not text: return "Watch video for details."
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    summary = text.split('\n')[0]
    return summary[:220] + "..." if len(summary) > 220 else summary

def clean_summary(summary):
    if not summary: return ""
    try:
        soup = BeautifulSoup(summary, 'html.parser')
        text = soup.get_text()
        return text[:200] + "..." if len(text) > 200 else text
    except: return summary[:200]

def translate_text(text, source_lang='sv'):
    try:
        return GoogleTranslator(source=source_lang, target='en').translate(text)
    except:
        return text 

def fetch_youtube_videos(channel_url, category):
    ydl_opts = {'quiet': True, 'extract_flat': 'in_playlist', 'playlistend': 10, 'ignoreerrors': True}
    videos = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            if "@" in channel_url and not channel_url.endswith("/videos"): channel_url += "/videos"
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                source = info.get('uploader', 'YouTube')
                for entry in info['entries']:
                    vid_id = entry.get('id')
                    img = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    
                    upload_date = entry.get('upload_date')
                    if upload_date:
                        pub_ts = datetime.strptime(upload_date, "%Y%m%d").timestamp()
                    else:
                        pub_ts = time.time()
                    
                    if (time.time() - pub_ts) / 86400 > MAX_VIDEO_DAYS_OLD: continue
                    
                    image_manager.mark_as_used(img)

                    videos.append({
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={vid_id}",
                        "summary": clean_youtube_description(entry.get('description', '')),
                        "image": img,
                        "source": source,
                        "category": category,
                        "published": pub_ts,
                        "time_str": "Recent",
                        "is_video": True
                    })
    except Exception: pass
    return videos

def generate_site():
    print("Startar SPECULA Generator v10.8.0 (Operation Variation)...")
    all_articles = []
    seen_titles = set()

    for url, cat in YOUTUBE_CHANNELS:
        all_articles.extend(fetch_youtube_videos(url, cat))

    headers = {'User-Agent': 'Mozilla/5.0'}
    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            
            is_swedish = any(s in url for s in SWEDISH_SOURCES)

            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                title = entry.title
                if title in seen_titles: continue
                seen_titles.add(title)

                pub_ts = time.time()
                if 'published_parsed' in entry and entry.published_parsed:
                    pub_ts = time.mktime(entry.published_parsed)
                
                days_old = (time.time() - pub_ts) / 86400
                if days_old > MAX_DAYS_OLD: continue
                
                time_str = "Just Now" if days_old < 1 else f"{int(days_old)}d Ago"

                summary = clean_summary(entry.summary if 'summary' in entry else "")
                note_html = ""
                
                if is_swedish:
                    title = translate_text(title)
                    summary = translate_text(summary)
                    note_html = ' <span class="lang-note">(Translated)</span>'

                final_image = get_best_image(entry, category, entry.link, source_name)

                all_articles.append({
                    "title": title,
                    "link": entry.link,
                    "summary": summary + note_html,
                    "image": final_image,
                    "source": source_name,
                    "category": category,
                    "published": pub_ts,
                    "time_str": time_str,
                    "is_video": False
                })

        except Exception as e:
            print(f"Error {url}: {e}")

    all_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
    json_data = json.dumps(all_articles)

    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
        
        final_html = template.replace("<!-- NEWS_DATA_JSON -->", json_data)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(final_html)
        
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        with open("sitemap.xml", "w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}/index.html</loc><lastmod>{now}</lastmod></url></urlset>')
        
        robots_content = f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""
        with open("robots.txt", "w", encoding="utf-8") as f:
            f.write(robots_content)

        print("Klar! Allt genererat.")

if __name__ == "__main__":
    generate_site()