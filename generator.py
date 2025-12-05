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
from urllib.parse import urljoin  # NYCKELN FÖR ATT FIXA TRASIGA LÄNKAR
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

# --- SÄKRA BILDER (RESERV) ---
STATIC_POOL = [
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
    "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1444723121867-bddbc7113f43?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1526304640152-d29241528c7d?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1530210124550-912dc1381cb8?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1504384308090-c54be3855833?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1566093097221-8563d80d2d31?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1620882352329-a41764645229?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1543286386-2e659306cd6c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1521791136064-7986608178d4?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1579532537598-459ecdaf39cc?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1611974765270-ca1258634369?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1529400971008-f566de0e6dfc?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1535320903710-d9cf11df87b6?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1531297461136-82lw9b283993?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1590644365607-1c5a38d07399?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1535732759880-bbd5c7265e3f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80",
]

# --- IMAGE LOGIC (FIX BROKEN LINKS) ---
def get_deterministic_image(title):
    if not title: return STATIC_POOL[0]
    hash_object = hashlib.md5(title.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    index = hash_int % len(STATIC_POOL)
    return STATIC_POOL[index]

def fetch_og_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                
                # *** HÄR ÄR FIXEN FÖR "BROKEN LINKS" ***
                # Om länken är relativ (t.ex. "/uploads/img.jpg") lägger vi till domänen före.
                if img_url and not img_url.startswith(('http:', 'https:')):
                    img_url = urljoin(url, img_url)
                    
                return img_url
    except Exception:
        pass
    return None

def get_best_image(entry, category, article_url, source_name):
    # KÄLLOR VI ALDRIG LITAR PÅ
    BANNED_SOURCES = [
        "cleantechnica", "oilprice", "dagens ps", "dagensps",
        "al jazeera", "scmp", "south china morning post"
    ]
    
    source_lower = source_name.lower()
    
    # 1. HÅRD BLOCKERING -> VÄLJ MATEMATISK BILD
    if any(banned in source_lower for banned in BANNED_SOURCES):
        return get_deterministic_image(entry.title)

    # 2. FÖRSÖK MED RSS
    rss_img = None
    try:
        if 'media_content' in entry: rss_img = entry.media_content[0]['url']
        elif 'media_thumbnail' in entry: rss_img = entry.media_thumbnail[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.type.startswith('image/'): rss_img = link.href
    except: pass
    
    if rss_img:
        # Extra koll så inte RSS-bilden är "relativ" (börjar med /)
        if not rss_img.startswith(('http:', 'https:')):
             # Försök gissa domän från artikelns länk, annars kasta
             rss_img = urljoin(article_url, rss_img)

        bad_keywords = ["placeholder", "pixel", "tracker", "feedburner", "default", "icon"]
        if any(bad in rss_img.lower() for bad in bad_keywords):
            rss_img = None
    
    if rss_img:
        return rss_img

    # 3. SCRAPING
    real_img = fetch_og_image(article_url)
    
    if real_img:
        # Om den skrapade bilden är från en bannad domän
        if any(banned in real_img.lower() for banned in BANNED_SOURCES):
            return get_deterministic_image(entry.title)
        return real_img

    # 4. SISTA UTVÄG
    return get_deterministic_image(entry.title)


# --- HELPERS ---
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
    print("Startar SPECULA Generator v12.1.0...")
    all_articles = []
    
    # 1. YouTube
    for url, cat in YOUTUBE_CHANNELS:
        all_articles.extend(fetch_youtube_videos(url, cat))

    # 2. RSS
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            is_swedish = any(s in url for s in SWEDISH_SOURCES)

            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                # Enkel titel-deduplication
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

                # Hämta bild
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

    # Sortera och spara
    all_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
    json_data = json.dumps(all_articles)

    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(template.replace("<!-- NEWS_DATA_JSON -->", json_data))
    
    # SEO Filer
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    with open("sitemap.xml", "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}/index.html</loc><lastmod>{now}</lastmod></url></urlset>')
    
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    print("Klar!")

if __name__ == "__main__":
    generate_site()