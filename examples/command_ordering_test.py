#!/usr/bin/env python
"""
Test script to verify that the command ordering fix works properly.
"""
import os
import sys
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath('..'))

try:
    import pathik
    print(f"Successfully imported pathik v{pathik.__version__}")
except ImportError as e:
    print(f"Error importing pathik: {e}")
    sys.exit(1)

def test_command_ordering():
    """Run tests to verify the command ordering fix"""
    print("\n=== Testing Command Ordering Fix ===")
    
    # Create an output directory
    output_dir = os.path.abspath("test_output")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Test URLs
    urls = [
        "https://example.com",
        "https://httpbin.org/html"
    ]
    
    # Test 1: Basic crawl with output directory
    print("\nTest 1: Basic crawl with output directory")
    try:
        results = pathik.crawl(urls[0], output_dir=output_dir)
        if urls[0] in results and "html" in results[urls[0]]:
            print(f"✅ Test 1 passed: Successfully crawled {urls[0]}")
            print(f"   HTML file: {results[urls[0]]['html']}")
        else:
            print(f"❌ Test 1 failed: Could not find expected output for {urls[0]}")
            print(f"   Result: {results}")
    except Exception as e:
        print(f"❌ Test 1 failed with exception: {e}")
    
    # Test 2: Multiple URLs with parallel processing
    print("\nTest 2: Multiple URLs with parallel processing")
    try:
        results = pathik.crawl(urls, output_dir=output_dir, parallel=True)
        success = True
        for url in urls:
            if url not in results or "html" not in results[url]:
                success = False
                print(f"❌ Missing output for {url}")
        
        if success:
            print(f"✅ Test 2 passed: Successfully crawled multiple URLs in parallel")
            for url in urls:
                print(f"   {url} -> {results[url]['html']}")
        else:
            print(f"❌ Test 2 failed: Some URLs did not complete successfully")
            print(f"   Result: {results}")
    except Exception as e:
        print(f"❌ Test 2 failed with exception: {e}")
    
    # Test 3: Advanced options
    print("\nTest 3: Advanced options")
    try:
        results = pathik.crawl(
            urls[0],
            output_dir=output_dir,
            validate=True,
            timeout=30,
            limit=100
        )
        if urls[0] in results and "html" in results[urls[0]]:
            print(f"✅ Test 3 passed: Successfully crawled with advanced options")
            print(f"   HTML file: {results[urls[0]]['html']}")
        else:
            print(f"❌ Test 3 failed: Could not find expected output")
            print(f"   Result: {results}")
    except Exception as e:
        print(f"❌ Test 3 failed with exception: {e}")
    
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    test_command_ordering() 