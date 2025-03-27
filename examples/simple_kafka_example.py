#!/usr/bin/env python
"""
Simple example showing real Kafka streaming with Pathik
"""
import sys
import os
import uuid

# Ensure we're using the local pathik module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import pathik

def run_example():
    # Generate a session ID
    session_id = str(uuid.uuid4())
    print(f"Generated session ID: {session_id}")
    
    # Set the Kafka topic through environment variable
    os.environ["KAFKA_TOPIC"] = "pathik_crawl_data"
    
    # URL to crawl and stream
    url = "https://httpbin.org/html"
    print(f"Crawling and streaming {url} to Kafka...")
    
    try:
        # Stream the content to Kafka
        result = pathik.stream_to_kafka(
            urls=url,
            content_type="both",
            session=session_id
        )
        
        # Print the result
        print("\nResult:")
        print("=======")
        print(f"URL: {url}")
        if result[url]["success"]:
            print("Status: Success")
            if "details" in result[url]:
                details = result[url]["details"]
                print(f"Topic: {details.get('topic')}")
                print(f"HTML file: {details.get('html_file')}")
                print(f"Markdown file: {details.get('markdown_file')}")
        else:
            print(f"Status: Failed - {result[url].get('error', 'Unknown error')}")
            
        print("\nTo consume these messages from Kafka:")
        print(f"  python examples/kafka_consumer.py --session={session_id}")
        
        return result
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_example() 