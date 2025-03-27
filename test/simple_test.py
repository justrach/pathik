#!/usr/bin/env python
"""
Simple direct test for pathik with the fixed command ordering.
"""
import os
import sys
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath('..'))

# Import pathik directly
import pathik

def main():
    """Test pathik directly to verify command ordering fix"""
    print(f"Testing pathik version: {pathik.__version__}")
    
    # Create output directory
    output_dir = "simple_test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test URL
    url = "https://example.com"
    
    print(f"\nCrawling {url}...")
    print(f"Output directory: {output_dir}")
    
    try:
        # This is the key test - this would fail before the fix
        # because -outdir would be placed after URLs
        results = pathik.crawl(url, output_dir=output_dir)
        
        if url in results and "html" in results[url]:
            print(f"\n✅ SUCCESS: {url} was crawled correctly")
            print(f"HTML file: {results[url]['html']}")
            print(f"Markdown file: {results[url]['markdown']}")
            
            # Check if files exist and have content
            html_file = results[url]['html']
            md_file = results[url]['markdown']
            
            if os.path.exists(html_file) and os.path.getsize(html_file) > 0:
                print(f"✅ HTML file has content ({os.path.getsize(html_file)} bytes)")
            else:
                print(f"❌ HTML file is missing or empty")
                
            if os.path.exists(md_file) and os.path.getsize(md_file) > 0:
                print(f"✅ Markdown file has content ({os.path.getsize(md_file)} bytes)")
            else:
                print(f"❌ Markdown file is missing or empty")
        else:
            print(f"❌ ERROR: Failed to crawl {url}")
            print(f"Results: {json.dumps(results, indent=2)}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
if __name__ == "__main__":
    main() 