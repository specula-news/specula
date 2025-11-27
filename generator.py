import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup
import math
import random
from deep_translator import GoogleTranslator

# --- KONFIGURATION ---
ARTICLES_PER_PAGE = 45   
MAX_ARTICLES_PER_SOURCE = 20

RSS_FEEDS = [
    "https://feber.se/rss/",
    "https://www.sweclockers.com/feeds/nyheter",
    "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    "http://feeds.marketwatch.com/marketwatch/topstories/",
    "https://asia.nikkei.com/rss/feed/nar",
    "https://technode.com/feed/",
    "https://spectrum.ieee.org/feeds/feed.rss",
    "https://www.sciencedaily.com/rss/top/technology.xml",
    "https://phys.org/rss-feed/nanotech-news/",
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/category/tech/latest/rss",
    "https://arstechnica.com/feed/",
    "https://www.universetoday.com/feed/",
    "https://singularityhub.com/feed/"
]

SWEDISH_SOURCES = ["feber.se", "sweclockers.com"]

# Fallback-bilder (Cyberpunk/Tech/Space)
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1531297461136-82lw9b283993?q=80&w=1000&auto=format&fit=crop"
]

def get_image_from_entry(entry):
    """
    Försöker hitta en GILTIG bild. 
    Om ingen giltig bild hittas, returneras None (så vi kan sätta fallback direkt).
    """
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    forbidden_terms = ['pixel', 'tracker', 'feedburner', 'ad', 'doubleclick', '1x1']

    potential_urls = []

    # 1. Samla alla kandidater
    if 'media_content' in entry: 
        potential_urls.append(entry.media_content[0]['url'])
    if 'media_thumbnail' in entry: 
        potential_urls.append(entry.media_thumbnail[0]['url'])
    if 'links' in entry:
        for link in entry.links:
            if link.type.startswith('image/'): potential_urls.append(link.href)
    
    # 2. Leta i HTML
    content = entry.content[0].value if 'content' in entry else (entry.summary if 'summary' in entry else "")
    if content:
        soup = BeautifulSoup(content, 'html.parser')
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            if src: potential_urls.append(src)

    # 3. Filtrera kandidaterna
    for url in potential_urls:
        url_lower = url.lower()
        
        # Måste se ut som en bild eller komma från en betrodd källa
        has_ext = any(ext in url_lower for ext in valid_extensions)
        is_bad = any(bad in url_lower for bad in forbidden_terms)
        
        if not is_bad:
            # Nikkei-specifik fix: Ignorera bilder utan filändelse om de ser misstänkta ut
            if "nikkei" in str(entry.link).lower() and not has_ext:
                continue
            return url # Returnera första bra bild

    return None # Ingen bra bild hittades

def clean_summary(summary):
    if not summary: return ""
    soup = BeautifulSoup(summary, 'html.parser')
    text = soup.get_text()
    text = text.replace("Continue reading", "").replace("Read more", "").replace("Läs mer", "")
    return text[:220] + "..." if len(text) > 220 else text

def translate_text(text, source_lang='sv'):
    try:
        return GoogleTranslator(source=source_lang, target='en').translate(text)
    except:
        return text 

def generate_pagination_html(current_page, total_pages):
    html = ""
    if current_page > 1:
        prev_link = "index.html" if current_page == 2 else f"page{current_page - 1}.html"
        html += f'<a href="{prev_link}" class="page-btn">&larr; PREV</a>'
    
    for i in range(1, total_pages + 1):
        if i == 1 or i == total_pages or (current_page - 2 <= i <= current_page + 2):
            link = "index.html" if i == 1 else f"page{i}.html"
            active_class = "active" if i == current_page else ""
            html += f'<a href="{link}" class="page-btn {active_class}">{i}</a>'
        elif i == current_page - 3 or i == current_page + 3:
            html += '<span style="color:var(--text-secondary); align-self:center;">...</span>'

    if current_page < total_pages:
        html += f'<a href="page{current_page + 1}.html" class="page-btn">NEXT &rarr;</a>'
    return html

