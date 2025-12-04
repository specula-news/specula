import feedparser
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import math
import random
import json
import sys
import os
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

SITE_URL = "https://specula-news.netlify.app"

# --- YOUTUBE KANALER ---
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

# --- TEXT NYHETER ---
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

# --- MASSIVE FALLBACK LIBRARY ---
SMART_IMAGES = {
    # GEOPOLITICS & BUSINESS
    "china": ["https://images.unsplash.com/photo-1543832923-44667a77d853?q=80&w=1000", "https://images.unsplash.com/photo-1547981609-4b6bfe6770b7?q=80&w=1000"],
    "asia": ["https://images.unsplash.com/photo-1535139262971-c51845709a48?q=80&w=1000"],
    "war": ["https://images.unsplash.com/photo-1597841028788-b24d772c72b2?q=80&w=1000", "https://images.unsplash.com/photo-1555881400-74d7acaacd81?q=80&w=1000", "https://images.unsplash.com/photo-1618336753974-aae8e04506aa?q=80&w=1000"],
    "conflict": ["https://images.unsplash.com/photo-1555881400-74d7acaacd81?q=80&w=1000"],
    "strike": ["https://images.unsplash.com/photo-1597841028788-b24d772c72b2?q=80&w=1000"],
    "business": ["https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1000", "https://images.unsplash.com/photo-1507679799987-c73779587ccf?q=80&w=1000", "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=1000"],
    "economy": ["https://images.unsplash.com/photo-1611974765270-ca1258634369?q=80&w=1000"],
    
    # CLIMATE & NATURE (Not Tech!)
    "climate": ["https://images.unsplash.com/photo-1466611653911-95081537e5b7?q=80&w=1000", "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=1000", "https://images.unsplash.com/photo-1501854140884-074cf272492b?q=80&w=1000"],
    "co2": ["https://images.unsplash.com/photo-1611273426761-53c8577a3dc7?q=80&w=1000"],
    "emission": ["https://images.unsplash.com/photo-1611273426761-53c8577a3dc7?q=80&w=1000"],
    "nature": ["https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1000"],

    # TECH & EV
    "ev": ["https://images.unsplash.com/photo-1593941707882-a5bba14938c7?q=80&w=1000", "https://images.unsplash.com/photo-1550505393-273a55239e24?q=80&w=1000", "https://images.unsplash.com/photo-1565373676955-349f71c4acbe?q=80&w=1000"],
    "tech": ["https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000", "https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1000"],
    "amazon": ["https://images.unsplash.com/photo-1523474253046-8cd2748b5fd2?q=80&w=1000", "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=1000"],
    
    # OIL & INDUSTRY
    "oil": ["https://images.unsplash.com/photo-1516937941348-c09645f31e88?q=80&w=1000", "https://images.unsplash.com/photo-1628522333060-637998ca4448?q=80&w=1000"],
    "gas": ["https://images.unsplash.com/photo-1628522333060-637998ca4448?q=80&w=1000"],
    
    # CONSTRUCTION
    "construction": ["https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=1000", "https://images.unsplash.com/photo-1503387762-592deb58ef4e?q=80&w=1000", "https://images.unsplash.com/photo-1581094794329-c8112a89af12?q=80&w=1000"],
    "building": ["https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1000"]
}

# --- 30 UNIKA GENERISKA BILDER (För att undvika upprepning) ---
GENERIC_FALLBACKS = [
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000",
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1000",
    "https://images.unsplash.com/photo-1535139262971-c51845709a48?q=80&w=1000",
    "https://images.unsplash.com/photo-1480506132288-68f7705954bd?q=80&w=1000",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1000",
    "https://images.unsplash.com/photo-1501854140884-074cf272492b?q=80&w=1000",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1000",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=1000",
    "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?q=80&w=1000",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=1000",
    "https://images.unsplash.com/photo-1497215728101-856f4ea42174?q=80&w=1000",
    "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?q=80&w=1000",
    "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=1000",
    "https://images.unsplash.com/photo-1555066931-4365d14bab8c?q=80&w=1000",
    "https://images.unsplash.com/photo-1531482615713-2afd69097998?q=80&w=1000",
    "https://images.unsplash.com/photo-1523961131990-5ea7c61b2107?q=80&w=1000",
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1000",
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?q=80&w=1000"
]

used_image_urls = []

def get_image_from_entry(entry):
    try:
        if 'yt_videoid' in entry:
            return f"https://img.youtube.com/vi/{entry.yt_videoid}/maxresdefault.jpg"
        if 'media_content' in entry: return entry.media_content[0]['url']
        if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
        if 'links' in entry:
            for link in entry.links:
                if link.type.startswith('image/'): return link.href
        content = entry.content[0].value if 'content' in entry else (entry.summary if 'summary' in entry else "")
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            images = soup.find_all('img')
            for img in images:
                src = img.get('src')
                if not src: continue
                if 'pixel' in src or 'tracker' in src or 'feedburner' in src: continue
                return src
    except: pass
    return ""

