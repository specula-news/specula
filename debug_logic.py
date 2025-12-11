import sys
import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FAKE BROWSER HEADERS ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,sv;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}

def run_test(url):
    print(f"\n{'='*60}")
    print(f"🔎 EXTENDED ANALYSIS: {url}")
    print(f"{'='*60}\n")

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        print("1. Connecting...")
        r = session.get(url, timeout=15, verify=False)
        print(f"   Status: {r.status_code}")
        
        if r.status_code != 200:
            print("❌ Connection Failed.")
            return

        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # --- LOGIC 1: OPEN GRAPH (STANDARD) ---
        og = soup.find("meta", property="og:image")
        res = og["content"] if og and og.get("content") else None
        results.append(("1. OpenGraph (og:image)", res))

        # --- LOGIC 2: TWITTER CARD ---
        tw = soup.find("meta", attrs={"name": "twitter:image"}) or soup.find("meta", attrs={"property": "twitter:image"})
        res = tw["content"] if tw and tw.get("content") else None
        results.append(("2. Twitter Card", res))

        # --- LOGIC 3: JSON-LD (SCHEMA) ---
        res = None
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list): data = data[0]
                if 'image' in data:
                    img = data['image']
                    if isinstance(img, dict) and 'url' in img: res = img['url']
                    elif isinstance(img, str): res = img
                    if res: break
            except: continue
        results.append(("3. JSON-LD (Schema)", res))

        # --- LOGIC 4: LINK REL=IMAGE_SRC ---
        # Gammal standard som vissa CMS använder
        lnk = soup.find("link", rel="image_src")
        res = lnk["href"] if lnk else None
        results.append(("4. Link Rel=image_src", res))

        # --- LOGIC 5: SWECLOCKERS REGEX (CDN) ---
        # Din specifika regex för ?l= länkar
        pattern = r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[^"\'\s>]+)'
        matches = re.findall(pattern, html)
        res = max(matches, key=len).replace("&amp;", "&") if matches else None
        results.append(("5. Sweclockers Regex (?l=)", res))

        # --- LOGIC 6: SWECLOCKERS HTML STRUCTURE ---
        # Letar i deras specifika div-struktur "article-head__media"
        res = None
        hero_div = soup.find("div", class_="article-head__media")
        if hero_div:
            # Kolla efter source srcset (ofta webp)
            srcs = hero_div.find_all("source")
            for s in srcs:
                srcset = s.get("srcset", "")
                if "cdn.sweclockers" in srcset:
                    # Tar sista URLen i srcset (oftast störst)
                    res = srcset.split(",")[-1].strip().split(" ")[0]
                    break
            if not res:
                img = hero_div.find("img")
                if img: res = img.get("src")
        
        if res and res.startswith("//"): res = "https:" + res
        results.append(("6. Swec HTML Structure", res))

        # --- LOGIC 7: HERO / FEATURED CLASS ---
        # Letar efter divar som heter "hero", "lead", "featured" och tar bild därifrån
        res = None
        for cls in ["hero", "lead", "featured", "article-image", "main-image", "post-thumbnail"]:
            container = soup.find(class_=re.compile(cls, re.I))
            if container:
                img = container.find("img")
                if img and img.get("src"):
                    src = img.get("src")
                    if "avatar" not in src and "icon" not in src:
                        res = urljoin(url, src)
                        break
        results.append(("7. Hero/Featured Class", res))

        # --- LOGIC 8: SRCSET PARSING (High Res) ---
        # Hitta den bild på sidan som har längst 'srcset' attribut (oftast huvudbilden)
        res = None
        all_imgs = soup.find_all("img", srcset=True)
        if all_imgs:
            # Sortera efter längden på srcset (mer data = ofta viktigare bild)
            best_img = max(all_imgs, key=lambda i: len(i["srcset"]))
            srcset = best_img["srcset"]
            # Ta den sista URLen (störst upplösning)
            res = srcset.split(",")[-1].strip().split(" ")[0]
            res = urljoin(url, res)
        results.append(("8. Largest Srcset", res))

        # --- LOGIC 9: AFTONBLADET REGEX ---
        pattern_ab = r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)'
        matches_ab = re.findall(pattern_ab, html)
        res = matches_ab[0] if matches_ab else None
        results.append(("9. Aftonbladet Regex", res))

        # --- SKRIV UT RESULTAT ---
        print("\n🏆 RESULTS:\n")
        working = []
        for name, result in results:
            if result:
                print(f"✅ {name}")
                print(f"   URL: {result}")
                working.append(name)
            else:
                print(f"❌ {name}")
        
        print(f"\n{'='*60}")
        if working:
            print(f"RECOMMENDATION: Use logic '{working[0]}' for this site.")
        else:
            print("FAILED: No image found with any logic.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_test(sys.argv[1])
    else:
        print("No URL provided.")