import feedparser
import requests
from bs4 import BeautifulSoup
import json

# ==========================================
# SOURCES
# ==========================================
SOURCES = [
    # Exempel: Lägg till alla dina källor här som i din lista
    {"url": "https://www.youtube.com/@LinusTechTips/videos", "cat": "youtubers", "type": "video", "source_name": "Linus Tech Tips", "lang": "en", "filter_tag": "tech"},
    {"url": "https://www.theverge.com/rss/index.xml", "cat": "tech", "type": "web", "source_name": "The Verge", "lang": "en"},
    # Lägg till resten...
]

# ==========================================
# FUNKTIONER
# ==========================================

def fetch_rss(url):
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source_name": "",
                "cat": "",
                "lang": "",
                "is_video": False,
            })
        return entries
    except Exception as e:
        print(f"RSS Error for {url}: {e}")
        return []

def fetch_youtube_videos(url):
    # För enkelhets skull hämtar vi bara metadata via YouTube RSS (om tillgängligt)
    # Alternativt: använd YouTube API
    try:
        feed = feedparser.parse(url + "/videos?view=2&flow=grid&sort=p&format=5")
        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source_name": "",
                "cat": "",
                "lang": "",
                "is_video": True,
            })
        return entries
    except Exception as e:
        print(f"YouTube Error for {url}: {e}")
        return []

def aggregate_sources():
    aggregated = []
    for source in SOURCES:
        entries = []
        if source["type"] == "web":
            entries = fetch_rss(source["url"])
            for e in entries:
                e["is_video"] = False
        elif source["type"] == "video":
            entries = fetch_youtube_videos(source["url"])
            for e in entries:
                e["is_video"] = True

        for e in entries:
            e["source_name"] = source.get("source_name", "")
            e["cat"] = source.get("cat", "")
            e["lang"] = source.get("lang", "en")
            e["filter_tag"] = source.get("filter_tag", "")

        aggregated.extend(entries)
    return aggregated

# ==========================================
# KÖRNING
# ==========================================
if __name__ == "__main__":
    all_articles = aggregate_sources()
    print(json.dumps(all_articles[:10], indent=2))  # Testa med de första 10
