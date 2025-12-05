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

# --- IMAGE MANAGER (NORMALIZED TRACKING) ---
class ImageManager:
    def __init__(self):
        self.global_used_urls = set()
        
        self.id_pools = {
            "tech": [
                "1518770660439-4636190af475", "1550751827-4bd374c3f58b", "1519389950473-47ba0277781c", "1504639725590-34d0984388bd",
                "1526374965328-7f61d4dc18c5", "1550009158-9ebf69056955", "1535378437268-13d143445347", "1531297461136-82lw9b283993",
                "1485827404703-89b55fcc595e", "1523961131990-5ea7c61b2107", "1558494949-efc52728101c", "1610563166150-b34df4f3bcd6",
                "1510915361405-ef8a93d77d29", "1563770095-39d468f421e2", "1525547719571-a2d4ac8945e2", "1592478411213-61535fdd861d",
                "1515378791036-0648a3ef77b2", "1555255707-c07966088b7b", "1517694712202-14dd9538aa97", "1531482615713-2afd69097998"
            ],
            "ev": [
                "1593941707882-a5bba14938c7", "1617788138017-80ad40651399", "1565373676955-349f71c4acbe", "1550505393-273a55239e24",
                "1620882352329-a41764645229", "1558628818-40db7871d007", "1594535182308-8ff248971649", "1605733513597-a8f8341084e6",
                "1494976388531-d1058494cdd8", "1558449028-b53a39d100fc", "1532935298550-6e02e8906652", "1456356627738-3a96db6d54cb",
                "1497435334941-8c899ee9e8e9", "1521618755572-156ae0cdd74d", "1487887235947-a955ef187fcc", "1513258496098-882717dbf58c"
            ],
            "geopolitics": [
                "1529101091760-6149d3c879d4", "1532375810709-75b1da00537c", "1543832923-44667a77d853", "1547981609-4b6bfe6770b7",
                "1464817739973-0128fe77aaa1", "1590283603385-17ffb3a7f29f", "1612178991541-b48cc8e92a4d", "1520699697851-3dc68aa3a474",
                "1474376962954-d8a681cc53b2", "1496442226666-8d4a0e62e6e9", "1524601500432-1e1a4c71d692", "1537254326439-0e78a8257938",
                "1516023353357-357c6032d288", "1555848962-6e79363ec58f", "1575320181282-9afab399332c", "1477039181047-94e702db8436"
            ],
            "science": [
                "1446776811953-b23d57bd21aa", "1614728853970-36279f57520b", "1541185933-710f50746747", "1517976487492-5750f3195933",
                "1457369804613-52c61a468e7d", "1533475418392-41543084b4f7", "1507413245164-6160d8298b31", "1532094349884-543bc11b234d",
                "1532187863486-abf9dbad1b69", "1451187580459-43490279c0fa", "1484589065579-248aad0d8b13", "1462331940025-496dfbfc7564",
                "1506318137071-a8bcbf67cc77", "1516339901601-2e1b62dc0c45", "1576086213369-97a306d36557", "1507668077129-56e32842fceb"
            ],
            "construction": [
                "1541888946425-d81bb19240f5", "1503387762-592deb58ef4e", "1581094794329-c8112a89af12", "1535732759880-bbd5c7265e3f",
                "1590644365607-1c5a38d07399", "1504307651254-35680f356dfd", "1531834685032-c34bf0d84c77", "1470290449668-02dd93d9420a",
                "1504917595217-d4dc5ebe6122", "1517646287304-4b8f9e9842a6", "1589939705384-5185137a7f0f", "1495819903255-00fdfa38a8de",
                "1503387920786-89d705445775", "1574359254888-9d10ad64d7df", "1599818817757-550604130096", "1534398079543-7ae6d016b86a"
            ]
        }
        self.generic_ids = ["1550684848-fac1c5b4e853", "1618005182384-a83a8bd57fbe", "1614850523060-8da1d56ae167", "1634152962476-4b8a00e1915c"]

    def clean_url(self, url):
        if not url: return ""
        return url.split('?')[0].strip()

    def is_url_used(self, url):
        clean = self.clean_url(url)
        return clean in self.global_used_urls

    def mark_as_used(self, url):
        clean = self.clean_url(url)
        if clean:
            self.global_used_urls.add(clean)

    def get_fallback_image(self, category):
        target_list = self.id_pools.get(category, self.generic_ids)
        attempts = 0
        while attempts < 50:
            selected_id = random.choice(target_list)
            base_url = f"https://images.unsplash.com/photo-{selected_id}"
            if base_url not in self.global_used_urls:
                self.global_used_urls.add(base_url)
                return f"{base_url}?auto=format&fit=crop&w=800&q=80"
            attempts += 1
        selected_id = random.choice(self.generic_ids)
        return f"https://images.unsplash.com/photo-{selected_id}?auto=format&fit=crop&w=800&q=80"

image_manager = ImageManager()

# --- REAL IMAGE SCRAPER ---
def fetch_og_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                img_url = og_image["content"]
                if "logo" in img_url.lower() or "icon" in img_url.lower():
                    return None
                return img_url
    except Exception:
        pass
    return None

def get_best_image(entry, category, article_url, source_name):
    # --- HARD BLOCK: DO NOT TRUST THESE SOURCES FOR IMAGES ---
    # Dessa källor använder generiska bilder som scrapers inte kan skilja från riktiga.
    # Vi tvingar dem att använda vårt interna bibliotek för att garantera variation.
    BANNED_IMAGE_SOURCES = ["cleantechnica", "oilprice", "dagens ps"]
    
    source_lower = source_name.lower()
    
    # 1. Om källan är svartlistad -> GÅ DIREKT TILL FALLBACK
    if any(banned in source_lower for banned in BANNED_IMAGE_SOURCES):
        # print(f"Source '{source_name}' blocked from external images. Using internal library.")
        return image_manager.get_fallback_image(category)

    # 2. RSS (Med Global Dubblett-koll)
    rss_img = None
    try:
        if 'media_content' in entry: rss_img = entry.media_content[0]['url']
        elif 'media_thumbnail' in entry: rss_img = entry.media_thumbnail[0]['url']
        elif 'links' in entry:
            for link in entry.links:
                if link.type.startswith('image/'): rss_img = link.href
    except: pass
    
    if rss_img:
        bad_keywords = ["placeholder", "pixel", "tracker", "feedburner", "default", "icon"]
        if any(bad in rss_img.lower() for bad in bad_keywords):
            rss_img = None
        elif image_manager.is_url_used(rss_img):
            rss_img = None
    
    if rss_img:
        image_manager.mark_as_used(rss_img)
        return rss_img

    # 3. Scraper
    real_img = fetch_og_image(article_url)
    
    if real_img:
        if image_manager.is_url_used(real_img):
            real_img = None
            
    if real_img:
        image_manager.mark_as_used(real_img)
        return real_img

    # 4. Fallback (Garanterat unik)
    return image_manager.get_fallback_image(category)


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
    print("Startar SPECULA Generator v10.4.0 (Hard Block CleanTechnica)...")
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

                # --- HÄMTA BILD (MED HARD BLOCK FÖR CLEANTECHNICA) ---
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