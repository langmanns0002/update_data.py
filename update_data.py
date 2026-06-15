import json
import re
import sys
# We import our new disguise tool
from curl_cffi import requests

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
    print("Disguising automated request as Google Chrome...")
    
    try:
        # impersonate="chrome" perfectly mimics a human browser fingerprint to bypass Cloudflare
        response = requests.get(RAW_URL, impersonate="chrome", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Target rejected connection. Status Code: {response.status_code}")
            sys.exit(1)
            
        data = response.json()
        print("✅ Success! Bypassed Cloudflare and secured live data.")
        
    except Exception as e:
        print(f"\n❌ CRITICAL: Connection failed. \nError: {e}")
        sys.exit(1)

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
