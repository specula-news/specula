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
from difflib import SequenceMatcher
import concurrent.futures

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# --- KONFIGURATION ---
MAX_ARTICLES_PER_SOURCE = 15
MAX_DAYS_OLD = 4
MAX_VIDEO_DAYS_OLD = 3
TIMEOUT_SECONDS = 5
JSON_FILE = "news.json"
MAX_WORKERS = 10 

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
    # GAMING
    ("https://feeds.feedburner.com/ign/news", "gaming"),
    ("https://www.gamespot.com/feeds/news/", "gaming"),
    ("https://www.polygon.com/rss/index.xml", "gaming"),
    ("https://kotaku.com/rss", "gaming"),
    ("https://www.eurogamer.net/?format=rss", "gaming"),
    ("https://www.pcgamer.com/rss/", "gaming"),
    ("https://www.vg247.com/feed", "gaming"),
    ("https://www.videogameschronicle.com/feed/", "gaming"),
    ("https://www.gematsu.com/feed", "gaming"),
    ("https://www.nintendolife.com/feeds/news", "gaming"),
    ("https://www.pushsquare.com/feeds/news", "gaming"),
    ("https://www.purexbox.com/feeds/news", "gaming"),
    ("https://gamingbolt.com/feed", "gaming"),
    ("https://www.theverge.com/games/rss/index.xml", "gaming"),

    # STANDARD
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

# --- SEMANTISK BILD-MOTOR ---
IMAGE_TOPICS = {
    "gaming": ["https://images.unsplash.com/photo-1552820728-8b83bb6b773f?w=800&q=80", "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&q=80", "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&q=80"],
    "general": ["https://images.unsplash.com/photo-1495020686667-45e86d4e6e0d?w=800&q=80", "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80"]
}

TOPIC_KEYWORDS = {
    "war": ["war", "military", "conflict", "ukraine", "russia"],
    "tech": ["ai", "chip", "nvidia", "apple", "google"],
    "gaming": ["game", "playstation", "xbox", "nintendo", "steam"]
}

def get_images_by_context(title, category):
    text = title.lower()
    # Endast en bild behövs nu
    
    if "gaming" in category.lower():
        pool = IMAGE_TOPICS.get("gaming", IMAGE_TOPICS["general"])
        return [random.choice(pool)]
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(k in text for k in keywords):
            pool = IMAGE_TOPICS.get(topic, IMAGE_TOPICS["general"])
            return [random.choice(pool)]
    
    general_pool = list(IMAGE_TOPICS["general"])
    return [random.choice(general_pool)]

def fetch_article_images(url, title, category):
    found_images = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img = og_image["content"]
                if not img.startswith(('http:', 'https:')): img = urljoin(url, img)
                found_images.append(img)
            
            # Om vi hittade en bild, sluta leta (vi behöver bara 1)
            if found_images: return found_images

            content_area = soup.find('article') or soup.find('main') or soup.body
            if content_area:
                imgs = content_area.find_all('img')
                for img_tag in imgs:
                    src = img_tag.get('src') or img_tag.get('data-src')
                    if src:
                        if not src.startswith(('http:', 'https:')): src = urljoin(url, src)
                        lower_src = src.lower()
                        bad = ['logo', 'icon', 'avatar', 'pixel', 'tracker', 'ad', 'svg', 'gif']
                        if any(b in lower_src for b in bad): continue
                        found_images.append(src)
                        break # Hittade en, bryt
    except Exception:
        pass

    if found_images:
        return found_images
        
    return get_images_by_context(title, category)

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