def get_smart_fallback(title, category, source):
    text = title.lower() + " " + category.lower()
    if "oilprice" in source.lower(): text += " oil gas money market energy" 
    
    potential_list = []
    
    for key, urls in SMART_IMAGES.items():
        if key in text:
            potential_list.extend(urls)
            
    if not potential_list:
        potential_list = GENERIC_FALLBACKS

    # GLOBAL ROTATION LOGIC
    # Try to find an unused image in the chosen list
    for img in potential_list:
        if img not in used_image_urls:
            used_image_urls.append(img)
            return img

    # If all used, just pick random
    return random.choice(potential_list)

def clean_summary(summary):
    if not summary: return ""
    try:
        soup = BeautifulSoup(summary, 'html.parser')
        text = soup.get_text()
        text = text.replace("Continue reading", "").replace("Read more", "").replace("Läs mer", "")
        return text[:200] + "..." if len(text) > 200 else text
    except: return summary[:200]

def translate_text(text, source_lang='sv'):
    try:
        return GoogleTranslator(source=source_lang, target='en').translate(text)
    except:
        return text 

def fetch_youtube_videos(channel_url, category):
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'playlistend': 10,
        'ignoreerrors': True
    }
    videos = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            if "@" in channel_url and not channel_url.endswith("/videos"):
                channel_url += "/videos"
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                source_title = info.get('uploader', 'YouTube Channel')
                for entry in info['entries']:
                    title = entry.get('title')
                    url = entry.get('url')
                    if "youtube.com" not in url and "youtu.be" not in url: url = f"https://www.youtube.com/watch?v={url}"
                    video_id = entry.get('id')
                    img = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    
                    upload_date = entry.get('upload_date')
                    if upload_date:
                        dt = datetime.strptime(upload_date, "%Y%m%d")
                        pub_ts = dt.timestamp()
                    else:
                        pub_ts = time.time()

                    now = time.time()
                    days_ago = (now - pub_ts) / 86400
                    
                    if days_ago > MAX_VIDEO_DAYS_OLD: continue
                    if days_ago < 1: time_str = "Just Now"
                    else: time_str = f"{int(days_ago)}d Ago"
                    
                    videos.append({
                        "title": title,
                        "link": url,
                        "summary": f"Latest update from {source_title}.",
                        "image": img,
                        "source": source_title,
                        "category": category,
                        "published": pub_ts,
                        "time_str": time_str,
                        "is_video": True,
                        "yt_id": video_id
                    })
                    print(f"Fetched YT: {title}")
    except Exception as e:
        print(f"Failed to fetch YT {channel_url}: {e}")
    return videos

def generate_sitemap():
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <url>
      <loc>{SITE_URL}/index.html</loc>
      <lastmod>{now}</lastmod>
      <changefreq>hourly</changefreq>
      <priority>1.0</priority>
   </url>
</urlset>
"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_content)

def generate_json_data():
    print("Fetching news...")
    all_articles = []
    seen_titles = set()

    # 1. YOUTUBE
    print("Starting YouTube Fetch...")
    for url, category in YOUTUBE_CHANNELS:
        videos = fetch_youtube_videos(url, category)
        for v in videos:
            if v['title'] not in seen_titles:
                all_articles.append(v)
                seen_titles.add(v['title'])

    # 2. RSS
    print("Starting RSS Fetch...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            try: print(f"Loaded {len(feed.entries)} from {source_name}")
            except: pass
            
            is_swedish = any(s in url for s in SWEDISH_SOURCES)
            
            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                try:
                    title = entry.title
                    if title in seen_titles: continue
                    seen_titles.add(title)

                    pub_ts = time.time()
                    if 'published_parsed' in entry and entry.published_parsed:
                        pub_ts = time.mktime(entry.published_parsed)
                    
                    now = time.time()
                    days_ago = (now - pub_ts) / 86400
                    if days_ago > MAX_DAYS_OLD: continue

                    if days_ago < 1: time_str = "Just Now"
                    else: time_str = f"{int(days_ago)}d Ago"

                    summary = clean_summary(entry.summary if 'summary' in entry else "")
                    note_html = ""

                    if is_swedish:
                        try:
                            title = translate_text(title)
                            summary = translate_text(summary)
                            note_html = ' <span class="lang-note">(Translated)</span>'
                        except: pass

                    found_image = get_image_from_entry(entry)
                    final_image = found_image if found_image else get_smart_fallback(title, category, source_name)

                    article = {
                        "title": title,
                        "link": entry.link,
                        "summary": summary + note_html,
                        "image": final_image,
                        "source": source_name,
                        "category": category,
                        "published": pub_ts,
                        "time_str": time_str,
                        "is_video": False,
                        "yt_id": None
                    }
                    all_articles.append(article)
                except Exception: continue

        except Exception as e:
            print(f"Error loading RSS {url}: {e}")

    try: all_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
    except: pass
    
    json_data = json.dumps(all_articles)

    if not os.path.exists("template.html"): return

    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("<!-- NEWS_DATA_JSON -->", json_data)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    generate_sitemap()
    print("Success! index.html generated.")

if __name__ == "__main__":
    generate_json_data()