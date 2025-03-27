#!/usr/bin/env python
"""
Simplified Kafka streaming example with error handling
"""
import sys
import os
import uuid
import traceback

# Ensure we're using the local pathik module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    
try:
    # Now import pathik
    from pathik.cli import crawl
    
    # Single URL to test
    url = "https://example.com"
    
    # Generate a session ID for this run
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    # Stream content to Kafka using the crawl function directly
    results = crawl(
        urls=url,
        parallel=False,  # Use sequential processing for simplicity
        kafka=True,      # Enable Kafka streaming
        kafka_topic="pathik.test",  # Specify topic
        session_id=session_id,
        content_type="both"  # Stream both HTML and Markdown
    )
    
    # Print results
    print("\nCrawl Results:")
    print("--------------")
    print(f"Session ID: {results.get('session_id', 'unknown')}")
    
    for key, value in results.items():
        if key != 'session_id':
            print(f"URL: {key}")
            for k, v in value.items():
                print(f"  {k}: {v}")
    
except Exception as e:
    print(f"Error: {e}")
    print(traceback.format_exc()) 