def fetch_youtube_videos(channel_url, category, existing_urls):
    ydl_opts = {'quiet': True, 'extract_flat': 'in_playlist', 'playlistend': 5, 'ignoreerrors': True}
    videos = []
    try:
        with YoutubeDL(ydl_opts) as ydl:
            if "@" in channel_url and not channel_url.endswith("/videos"): channel_url += "/videos"
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                source = info.get('uploader', 'YouTube')
                for entry in info['entries']:
                    vid_id = entry.get('id')
                    link = f"https://www.youtube.com/watch?v={vid_id}"
                    
                    if link in existing_urls: continue
                        
                    img = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                    upload_date = entry.get('upload_date')
                    pub_ts = time.time()
                    if upload_date:
                        pub_ts = datetime.strptime(upload_date, "%Y%m%d").timestamp()
                    if (time.time() - pub_ts) / 86400 > MAX_VIDEO_DAYS_OLD: continue
                    
                    # Endast 1 bild i listan
                    img_list = [img] 
                    videos.append({
                        "title": entry.get('title'),
                        "link": link,
                        "summary": clean_youtube_description(entry.get('description', '')),
                        "images": img_list,
                        "source": source,
                        "category": category,
                        "published": pub_ts,
                        "time_str": "Recent",
                        "is_video": True
                    })
    except Exception: pass
    return videos

# --- ARBETARE FÖR TRÅDNING ---
def process_rss_entry(args):
    entry, category, source_name, is_swedish = args
    try:
        pub_ts = time.time()
        if 'published_parsed' in entry and entry.published_parsed:
            pub_ts = time.mktime(entry.published_parsed)
        
        if (time.time() - pub_ts) / 86400 > MAX_DAYS_OLD:
            return None
        
        time_str = "Just Now" if (time.time() - pub_ts) < 86400 else f"{int((time.time()-pub_ts)/86400)}d Ago"
        summary = clean_summary(entry.summary if 'summary' in entry else "")
        note_html = ' <span class="lang-note">(Translated)</span>' if is_swedish else ""
        
        title = entry.title
        if is_swedish:
            title = translate_text(title)
            summary = translate_text(summary)

        # Hämta 1 bild
        images = fetch_article_images(entry.link, title, category)

        return {
            "title": title,
            "link": entry.link,
            "summary": summary + note_html,
            "images": images,
            "source": source_name,
            "category": category,
            "published": pub_ts,
            "time_str": time_str,
            "is_video": False
        }
    except Exception as e:
        print(f"Skipping article due to error: {e}")
        return None

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def generate_site():
    print("Startar SPECULA Generator v19.1 (Clean & Fast)...")
    
    existing_articles = []
    existing_urls = set()
    
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
                current_time = time.time()
                existing_articles = [
                    a for a in existing_articles 
                    if (current_time - a.get('published', 0)) / 86400 <= MAX_DAYS_OLD
                ]
                for a in existing_articles:
                    existing_urls.add(a['link'])
            print(f"Laddade {len(existing_articles)} befintliga artiklar.")
        except Exception: pass

    new_articles = []

    print("Hämtar YouTube...")
    for url, cat in YOUTUBE_CHANNELS:
        new_articles.extend(fetch_youtube_videos(url, cat, existing_urls))

    print("Hämtar RSS-flöden...")
    rss_tasks = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            is_swedish = any(s in url for s in SWEDISH_SOURCES)

            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                if entry.link in existing_urls: continue

                title = entry.title
                is_duplicate_title = False
                for existing in existing_articles:
                    if similar(title.lower(), existing['title'].lower()) > 0.85:
                        is_duplicate_title = True
                        break
                if is_duplicate_title: continue

                rss_tasks.append((entry, category, source_name, is_swedish))
                existing_urls.add(entry.link)
        except Exception as e:
            print(f"Feed error {url}: {e}")

    print(f"Bearbetar {len(rss_tasks)} nya artiklar...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(process_rss_entry, rss_tasks))
    
    for res in results:
        if res:
            new_articles.append(res)

    all_content = new_articles + existing_articles
    all_content.sort(key=lambda x: x.get('published', 0), reverse=True)
    
    print(f"Hittade {len(new_articles)} nya. Totalt: {len(all_content)}")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_content, f, ensure_ascii=False)

    print("Klar! news.json uppdaterad.")

if __name__ == "__main__":
    generate_site()
    sys.exit()