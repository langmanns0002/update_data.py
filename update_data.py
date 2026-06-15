import json
import urllib.request
import re
import sys

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
    print("Hunting for a clear connection to Canada.ca...")
    
    # We now have 3 different doors to try
    proxies = [
        f"https://api.allorigins.win/raw?url={RAW_URL}",
        f"https://api.codetabs.com/v1/proxy?quest={RAW_URL}",
        f"https://thingproxy.freeboard.io/fetch/{RAW_URL}"
    ]
    
    data = None
    
    for proxy in proxies:
        print(f"Trying proxy: {proxy}")
        req = urllib.request.Request(proxy, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                raw_response = response.read().decode('utf-8')
                
                # Check if it is actually JSON and not a firewall HTML page
                try:
                    parsed_json = json.loads(raw_response)
                    # Make sure the actual country list is inside
                    if "data" in parsed_json or "MEX" in parsed_json:
                        data = parsed_json
                        print("✅ Success! Valid data received.")
                        break
                    else:
                        print("⚠️ Valid JSON, but missing country data. Trying next...")
                except json.JSONDecodeError:
                    print("⚠️ Proxy returned an HTML block page instead of data. Trying next proxy...")
                    
        except Exception as e:
            print(f"⚠️ Proxy failed to connect: {e}")

    # If all 3 proxies fail, exit the script cleanly without breaking your website
    if data is None:
        print("\n❌ CRITICAL: All proxies failed.")
        print("This is normal! Your live map will simply continue using yesterday's data until tomorrow's run succeeds.")
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
