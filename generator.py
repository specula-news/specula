import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup
import math

# --- KONFIGURATION ---
# Vi sänker antal per sida något för att göra laddningstiden snabbare, 
# men hämtar MÅNGA fler artiklar totalt.
ARTICLES_PER_PAGE = 12 
MAX_ARTICLES_PER_SOURCE = 20  # Hämtar 20 artiklar från varje källa (totalt ca 300+ artiklar)

RSS_FEEDS = [
    # --- SWEDISH TECH ---
    "https://feber.se/rss/",
    "https://www.sweclockers.com/feeds/nyheter",
    
    # --- GLOBAL ECONOMY & MARKETS ---
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",   # CNBC Tech & Money
    "http://feeds.marketwatch.com/marketwatch/topstories/",   # MarketWatch (Global Economy)
    
    # --- CHINA & ASIA TECH (Geopolitics) ---
    "https://asia.nikkei.com/rss/feed/nar",                   # Nikkei Asia (Asian Market Focus)
    "https://technode.com/feed/",                             # TechNode (Deep dive China Tech)
    
    # --- HARD TECH & INVENTIONS ---
    "https://spectrum.ieee.org/feeds/feed.rss",               # IEEE Spectrum (Engineering/Inventions)
    "https://www.sciencedaily.com/rss/top/technology.xml",    # Science Daily (Breakthroughs)
    "https://phys.org/rss-feed/nanotech-news/",               # Nanotechnology
    
    # --- MAJOR TECH NEWS ---
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/category/tech/latest/rss",
    "https://arstechnica.com/feed/",
    
    # --- FUTURE & SPACE ---
    "https://www.universetoday.com/feed/",                    # Space & Astronomy
    "https://singularityhub.com/feed/"                        # AI & Singularity
]

# Fallback image
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"

def get_image_from_entry(entry):
    """Försöker hitta en bild i RSS-flödet på olika sätt"""
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    if 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    if 'links' in entry:
        for link in entry.links:
            if link.type.startswith('image/'):
                return link.href
    if 'content' in entry:
        soup = BeautifulSoup(entry.content[0].value, 'html.parser')
        img = soup.find('img')
        if img: return img['src']
    if 'summary' in entry:
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img = soup.find('img')
        if img: return img['src']
    return DEFAULT_IMAGE

def clean_summary(summary):
    soup = BeautifulSoup(summary, 'html.parser')
    text = soup.get_text()
    return text[:220] + "..." if len(text) > 220 else text

def generate_pagination_html(current_page, total_pages):
    html = ""
    
    # Previous Button
    if current_page > 1:
        prev_link = "index.html" if current_page == 2 else f"page{current_page - 1}.html"
        html += f'<a href="{prev_link}" class="page-btn">&larr; PREV</a>'
    
    # Smart Page Numbers (shows 1 ... 4 5 6 ... 99)
    for i in range(1, total_pages + 1):
        # Visa alltid första, sista, och sidorna runt den vi är på
        if i == 1 or i == total_pages or (current_page - 2 <= i <= current_page + 2):
            link = "index.html" if i == 1 else f"page{i}.html"
            active_class = "active" if i == current_page else ""
            html += f'<a href="{link}" class="page-btn {active_class}">{i}</a>'
        elif i == current_page - 3 or i == current_page + 3:
            html += '<span style="color:var(--text-secondary); align-self:center;">...</span>'

    # Next Button
    if current_page < total_pages:
        html += f'<a href="page{current_page + 1}.html" class="page-btn">NEXT &rarr;</a>'
        
    return html

def generate_pages():
    print("Fetching news from global sources...")
    all_articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            print(f"Loaded {len(feed.entries)} from {source_name}")
            
            # Hämta fler artiklar per källa
            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                # Försök hitta datum, använd nu-tid om det saknas
                pub_date = entry.published_parsed if 'published_parsed' in entry else time.gmtime()
                
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'summary': clean_summary(entry.summary if 'summary' in entry else ""),
                    'image': get_image_from_entry(entry),
                    'source': source_name,
                    'published': pub_date
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error loading {feed_url}: {e}")

    # Sortera nyast först
    all_articles.sort(key=lambda x: x['published'], reverse=True)
    
    # Räkna ut sidor
    total_articles = len(all_articles)
    total_pages = math.ceil(total_articles / ARTICLES_