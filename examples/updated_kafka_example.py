#!/usr/bin/env python
"""
Updated Kafka streaming example with error handling and detailed output
"""
import sys
import os
import uuid
import json

# Ensure we're using the local pathik module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    
# Import pathik
import pathik

def main():
    # URLs to crawl and stream
    urls = [
        "https://example.com",
        "https://www.wikipedia.org",
        "https://news.ycombinator.com"
    ]
    
    # Generate a session ID for this run
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print(f"Streaming {len(urls)} URLs to Kafka...")
    
    try:
        # Stream content to Kafka
        results = pathik.stream_to_kafka(
            urls=urls,
            content_type="both",      # Stream both HTML and Markdown
            session=session_id,       # Add session ID to messages
            topic="pathik.crawl",     # Set Kafka topic
            parallel=True             # Process URLs in parallel
        )
        
        # Print results in a nice format
        print("\nStreaming Results:")
        print("=================")
        
        for url, result in results.items():
            if result["success"]:
                print(f"✅ {url}")
                if "details" in result:
                    print(f"   HTML: {result['details']['html_file']}")
                    print(f"   Markdown: {result['details']['markdown_file']}")
                    print(f"   Topic: {result['details']['topic']}")
            else:
                print(f"❌ {url}: {result.get('error', 'Unknown error')}")
        
        print("\nTo consume these messages from Kafka, filter by the session ID:")
        print(f"  session_id = '{session_id}'")
        
        # Display complete output in JSON format if requested
        if "--json" in sys.argv:
            print("\nComplete results (JSON):")
            print(json.dumps(results, indent=2))
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 