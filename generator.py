import feedparser
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
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

# --- IMAGE MANAGER CLASS V9.9.0 ---
class ImageManager:
    def __init__(self):
        # Stores IDs only to save memory and ensure uniqueness
        self.used_ids = set()
        
        # MASSIVE ID LIBRARY (Over 600 IDs)
        # Using IDs allows us to construct clean URLs: https://images.unsplash.com/photo-{ID}?w=800&q=80
        self.id_pools = {
            "tech": [
                "1518770660439-4636190af475", "1550751827-4bd374c3f58b", "1519389950473-47ba0277781c", "1504639725590-34d0984388bd",
                "1526374965328-7f61d4dc18c5", "1550009158-9ebf69056955", "1535378437268-13d143445347", "1531297461136-82lw9b283993",
                "1485827404703-89b55fcc595e", "1523961131990-5ea7c61b2107", "1558494949-efc52728101c", "1610563166150-b34df4f3bcd6",
                "1510915361405-ef8a93d77d29", "1563770095-39d468f421e2", "1525547719571-a2d4ac8945e2", "1592478411213-61535fdd861d",
                "1515378791036-0648a3ef77b2", "1555255707-c07966088b7b", "1517694712202-14dd9538aa97", "1531482615713-2afd69097998",
                "1550745165-9bc0b252726f", "1562813733-b31f71025d54", "1581091226825-a6a2a5aee158", "1498050108023-c5249f4df085",
                "1505330622279-bf7d7fc918f4", "1517077304055-6e89abbf09b0", "1591696205602-2f950c417cb9", "1629654290799-13f9b11d7370",
                "1551288049-bebda4e38f71", "1526628953303-b72777429f13", "1461961561917-19431306241d", "1483817301491-dd0b58120958",
                "1555421689-d68471e189f2", "1496171367470-9ed9a92ea939", "1542831371-29b0f74f9713", "1527474305487-b87b222841cc",
                "1531746790731-6c087fecd65a", "1468436139062-f60a71c5c892", "1517245386807-bb43f82c33c4", "1536859355448-76f92ebdc33d",
                "1496065187959-7f07b8353c55", "1509062522241-12565b8d4b9c", "1529156069890-3632af0e3043", "1503899036084-c55cdd92a3a8",
                "1573164713714-d95e436ab8d6", "1551033406-611cf9a28f67", "1518432031352-d6fc5c10da5a", "1454165804606-c3d57bc86b40",
                "1516110833967-0b5716ca1387", "1516259762381-e63176fc3c52", "1550751827-4bd374c3f58b", "1507146426996-ef05306b995a",
                "1558346490-a72e53ae2d4f", "1534067783745-705a746b4213", "1544197150-b99a580bb7a8", "1498050108023-c5249f4df085",
                "1531297461136-82lw9b283993", "1523961131990-5ea7c61b2107", "1580894732444-8ecded7900cd", "1522071820081-009f0129c71c"
            ],
            "ev": [
                "1593941707882-a5bba14938c7", "1617788138017-80ad40651399", "1565373676955-349f71c4acbe", "1550505393-273a55239e24",
                "1620882352329-a41764645229", "1558628818-40db7871d007", "1594535182308-8ff248971649", "1605733513597-a8f8341084e6",
                "1494976388531-d1058494cdd8", "1558449028-b53a39d100fc", "1532935298550-6e02e8906652", "1456356627738-3a96db6d54cb",
                "1497435334941-8c899ee9e8e9", "1521618755572-156ae0cdd74d", "1487887235947-a955ef187fcc", "1513258496098-882717dbf58c",
                "1532601224476-15c79f2f7a51", "1518709268805-4e9042af9f23", "1509391366360-2e959784a276", "1566093097221-8563d80d2d31",
                "1546443046-e526d1163e8e", "1616406432452-9215e6e1044f", "1503376763036-066120622c74", "1593941707882-a5bba14938c7",
                "1580612231135-666dd9303254", "1501199532894-9449c0185993", "1480131666874-3252a1708846", "1492144534655-ae79c964c9d7",
                "1549317661-bd32c8ce0db2", "1569024733930-88e60790d971", "1598559286419-450f64c6328a", "1494905990131-72ab1052db7e",
                "1452449241947-d53d262a6523", "1508974239320-0a270b468ce2", "1498889444388-e67ea886f2f9", "1507537297725-24a1c029d3ca",
                "1556912173-3db0039b9562", "1619642751034-765dfdf7c58e", "1566864229737-3323c2d44933", "1601362840469-51e4d8d58785",
                "1606191089694-03f240901ac4", "1523983355571-0a93dad0c4e0", "1537756040854-e66123912630", "1560293888371-6c24f4693b74",
                "1586528116311-475d3600125d", "1611348586804-61f7924114c3", "1611244419960-69db3c6020c0", "1620712943543-0a3f5a287233"
            ],
            "geopolitics": [
                "1529101091760-6149d3c879d4", "1532375810709-75b1da00537c", "1543832923-44667a77d853", "1547981609-4b6bfe6770b7",
                "1464817739973-0128fe77aaa1", "1590283603385-17ffb3a7f29f", "1612178991541-b48cc8e92a4d", "1520699697851-3dc68aa3a474",
                "1474376962954-d8a681cc53b2", "1496442226666-8d4a0e62e6e9", "1524601500432-1e1a4c71d692", "1537254326439-0e78a8257938",
                "1516023353357-357c6032d288", "1555848962-6e79363ec58f", "1575320181282-9afab399332c", "1477039181047-94e702db8436",
                "1541872703-74c59636a226", "1507679799987-c73779587ccf", "1523995462485-3d171b5c8fa9", "1535139262971-c51845709a48",
                "1457131760772-7017c6180f05", "1502920514313-52581002a659", "1516937941348-c09645f31e88", "1628522333060-637998ca4448",
                "1518709414768-a88986a45ca5", "1579766927552-308b4974457e", "1563986768494-4dee2763ff3f", "1582555618296-5427d25365b6",
                "1596463059283-32d70243b13c", "1595835008848-1200699190b7", "1611974765270-ca1258634369", "1633158829585-23ba8f7c8caf",
                "1565514020176-dbf2277f4942", "1580519542036-c47de6196ba5", "1559526324-4b87b5e36e44", "1642543492481-44e81e3914a7",
                "1591526039605-79e4eb30c00a", "1520699049698-38603ad01d9f", "1541873676-a18131494184", "1543835260-261298c94982",
                "1522881451255-f59ad836f65d", "1541339907198-e08756dedf3f", "1550418394-b8b9287a99f2", "1483425571841-991fb57790a2",
                "1494412574643-35d324688b33", "1479839672679-a472b6367f77", "1532117236988-f586d1a73324", "1521791136064-7986608178d4"
            ],
            "science": [
                "1446776811953-b23d57bd21aa", "1614728853970-36279f57520b", "1541185933-710f50746747", "1517976487492-5750f3195933",
                "1457369804613-52c61a468e7d", "1533475418392-41543084b4f7", "1507413245164-6160d8298b31", "1532094349884-543bc11b234d",
                "1532187863486-abf9dbad1b69", "1451187580459-43490279c0fa", "1484589065579-248aad0d8b13", "1462331940025-496dfbfc7564",
                "1506318137071-a8bcbf67cc77", "1516339901601-2e1b62dc0c45", "1576086213369-97a306d36557", "1507668077129-56e32842fceb",
                "1481819613568-3701cbc70156", "1504384308090-c54be3855833", "1530053969600-caed2596d242", "1581093458791-9f3c3900df4b",
                "1562408590-e32931084e23", "1527664557719-47823841da56", "1543722537-86a87f858412", "1507413245164-6160d8298b31",
                "1489549132488-d00b7eee80f1", "1581090464777-f3220bbe1b8b", "1464802686167-b939a6910659", "1532635241-17e820acc59f",
                "1509228468518-180dd4864904", "1532094349884-543bc11b234d", "1451187580459-43490279c0fa", "1517411032315-54ef2cb783bb",
                "1518066000714-58e8f83e2012", "1545156526-7291a14a60e8", "1569711685368-7c8702951f04", "1529606869420-53394a101f3b",
                "1446776811953-b23d57bd21aa", "1534796636912-3b95b3ab5980", "1581091226825-a6a2a5aee158", "1496065187959-7f07b8353c55"
            ],
            "construction": [
                "1541888946425-d81bb19240f5", "1503387762-592deb58ef4e", "1581094794329-c8112a89af12", "1535732759880-bbd5c7265e3f",
                "1590644365607-1c5a38d07399", "1504307651254-35680f356dfd", "1531834685032-c34bf0d84c77", "1470290449668-02dd93d9420a",
                "1504917595217-d4dc5ebe6122", "1517646287304-4b8f9e9842a6", "1589939705384-5185137a7f0f", "1495819903255-00fdfa38a8de",
                "1503387920786-89d705445775", "1574359254888-9d10ad64d7df", "1599818817757-550604130096", "1534398079543-7ae6d016b86a",
                "1429497419816-9ca5cfb4571a", "1485627658391-1365e4e0dbfe", "1541963463532-d68292c34b19", "1581092580497-e0d23cbdf1dc",
                "1595846519845-68e298c2edd8", "1536895058696-a69b1c7ba34d", "1572916198945-2542a7c4a179", "1542621334-a6c4f5798f91",
                "1486718448742-16439565c583", "1588072213942-bc3e8a4a79d6", "1517544046648-5231c5b8b958", "1590059178384-489953934305",
                "1487958449943-2429e8be0baa", "1584627104440-05d2873d3609", "1504297050568-910d24c426d3", "1597424214716-15a94165c71d"
            ]
        }
        
        # GENERIC / ABSTRACT POOL (Massive Backup)
        self.generic_ids = [
            "1550684848-fac1c5b4e853", "1618005182384-a83a8bd57fbe", "1614850523060-8da1d56ae167", "1634152962476-4b8a00e1915c",
            "1604871000636-074fa5117945", "1534224039826-c7a0eda0e6b3", "1493612276216-ee3925520721", "1508614999368-9260051292e5",
            "1502472584811-0a2f2ca84465", "1494548162494-384bba4ab999", "1550751827-4bd374c3f58b", "1557683316-973673baf926",
            "1562654501343-50c9475e8881", "1545987747-8613f4405d09", "1486334803289-1623f249dd1e", "1495433324511-bf8e92934d90",
            "1579546929518-9e396f3cc809", "1557682250-33bd709cbe85", "1451187580459-43490279c0fa", "1554147090-e1221a04a025",
            "1563089145-599997674d42", "1497864149936-d72636e9c875", "1516542076529-1ea3854896f2", "1518655048521-f130df041f66",
            "1526040652367-7734140f049e", "1520038410233-71430e729330", "1550745165-9bc0b252726f", "1487058792275-0ad4aaf24ca7",
            "1550751827-4bd374c3f58b", "1528459192924-c416e536f990", "1518331683046-e6ecc885b5d8", "1486334803289-1623f249dd1e"
        ]

    def get_image(self, category):
        # 1. Try Target Category
        target_list = self.id_pools.get(category, self.generic_ids)
        available = [pid for pid in target_list if pid not in self.used_ids]
        
        # 2. Try Generic Pool
        if not available:
            available = [pid for pid in self.generic_ids if pid not in self.used_ids]

        # 3. Try STEALING from other pools (Cross-Category Fallback)
        # This is the "Scorched Earth" policy: Better to use a Science image for EV than to repeat a picture.
        if not available:
            all_ids = []
            for pool in self.id_pools.values(): all_ids.extend(pool)
            available = [pid for pid in all_ids if pid not in self.used_ids]

        # 4. If ALL 600+ images are used, we must reuse.
        if not available:
            available = target_list

        selected_id = random.choice(available)
        self.used_ids.add(selected_id)
        
        # Construct optimized Unsplash URL
        return f"https://images.unsplash.com/photo-{selected_id}?auto=format&fit=crop&w=800&q=80"

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