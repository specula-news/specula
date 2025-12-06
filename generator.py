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
import hashlib
from urllib.parse import urljoin
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

# --- SEMANTISK BILD-MOTOR (Expanded Library) ---
IMAGE_TOPICS = {
    "crisis": [
        "https://images.unsplash.com/photo-1469571486292-0ba58a3f068b?w=800&q=80",
        "https://images.unsplash.com/photo-1541696280456-4299b9f7c02c?w=800&q=80",
        "https://images.unsplash.com/photo-1533519396340-a3cb306a4b36?w=800&q=80",
        "https://images.unsplash.com/photo-1596464522904-9430db72744c?w=800&q=80"
    ],
    "war": [
        "https://images.unsplash.com/photo-1595225476474-87563907a212?w=800&q=80",
        "https://images.unsplash.com/photo-1550614000-4b9519e09eb3?w=800&q=80",
        "https://images.unsplash.com/photo-1618609204739-9993309a4563?w=800&q=80"
    ],
    "police": [
        "https://images.unsplash.com/photo-1595150824222-6b9623e80069?w=800&q=80",
        "https://images.unsplash.com/photo-1455273397940-2777dfb20c93?w=800&q=80",
        "https://images.unsplash.com/photo-1587329107937-234b3e390c21?w=800&q=80"
    ],
    "china": [
        "https://images.unsplash.com/photo-1547981609-4b6bfe6770b7?w=800&q=80",
        "https://images.unsplash.com/photo-1504966981333-60a880373d32?w=800&q=80",
        "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?w=800&q=80",
        "https://images.unsplash.com/photo-1535139262971-c51845709a48?w=800&q=80"
    ],
    "usa": [
        "https://images.unsplash.com/photo-1501229691287-95713437517c?w=800&q=80",
        "https://images.unsplash.com/photo-1550505393-273a55239e24?w=800&q=80",
        "https://images.unsplash.com/photo-1485738422979-f5c462d49f74?w=800&q=80"
    ],
    "market": [
        "https://images.unsplash.com/photo-1611974765270-ca1258634369?w=800&q=80",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&q=80",
        "https://images.unsplash.com/photo-1565514020176-dbf2277f4942?w=800&q=80"
    ],
    "chips": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80",
        "https://images.unsplash.com/photo-1591696205602-2f950c417cb9?w=800&q=80",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80"
    ],
    "oil": [
        "https://images.unsplash.com/photo-1516937941348-c09645f31e88?w=800&q=80",
        "https://images.unsplash.com/photo-1628522333060-637998ca4448?w=800&q=80",
        "https://images.unsplash.com/photo-1582555618296-5427d25365b6?w=800&q=80"
    ],
    "solar": [
        "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800&q=80",
        "https://images.unsplash.com/photo-1508514177221-188b1cf16e9d?w=800&q=80",
        "https://images.unsplash.com/photo-1566093097221-8563d80d2d31?w=800&q=80"
    ],
    "space": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=800&q=80",
        "https://images.unsplash.com/photo-1614728853970-36279f57520b?w=800&q=80"
    ],
    # Backup-pools
    "general": [
        "https://images.unsplash.com/photo-1495020686667-45e86d4e6e0d?w=800&q=80",
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80",
        "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=800&q=80",
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80"
    ]
}

# ORDBOK: Kopplar ord i titeln till bildkategorier
TOPIC_KEYWORDS = {
    "crisis": ["struggle", "refugee", "crisis", "aid", "humanitarian", "disaster", "famine", "camp", "dead"],
    "war": ["war", "attack", "strike", "missile", "army", "military", "defense", "conflict", "bomb", "blast"],
    "police": ["police", "arrest", "crime", "jail", "court", "law", "prison", "investigation", "suspect"],
    "china": ["china", "chinese", "beijing", "shanghai", "hong kong", "asia", "taiwan"],
    "usa": ["usa", "us", "america", "trump", "biden", "white house", "congress", "senate"],
    "market": ["market", "stock", "trade", "economy", "dollar", "bank", "inflation", "price", "share"],
    "chips": ["chip", "semiconductor", "nvidia", "intel", "processor", "compute", "ai", "hardware"],
    "oil": ["oil", "gas", "petroleum", "fuel", "pipeline", "barrel", "energy"],
    "solar": ["solar", "wind", "renewable", "climate", "green", "battery", "grid"],
    "space": ["space", "nasa", "moon", "mars", "rocket", "orbit", "satellite", "star"]
}

