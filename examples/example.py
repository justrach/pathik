import os
import sys
import traceback

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

# List of URLs to crawl
urls = [
    "https://example.com",
    "https://news.ycombinator.com"
]

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