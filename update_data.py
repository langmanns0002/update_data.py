import json
import urllib.request
import re

# The official Government of Canada open data endpoint
URL = "https://data.international.gc.ca/travel-voyage/index-alpha-eng.json"

def clean_html(raw_html):
    """Removes messy HTML tags from the government's advisory text."""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def determine_color(advisory_text):
    """Assigns the correct map color based on Canada's official text."""
    text = advisory_text.lower()
    
    # Matching Canada's official 4-tier risk levels
    if "avoid all travel" in text:
        return "#dc3545" # Red
    elif "avoid non-essential travel" in text:
        return "#fd7e14" # Orange
    elif "high degree of caution" in text:
        return "#ffc107" # Yellow
    elif "normal security precautions" in text:
        return "#28a745" # Green
        
    return "#cccccc" # Default Gray if no data is found

def main():
    print("Connecting to Global Affairs Canada...")
    
    # Download the live data (using a User-Agent so the firewall allows us in)
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    countries_data = data.get("data", {})
    clean_database = {}

    # Loop through every country in the database
    for code, info in countries_data.items():
        eng_data = info.get("eng", {})
        country_name = eng_data.get("name", "")
        
        raw_advisory = eng_data.get("advisory-text", "")
        clean_advisory = clean_html(raw_advisory)
        
        color = determine_color(clean_advisory)
        
        # Package only the exact data our Javascript map needs
        clean_database[code] = {
            "name": country_name,
            "advisory_text": clean_advisory,
            "color": color,
            "url_slug": eng_data.get("url", code.lower())
        }
        
    # Save the cleaned data to a local JSON file
    with open("advisories.json", "w", encoding="utf-8") as f:
        json.dump(clean_database, f, indent=4)
        
    print(f"Success! Cleaned and saved {len(clean_database)} countries to advisories.json.")

if __name__ == "__main__":
    main()