def get_images_by_context(title, category):
    text = title.lower()
    selected_images = []
    
    # 1. Hitta nyckelord i titeln
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(k in text for k in keywords):
            pool = IMAGE_TOPICS.get(topic, IMAGE_TOPICS["general"])
            shuffled = list(pool)
            random.shuffle(shuffled)
            selected_images.extend(shuffled[:3])
            break
            
    # 2. Om ingen match, fyll på från General
    if len(selected_images) < 3:
        general_pool = list(IMAGE_TOPICS["general"])
        random.shuffle(general_pool)
        
        while len(selected_images) < 3 and general_pool:
            img = general_pool.pop()
            if img not in selected_images:
                selected_images.append(img)
                
    # 3. Nödfall: Dubblera om slut på unika bilder
    while len(selected_images) < 3:
        selected_images.append(selected_images[0])
        
    return selected_images[:3]

def fetch_og_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                if img_url and not img_url.startswith(('http:', 'https:')):
                    img_url = urljoin(url, img_url)
                return img_url
    except Exception:
        pass
    return None

def get_article_images(entry, category, article_url, source_name):
    BANNED_SOURCES = ["cleantechnica", "oilprice", "dagens ps", "dagensps", "al jazeera", "scmp", "south china morning post"]
    source_lower = source_name.lower()
    
    # Förbjudna källor -> Direkt till semantisk bild
    context_images = get_images_by_context(entry.title, category)
    if any(banned in source_lower for banned in BANNED_SOURCES):
        return context_images 

    # Andra källor -> Försök hitta riktig bild
    real_img = None
    try:
        if 'media_content' in entry: real_img = entry.media_content[0]['url']
        elif 'media_thumbnail' in entry: real_img = entry.media_thumbnail[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.type.startswith('image/'): real_img = link.href
    except: pass
    
    if not real_img:
        real_img = fetch_og_image(article_url)
        
    if real_img:
        bad = ["placeholder", "pixel", "tracker", "icon"]
        if not any(b in real_img.lower() for b in bad):
            return [real_img] + context_images[:2]
            
    return context_images

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
                    pub_ts = time.time()
                    if upload_date:
                        pub_ts = datetime.strptime(upload_date, "%Y%m%d").timestamp()
                    if (time.time() - pub_ts) / 86400 > MAX_VIDEO_DAYS_OLD: continue
                    
                    videos.append({
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={vid_id}",
                        "summary": clean_youtube_description(entry.get('description', '')),
                        "images": [img, img, img],
                        "source": source,
                        "category": category,
                        "published": pub_ts,
                        "time_str": "Recent",
                        "is_video": True
                    })
    except Exception: pass
    return videos

def generate_site():
    print("Startar SPECULA Generator v13.1.0...")
    all_articles = []
    for url, cat in YOUTUBE_CHANNELS:
        all_articles.extend(fetch_youtube_videos(url, cat))

    headers = {'User-Agent': 'Mozilla/5.0'}
    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            is_swedish = any(s in url for s in SWEDISH_SOURCES)

            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                if any(a['title'] == entry.title for a in all_articles): continue
                pub_ts = time.time()
                if 'published_parsed' in entry and entry.published_parsed:
                    pub_ts = time.mktime(entry.published_parsed)
                if (time.time() - pub_ts) / 86400 > MAX_DAYS_OLD: continue
                time_str = "Just Now" if (time.time() - pub_ts) < 86400 else f"{int((time.time()-pub_ts)/86400)}d Ago"
                summary = clean_summary(entry.summary if 'summary' in entry else "")
                note_html = ' <span class="lang-note">(Translated)</span>' if is_swedish else ""
                
                if is_swedish:
                    title = translate_text(entry.title)
                    summary = translate_text(summary)
                else:
                    title = entry.title

                images = get_article_images(entry, category, entry.link, source_name)

                all_articles.append({
                    "title": title,
                    "link": entry.link,
                    "summary": summary + note_html,
                    "images": images,
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

    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(template.replace("<!-- NEWS_DATA_JSON -->", json_data))
    
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    with open("sitemap.xml", "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}/index.html</loc><lastmod>{now}</lastmod></url></urlset>')
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    print("Klar!")

if __name__ == "__main__":
    generate_site()