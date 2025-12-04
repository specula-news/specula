import feedparser
import json
import os
import glob
import random
import datetime
import yt_dlp
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# --- KONFIGURATION ---
OUTPUT_DIR = "public"
TEMPLATE_FILE = "template.html"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

# --- IMAGE MANAGER CLASS (LÖSNINGEN PÅ DUBBLETTER) ---
class ImageManager:
    def __init__(self):
        # Global tracker för att minnas vilka bilder som använts under denna körning
        self.used_images = set()
        
        # HÄR DEFINIERAR DU DINA BILD-LISTOR (Kopiera in dina 150+ länkar här)
        # Jag har lagt in platshållare, se till att fylla på dessa listor rejält!
        self.image_pools = {
            "Geopolitics": [
                "https://images.unsplash.com/photo-1529101091760-6149d3c879d4?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1532375810709-75b1da00537c?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                # ... Lägg till dina kartor/militär/politik bilder här
            ],
            "Tech": [
                "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                # ... Lägg till dina kretskort/cyber/kod bilder här
            ],
            "EV": [
                "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1617788138017-80ad40651399?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                # ... Lägg till bilar/laddstolpar/batterier
            ],
            "Science": [
                "https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                # ... Rymden/Mikroskop/DNA
            ],
            "Construction": [
                 "https://images.unsplash.com/photo-1541888946425-d81bb19240f5?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                 "https://images.unsplash.com/photo-1503387762-592deb58ef4e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
            ],
            "All News": [
                # En generell pool om inget annat passar
                "https://images.unsplash.com/photo-1504711434969-e33886168f5c?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
            ]
        }

    def get_image(self, category):
        """
        Returnerar en bild som GARANTERAT inte visats tidigare i denna körning,
        om det finns några bilder kvar att välja på.
        """
        # 1. Bestäm vilken lista vi ska leta i
        target_pool = self.image_pools.get(category, self.image_pools["All News"])
        
        # 2. Hitta bilder i denna pool som INTE finns i self.used_images
        available_images = [img for img in target_pool if img not in self.used_images]
        
        # 3. Om poolen för kategorin är slut (alla använda), gå till reservplanen
        if not available_images:
            print(f"WARNING: Slut på unika bilder för {category}. Letar i globala poolen...")
            # Samla ALLA bilder från alla kategorier
            all_images = []
            for pool in self.image_pools.values():
                all_images.extend(pool)
            
            # Filtrera igen mot använda bilder
            available_images = [img for img in all_images if img not in self.used_images]

        # 4. Om det FORTFARANDE är tomt (extremt sällsynt om du har 150 bilder),
        # då måste vi tyvärr återanvända en (panic mode), men vi tar en slumpmässig.
        if not available_images:
             print("CRITICAL: Slut på ALLA unika bilder. Måste återanvända.")
             # Återgå till kategorins pool även om de är använda
             available_images = target_pool

        # 5. Välj en bild, markera som använd, returnera
        selected_image = random.choice(available_images)
        self.used_images.add(selected_image)
        return selected_image

# Initiera bildhanteraren
image_manager = ImageManager()

# --- INSTÄLLNINGAR FÖR FEEDS ---
FEEDS = [
    # Dina RSS-feeds här (exempel)
    {"url": "https://feeds.feedburner.com/TechCrunch/", "category": "Tech"},
    {"url": "http://feeds.arstechnica.com/arstechnica/index", "category": "Tech"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "Geopolitics"},
    {"url": "https://insideevs.com/rss/articles/all/", "category": "EV"},
    {"url": "https://www.space.com/feeds/all", "category": "Science"},
    # Lägg till resten av dina feeds...
]

YOUTUBE_CHANNELS = [
    # Dina YT-kanaler här...
]

def clean_summary(summary):
    soup = BeautifulSoup(summary, "html.parser")
    return soup.get_text()[:200] + "..."

def get_thumbnail(entry, category):
    # 1. Försök hitta en bild i RSS-flödet först (Media thumbnail etc)
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media and ('jpg' in media['url'] or 'png' in media['url']):
                return media['url']
    if 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    
    # 2. Om ingen bild finns i RSS -> Använd ImageManager för Smart Fallback utan dubbletter
    return image_manager.get_image(category)

def get_youtube_video(channel_url, category):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'playlistend': 2  # Hämtar de 2 senaste
    }
    videos = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    # Prioritera hqdefault för att slippa gråa rutor
                    thumb = entry.get('thumbnails', [{}])[-1].get('url', '')
                    # Fix för vanliga youtube thumbnails
                    if not thumb or "hqdefault" not in thumb:
                         video_id = entry.get('id')
                         thumb = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

                    videos.append({
                        "title": entry.get('title'),
                        "link": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "summary": "Watch the latest coverage on YouTube.",
                        "published": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "image": thumb, # Youtube har sina egna bilder, behöver inte ImageManager oftast
                        "source": info.get('uploader', 'YouTube'),
                        "category": category,
                        "is_video": True
                    })
        except Exception as e:
            print(f"Error fetching YouTube {channel_url}: {e}")
    return videos

def generate_site():
    print("Startar SPECULA Generator v9.6.0...")
    all_articles = []

    # Hämta RSS
    for feed_info in FEEDS:
        print(f"Processing RSS: {feed_info['url']}")
        try:
            feed = feedparser.parse(feed_info['url'])
            for entry in feed.entries[:4]: # Begränsa till 4 per feed
                img_url = get_thumbnail(entry, feed_info['category'])
                
                article = {
                    "title": entry.title,
                    "link": entry.link,
                    "summary": clean_summary(entry.get('summary', '')),
                    "published": entry.get('published', 'Just Now'),
                    "image": img_url,
                    "source": feed.feed.get('title', 'Unknown Source'),
                    "category": feed_info['category'],
                    "is_video": False
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error parsing feed {feed_info['url']}: {e}")

    # Hämta YouTube
    for channel in YOUTUBE_CHANNELS:
        print(f"Processing YouTube: {channel['url']}")
        videos = get_youtube_video(channel['url'], channel['category'])
        all_articles.extend(videos)

    # Blanda artiklarna för en dynamisk feed
    random.shuffle(all_articles)

    # Generera HTML
    print("Genererar HTML...")
    articles_html = ""
    for article in all_articles:
        # Bestäm etikettklass
        cat_class = article['category'].lower().replace(" ", "-")
        
        # Ikon overlay för video
        play_icon = ""
        if article.get('is_video'):
            play_icon = """<div class="play-overlay"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M8 5v14l11-7z"/></svg></div>"""

        article_html = f"""
        <article class="news-card" data-category="{article['category']}">
            <div class="card-image-container">
                <img src="{article['image']}" alt="{article['title']}" loading="lazy">
                {play_icon}
                <span class="category-tag {cat_class}">{article['category']}</span>
            </div>
            <div class="card-content">
                <div class="meta">
                    <span class="source">{article['source'].upper()}</span>
                    <span class="time">{article['published'][:16]}</span>
                </div>
                <h3><a href="{article['link']}" target="_blank">{article['title']}</a></h3>
                <p>{article['summary']}</p>
                <a href="{article['link']}" class="read-more" target="_blank">FULL STORY &rarr;</a>
            </div>
        </article>
        """
        articles_html += article_html

    # Läs template och skriv fil
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("<!-- CONTENT_PLACEHOLDER -->", articles_html)
    final_html = final_html.replace("<!-- DATE_GENERATED -->", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"Klar! index.html genererad i {OUTPUT_DIR}/ med {len(all_articles)} artiklar.")

if __name__ == "__main__":
    generate_site()