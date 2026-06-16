import json
import urllib.request
import urllib.parse
import re
import sys

# We strictly scrape the human-facing public table now. No more unstable JSON APIs.
URL = "https://travel.gc.ca/travelling/advisories"

def clean_html(raw_html):
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def determine_color(advisory_text):
    text = advisory_text.lower()
    if "avoid all travel" in text: return "#dc3545" 
    elif "avoid non-essential travel" in text: return "#fd7e14" 
    elif "high degree of caution" in text: return "#ffc107" 
    elif "normal security precautions" in text: return "#28a745" 
    return "#cccccc"

def main():
    print("Scraping live HTML directly from travel.gc.ca...")
    html = ""
    
    # 1. Try a direct connection first
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            print("✅ Direct connection successful.")
    except Exception as e:
        print(f"⚠️ Direct connection blocked ({e}). Routing through proxy...")
        
        # 2. If GitHub is blocked, bounce the request off a proxy
        try:
            proxy_url = f"https://api.allorigins.win/get?url={urllib.parse.quote(URL)}"
            req = urllib.request.Request(proxy_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode())
                html = data.get("contents", "")
                print("✅ Proxy connection successful.")
        except Exception as e2:
            print(f"❌ CRITICAL: Proxy also failed. Error: {e2}")
            sys.exit(1)

    # 3. Hunt for the country rows inside the HTML table
    pattern = r'<a [^>]*href="[^"]*/destinations/([^"]+)"[^>]*>([^<]+)</a>\s*</td>\s*<td[^>]*>(.*?)</td>'
    matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
    
    if not matches:
        print("❌ Regex failed to find table data. The website layout may have changed.")
        sys.exit(1)
        
    clean_database = {}
    
    # 4. Clean the text and assign the map colors
    for url_slug, country_name, advisory_text in matches:
        text_clean = clean_html(advisory_text)
        
        clean_database[country_name.strip().upper()] = {
            "name": country_name.strip(),
            "advisory_text": text_clean,
            "color": determine_color(text_clean),
            "url_slug": url_slug.strip()
        }
        
    # 5. Save the flawless JSON file for your map to read
    with open("advisories.json", "w", encoding="utf-8") as f:
        json.dump(clean_database, f, indent=4)
        
    print(f"Success! Saved {len(clean_database)} countries to advisories.json.")

if __name__ == "__main__":
    main()

