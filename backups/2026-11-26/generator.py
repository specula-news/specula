#!/usr/bin/env python3
"""
SPECULA generator — v8.0

Fetches every source in sources.py (RSS/Atom feeds and YouTube channels) and writes three
data files into the output folder (default: ./data):

    news.json    all articles (loaded by the site and by admin.html)
    meta.json    tiny file: when the feed was built (the site polls it for "Fresh stories")
    status.json  per-source health report + caches (read by admin.html)

On GitHub, the "Update News" Action pushes that folder to the repo's `data` branch.
The website (site/index.html on Netlify) loads the files from there at runtime,
so the site itself never has to be rebuilt or redeployed when the news changes.

Usage:
    python generator.py                    # normal run (what GitHub Actions does)
    python generator.py --out data         # choose the output folder
    python generator.py --only "Electrek"  # test one or more sources by name (writes nothing)
    python generator.py --no-scrape        # never download article pages to look for images
"""
import argparse
import calendar
import concurrent.futures
import html as htmlmod
import json
import os
import re
import sys
import threading
import time
import warnings
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import feedparser
import requests
import urllib3
from bs4 import BeautifulSoup

try:
    from bs4 import MarkupResemblesLocatorWarning
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
except ImportError:
    pass

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_ACTIVE = True
except ImportError:
    TRANSLATOR_ACTIVE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION -----------------------------------------------------------
VERSION = "8.0"
MAX_ARTICLES = 10          # newest items taken from each web feed
MAX_VIDEOS = 5             # newest videos taken from each YouTube channel
TOTAL_LIMIT = 2000         # max articles written to news.json / index.html
MAX_AGE_DAYS = 90          # drop anything older than this
SKIP_SHORTS = True         # ignore YouTube Shorts
TRANSLATE_LANGS = {"sv"}   # source languages whose headlines get translated
TRANSLATE_TARGET = "en"
KEEP_ON_FAILURE = True     # if a source fails, keep its articles from the previous run
WORKERS = 12
FEED_TIMEOUT = 15
PAGE_TIMEOUT = 10
SUMMARY_LEN = 280

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "data")   # changed with --out

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,sv;q=0.8",
    "Referer": "https://www.google.com/",
}

LOCK = threading.Lock()
_local = threading.local()
SCRAPE_PAGES = True


def p(name):
    """Path of a data file in the output folder."""
    return os.path.join(OUT_DIR, name)


def legacy(name):
    """Path of a data file in the repo root (where v7 kept them) — only read, as a cache fallback."""
    return os.path.join(BASE_DIR, name)


def sess():
    """One requests.Session per worker thread (Session is not thread-safe)."""
    s = getattr(_local, "session", None)
    if s is None:
        s = requests.Session()
        s.headers.update(HEADERS)
        retry = urllib3.util.Retry(total=2, backoff_factor=0.6, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET", "HEAD"))
        adapter = requests.adapters.HTTPAdapter(max_retries=retry, pool_maxsize=4)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _local.session = s
    return s


def short_err(e):
    msg = str(e) or e.__class__.__name__
    msg = re.sub(r"\s+", " ", msg)
    if "Max retries exceeded" in msg:
        m = re.search(r"\(Caused by (\w+)", msg)
        msg = "Connection failed" + (f" ({m.group(1)})" if m else "")
    return msg[:160]


# --- PREVIOUS RUN (cache) ----------------------------------------------------
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_status():
    """Previous status.json (output folder first, then the old v7 location in the repo root)."""
    for path in (p("status.json"), legacy("status.json")):
        data = load_json(path, None)
        if isinstance(data, dict):
            return data
    return {}


def _embedded_from_index():
    """Read the article list embedded in an old v7 index.html (only used as a one-time cache fallback)."""
    try:
        with open(legacy("index.html"), encoding="utf-8") as f:
            s = f.read()
    except Exception:
        return []
    m = re.search(r'<script id="news-data" type="application/json">(.*?)</script>', s, re.S)
    raw = m.group(1) if m else None
    if raw is None:
        i = s.find("const newsData = ")
        if i == -1:
            return []
        j = s.find(";</script>", i)
        raw = s[i + len("const newsData = "):j]
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def load_previous():
    """Pick whichever previous copy (data/news.json, or the old root news.json / index.html) is newest."""
    best = []
    for data in (load_json(p("news.json"), []), load_json(legacy("news.json"), []), _embedded_from_index()):
        if not isinstance(data, list) or not data:
            continue
        newest = max((a.get("timestamp", 0) for a in data if isinstance(a, dict)), default=0)
        best_newest = max((a.get("timestamp", 0) for a in best), default=0)
        if newest > best_newest:
            best = [a for a in data if isinstance(a, dict) and a.get("link")]
    return best


PREV = {}
CHANNEL_IDS = {}


# --- TEXT & URL HELPERS ------------------------------------------------------
TRACKING = re.compile(r"^(utm_\w+|fbclid|gclid|mc_cid|mc_eid|ref_src|cmpid|ncid|taid|sr_share|smid|rss)$", re.I)


def clean_link(url):
    try:
        u = urlparse(url.strip())
        q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True) if not TRACKING.match(k)]
        return urlunparse(u._replace(query=urlencode(q), fragment=""))
    except Exception:
        return url


