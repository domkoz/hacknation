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

CACHE_FILE = 'data/arxiv_hype.json'

def fetch_arxiv_count(query):
    # Search for "AI" AND "Keyword" in Title or Abstract
    base_url = 'http://export.arxiv.org/api/query?'
    search_query = f'all:"artificial intelligence" AND all:"{query}"'
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
        print(f"Error fetching {query}: {e}")
        return 0

def run_scraper():
    print("🚀 Starting ArXiv Hype Scraper...")
    
    results = {}
    
    # Check cache first
    try:
        if os.path.exists(CACHE_FILE):
             with open(CACHE_FILE, 'r') as f:
                 results = json.load(f)
             print(f"Loaded {len(results)} metrics from cache.")
    except:
        pass

    for section_code, keyword in SECTION_MAP.items():
        if section_code in results:
            print(f"Skipping {section_code} (Cached): {results[section_code]} papers")
            continue
            
        print(f"Querying ArXiv for: AI + {keyword}...")
        count = fetch_arxiv_count(keyword)
        results[section_code] = count
        print(f"Found: {count} papers")
        
        # Rate limit friendly (3s)
        time.sleep(3)
        
        # Save incrementally
        with open(CACHE_FILE, 'w') as f:
            json.dump(results, f, indent=2)
            
    print("✅ ArXiv Scraper Finished.")

if __name__ == "__main__":
    run_scraper()
