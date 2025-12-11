import sys
import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- FAKE BROWSER HEADERS (Samma som generator.py) ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def run_test(url):
    print(f"\n{'='*60}")
    print(f"🔎 ANALYZING URL: {url}")
    print(f"{'='*60}\n")

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        print("1. Connecting to website...")
        r = session.get(url, timeout=15, verify=False)
        print(f"   Status Code: {r.status_code}")
        
        if r.status_code != 200:
            print("❌ FAILED TO CONNECT. STOPPING.")
            return

        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        print("   Page content loaded successfully.\n")

        results = []

        # --- LOGIC 1: OPEN GRAPH (STANDARD) ---
        print("--- TEST LOGIC 1: OpenGraph (og:image) ---")
        og = soup.find("meta", property="og:image")
        res1 = og["content"] if og and og.get("content") else None
        if res1: print(f"✅ FOUND: {res1}")
        else: print("❌ NOT FOUND")
        results.append(("Logic 1 (OpenGraph)", res1))

        # --- LOGIC 2: SWECLOCKERS REGEX (CDN) ---
        print("\n--- TEST LOGIC 2: Sweclockers Regex (?l=...) ---")
        # Letar efter cdn.sweclockers.com... följt av ?l=
        pattern_swec = r'(https://cdn\.sweclockers\.com/artikel/bild/\d+\?l=[^"\'\s>]+)'
        matches_swec = re.findall(pattern_swec, html)
        res2 = None
        if matches_swec:
            res2 = max(matches_swec, key=len).replace("&amp;", "&")
            print(f"✅ FOUND: {res2}")
        else:
            print("❌ NOT FOUND")
        results.append(("Logic 2 (Swec Regex)", res2))

        # --- LOGIC 3: JSON-LD (GOOGLE SCHEMA) ---
        print("\n--- TEST LOGIC 3: JSON-LD (Schema.org) ---")
        res3 = None
        scripts = soup.find_all('script', type='application/ld+json')
        for i, script in enumerate(scripts):
            try:
                data = json.loads(script.string)
                # Ofta ligger bilden i en lista eller ett objekt
                if isinstance(data, list): data = data[0]
                
                if 'image' in data:
                    img = data['image']
                    if isinstance(img, dict) and 'url' in img:
                        res3 = img['url']
                    elif isinstance(img, str):
                        res3 = img
                    
                    if res3:
                        print(f"   Found in Script #{i}")
                        break
            except: continue
        
        if res3: print(f"✅ FOUND: {res3}")
        else: print("❌ NOT FOUND")
        results.append(("Logic 3 (JSON-LD)", res3))

        # --- LOGIC 4: AFTONBLADET REGEX ---
        print("\n--- TEST LOGIC 4: Aftonbladet Regex ---")
        pattern_ab = r'(https://images\.aftonbladet-cdn\.se/v2/images/[a-zA-Z0-9\-]+)'
        matches_ab = re.findall(pattern_ab, html)
        res4 = matches_ab[0] if matches_ab else None
        if res4: print(f"✅ FOUND: {res4}")
        else: print("❌ NOT FOUND")
        results.append(("Logic 4 (AB Regex)", res4))

        # --- LOGIC 5: GENERIC IMG TAG SCRAPE ---
        print("\n--- TEST LOGIC 5: Generic HTML Scrape ---")
        res5 = None
        # Letar efter första bästa bild som är stor nog eller heter något vettigt
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            if src.startswith('//'): src = 'https:' + src
            if not src.startswith('http'): continue
            
            # Filter
            if 'logo' in src or 'icon' in src or 'avatar' in src: continue
            if '.svg' in src: continue
            
            res5 = src
            break
            
        if res5: print(f"✅ FOUND (First Guess): {res5}")
        else: print("❌ NOT FOUND")
        results.append(("Logic 5 (Generic)", res5))


        print(f"\n{'='*60}")
        print("🏆 SUMMARY - WHAT WORKS?")
        print(f"{'='*60}")
        
        working_logics = [name for name, url in results if url]
        
        if not working_logics:
            print("💀 CRITICAL: NO LOGIC WORKED FOR THIS URL.")
        else:
            print(f"These logics worked: {', '.join(working_logics)}")
            print("\nRecommended URL to use:")
            # Prioritering
            for name, url in results:
                if url:
                    print(f"👉 {url} (via {name})")
                    break

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        run_test(target_url)
    else:
        print("Error: No URL provided.")