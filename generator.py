import feedparser
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import math
import random
import json
import sys
import os
import re
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

# --- KANALER & KÄLLOR ---
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

# --- IMAGE MANAGER V9.8.0 ---
class ImageManager:
    def __init__(self):
        self.used_images = set()
        
        # ENORM LISTA (MASSIVE LIBRARY)
        self.pools = {
            "tech": [
                "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80", "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80",
                "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80", "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&q=80",
                "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80", "https://images.unsplash.com/photo-1550009158-9ebf69056955?w=800&q=80",
                "https://images.unsplash.com/photo-1535378437268-13d143445347?w=800&q=80", "https://images.unsplash.com/photo-1531297461136-82lw9b283993?w=800&q=80",
                "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&q=80", "https://images.unsplash.com/photo-1523961131990-5ea7c61b2107?w=800&q=80",
                "https://images.unsplash.com/photo-1558494949-efc52728101c?w=800&q=80", "https://images.unsplash.com/photo-1610563166150-b34df4f3bcd6?w=800&q=80",
                "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80", "https://images.unsplash.com/photo-1510915361405-ef8a93d77d29?w=800&q=80",
                "https://images.unsplash.com/photo-1563770095-39d468f421e2?w=800&q=80", "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=800&q=80",
                "https://images.unsplash.com/photo-1592478411213-61535fdd861d?w=800&q=80", "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=800&q=80",
                "https://images.unsplash.com/photo-1555255707-c07966088b7b?w=800&q=80", "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&q=80",
                "https://images.unsplash.com/photo-1531482615713-2afd69097998?w=800&q=80", "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=80",
                "https://images.unsplash.com/photo-1562813733-b31f71025d54?w=800&q=80", "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&q=80",
                "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&q=80", "https://images.unsplash.com/photo-1505330622279-bf7d7fc918f4?w=800&q=80",
                "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=800&q=80", "https://images.unsplash.com/photo-1591696205602-2f950c417cb9?w=800&q=80"
            ],
            "geopolitics": [
                "https://images.unsplash.com/photo-1529101091760-6149d3c879d4?w=800&q=80", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
                "https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=800&q=80", "https://images.unsplash.com/photo-1543832923-44667a77d853?w=800&q=80",
                "https://images.unsplash.com/photo-1547981609-4b6bfe6770b7?w=800&q=80", "https://images.unsplash.com/photo-1464817739973-0128fe77aaa1?w=800&q=80",
                "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=800&q=80", "https://images.unsplash.com/photo-1612178991541-b48cc8e92a4d?w=800&q=80",
                "https://images.unsplash.com/photo-1520699697851-3dc68aa3a474?w=800&q=80", "https://images.unsplash.com/photo-1474376962954-d8a681cc53b2?w=800&q=80",
                "https://images.unsplash.com/photo-1496442226666-8d4a0e62e6e9?w=800&q=80", "https://images.unsplash.com/photo-1524601500432-1e1a4c71d692?w=800&q=80",
                "https://images.unsplash.com/photo-1537254326439-0e78a8257938?w=800&q=80", "https://images.unsplash.com/photo-1516023353357-357c6032d288?w=800&q=80",
                "https://images.unsplash.com/photo-1555848962-6e79363ec58f?w=800&q=80", "https://images.unsplash.com/photo-1575320181282-9afab399332c?w=800&q=80",
                "https://images.unsplash.com/photo-1477039181047-94e702db8436?w=800&q=80", "https://images.unsplash.com/photo-1532601224476-15c79f2f7a51?w=800&q=80",
                "https://images.unsplash.com/photo-1541872703-74c59636a226?w=800&q=80", "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80",
                "https://images.unsplash.com/photo-1523995462485-3d171b5c8fa9?w=800&q=80", "https://images.unsplash.com/photo-1535139262971-c51845709a48?w=800&q=80",
                "https://images.unsplash.com/photo-1457131760772-7017c6180f05?w=800&q=80", "https://images.unsplash.com/photo-1502920514313-52581002a659?w=800&q=80"
            ],
            "ev": [
                "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&q=80", "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800&q=80",
                "https://images.unsplash.com/photo-1565373676955-349f71c4acbe?w=800&q=80", "https://images.unsplash.com/photo-1550505393-273a55239e24?w=800&q=80",
                "https://images.unsplash.com/photo-1620882352329-a41764645229?w=800&q=80", "https://images.unsplash.com/photo-1558628818-40db7871d007?w=800&q=80",
                "https://images.unsplash.com/photo-1594535182308-8ff248971649?w=800&q=80", "https://images.unsplash.com/photo-1605733513597-a8f8341084e6?w=800&q=80",
                "https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800&q=80", "https://images.unsplash.com/photo-1558449028-b53a39d100fc?w=800&q=80",
                "https://images.unsplash.com/photo-1532935298550-6e02e8906652?w=800&q=80", "https://images.unsplash.com/photo-1456356627738-3a96db6d54cb?w=800&q=80",
                "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?w=800&q=80", "https://images.unsplash.com/photo-1521618755572-156ae0cdd74d?w=800&q=80",
                "https://images.unsplash.com/photo-1487887235947-a955ef187fcc?w=800&q=80", "https://images.unsplash.com/photo-1513258496098-882717dbf58c?w=800&q=80",
                "https://images.unsplash.com/photo-1532601224476-15c79f2f7a51?w=800&q=80", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&q=80",
                "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=800&q=80", "https://images.unsplash.com/photo-1566093097221-8563d80d2d31?w=800&q=80",
                "https://images.unsplash.com/photo-1546443046-e526d1163e8e?w=800&q=80", "https://images.unsplash.com/photo-1616406432452-9215e6e1044f?w=800&q=80"
            ],
            "science": [
                "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=800&q=80", "https://images.unsplash.com/photo-1614728853970-36279f57520b?w=800&q=80",
                "https://images.unsplash.com/photo-1541185933-710f50746747?w=800&q=80", "https://images.unsplash.com/photo-1517976487492-5750f3195933?w=800&q=80",
                "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=800&q=80", "https://images.unsplash.com/photo-1533475418392-41543084b4f7?w=800&q=80",
                "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=800&q=80", "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=800&q=80",
                "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800&q=80", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
                "https://images.unsplash.com/photo-1484589065579-248aad0d8b13?w=800&q=80", "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=800&q=80",
                "https://images.unsplash.com/photo-1506318137071-a8bcbf67cc77?w=800&q=80", "https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?w=800&q=80",
                "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800&q=80", "https://images.unsplash.com/photo-1507668077129-56e32842fceb?w=800&q=80",
                "https://images.unsplash.com/photo-1481819613568-3701cbc70156?w=800&q=80", "https://images.unsplash.com/photo-1504384308090-c54be3855833?w=800&q=80",
                "https://images.unsplash.com/photo-1530053969600-caed2596d242?w=800&q=80", "https://images.unsplash.com/photo-1581093458791-9f3c3900df4b?w=800&q=80"
            ],
            "construction": [
                "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?w=800&q=80", "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=800&q=80",
                "https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=800&q=80", "https://images.unsplash.com/photo-1535732759880-bbd5c7265e3f?w=800&q=80",
                "https://images.unsplash.com/photo-1590644365607-1c5a38d07399?w=800&q=80", "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&q=80",
                "https://images.unsplash.com/photo-1531834685032-c34bf0d84c77?w=800&q=80", "https://images.unsplash.com/photo-1470290449668-02dd93d9420a?w=800&q=80",
                "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=800&q=80", "https://images.unsplash.com/photo-1517646287304-4b8f9e9842a6?w=800&q=80",
                "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=800&q=80", "https://images.unsplash.com/photo-1495819903255-00fdfa38a8de?w=800&q=80",
                "https://images.unsplash.com/photo-1503387920786-89d705445775?w=800&q=80", "https://images.unsplash.com/photo-1574359254888-9d10ad64d7df?w=800&q=80",
                "https://images.unsplash.com/photo-1599818817757-550604130096?w=800&q=80", "https://images.unsplash.com/photo-1534398079543-7ae6d016b86a?w=800&q=80",
                "https://images.unsplash.com/photo-1429497419816-9ca5cfb4571a?w=800&q=80", "https://images.unsplash.com/photo-1485627658391-1365e4e0dbfe?w=800&q=80"
            ]
        }
        
        # NEUTRAL / ABSTRAKT POOL (Fallback Nivå 2 - Passar allt)
        self.generic_pool = [
            "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=800&q=80", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&q=80",
            "https://images.unsplash.com/photo-1614850523060-8da1d56ae167?w=800&q=80", "https://images.unsplash.com/photo-1634152962476-4b8a00e1915c?w=800&q=80",
            "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&q=80", "https://images.unsplash.com/photo-1604871000636-074fa5117945?w=800&q=80",
            "https://images.unsplash.com/photo-1484589065579-248aad0d8b13?w=800&q=80", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80",
            "https://images.unsplash.com/photo-1534224039826-c7a0eda0e6b3?w=800&q=80", "https://images.unsplash.com/photo-1516339901601-2e1b62dc0c45?w=800&q=80",
            "https://images.unsplash.com/photo-1493612276216-ee3925520721?w=800&q=80", "https://images.unsplash.com/photo-1508614999368-9260051292e5?w=800&q=80",
            "https://images.unsplash.com/photo-1489549132488-d00b7eee80f1?w=800&q=80", "https://images.unsplash.com/photo-1502472584811-0a2f2ca84465?w=800&q=80",
            "https://images.unsplash.com/photo-1494548162494-384bba4ab999?w=800&q=80", "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&q=80"
        ]

    def get_image(self, category):
        # 1. Hämta RÄTT kategori
        target_list = self.pools.get(category, self.generic_pool)
        available = [img for img in target_list if img not in self.used_images]
        
        # 2. Om RÄTT kategori är slut -> Använd GENERELL pool (Abstract/News)
        if not available:
            # print(f"DEBUG: Category {category} empty. Using Generic Pool.")
            available = [img for img in self.generic_pool if img not in self.used_images]

        # 3. Om GENERELL är slut -> Panik! Låna från ANDRA kategorier (Men ta bara en oanvänd!)
        if not available:
            # print(f"DEBUG: Generic Pool empty. Searching all pools...")
            all_imgs = []
            for p in self.pools.values(): all_imgs.extend(p)
            available = [img for img in all_imgs if img not in self.used_images]
            
        # 4. Om ALLT är slut (200+ bilder) -> Reset (ta vad som helst)
        if not available:
             # print("DEBUG: CRITICAL - All images used. Resetting.")
             available = target_list

        selected = random.choice(available)
        self.used_images.add(selected)
        return selected

# Initiera manager globalt
image_manager = ImageManager()

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

def clean_youtube_description(text):
    if not text: return "Watch video for details."
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'#\S+', '', text)
    spam_phrases = ["subscribe", "patreon", "instagram", "twitter", "facebook", "follow me", "support", "merch", "discord", "copyright"]
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        line_lower = line.lower()
        if not any(spam in line_lower for spam in spam_phrases):
            clean_line = line.strip()
            if len(clean_line) > 20:
                clean_lines.append(clean_line)
    summary = ". ".join(clean_lines[:2])
    return summary[:220] + "..." if len(summary) > 220 else summary

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
                    
                    img = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    
                    raw_desc = entry.get('description', '')
                    clean_desc = clean_youtube_description(raw_desc)

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
                        "summary": clean_desc,
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
                    # ANVÄND NYA MANAGERN HÄR - Skickar bara category nu
                    final_image = found_image if found_image else image_manager.get_image(category)

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