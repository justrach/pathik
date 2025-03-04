import os
import sys
import traceback
import requests
import xml.etree.ElementTree as ET

# Function to fetch URLs from sitemap.xml
def fetch_urls_from_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    response.raise_for_status()  # Raise an error for bad responses
    
    # Parse the XML content
    root = ET.fromstring(response.content)
    
    # Extract the namespace from the root element
    ns = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else ''
    
    # If there's a namespace, we need to use it to find elements
    if ns:
        urls = [url_elem.find('ns:loc', ns).text for url_elem in root.findall('ns:url', ns)]
    else:
        # Default namespace handling
        urls = [url_elem.find('loc').text for url_elem in root.findall('url')]
    
    print(f"Found {len(urls)} URLs in the sitemap")
    return urls

# Add the parent directory to the Python path if needed
#sys.path.insert(0, os.path.abspath('..'))

try:
    import pathik
    print(f"Successfully imported pathik from {pathik.__file__}")
    print(f"Available attributes: {dir(pathik)}")
except ImportError as e:
    print(f"Error importing pathik: {e}")
    sys.exit(1)

# Create an output directory with an absolute path
output_dir = os.path.abspath("output_data")
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory: {output_dir}")

# Fetch URLs from sitemap.xml
sitemap_url = "https://jan.ai/sitemap-0.xml"  # The sitemap URL
print(f"Fetching URLs from {sitemap_url}...")
urls = fetch_urls_from_sitemap(sitemap_url)

# Limit the number of URLs to crawl if there are too many
max_urls = 10  # Adjust this number as needed
if len(urls) > max_urls:
    print(f"Limiting to {max_urls} URLs out of {len(urls)} total")
    urls = urls[:max_urls]

# Crawl the URLs and save to the output directory
print(f"Crawling {len(urls)} URLs...")
try:
    results = pathik.crawl(urls, output_dir=output_dir)
    
    # Print the results
    print("\nCrawling results:")
    for url, files in results.items():
        print(f"\nURL: {url}")
        print(f"HTML file: {files['html']}")
        print(f"Markdown file: {files['markdown']}")

        # Print sample content from markdown file
        if files['markdown'] and os.path.exists(files['markdown']):
            with open(files['markdown'], 'r', encoding='utf-8') as f:
                content = f.read(500)  # First 500 characters
                print(f"\nSample markdown content:")
                print(f"{content}...")
        else:
            print(f"WARNING: Markdown file not found or empty!")
except Exception as e:
    print(f"Error during crawling: {e}")
    traceback.print_exc() 