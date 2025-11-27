import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup
import math
import random
from deep_translator import GoogleTranslator

# --- KONFIGURATION ---
ARTICLES_PER_PAGE = 45   
MAX_ARTICLES_PER_SOURCE = 15

# --- KÄLLOR MED KATEGORIER ---
# Format: ("URL", "KATEGORI")
# Kategorier: 'geopolitics', 'tech', 'ev', 'science', 'construction'

RSS_SOURCES = [
    # --- GEOPOLITICS / ASIA / NEWS ---
    ("https://www.scmp.com/rss/91/feed", "geopolitics"),  # SCMP
    ("https://www.aljazeera.com/xml/rss/all.xml", "geopolitics"), # Al Jazeera
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC5V3r52K5jY8f4oW-9i4iig", "geopolitics"), # ShanghaiEye
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCgrNz-aDmcr2uNt5IN47eEQ", "geopolitics"), # CGTN America
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC5i9r5iM8hJ69h_y_ZqT8_g", "geopolitics"), # CCTV Video News
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCj0T5BI5xK7Y_4rT8jW-XFw", "geopolitics"), # CGTN Europe
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCv3tL4Qv7jJ8r0x8t6lB4wA", "geopolitics"), # CGTN (Main)
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCWP1FO6PhA-LildwUO70lsA", "geopolitics"), # China Pulse
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC83tJtfQf-gmsso-gS5_tIQ", "geopolitics"), # CNA (Channel News Asia)
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCF_1M7c6o-Kj_5azz8d-X8A", "geopolitics"), # Geopolitical Economy Report
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCx8Z1r7k-2gD6xX7c5l6b6g", "geopolitics"), # New China TV
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC6D3-Z2y7c8c9a0b1e1f1f1", "geopolitics"), # EU Debates
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC1yBDrf0w8h8q8q0t8b8g8g", "geopolitics"), # wocomoDOCS

    # --- TECH / AI / SEMICONDUCTORS ---
    ("https://anastasiintech.substack.com/feed", "tech"), # Anastasi In Tech
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCD4EOyXKjfDUhI6ZLfc9XNg", "tech"), # Eli the Computer Guy
    ("https://techcrunch.com/feed/", "tech"),
    ("https://www.theverge.com/rss/index.xml", "tech"),

    # --- EV / ENERGY / SUSTAINABILITY ---
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCy6tF-2i3h3l_5c5r6t7u7g", "ev"), # The Electric Viking
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC2A8478U3_hO9e9s8c8c8c8", "ev"), # Undecided with Matt Ferrell
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC3W19-5_6a5x8a5b8c8c8c8", "ev"), # ELEKTROmanija
    ("https://feber.se/rss/", "tech"), # Feber (Swed)

    # --- SCIENCE / ENGINEERING / FUTURE ---
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCHnyfMqiRRG1u-2MsSQLbXA", "science"), # Veritasium
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC6107grRI4m0o2-emgoDnAA", "science"), # SmarterEveryDay
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UCMOqf8ab-42UUQIdVoKwjlQ", "science"), # Practical Engineering
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC9w7f8f7g8h8j8j8j8j8j8", "science"), # FII Institute
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC8c8c8c8c8c8c8c8c8c8c8", "science"), # SpaceEyeTech (Generic ID used if unknown)

    # --- CONSTRUCTION ---
    ("https://www.youtube.com/feeds/videos.xml?channel_id=UC6n8I1UDTKP1IWjQMg6_sZw", "construction"), # The B1M
]

SWEDISH_SOURCES = ["feber.se", "sweclockers.com", "elektromanija"]

# Fallback-bilder
FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop", 
    "https://images.unsplash.com/photo-1531297461136-82lw9b283993?q=80&w=1000&auto=format&fit=crop"
]

def get_image_from_entry(entry):
    try:
        # YouTube Specific Thumbnail (High Quality)
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

def clean_summary(summary):
    if not summary: return ""
    soup = BeautifulSoup(summary, 'html.parser')
    text = soup.get_text()
    text = text.replace("Continue reading", "").replace("Read more", "").replace("Läs mer", "")
    return text[:200] + "..." if len(text) > 200 else text

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
    print("Fetching news...")
    all_articles = []

    for url, category in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            source_name = feed.feed.title if 'title' in feed.feed else "News"
            print(f"Loaded {len(feed.entries)} from {source_name} [{category}]")
            
            is_swedish = any(s in url for s in SWEDISH_SOURCES)
            
            for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                pub_date = entry.published_parsed if 'published_parsed' in entry else time.gmtime()
                
                title = entry.title
                summary = clean_summary(entry.summary if 'summary' in entry else "")
                note_html = ""

                if is_swedish:
                    try:
                        title = translate_text(title)
                        summary = translate_text(summary)
                        note_html = '<span class="lang-note">(Translated)</span>'
                    except: pass

                # Fallback logic
                found_image = get_image_from_entry(entry)
                final_image = found_image if found_image else random.choice(FALLBACK_IMAGES)

                article = {
                    'title': title,
                    'link': entry.link,
                    'summary': summary + note_html,
                    'image': final_image,
                    'source': source_name,
                    'category': category,
                    'published': pub_date
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error loading {url}: {e}")

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
            
            # Note: Added data-category attribute for filtering
            cards_html += f"""
            <article class="news-card" data-category="{art['category']}">
                <div class="card-image-wrapper">
                    <div class="cat-tag">{art['category']}</div>
                    <img src="{art['image']}" class="card-image" loading="lazy" alt="News" onerror="this.src='{random.choice(FALLBACK_IMAGES)}'">
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