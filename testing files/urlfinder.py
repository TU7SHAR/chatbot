from utils.scraper import extract_sitemap_urls

name="Drish Infotech"
url="https://drishinfo.com/sitemap.xml"
url1=""

print(f"Scanning: {name} for all pages...")
data = extract_sitemap_urls(f"{url}", max_urls=10000)

if data['success']:
    print(f"\nGRAND TOTAL: The website has exactly {data['total_found']} valid URLs.")
else:
    print(f"Error: {data['error']}")