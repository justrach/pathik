#!/usr/bin/env python
"""
Simple example demonstrating Pathik's basic crawling
"""
import sys
import os
import uuid

# Ensure we're using the local pathik module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    
# Now import pathik
import pathik
from pathik.crawler import crawl

# URLs to crawl
urls = ["https://example.com"]

# Create a temporary directory for output
import tempfile
output_dir = tempfile.mkdtemp(prefix="pathik_simple_crawl_")
print(f"Output directory: {output_dir}")

# Use the basic crawl function
results = crawl(urls=urls, output_dir=output_dir, parallel=False)

# Print results
print("\nCrawl Results:")
print("--------------")
for url, info in results.items():
    if "error" in info:
        print(f"❌ {url}: Error - {info['error']}")
    else:
        print(f"✅ {url}: Success")
        print(f"   HTML: {info.get('html', 'Not found')}")
        print(f"   Markdown: {info.get('markdown', 'Not found')}")

# Clean up
print(f"\nFiles in {output_dir}:")
for file in os.listdir(output_dir):
    print(f"  {file}")
    
# Optionally display file contents
for url, info in results.items():
    if "html" in info and os.path.exists(info["html"]):
        with open(info["html"], "r", encoding="utf-8") as f:
            contents = f.read()
            preview = contents[:100] + "..." if len(contents) > 100 else contents
            print(f"\nHTML preview for {url}:")
            print(preview) 