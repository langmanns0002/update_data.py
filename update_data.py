import json
import urllib.request
import re

# The official Government of Canada open data endpoint
RAW_URL = "https://data.international.gc.ca/travel-voyage/index-alpha-eng.json"

def clean_html(raw_html):
    """Removes messy HTML tags from the government's advisory text."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def determine_color(advisory_text):
    """Assigns the correct map color based on Canada's official text."""
    text = advisory_text.lower()
    
    if "avoid all travel" in text:
        return "#dc3545" # Red
    elif "avoid non-essential travel" in text:
        return "#fd7e14" # Orange
    elif "high degree of caution" in text:
        return "#ffc107" # Yellow
    elif "normal security precautions" in text:
        return "#28a745" # Green
        
    return "#cccccc" # Default Gray

def main():
    print("Connecting to Global Affairs Canada via proxy...")
    
    # We wrap the API in a proxy to bypass the firewall block on GitHub's servers
    primary_proxy = f"https://api.allorigins.win/raw?url={RAW_URL}"
    req = urllib.request.Request(primary_proxy, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        # Added a strict 30-second timeout so it never hangs for 2 minutes again
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Primary proxy failed: {e}")
        print("Switching to backup proxy...")
        # A reliable fallback just in case the first proxy is busy
        backup_proxy = f"https://api.codetabs.com/v1/proxy?quest={RAW_URL}"
        req2 = urllib.request.Request(backup_proxy, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req2, timeout=30) as response:
            data = json.loads(response.read().decode())
    
    countries_data = data.get("data", data)
    clean_database = {}

    for code, info in countries_data.items():
        # Skip any hidden metadata keys
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
        
    print(f"Success! Cleaned and saved {len(clean_database)} countries to advisories.json.")

if __name__ == "__main__":
    main()
