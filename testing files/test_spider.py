from utils.scraper import crawl_website_links, scrape_single_url
import os
from dotenv import load_dotenv
load_dotenv()

# TEST CONFIG
TARGET_SITE = "https://news.ycombinator.com/" # A famous site for testing crawlers
MAX_TO_FIND = 10

print(f"---  Phase 1: Spider Discovery ---")
discovery = crawl_website_links(TARGET_SITE, max_pages=MAX_TO_FIND)

if discovery['success']:
    links = discovery['urls']
    print(f"\n Spider found {len(links)} pages without a sitemap!")
    
    print(f"\n--- Phase 2: Firecrawl Extraction ---")
    for i, url in enumerate(links[:3]): # Just testing the first 3 to save credits
        print(f"Scraping {i+1}/3: {url}")
        data = scrape_single_url(url)
        if data['success']:
            print(f"   Captured Title: {data['title']}")
        else:
            print(f"   Failed: {data.get('error')}")