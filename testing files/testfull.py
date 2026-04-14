import os
import requests
import xml.etree.ElementTree as ET
from utils.scraper import extract_sitemap_urls

print("Hunting for sitemap URLs...")

test_url = "https://drishinfo.com/sitemap.xml"
data = extract_sitemap_urls(test_url, max_urls=5)

if data['success']:
    print(f"\n✅ SUCCESS! Found {data['total_found']} total pages.")
    print(f"Here are the first {len(data['urls_to_scrape'])} URLs we extracted:")
    for i, url in enumerate(data['urls_to_scrape']):
        print(f"  {i+1}. {url}")
else:
    print("\n❌ FAILED:", data['error'])