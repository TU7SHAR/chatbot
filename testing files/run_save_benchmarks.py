import time
import os
import re
from dotenv import load_dotenv
from utils.scraper import extract_sitemap_urls, scrape_single_url

load_dotenv()

def make_safe_filename(title):
    safe = re.sub(r'[\\/*?:"<>|]', "", title)
    return safe.strip()[:100]

print(" Fetching 120 URLs from the sitemap...")
sitemap_data = extract_sitemap_urls("https://drishinfo.com/sitemap.xml", max_urls=120)

if not sitemap_data['success']:
    print(f" Failed to fetch sitemap: {sitemap_data['error']}")
    exit()

urls = sitemap_data['urls_to_scrape']
print(f" Found {len(urls)} valid URLs to test with.\n")

test_batches = [5, 10, 50, 100]

for batch_size in test_batches:
    if len(urls) < batch_size:
        print(f" Not enough URLs for the {batch_size}-page test.")
        continue

    folder_name = f"benchmark_{batch_size}_pages"
    os.makedirs(folder_name, exist_ok=True)
    
    current_batch = urls[:batch_size]
    print(f"---  RUNNING {batch_size} PAGE TEST (Saving to /{folder_name}) ---")
    
    start_time = time.time()
    successes = 0

    for i, url in enumerate(current_batch):
        print(f"  Scraping & Saving {i+1}/{batch_size}... ", end="", flush=True)
        
        res = scrape_single_url(url)
        
        if res['success']:
            title = res.get('title', f"page_{i+1}")
            safe_title = make_safe_filename(title)
            filepath = os.path.join(folder_name, f"{safe_title}.md")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(res['content'])
            
            print("success!")
            successes += 1
        else:
            print(f" (Error: {res.get('error')})")

    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{batch_size} PAGE RESULTS:")
    print(f"Files successfully saved: {successes} / {batch_size}")
    print(f"Total Time Spent: {duration:.2f} seconds\n")
    print("-" * 40)

print(" ALL TESTS COMPLETE! Zip up the 4 folders and send them to Karan.")