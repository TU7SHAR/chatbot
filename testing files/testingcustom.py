import time,os
from dotenv import load_dotenv
from utils.scraper import extract_sitemap_urls, scrape_single_url

load_dotenv()

print(" Fetching a large batch of URLs from the sitemap...")
sitemap_data = extract_sitemap_urls("https://drishinfo.com/sitemap.xml", max_urls=120)

if not sitemap_data['success']:
    print(f" Failed to fetch sitemap: {sitemap_data['error']}")
    exit()

urls = sitemap_data['urls_to_scrape']
print(f"Found {len(urls)} valid URLs to test with.\n")

test_batches = [5, 10, 50, 100]

for batch_size in test_batches:
    if len(urls) < batch_size:
        print(f" Website only has {len(urls)} pages. Skipping the {batch_size}-page test.")
        continue

    current_batch = urls[:batch_size]
    print(f"--- RUNNING {batch_size} PAGE TEST ---")
    start_time = time.time()
    successes = 0

    for i, url in enumerate(current_batch):
        print(f"  Scraping page {i+1}/{batch_size}... ", end="", flush=True)        
        res = scrape_single_url(url)
        if res['success']:
            print("success!")
            successes += 1
        else:
            print(f" (Error: {res.get('error')})")

    end_time = time.time()
    duration = end_time - start_time
    
    print("\n RESULTS:")
    print(f"Total Pages Scraped: {successes} / {batch_size}")
    print(f"Total Time Spent: {duration:.2f} seconds")
    print(f"Average Time per Page: {(duration/batch_size):.2f} seconds\n")
    print("-" * 40)