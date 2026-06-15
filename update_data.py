import json
import re
import sys
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
    print("Initializing Stealth Mode & Proxy Waterfall...")
    
    # We bounce the request off 4 different external servers to hide GitHub's IP address
    proxies = [
        f"https://corsproxy.io/?url={RAW_URL}",
        f"https://api.allorigins.win/raw?url={RAW_URL}",
        f"https://api.codetabs.com/v1/proxy?quest={RAW_URL}",
        # The ultimate failsafe: grabbing the latest live snapshot from the Web Archive
        f"https://web.archive.org/web/latest/{RAW_URL}"
    ]
    
    data = None
    
    for proxy_url in proxies:
        proxy_name = proxy_url.split('/')[2]
        print(f"Bouncing request through: {proxy_name}")
        
        try:
            # We use the Chrome disguise so the proxy servers don't block us either!
            response = requests.get(proxy_url, impersonate="chrome", timeout=20)
            
            if response.status_code == 200:
                try:
                    parsed_json = response.json()
                    # Validate that it contains real country data, not a firewall CAPTCHA page
                    if "data" in parsed_json or "MEX" in parsed_json:
                        data = parsed_json
                        print(f"✅ Success! Live data secured via {proxy_name}.")
                        break
                except Exception:
                    pass
            print("⚠️ Proxy blocked or returned invalid data. Bouncing to the next...")
        except Exception as e:
            print(f"⚠️ Proxy connection failed. Bouncing to the next...")

    # If all 4 proxies get blocked, abort cleanly.
    if data is None:
        print("\n❌ CRITICAL: All bounce proxies were blocked.")
        print("Your map will safely keep using yesterday's data.")
        sys.exit(1)

    # Clean the data and prep it for the website
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
