import pathik
import sys

# Print diagnostic info
print(f"Python version: {sys.version}")
print(f"pathik version: {pathik.__file__}")

# Test with a single URL
try:
    result = pathik.crawl('https://example.com', output_dir='./output')
    print(f"Crawl result: {result}")
except Exception as e:
    print(f"Error: {e}")

# Crawl multiple URLs
results = pathik.crawl(['https://example.com', 'https://news.ycombinator.com'], output_dir='./output')

# Print the results
print(results)