def generate_pages():
    print("Fetching and translating news...")
    all_articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            print(f"Loaded {len(feed.entries)} from {source_name}")
            
            is_swedish = any(s in feed_url for s in SWEDISH_SOURCES)
            
            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                pub_date = entry.published_parsed if 'published_parsed' in entry else time.gmtime()
                
                title = entry.title
                summary = clean_summary(entry.summary if 'summary' in entry else "")
                note_html = ""

                if is_swedish:
                    try:
                        title = translate_text(title)
                        summary = translate_text(summary)
                        note_html = '<span class="lang-note">(Translated from Swedish)</span>'
                    except Exception as e:
                        print(f"Translation failed: {e}")

                # BILD-LOGIK: Hämta bild ELLER tvinga fallback
                found_image = get_image_from_entry(entry)
                final_image = found_image if found_image else random.choice(FALLBACK_IMAGES)

                article = {
                    'title': title,
                    'link': entry.link,
                    'summary': summary + note_html,
                    'image': final_image,
                    'source': source_name,
                    'published': pub_date
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error loading {feed_url}: {e}")

    all_articles.sort(key=lambda x: x['published'], reverse=True)
    
    total_articles = len(all_articles)
    if total_articles == 0: return

    total_pages = math.ceil(total_articles / ARTICLES_PER_PAGE)
    print(f"Total Articles: {total_articles} | Total Pages: {total_pages}")

    with open("template.html", "r", encoding="utf-8") as f:
        template_content = f.read()

    for i in range(total_pages):
        page_num = i + 1
        start_idx = i * ARTICLES_PER_PAGE
        end_idx = start_idx + ARTICLES_PER_PAGE
        page_articles = all_articles[start_idx:end_idx]
        
        cards_html = ""
        for art in page_articles:
            now = time.time()
            try:
                pub_time = time.mktime(art['published'])
                hours_ago = int((now - pub_time) / 3600)
                if hours_ago < 1: time_str = "Just Now"
                elif hours_ago < 24: time_str = f"{hours_ago}h Ago"
                else: days = int(hours_ago / 24); time_str = f"{days}d Ago"
            except: time_str = "Recent"
            
            # Använd bilden som Python valde (som aldrig är tom nu)
            img_src = art['image']
            fallback = random.choice(FALLBACK_IMAGES)

            cards_html += f"""
            <article class="news-card">
                <div class="card-image-wrapper">
                    <img src="{img_src}" 
                         class="card-image" 
                         loading="lazy" 
                         alt="News"
                         onerror="this.onerror=null;this.src='{fallback}';"> 
                    <div class="card-overlay"></div>
                </div>
                <div class="card-content">
                    <div class="card-meta">
                        <div class="source-badge">{art['source'][:25]}</div>
                        <time>{time_str}</time>
                    </div>
                    <h2 class="card-title"><a href="{art['link']}" target="_blank">{art['title']}</a></h2>
                    <p class="ai-summary">{art['summary']}</p>
                    <div class="card-footer">
                        <a href="{art['link']}" target="_blank" class="read-more">FULL STORY &rarr;</a>
                    </div>
                </div>
            </article>
            """

        float_prev = ""
        float_next = ""
        if page_num > 1:
            prev_link = "index.html" if page_num == 2 else f"page{page_num - 1}.html"
            float_prev = f'<a href="{prev_link}" class="floating-nav nav-prev">&larr;</a>'
        if page_num < total_pages:
            next_link = f"page{page_num + 1}.html"
            float_next = f'<a href="{next_link}" class="floating-nav nav-next">&rarr;</a>'

        pagination_html = generate_pagination_html(page_num, total_pages)
        final_html = template_content.replace("<!-- NEWS_PLACEHOLDER -->", cards_html)
        final_html = final_html.replace("<!-- PAGINATION_PLACEHOLDER -->", pagination_html)
        final_html = final_html.replace("<!-- FLOATING_PREV -->", float_prev)
        final_html = final_html.replace("<!-- FLOATING_NEXT -->", float_next)
        
        filename = "index.html" if page_num == 1 else f"page{page_num}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_html)
            
        print(f"Generated {filename}")

if __name__ == "__main__":
    generate_pages()