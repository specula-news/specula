import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup

# --- CONFIGURATION: Add your sources here ---
RSS_FEEDS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/category/tech/latest/rss",
    "https://arstechnica.com/feed/"
]

# Fallback image if the RSS feed doesn't provide one
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop"

def get_image_from_entry(entry):
    """Try to find an image in the RSS entry"""
    # 1. Check media_content
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    # 2. Check media_thumbnail
    if 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    # 3. Parse HTML content to find <img src="...">
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
    """Remove HTML tags from summary for a clean look"""
    soup = BeautifulSoup(summary, 'html.parser')
    text = soup.get_text()
    return text[:200] + "..." if len(text) > 200 else text

def generate_html():
    print("Fetching news...")
    all_articles = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Loaded {len(feed.entries)} articles from {feed.feed.title if 'title' in feed.feed else feed_url}")
            
            for entry in feed.entries[:5]: # Take top 5 from each source
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'summary': clean_summary(entry.summary if 'summary' in entry else ""),
                    'image': get_image_from_entry(entry),
                    'source': feed.feed.title if 'title' in feed.feed else "News",
                    'published': entry.published_parsed if 'published_parsed' in entry else time.gmtime()
                }
                all_articles.append(article)
        except Exception as e:
            print(f"Error loading {feed_url}: {e}")

    # Sort by date (newest first)
    all_articles.sort(key=lambda x: x['published'], reverse=True)

    # Generate HTML cards
    cards_html = ""
    for art in all_articles:
        # Calculate "Hours Ago"
        now = time.time()
        pub_time = time.mktime(art['published'])
        hours_ago = int((now - pub_time) / 3600)
        time_str = f"{hours_ago}h Ago" if hours_ago > 0 else "Just Now"

        card = f"""
        <article class="news-card">
            <div class="card-image-wrapper">
                <img src="{art['image']}" class="card-image" loading="lazy" alt="News Image">
                <div class="card-overlay"></div>
            </div>
            <div class="card-content">
                <div class="card-meta">
                    <div class="source-badge">
                        {art['source']}
                    </div>
                    <time>{time_str}</time>
                </div>
                <h2 class="card-title"><a href="{art['link']}" target="_blank">{art['title']}</a></h2>
                <p class="ai-summary">
                    {art['summary']}
                </p>
                <div class="card-footer">
                    <a href="{art['link']}" target="_blank" class="read-more">FULL STORY &rarr;</a>
                </div>
            </div>
        </article>
        """
        cards_html += card

    # Read template and replace
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    final_html = template.replace("<!-- NEWS_PLACEHOLDER -->", cards_html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print("Success! index.html generated.")

if __name__ == "__main__":
    generate_html()