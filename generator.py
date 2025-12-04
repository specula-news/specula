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

# --- FIX: UTF-8 Encoding ---
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# --- KONFIGURATION ---
MAX_ARTICLES_PER_SOURCE = 50 

# --- MANUELLA INLÄGG (Endast om nödvändigt) ---
MANUAL_ENTRIES = [
    {
        "title": "New EV Battery Tech Analysis (Specula Pick)",
        "link": "https://youtu.be/Fb0s1uBZu44",
        "summary": "Featured video analysis regarding the latest breakthroughs in EV battery technology and market dynamics.",
        "image": "https://img.youtube.com/vi/Fb0s1uBZu44/maxresdefault.jpg",
        "source": "Specula Select",
        "category": "ev",
        "published": time.time(),
        "time_str": "Just Now",
        "is_video": True
    }
]

# --- KÄLLOR ---
RSS_SOURCES = [
    # --- EV / ENERGY (PRIORITY) ---
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCy6tF-2i3h3l_5c5r6t7u7g", "ev"), # The Electric Viking
    ("https://cleantechnica.com/feed/", "ev"), 
    ("https://electrek.co/feed/", "ev"), 
    ("https://insideevs.com/rss/articles/all/", "ev"),
    ("https://www.greencarreports.com/rss/news", "ev"),
    ("https://oilprice.com/rss/main", "ev"),
    ("https://www.renewableenergyworld.com/feed/", "ev"),
    ("https://www.autoblog.com/category/green/rss.xml", "ev"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC2A8478U3_hO9e9s8c8c8c8", "ev"), # Matt Ferrell
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC3W19-5_6a5x8a5b8c8c8c8", "ev"), # ELEKTROmanija
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCczkqjGBMjcnXuV41jBSHKQ", "ev"), # Fully Charged

    # --- GEOPOLITICS ---
    ("https://www.scmp.com/rss/91/feed", "geopolitics"),
    ("https://www.aljazeera.com/xml/rss/all.xml", "geopolitics"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC1DXHptI9MNh9NRcDqGnIqw", "geopolitics"), # Asianometry
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCW39zufHfsuGgpLviKh297Q", "geopolitics"), # DW Docu
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC2mg_hL_8XqD06sDk9-0hNw", "geopolitics"), # Inside China Biz
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCmGSJVG3mCRXVOP4yXU1rQQ", "geopolitics"), # Johnny Harris
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCGq-a57w-1PqqjiISbS-iuA", "geopolitics"), # Diary CEO
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC5V3r52K5jY8f4oW-9i4iig", "geopolitics"), # ShanghaiEye
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCgrNz-aDmcr2uNt5IN47eEQ", "geopolitics"), # CGTN US
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC5i9r5iM8hJ69h_y_ZqT8_g", "geopolitics"), # CCTV
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCj0T5BI5xK7Y_4rT8jW-XFw", "geopolitics"), # CGTN EU
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCv3tL4Qv7jJ8r0x8t6lB4wA", "geopolitics"), # CGTN Main
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCWP1FO6PhA-LildwUO70lsA", "geopolitics"), # China Pulse
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC83tJtfQf-gmsso-gS5_tIQ", "geopolitics"), # CNA
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCF_1M7c6o-Kj_5azz8d-X8A", "geopolitics"), # Geopol Eco
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCx8Z1r7k-2gD6xX7c5l6b6g", "geopolitics"), # New China
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC6D3-Z2y7c8c9a0b1e1f1f1", "geopolitics"), # EU Debates
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC1yBDrf0w8h8q8q0t8b8g8g", "geopolitics"), # wocomoDOCS

    # --- TECH ---
    ("https://anastasiintech.substack.com/feed", "tech"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCD4EOyXKjfDUhI6ZLfc9XNg", "tech"), 
    ("https://techcrunch.com/feed/", "tech"),
    ("https://www.theverge.com/rss/index.xml", "tech"),
    ("https://arstechnica.com/feed/", "tech"),
    ("https://www.nyteknik.se/rss", "tech"), 
    ("https://feber.se/rss/", "tech"),

    # --- SCIENCE ---
    ("https://www.space.com/feeds/all", "science"),
    ("https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss", "science"),
    ("http://rss.sciam.com/ScientificAmerican-Global", "science"),
    ("https://www.newscientist.com/feed/home/", "science"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCvMj6UH48y1Ps-p-e-eJzHQ", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCHnyfMqiRRG1u-2MsSQLbXA", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC6107grRI4m0o2-emgoDnAA", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCMOqf8ab-42UUQIdVoKwjlQ", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC9w7f8f7g8h8j8j8j8j8j8", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC8c8c8c8c8c8c8c8c8c8c8", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCsXVk37bltHxD1rDPwtNM8Q", "science"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC7_gcs09iThXybpVgjHZ_7g", "science"), 

    # --- CONSTRUCTION ---
    ("https://www.constructiondive.com/feeds/news/", "construction"),
    ("http://feeds.feedburner.com/ArchDaily", "construction"),
    ("https://www.building.co.uk/rss/news", "construction"),
    ("https://www.constructionenquirer.com/feed/", "construction"),
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC7z8sK378O9H5_2-lJg9gDw", "construction"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC6n8I1UDTKP1IWjQMg6_sZw", "construction"), 
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCL3a7Xr-W8L7TC6K5am41DQ", "construction"), 
    ("https://www.dagensps.se/feed/", "geopolitics"), 
]

SWEDISH_SOURCES = ["feber.se", "sweclockers.com", "elektromanija", "dagensps.se", "nyteknik.se"]

# --- SMART FALLBACK (NYA KATEGORIER) ---
SMART_IMAGES = {
    "china": ["https://images.unsplash.com/photo-1543832923-44667a77d853?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1547981609-4b6bfe6770b7?q=80&w=1000&auto=format&fit=crop"],
    "asia": ["https://images.unsplash.com/photo-1535139262971-c51845709a48?q=80&w=1000&auto=format&fit=crop"],
    "ev": ["https://images.unsplash.com/photo-1593941707882-a5bba14938c7?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1550505393-273a55239e24?q=80&w=1000&auto=format&fit=crop"],
    "oil": ["https://images.unsplash.com/photo-1516937941348-c09645f31e88?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1628522333060-637998ca4448?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1518709414768-a88986a45ca5?q=80&w=1000&auto=format&fit=crop"],
    "tanker": ["https://images.unsplash.com/photo-1516937941348-c09645f31e88?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1605745341112-85968b19335b?q=80&w=1000&auto=format&fit=crop"],
    "gas": ["https://images.unsplash.com/photo-1628522333060-637998ca4448?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1579766927552-308b4974457e?q=80&w=1000&auto=format&fit=crop"],
    "money": ["https://images.unsplash.com/photo-1611974765270-ca1258634369?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?q=80&w=1000&auto=format&fit=crop"],
    "space": ["https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=1000&auto=format&fit=crop"],
    "nasa": ["https://images.unsplash.com/photo-1454789548728-85d2696cf667?q=80&w=1000&auto=format&fit=crop"],
    "ai": ["https://images.unsplash.com/photo-1677442136019-21780ecad995?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1000&auto=format&fit=crop"],
    "data center": ["https://images.unsplash.com/photo-1558494949-ef526b0042a0?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1544197150-b99a580bbcbf?q=80&w=1000&auto=format&fit=crop"],
    "tech": ["https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1519389950473-47ba0277781c?q=80&w=1000&auto=format&fit=crop"],
    "construction": ["https://images.unsplash.com/photo-1541888946425-d81bb19240f5?q=80&w=1000&auto=format&fit=crop", "https://images.unsplash.com/photo-1503387762-592deb58ef4e?q=80&w=1000&auto=format&fit=crop"],
    "building": ["https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=1000&auto=format&fit=crop"],
    "industry": ["https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=1000&auto=format&fit=crop"]
}

# --- GENERISK FALLBACK (RENSAD FRÅN RYMDEN) ---
GENERIC_FALLBACKS = [
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop", # Cyber City
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop", # Abstract Tech
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1000&auto=format&fit=crop", # Matrix
    "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=1000&auto=format&fit=crop", # Circuit
    "https://images.unsplash.com/photo-1535139262971-c51845709a48?q=80&w=1000&auto=format&fit=crop"  # Asia Night
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
    
    # OILPRICE SPECIFIC FIX
    if "oilprice" in source.lower():
        text += " oil gas money market energy" 

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

def generate_json_data():
    print("Fetching news...")
    all_articles = []
    seen_titles = set()

    for entry in MANUAL_ENTRIES:
        all_articles.append(entry)
        seen_titles.add(entry['title'])

    # ROTATING USER AGENTS FOR YOUTUBE
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    for url, category in RSS_SOURCES:
        try:
            agent = random.choice(user_agents)
            feed = feedparser.parse(url, agent=agent)
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            
            try: print(f"Loaded {len(feed.entries)} from {source_name}")
            except: pass
            
            is_swedish = any(s in url for s in SWEDISH_SOURCES)
            is_youtube = "youtube.com" in url or "youtu.be" in url
            
            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                try:
                    title = entry.title
                    
                    if title in seen_titles: continue
                    seen_titles.add(title)

                    pub_ts = time.time()
                    if 'published_parsed' in entry and entry.published_parsed:
                        pub_ts = time.mktime(entry.published_parsed)
                    
                    now = time.time()
                    hours_ago = int((now - pub_ts) / 3600)
                    if hours_ago < 1: time_str = "Just Now"
                    elif hours_ago < 24: time_str = f"{hours_ago}h Ago"
                    else: days = int(hours_ago / 24); time_str = f"{days}d Ago"

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

                    # CORRECT LINK LOGIC
                    final_link = entry.link
                    if 'yt_videoid' in entry:
                        final_link = f"https://www.youtube.com/watch?v={entry.yt_videoid}"

                    article = {
                        "title": title,
                        "link": final_link,
                        "summary": summary + note_html,
                        "image": final_image,
                        "source": source_name,
                        "category": category,
                        "published": pub_ts,
                        "time_str": time_str,
                        "is_video": is_youtube
                    }
                    all_articles.append(article)
                except Exception as inner_e:
                    continue

        except Exception as e:
            print(f"Error loading {url}: {e}")

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