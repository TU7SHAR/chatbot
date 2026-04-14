from dotenv import load_dotenv
from utils.scraper import scrape_single_url

load_dotenv()

print("Firing up the scraper... this might take a few seconds.")

url_to_test = "https://en.wikipedia.org/wiki/Web_scraping"
data = scrape_single_url(url_to_test)

if data['success']:
    print("\n SUCCESS! Here is the title:", data['title'])
    print("-" * 40)
    print(data['content'][:500])
    print("-" * 40)
    print("...and it keeps going!")
else:
    print("\nFAILED:", data['error'])