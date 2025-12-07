import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import os

# Mapping Polish Sections to English Search Terms
SECTION_MAP = {
    'SEK_A': "agriculture",
    'SEK_B': "mining",
    'SEK_C': "manufacturing", 
    'SEK_D': "energy grid",
    'SEK_E': "waste management",
    'SEK_F': "construction",
    'SEK_G': "retail",
    'SEK_H': "transportation",
    'SEK_I': "hospitality",
    'SEK_J': "software", 
    'SEK_K': "finance",
    'SEK_L': "real estate",
    'SEK_M': "consulting",
    'SEK_N': "administration",
    'SEK_O': "public administration",
    'SEK_P': "education",
    'SEK_Q': "healthcare",
    'SEK_R': "arts",
    'SEK_S': "service industry"
}

CACHE_FILE = 'data/arxiv_daily_hype.json'

def fetch_arxiv_count(query, year=None):
    # Search for "AI" AND "Keyword"
    base_url = 'http://export.arxiv.org/api/query?'
    search_query = f'all:"artificial intelligence" AND all:"{query}"'
    
    # Add Date Filter if year is provided
    if year:
        # Date format: YYYYMMDDHHMM
        start_date = f"{year}01010000"
        end_date = f"{year}12312359"
        search_query += f' AND submittedDate:[{start_date} TO {end_date}]'
        
    encoded_query = urllib.parse.quote(search_query)
    
    url = f'{base_url}search_query={encoded_query}&start=0&max_results=1'
    
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            root = ET.fromstring(data)
            ns = {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
            total_results = root.find('opensearch:totalResults', ns)
            if total_results is not None:
                return int(total_results.text)
            return 0
    except Exception as e:
        print(f"Error fetching {query} ({year}): {e}")
        return 0

def run_scraper():
    print("🚀 Starting ArXiv Temporal Scraper (2019-2025)...")
    
    results = {}
    years = range(2019, 2026) # 2019 to 2025 inclusive
    
    # Check cache first
    try:
        if os.path.exists(CACHE_FILE):
             with open(CACHE_FILE, 'r') as f:
                 results = json.load(f)
             print(f"Loaded cache with {len(results)} sections.")
    except:
        pass

    for section_code, keyword in SECTION_MAP.items():
        if section_code not in results:
            results[section_code] = {}
            
        print(f"--- Processing {section_code} ({keyword}) ---")
        
        for year in years:
            year_str = str(year)
            if year_str in results[section_code]:
                print(f"  {year}: {results[section_code][year_str]} (Cached)")
                continue

            count = fetch_arxiv_count(keyword, year)
            results[section_code][year_str] = count
            print(f"  {year}: {count} papers")
            
            # Rate limit friendly (3s)
            time.sleep(3)
            
        # Save incrementally after each section
        with open(CACHE_FILE, 'w') as f:
            json.dump(results, f, indent=2)
            
    print("✅ ArXiv Scraper Finished.")
            
    print("✅ ArXiv Scraper Finished.")

if __name__ == "__main__":
    run_scraper()
