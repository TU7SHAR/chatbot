import os, requests
from wsgiref import headers
import xml.etree.ElementTree as ET
from firecrawl import Firecrawl
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

def init_firecrawl():
    """Initializes the Firecrawl client using the API key from .env"""
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY is missing from environment variables.")
    return Firecrawl(api_key=api_key)

def scrape_single_url(url):
    """
    Scrapes a single webpage and returns the markdown content.
    """
    try:
        app = init_firecrawl()
        
        result = app.scrape(url, formats=['markdown'])
        
        if hasattr(result, 'markdown') and result.markdown:
            title = 'Scraped Document'
            if hasattr(result, 'metadata') and hasattr(result.metadata, 'title'):
                title = result.metadata.title

            return {
                "success": True,
                "title": title,
                "content": result.markdown
            }
        else:
            return {"success": False, "error": "No markdown content found on this page."}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_sitemap_urls(sitemap_url, max_urls=10):
    """
    Fetches a sitemap.xml, parses it, and returns a list of URLs.
    Filters out media files (images, PDFs) and dives into nested sitemaps.
    """
    BAD_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.pdf', '.mp4', '.zip')

    def _fetch_urls(url, visited, current_list):
        if url in visited or len(current_list) >= max_urls:
            return
        
        visited.add(url)
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code != 200: 
                return
            
            root = ET.fromstring(resp.content)
            
            for elem in root.iter():
                if len(current_list) >= max_urls:
                    break
                    
                if 'loc' in elem.tag and elem.text:
                    loc = elem.text.strip()
                    
                    clean_loc = loc.split('?')[0].lower() 
                    
                    if clean_loc.endswith('.xml'):
                        _fetch_urls(loc, visited, current_list)
                    elif not clean_loc.endswith(BAD_EXTENSIONS) and loc not in current_list:
                        current_list.append(loc)
                        
        except Exception as e:
            print(f"Skipping {url} due to error: {e}")

    try:
        final_urls = []
        _fetch_urls(sitemap_url, set(), final_urls)
        
        return {
            "success": True,
            "total_found": len(final_urls),
            "urls_to_scrape": final_urls
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    import requests

def crawl_website_links(start_url, max_pages=50):
    """
    Finds internal links by physically 'reading' the HTML of each page.
    No Sitemap required.
    """
    print(f"Spider starting at: {start_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    visited = set()
    queue = [start_url]
    found_urls = []
    
    domain = urlparse(start_url).netloc 

    while queue and len(found_urls) < max_pages:
        current_url = queue.pop(0)
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        found_urls.append(current_url)
        
        try:
            response = requests.get(current_url, headers=headers, timeout=5)
            
            if response.status_code != 200:
                print(f"  Blocked or Not Found ({response.status_code}): {current_url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                full_url = urljoin(current_url, link['href']).split('?')[0]
                
                if (urlparse(full_url).netloc == domain and 
                    full_url not in visited and 
                    full_url not in queue and
                    not full_url.lower().endswith(('.pdf', '.jpg', '.png', '.xml', '.zip', '.css', '.js'))):
                    
                    queue.append(full_url)
            
            print(f"  Found {len(queue)} links in queue... (Total found: {len(found_urls)})")
                    
        except Exception as e:
            print(f"  Skipping {current_url} due to error: {e}")

    return {
        "success": True, 
        "urls": found_urls
    }