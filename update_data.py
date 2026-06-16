import json
import re
import sys
import urllib.request

RAW_URL = "https://data.international.gc.ca/travel-voyage/index-alpha-eng.json"

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
    print("Bypassing firewalls using the Internet Archive...")
    
    data = None
    
    try:
        print("Locating the latest secure snapshot...")
        archive_api = f"http://archive.org/wayback/available?url={RAW_URL}"
        req = urllib.request.Request(archive_api, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            archive_info = json.loads(response.read().decode())
            
        if archive_info.get("archived_snapshots", {}).get("closest", {}).get("available"):
            snapshot_url = archive_info["archived_snapshots"]["closest"]["url"]
            
            # Convert the Wayback HTML viewer URL into a Raw Data URL
            # We do this by appending 'id_' to the timestamp section of the URL
            parts = snapshot_url.split('/')
            parts[4] = parts[4] + 'id_'
            raw_snapshot_url = '/'.join(parts)
            
            print(f"Downloading raw data from archive: {raw_snapshot_url}")
            
            req_raw = urllib.request.Request(raw_snapshot_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_raw, timeout=30) as response_raw:
                parsed_json = json.loads(response_raw.read().decode())
                
                if "data" in parsed_json or "MEX" in parsed_json:
                    data = parsed_json
                    print("✅ Success! Live data secured from the Archive.")
    except Exception as e:
        print(f"⚠️ Archive retrieval failed: {e}")

    # If the Archive happens to be down, we abort cleanly so your website doesn't crash
    if data is None:
        print("\n❌ CRITICAL: Could not retrieve data from the Internet Archive.")
        sys.exit(1)

    # Clean the data and prep it for your Leaflet map
    countries_data = data.get("data", data)
    clean_database = {}

    for code, info in countries_data.items():
        if not isinstance(info, dict): continue 
        
        eng_data = info.get("eng", {})
        country_name = eng_data.get("name", "")
        if not country_name: continue
        
        raw_advisory = eng_data.get("advisory-text", "")
        clean_advisory = clean_html(raw_advisory)
        color = determine_color(clean_advisory)
        
        clean_database[code] = {
            "name": country_name,
            "advisory_text": clean_advisory,
            "color": color,
            "url_slug": eng_data.get("url", code.lower())
        }
        
    with open("advisories.json", "w", encoding="utf-8") as f:
        json.dump(clean_database, f, indent=4)
        
    print(f"Success! Saved {len(clean_database)} countries to advisories.json.")

if __name__ == "__main__":
    main()