def clean_text(raw):
    if not raw:
        return ""
    txt = str(raw)
    if "<" in txt and ">" in txt:
        txt = BeautifulSoup(txt, "html.parser").get_text(separator=" ")
    txt = htmlmod.unescape(txt)
    txt = " ".join(txt.split())
    return re.sub(r"\s+([,.;:!?)])", r"\1", txt)


def truncate(txt, n=SUMMARY_LEN):
    if len(txt) <= n:
        return txt
    cut = txt[:n].rsplit(" ", 1)[0].rstrip(",.;:–-— ")
    return cut + "…"


def fix_url(u, base):
    if not u:
        return None
    u = str(u).strip().replace("&amp;", "&")
    if u.startswith("//"):
        u = "https:" + u
    return urljoin(base, u)


BAD_IMG = re.compile(r"(feedburner|/pixel|tracking|spacer|blank\.gif|gravatar\.com|/avatars?/|emoji|1x1|doubleclick|\.svg(\?|$)|data:image)", re.I)


def good_img(u):
    return bool(u) and u.startswith(("http://", "https://")) and not BAD_IMG.search(u)


def entry_date(entry):
    """UTC epoch seconds from a feedparser entry (feedparser's *_parsed tuples are UTC)."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = entry.get(key)
        if t:
            try:
                return float(calendar.timegm(t))
            except Exception:
                pass
    return None


# --- IMAGE STRATEGIES ---------------------------------------------------------
def strat_og(soup, html, url):
    m = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
    return urljoin(url, m["content"]) if m and m.get("content") else None


def strat_twitter(soup, html, url):
    m = soup.find("meta", attrs={"name": "twitter:image"}) or soup.find("meta", attrs={"property": "twitter:image"})
    return urljoin(url, m["content"]) if m and m.get("content") else None


def strat_jsonld(soup, html, url):
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue
        for item in (data if isinstance(data, list) else [data]):
            if not isinstance(item, dict):
                continue
            for node in [item] + list(item.get("@graph", []) if isinstance(item.get("@graph"), list) else []):
                img = node.get("image") if isinstance(node, dict) else None
                if isinstance(img, list) and img:
                    img = img[0]
                if isinstance(img, dict):
                    img = img.get("url")
                if isinstance(img, str) and img:
                    return urljoin(url, img)
    return None


def strat_swec(soup, html, url):
    m = re.findall(r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[^"\'\s>]+)', html)
    return max(m, key=len).replace("&amp;", "&") if m else None


def strat_afton(soup, html, url):
    m = re.findall(r"(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)", html)
    return m[0] if m else None


def strat_wordpress(soup, html, url):
    img = soup.find("img", class_=re.compile("wp-post-image"))
    return urljoin(url, img.get("src")) if img and img.get("src") else None


def strat_lazy(soup, html, url):
    img = soup.find("img", attrs={"data-src": True})
    return urljoin(url, img["data-src"]) if img else None


def strat_hero(soup, html, url):
    for cls in ["hero", "featured", "main-image", "article-image", "post-thumbnail", "lead"]:
        div = soup.find(class_=re.compile(cls, re.I))
        if div:
            img = div.find("img")
            if img and (img.get("src") or img.get("data-src")):
                return urljoin(url, img.get("src") or img.get("data-src"))
    return None


def strat_srcset(soup, html, url):
    imgs = soup.find_all("img", srcset=True)
    if not imgs:
        return None
    best = max(imgs, key=lambda i: len(i["srcset"]))
    last = best["srcset"].split(",")[-1].strip().split(" ")[0]
    return urljoin(url, last) if last else None


def strat_largest(soup, html, url):
    target = soup.find("article")
    if target:
        img = target.find("img", src=True)
        if img:
            return urljoin(url, img["src"])
    imgs = soup.find_all("img", src=True)
    return urljoin(url, imgs[0]["src"]) if imgs else None


STRATEGY_MAP = {
    "og": strat_og, "twitter": strat_twitter, "jsonld": strat_jsonld,
    "swec": strat_swec, "afton": strat_afton,
    "wordpress": strat_wordpress, "lazy": strat_lazy,
    "hero": strat_hero, "srcset": strat_srcset,
    "largest": strat_largest, "first_img": strat_largest,  # admin "First Image" == largest
}
FALLBACK_ORDER = ["og", "twitter", "jsonld", "wordpress", "hero", "lazy"]


def rss_image(entry, base):
    for key in ("media_content", "media_thumbnail"):
        for m in entry.get(key) or []:
            typ, medium = (m.get("type") or ""), (m.get("medium") or "")
            if typ.startswith(("video", "audio")) or medium in ("video", "audio"):
                continue
            u = fix_url(m.get("url"), base)
            if good_img(u):
                return u
    for enc in entry.get("enclosures") or []:
        if (enc.get("type") or "").startswith("image"):
            u = fix_url(enc.get("href") or enc.get("url"), base)
            if good_img(u):
                return u
    blobs = [c.get("value", "") for c in (entry.get("content") or []) if isinstance(c, dict)]
    blobs.append(entry.get("summary", "") or "")
    for v in blobs:
        if v and "<img" in v:
            for img in BeautifulSoup(v, "html.parser").find_all("img"):
                u = fix_url(img.get("src") or img.get("data-src"), base)
                if good_img(u):
                    return u
    return None


def fetch_page(url):
    r = sess().get(url, timeout=PAGE_TIMEOUT, verify=False)
    if r.status_code >= 400:
        return None
    return r.text


def get_image(entry, source, link, prev):
    # 0. Seen in the previous run → reuse its result (avoids re-downloading every article page)
    if prev is not None:
        imgs = prev.get("images") or []
        return imgs[0] if imgs and good_img(imgs[0]) and "unsplash.com" not in imgs[0] else ""

    page = None
    forced = source.get("image_strategy")

    # 1. Forced strategy (set via the admin analyzer)
    if forced in STRATEGY_MAP and SCRAPE_PAGES:
        try:
            page = fetch_page(link)
            if page:
                u = STRATEGY_MAP[forced](BeautifulSoup(page, "html.parser"), page, link)
                if good_img(u):
                    return u
        except Exception:
            pass

    # 2. Image inside the feed itself
    u = rss_image(entry, link)
    if u:
        return u

    # 3. Look at the article page
    if not SCRAPE_PAGES:
        return ""
    try:
        page = page or fetch_page(link)
        if page:
            soup = BeautifulSoup(page, "html.parser")
            for name in FALLBACK_ORDER:
                u = STRATEGY_MAP[name](soup, page, link)
                if good_img(u):
                    return u
    except Exception:
        pass
    return ""


# --- TRANSLATION --------------------------------------------------------------
def translate_title(title, lang, prev):
    """Returns (display_title, original_or_None)."""
    if not TRANSLATOR_ACTIVE or lang not in TRANSLATE_LANGS or not title:
        return title, None
    if prev and prev.get("title_original") == title and prev.get("title"):
        return prev["title"], title
    try:
        out = GoogleTranslator(source=lang, target=TRANSLATE_TARGET).translate(title)
        if out and out.strip() and out.strip().lower() != title.lower():
            return out.strip(), title
    except Exception:
        pass
    return title, None


# --- WEB FEEDS ----------------------------------------------------------------
def process_feed(source):
    articles, st = [], {"ok": False, "count": 0, "error": ""}
    r = sess().get(source["url"], timeout=FEED_TIMEOUT, verify=False)
    if r.status_code != 200:
        st["error"] = f"HTTP {r.status_code}"
        return articles, st
    feed = feedparser.parse(r.content)
    if not feed.entries:
        ctype = r.headers.get("content-type", "")
        st["error"] = "Not an RSS/Atom feed (got a web page)" if "html" in ctype else "Feed has no entries"
        return articles, st

    now = time.time()
    for entry in feed.entries[:MAX_ARTICLES]:
        raw_link = entry.get("link") or ""
        if not raw_link:
            continue
        link = clean_link(urljoin(source["url"], raw_link))
        prev = PREV.get(link)
        ts = entry_date(entry)
        if ts is None:
            ts = prev["timestamp"] if prev else now
        ts = min(ts, now)
        if now - ts > MAX_AGE_DAYS * 86400:
            continue

        raw_title = clean_text(entry.get("title", ""))
        if not raw_title:
            continue
        title, original = translate_title(raw_title, source.get("lang"), prev)
        summary = truncate(clean_text(entry.get("summary") or entry.get("description") or ""))
        img = get_image(entry, source, link, prev)

        art = {
            "title": title, "link": link, "images": [img] if img else [],
            "summary": summary if summary != raw_title else "",
            "category": source["cat"], "filter_tag": source.get("filter_tag", ""),
            "source": source.get("source_name", "News"), "lang": source.get("lang", "en"),
            "timestamp": ts, "is_video": False, "feed_url": source["url"],
        }
        if original:
            art["title_original"] = original
        articles.append(art)

    st.update(ok=True, count=len(articles))
    if not articles:
        st["error"] = f"No items newer than {MAX_AGE_DAYS} days"
    return articles, st


# --- YOUTUBE ------------------------------------------------------------------
YT_ID = re.compile(r"(?:v=|/shorts/|youtu\.be/|/embed/|/live/)([\w-]{11})")


def channel_key(url):
    return url.split("/videos")[0].split("/featured")[0].rstrip("/").lower()


def get_channel_id(source):
    """Channel ID for a YouTube channel URL (cached in status.json between runs)."""
    if source.get("channel_id"):
        return source["channel_id"]
    url = source["url"]
    m = re.search(r"channel_id=(UC[\w-]{22})", url) or re.search(r"/channel/(UC[\w-]{22})", url)
    if m:
        return m.group(1)
    key = channel_key(url)
    if key in CHANNEL_IDS:
        return CHANNEL_IDS[key]

    cid = None
    try:  # Method 1: read it from the channel page (fast)
        r = sess().get(url, timeout=10, cookies={"CONSENT": "YES+1", "SOCS": "CAI"})
        if r.status_code == 200:
            for pat in (r'"externalId":"(UC[\w-]{22})"', r'<meta itemprop="identifier" content="(UC[\w-]{22})"',
                        r'"browseId":"(UC[\w-]{22})"', r'channel_id=(UC[\w-]{22})'):
                m = re.search(pat, r.text)
                if m:
                    cid = m.group(1)
                    break
    except Exception:
        pass
    if not cid and yt_dlp:  # Method 2: yt-dlp (robust but slower)
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True, "playlistend": 1}) as ydl:
                info = ydl.extract_info(url, download=False)
                cid = info.get("channel_id")
        except Exception:
            pass
    if cid:
        with LOCK:
            CHANNEL_IDS[key] = cid
    return cid


def make_video(source, vid, title, desc, ts, prev):
    return {
        "title": clean_text(title) or "Video", "link": f"https://www.youtube.com/watch?v={vid}",
        "images": [f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"],
        "summary": truncate(clean_text(desc)), "category": source["cat"], "filter_tag": source.get("filter_tag", ""),
        "source": source.get("source_name", "YouTube"), "lang": source.get("lang", "en"),
        "timestamp": ts, "is_video": True, "video_id": vid, "feed_url": source["url"],
    }


def get_video_info(source):
    """RSS first (exact publish time), yt-dlp as a fallback."""
    videos, st = [], {"ok": False, "count": 0, "error": ""}
    now = time.time()
    rss_url = source["url"] if "youtube.com/feeds" in source["url"] else None
    if not rss_url:
        cid = get_channel_id(source)
        if cid:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        else:
            st["error"] = "Could not find the channel ID"

    if rss_url:
        try:
            r = sess().get(rss_url, timeout=FEED_TIMEOUT)
            if r.status_code == 200:
                feed = feedparser.parse(r.content)
                for entry in feed.entries:
                    if len(videos) >= MAX_VIDEOS:
                        break
                    link = entry.get("link", "")
                    if SKIP_SHORTS and "/shorts/" in link:
                        continue
                    vid = entry.get("yt_videoid") or (YT_ID.search(link).group(1) if YT_ID.search(link) else None)
                    if not vid:
                        continue
                    prev = PREV.get(f"https://www.youtube.com/watch?v={vid}")
                    ts = entry_date(entry) or (prev["timestamp"] if prev else now)
                    if now - ts > MAX_AGE_DAYS * 86400:
                        continue
                    desc = entry.get("summary") or entry.get("media_description") or ""
                    videos.append(make_video(source, vid, entry.get("title", ""), desc, min(ts, now), prev))
                st["error"] = ""
            else:
                st["error"] = f"RSS HTTP {r.status_code}"
        except Exception as e:
            st["error"] = short_err(e)

    if not videos and yt_dlp and (not rss_url or st["error"]):
        try:
            opts = {"quiet": True, "no_warnings": True, "ignoreerrors": True, "extract_flat": True, "playlistend": MAX_VIDEOS}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(source["url"], download=False) or {}
            for entry in info.get("entries") or []:
                if not entry or not entry.get("id"):
                    continue
                vid = entry["id"]
                prev = PREV.get(f"https://www.youtube.com/watch?v={vid}")
                ts = entry.get("timestamp")
                if not ts and entry.get("upload_date"):
                    try:
                        ts = datetime.strptime(entry["upload_date"], "%Y%m%d").replace(tzinfo=timezone.utc).timestamp()
                    except Exception:
                        ts = None
                ts = ts or (prev["timestamp"] if prev else now - 86400)
                videos.append(make_video(source, vid, entry.get("title", ""), entry.get("description") or "", min(ts, now), prev))
            if videos:
                st["error"] = ""
        except Exception as e:
            st["error"] = st["error"] or short_err(e)

    st["ok"] = bool(videos) or (bool(rss_url) and not st["error"])
    st["count"] = len(videos)
    return videos, st


# --- RUN ----------------------------------------------------------------------
def load_sources():
    sys.path.insert(0, BASE_DIR)
    from sources import SOURCES  # noqa: E402
    out = []
    for s in SOURCES:
        if not isinstance(s, dict) or not s.get("url"):
            continue
        if s.get("disabled") in (True, 1, "1", "true", "yes"):
            continue
        s = dict(s)
        s.setdefault("type", "video" if "youtube.com" in s["url"] else "web")
        s.setdefault("cat", "tech")
        s.setdefault("source_name", urlparse(s["url"]).hostname or "News")
        out.append(s)
    return out


def fetch_source(source):
    t0 = time.time()
    try:
        if source["type"] == "video":
            arts, st = get_video_info(source)
        else:
            arts, st = process_feed(source)
    except Exception as e:
        arts, st = [], {"ok": False, "count": 0, "error": short_err(e)}
    st["ms"] = int((time.time() - t0) * 1000)
    return arts, st


def write_json(name, obj, compact=True):
    """Write atomically (temp file + rename) so a crash never leaves half a file behind."""
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = p(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p(name))


def main():
    global PREV, CHANNEL_IDS, SCRAPE_PAGES, WORKERS, OUT_DIR
    ap = argparse.ArgumentParser(description="Build the SPECULA news feed.")
    ap.add_argument("--out", default="data", help="output folder for news.json / meta.json / status.json (default: data)")
    ap.add_argument("--only", nargs="+", help="only fetch sources whose name contains one of these words (test mode, writes nothing)")
    ap.add_argument("--no-scrape", action="store_true", help="never download article pages to find images")
    ap.add_argument("--workers", type=int, default=WORKERS)
    args = ap.parse_args()
    SCRAPE_PAGES = not args.no_scrape
    WORKERS = max(1, args.workers)
    OUT_DIR = os.path.abspath(args.out if os.path.isabs(args.out) else os.path.join(os.getcwd(), args.out))

    t0 = time.time()
    previous = load_previous()
    PREV = {clean_link(a["link"]): a for a in previous}
    CHANNEL_IDS = dict(load_status().get("channel_ids", {}))

    sources = load_sources()
    if args.only:
        words = [w.lower() for w in args.only]
        sources = [s for s in sources if any(w in s["source_name"].lower() for w in words)]
    print(f"SPECULA generator {VERSION} — {len(sources)} sources, {len(PREV)} cached articles, translator {'on' if TRANSLATOR_ACTIVE else 'off'}")

    results, report = [], []
    now = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_source, s): s for s in sources}
        for fut in concurrent.futures.as_completed(futures):
            s = futures[fut]
            arts, st = fut.result()
            kept = 0
            if not st["ok"] and KEEP_ON_FAILURE and not args.only:
                old = [a for a in previous if a.get("feed_url") == s["url"] and now - a.get("timestamp", 0) < MAX_AGE_DAYS * 86400]
                if old:
                    arts, kept = old, len(old)
            results.extend(arts)
            report.append({
                "name": s["source_name"], "url": s["url"], "cat": s["cat"], "type": s["type"],
                "ok": st["ok"], "count": st["count"], "kept": kept, "error": st["error"], "ms": st.get("ms", 0),
            })
            mark = "✓" if st["ok"] else ("↺" if kept else "✗")
            print(f"  {mark} {s['source_name'][:34]:<34} {st['count']:>3}  {st['error']}")

    # Newest first, de-duplicate by link and by headline
    results.sort(key=lambda a: a.get("timestamp", 0), reverse=True)
    final, seen_links, seen_titles = [], set(), set()
    for a in results:
        tkey = (re.sub(r"\W+", "", a["title"].lower())[:90], a.get("is_video", False))
        if a["link"] in seen_links or (tkey[0] and tkey in seen_titles):
            continue
        seen_links.add(a["link"])
        seen_titles.add(tkey)
        a.pop("time_str", None)   # old v7 field, the site computes "x ago" itself
        final.append(a)
    final = final[:TOTAL_LIMIT]

    ok = sum(1 for r in report if r["ok"])
    print(f"Done in {time.time() - t0:.1f}s — {len(final)} articles, {ok}/{len(report)} sources OK")

    if args.only:
        print("(--only test mode: nothing written)")
        return 0
    if not final:
        print("! No articles at all — keeping the previous files untouched.")
        return 1

    meta = {"generated_at": int(now), "count": len(final), "sources_ok": ok, "sources_total": len(report), "generator": VERSION}
    status = {
        "generated_at": int(now),
        "generated_iso": datetime.fromtimestamp(now, timezone.utc).isoformat(timespec="seconds"),
        "generator": VERSION, "duration_s": round(time.time() - t0, 1),
        "articles": len(final), "sources_ok": ok, "sources_total": len(report),
        "sources": sorted(report, key=lambda r: (r["ok"], r["name"].lower())),
        "channel_ids": CHANNEL_IDS,
    }
    write_json("news.json", final)
    write_json("status.json", status, compact=False)
    write_json("meta.json", meta)          # written last: it tells the site that new data is ready
    print(f"Wrote news.json, status.json and meta.json to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
