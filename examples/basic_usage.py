#!/usr/bin/env python
"""
Basic usage examples for Pathik

This script demonstrates how to use Pathik for crawling web pages
and handling the results properly.
"""

import os
import sys
import pathlib
import uuid
from pprint import pprint

# Add the parent directory to sys.path to find pathik if running from the examples directory
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

try:
    import pathik
    from pathik.crawler import CrawlerError
except ImportError:
    print("Pathik not found. Install it with: pip install pathik")
    sys.exit(1)

def crawl_single_url():
    """Example of crawling a single URL"""
    print("\n=== Crawling a single URL ===")
    
    try:
        # Basic crawl of a single URL
        result = pathik.crawl("https://example.com")
        
        # Check if the URL is in the result
        if "https://example.com" in result:
            url_result = result["https://example.com"]
            
            if url_result.get("success", False):
                print(f"✅ Successfully crawled https://example.com")
                print(f"HTML saved to: {url_result.get('html', 'N/A')}")
                print(f"Markdown saved to: {url_result.get('markdown', 'N/A')}")
            else:
                print(f"❌ Failed to crawl https://example.com")
                print(f"Error: {url_result.get('error', 'Unknown error')}")
        else:
            print("❌ URL not found in results")
            pprint(result)
    
    except CrawlerError as e:
        print(f"❌ Crawler error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def crawl_multiple_urls():
    """Example of crawling multiple URLs in parallel"""
    print("\n=== Crawling multiple URLs in parallel ===")
    
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com"
    ]
    
    try:
        # Crawl multiple URLs in parallel (default behavior)
        results = pathik.crawl(urls)
        
        # Process each URL result
        for url in urls:
            if url in results:
                url_result = results[url]
                
                if url_result.get("success", False):
                    print(f"✅ Successfully crawled {url}")
                    print(f"  HTML saved to: {url_result.get('html', 'N/A')}")
                    print(f"  Markdown saved to: {url_result.get('markdown', 'N/A')}")
                else:
                    print(f"❌ Failed to crawl {url}")
                    print(f"  Error: {url_result.get('error', 'Unknown error')}")
            else:
                print(f"❌ URL not found in results: {url}")
    
    except CrawlerError as e:
        print(f"❌ Crawler error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def crawl_with_custom_output():
    """Example of crawling with a custom output directory"""
    print("\n=== Crawling with custom output directory ===")
    
    # Create a custom output directory
    output_dir = "pathik_output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Crawl with custom output directory
        result = pathik.crawl("https://example.com", output_dir=output_dir)
        
        if "https://example.com" in result:
            url_result = result["https://example.com"]
            
            if url_result.get("success", False):
                print(f"✅ Successfully crawled with custom output directory")
                print(f"HTML saved to: {url_result.get('html', 'N/A')}")
                print(f"Markdown saved to: {url_result.get('markdown', 'N/A')}")
            else:
                print(f"❌ Failed to crawl with custom output")
                print(f"Error: {url_result.get('error', 'Unknown error')}")
        else:
            print("❌ URL not found in results")
    
    except CrawlerError as e:
        print(f"❌ Crawler error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def kafka_streaming_example():
    """Example of streaming to Kafka"""
    print("\n=== Streaming to Kafka ===")
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    try:
        # Stream to Kafka
        result = pathik.stream_to_kafka(
            "https://example.com",
            session=session_id,
            # Increase buffer sizes for large pages
            max_message_size=15728640,  # 15MB
            buffer_memory=104857600     # 100MB
        )
        
        if "https://example.com" in result:
            url_result = result["https://example.com"]
            
            if url_result.get("success", False):
                print(f"✅ Successfully streamed to Kafka")
                print(f"Session ID: {session_id}")
                
                # Instructions for consuming
                print("\nTo consume the messages, run:")
                print(f"python kafka_consumer_direct.py --session={session_id}")
            else:
                print(f"❌ Failed to stream to Kafka")
                print(f"Error: {url_result.get('error', 'Unknown error')}")
        else:
            print("❌ URL not found in results")
    
    except CrawlerError as e:
        print(f"❌ Crawler error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def main():
    """Run all examples"""
    print(f"Pathik version: {pathik.__version__}")
    
    # Run examples
    crawl_single_url()
    crawl_multiple_urls()
    crawl_with_custom_output()
    
    # Uncomment to run Kafka example (requires Kafka setup)
    # kafka_streaming_example()
    
    print("\nAll examples completed!")

if __name__ == "__main__":
    main() 