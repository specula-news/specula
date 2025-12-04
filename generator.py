import feedparser
import time
from datetime import datetime
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

SMART_IMAGES = {
    "china": ["https://images.unsplash.com/photo-1543832923-44667a77d853?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1547981609-4b6bfe6770b7?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1504966981333-60a880373d32?q=80&w=1000&auto=format&fit=crop"],
    "asia": ["https://images.unsplash.com/photo-1535139262971-c51845709a48?q=80&w=1000&auto=format&fit=crop"],
    "ev": ["https://images.unsplash.com/photo-1593941707882-a5bba14938c7?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1550505393-273a55239e24?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1565373676955-349f71c4acbe?q=80&w=1000&auto=format&fit=crop"],
    "oil": ["https://images.unsplash.com/photo-1516937941348-c09645f31e88?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1628522333060-637998ca4448?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1518709414768-a88986a45ca5?q=80&w=1000&auto=format&fit=crop"],
    "gas": ["https://images.unsplash.com/photo-1628522333060-637998ca4448?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1579766927552-308b4974457e?q=80&w=1000&auto=format&fit=crop"],
    "money": ["https://images.unsplash.com/photo-1611974765270-ca1258634369?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=1000&auto=format&fit=crop"],
    "space": ["https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1614728853970-36279f57520b?q=80&w=1000&auto=format&fit=crop"],
    "tech": ["https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1000&auto=format&fit=crop"],
    "construction": ["https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1503387762-592deb58ef4e?q=80&w=1000&auto=format&fit=crop"]
}
GENERIC_FALLBACKS = [
    "https://images.unsplash.com/photo-1531297461136-82lw9b283993?q=80&w=1000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"
]

used_image_urls = []

def get_image_from_entry(entry):
    try:
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
    for key, urls in SMART_IMAGES.items():
        if key in text:
            for _ in range(5):
                img = random.choice(urls)
                if img not in used_image_urls:
                    used_image_urls.append(img)
                    return img
            return random.choice(urls)
    for _ in range(5):
        img = random.choice(GENERIC_FALLBACKS)
        if img not in used_image_urls:
            used_image_urls.append(img)
            return img
    return random.choice(GENERIC_FALLBACKS)

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
                    
                    # 1. Hämta MaxResDefault först
                    img = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    
                    upload_date = entry.get('upload_date')
                    if upload_date:
                        dt = datetime.strptime(upload_date, "%Y%m%d")
                        pub_ts = dt.timestamp()
                    else:
                        pub_ts = time.time()

                    now = time.time()
                    days_ago = (now - pub_ts) / 86400
                    if days_ago > MAX_DAYS_OLD: continue

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
                        "yt_id": video_id  # NYTT: Skicka med ID så frontend kan fixa bilden
                    })
                    print(f"Fetched YT: {title}")
    except Exception as e:
        print(f"Failed to fetch YT {channel_url}: {e}")
    return videos

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
    
    print("Success! index.html generated.")

if __name__ == "__main__":
    generate_json_data()