import json
import urllib.request
import re
import sys

RAW_JSON_URL = "https://data.international.gc.ca/travel-voyage/index-alpha-eng.json"
HTML_PAGE_URL = "https://travel.gc.ca/travelling/advisories"

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

def fetch_json_api():
    """Attempt 1: Try getting the raw JSON via Wayback Machine."""
    print("Attempt 1: Querying Wayback Machine for JSON API...")
    try:
        archive_api = f"http://archive.org/wayback/available?url={RAW_JSON_URL}"
        req = urllib.request.Request(archive_api, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            archive_info = json.loads(response.read().decode())
            
        if archive_info.get("archived_snapshots", {}).get("closest", {}).get("available"):
            snapshot_url = archive_info["archived_snapshots"]["closest"]["url"]
            parts = snapshot_url.split('/')
            parts[4] = parts[4] + 'id_'
            raw_url = '/'.join(parts)
            
            req_raw = urllib.request.Request(raw_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_raw, timeout=20) as response_raw:
                raw_text = response_raw.read().decode('utf-8')
                if not raw_text.strip():
                    raise ValueError("Wayback returned an empty file.")
                
                parsed = json.loads(raw_text)
                if "data" in parsed:
                    return parsed["data"]
    except Exception as e:
        print(f"⚠️ JSON API Attempt failed: {e}")
    return None

def fetch_html_scraper():
    """Attempt 2: Directly scrape the official Canada Travel HTML page."""
    print("Attempt 2: Scraping the official HTML table...")
    try:
        req = urllib.request.Request(HTML_PAGE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8')
            
        # Regex designed to extract the Country Name and Risk Level from the HTML table
        pattern = r'<a [^>]*href="[^"]*/destinations/([^"]+)"[^>]*>([^<]+)</a>\s*</td>\s*<td[^>]*>(.*?)</td>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        
        if not matches:
            raise ValueError("Regex found no table rows. HTML structure may have changed.")
            
        database = {}
        for url_slug, country_name, advisory_text in matches:
            clean_advisory = clean_html(advisory_text)
            database[url_slug.strip().upper()] = {
                "name": country_name.strip(),
                "advisory_text": clean_advisory,
                "color": determine_color(clean_advisory),
                "url_slug": url_slug.strip()
            }
        return database
    except Exception as e:
        print(f"⚠️ HTML Scraper failed: {e}")
    return None

def main():
    print("Initializing Data Retrieval...")
    
    clean_database = {}
    
    # Try getting the JSON first
    raw_data = fetch_json_api()
    if raw_data:
        print("✅ Data secured via JSON API.")
        for code, info in raw_data.items():
            if not isinstance(info, dict): continue 
            eng_data = info.get("eng", {})
            country_name = eng_data.get("name", "")
            if not country_name: continue
            
            raw_advisory = eng_data.get("advisory-text", "")
            clean_advisory = clean_html(raw_advisory)
            
            clean_database[code] = {
                "name": country_name,
                "advisory_text": clean_advisory,
                "color": determine_color(clean_advisory),
                "url_slug": eng_data.get("url", code.lower())
            }
    else:
        # Fallback to the HTML Scraper
        scraped_data = fetch_html_scraper()
        if scraped_data:
            print("✅ Data secured via HTML Scraper.")
            clean_database = scraped_data
        else:
            print("\n❌ CRITICAL: Both JSON and HTML methods failed.")
            sys.exit(1)

    with open("advisories.json", "w", encoding="utf-8") as f:
        json.dump(clean_database, f, indent=4)
        
    print(f"Success! Saved {len(clean_database)} countries to advisories.json.")

if __name__ == "__main__":
    main()
