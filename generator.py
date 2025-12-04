import feedparser
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import random
import json
import sys
import os
import re
import requests  # NYTT BIBLIOTEK KRÄVS
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
TIMEOUT_SECONDS = 3  # Max tid vi väntar på att en sida ska ladda bild

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

# --- IMAGE MANAGER (LAST RESORT FALLBACK) ---
class ImageManager:
    def __init__(self):
        self.used_ids = set()
        # Fallback IDs if real scraping fails
        self.id_pools = {
            "tech": ["1518770660439-4636190af475", "1550751827-4bd374c3f58b", "1519389950473-47ba0277781c", "1504639725590-34d0984388bd"],
            "ev": ["1593941707882-a5bba14938c7", "1617788138017-80ad40651399", "1565373676955-349f71c4acbe", "1550505393-273a55239e24"],
            "geopolitics": ["1529101091760-6149d3c879d4", "1532375810709-75b1da00537c", "1543832923-44667a77d853", "1464817739973-0128fe77aaa1"],
            "science": ["1446776811953-b23d57bd21aa", "1614728853970-36279f57520b", "1541185933-710f50746747", "1517976487492-5750f3195933"],
            "construction": ["1541888946425-d81bb19240f5", "1503387762-592deb58ef4e", "1581094794329-c8112a89af12", "1535732759880-bbd5c7265e3f"]
        }
        self.generic_ids = ["1550684848-fac1c5b4e853", "1618005182384-a83a8bd57fbe", "1614850523060-8da1d56ae167", "1634152962476-4b8a00e1915c"]

    def get_image(self, category):
        target_list = self.id_pools.get(category, self.generic_ids)
        available = [pid for pid in target_list if pid not in self.used_ids]
        if not available:
            # Cross-pool fallback
            all_ids = []
            for pool in self.id_pools.values(): all_ids.extend(pool)
            available = [pid for pid in all_ids if pid not in self.used_ids]
        
        if not available: available = target_list # Reset if totally full

        selected_id = random.choice(available)
        self.used_ids.add(selected_id)
        return f"https://images.unsplash.com/photo-{selected_id}?auto=format&fit=crop&w=800&q=80"

image_manager = ImageManager()

# --- REAL IMAGE SCRAPER (The "Magic" Part) ---
def fetch_og_image(url):
    """
    Besöker artikeln och hämtar 'og:image' metataggen.
    Detta ger den exakta bilden som nyhetssajten själv använder.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Leta efter og:image
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                # Filtrera bort små ikoner eller loggor
                if "logo" in img_url.lower() or "icon" in img_url.lower():
                    return None
                return img_url
    except Exception:
        pass # Om det tar för lång tid eller failar, gå vidare tyst
    return None

def get_best_image(entry, category, article_url):
    # 1. Kolla RSS först (Men var skeptisk)
    rss_img = None
    try:
        if 'media_content' in entry: rss_img = entry.media_content[0]['url']
        elif 'media_thumbnail' in entry: rss_img = entry.media_thumbnail[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.type.startswith('image/'): rss_img = link.href
    except: pass
    
    # 2. SVARTLISTA KÄNDA DÅLIGA BILDER
    # Om RSS ger oss en bild, kolla om det är en känd "placeholder"
    if rss_img:
        bad_keywords = ["placeholder", "pixel", "tracker", "feedburner", "default"]
        if any(bad in rss_img.lower() for bad in bad_keywords):
            rss_img = None
    
    # Om vi hittade en bra RSS-bild, använd den (snabbast)
    if rss_img:
        return rss_img

    # 3. "REAL DEAL": Scrapa artikeln efter rätt bild
    print(f"   > Scraping real image for: {article_url[:30]}...")
    real_img = fetch_og_image(article_url)
    if real_img:
        return real_img

    # 4. SISTA UTVÄG: Fallback från ImageManager
    return image_manager.get_image(category)


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
                    
                    # Datumkoll
                    upload_date = entry.get('upload_date')
                    if upload_date:
                        pub_ts = datetime.strptime(upload_date, "%Y%m%d").timestamp()
                    else:
                        pub_ts = time.time()
                    
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
    print("Startar SPECULA Generator v10.0.0 (The Scraper)...")
    all_articles = []
    seen_titles = set()

    # YOUTUBE
    for url, cat in YOUTUBE_CHANNELS:
        all_articles.extend(fetch_youtube_videos(url, cat))

    # RSS
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url, agent=headers['User-Agent'])
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            print(f"RSS: {source_name}")
            
            is_swedish = any(s in url for s in SWEDISH_SOURCES)

            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                title = entry.title
                if title in seen_titles: continue
                seen_titles.add(title)

                # Datumkoll
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

                # --- HÄR ANROPAS NYA BILDLOGIKEN ---
                final_image = get_best_image(entry, category, entry.link)

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

    # Sortera & Generera
    all_articles.sort(key=lambda x: x.get('published', 0), reverse=True)
    json_data = json.dumps(all_articles)

    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
        
        final_html = template.replace("<!-- NEWS_DATA_JSON -->", json_data)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(final_html)
        
        # Sitemap
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        with open("sitemap.xml", "w") as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}/index.html</loc><lastmod>{now}</lastmod></url></urlset>')
            
        print("Klar! index.html genererad.")

if __name__ == "__main__":
    generate_site()