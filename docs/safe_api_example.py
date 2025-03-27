#!/usr/bin/env python
"""
Example of using Pathik's type-safe API.

This example demonstrates how to use the safe_crawl function
for better type safety and error handling.
"""
import os
import sys
import json
from typing import Dict, Any

# Add parent directory to path to find local pathik
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

try:
    # Try to import from local module first
    from pathik.safe_api import safe_crawl
    print("Imported safe_crawl from local pathik module")
except ImportError:
    try:
        # Fall back to installed module
        from pathik import safe_crawl
        print("Imported safe_crawl from installed pathik module")
    except ImportError:
        print("Pathik is not installed. Install with: pip install pathik")
        exit(1)

def crawl_with_validation(url: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Crawl a URL using the type-safe API.
    
    Args:
        url: The URL to crawl
        output_dir: Directory to save crawled files
        
    Returns:
        Dictionary with crawl results
    """
    print(f"Crawling {url} with type-safe API...")
    
    # Create output directory if it doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Call the type-safe API
        result = safe_crawl(
            urls=url,
            output_dir=output_dir,
            parallel=False,
            num_workers=4,
            timeout=60
        )
        
        # Check if the crawl was successful
        if url in result and result[url].get("success", False):
            print(f"✅ Successfully crawled {url}")
            # Extract file paths
            html_file = result[url].get("html", "No HTML file")
            md_file = result[url].get("markdown", "No Markdown file")
            print(f"HTML file: {html_file}")
            print(f"Markdown file: {md_file}")
            
            # Check if files exist
            if os.path.exists(html_file):
                print(f"HTML file size: {os.path.getsize(html_file)} bytes")
            if os.path.exists(md_file):
                print(f"Markdown file size: {os.path.getsize(md_file)} bytes")
        else:
            error = result[url].get("error", "Unknown error")
            print(f"❌ Failed to crawl {url}: {error}")
            
        return result
    except ValueError as e:
        # Handle validation errors
        print(f"❌ Validation error: {e}")
        return {url: {"success": False, "error": str(e)}}
    except Exception as e:
        # Handle other errors
        print(f"❌ Error: {e}")
        return {url: {"success": False, "error": str(e)}}

def demonstrate_validation_error():
    """Demonstrate parameter validation error handling"""
    print("\n=== Demonstrating Validation Error Handling ===")
    
    try:
        # Invalid URL, should be caught by validation
        result = safe_crawl(
            urls="not-a-url",
            output_dir="/tmp/pathik_example"
        )
        print("This shouldn't happen - validation should catch the invalid URL")
    except ValueError as e:
        print(f"✅ Validation caught the error: {e}")

def demonstrate_multiple_urls():
    """Demonstrate crawling multiple URLs"""
    print("\n=== Demonstrating Multiple URL Crawling ===")
    
    output_dir = "/tmp/pathik_example_multi"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Crawl multiple URLs
        result = safe_crawl(
            urls=["https://example.com", "https://httpbin.org/html"],
            output_dir=output_dir,
            parallel=True
        )
        
        print("Results:")
        for url, data in result.items():
            success = data.get("success", False)
            if success:
                print(f"✅ {url}: Success")
                print(f"  HTML: {data.get('html', 'No HTML file')}")
                print(f"  Markdown: {data.get('markdown', 'No Markdown file')}")
            else:
                print(f"❌ {url}: Failed - {data.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function to demonstrate the type-safe API"""
    # Simple crawl with valid parameters
    output_dir = "/tmp/pathik_example"
    result = crawl_with_validation("https://example.com", output_dir)
    
    # Print the full result
    print("\nFull result:")
    print(json.dumps(result, indent=2))
    
    # Demonstrate validation error handling
    demonstrate_validation_error()
    
    # Demonstrate multiple URLs
    demonstrate_multiple_urls()

if __name__ == "__main__":
    main() 