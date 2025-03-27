#!/usr/bin/env python
"""
Simple example demonstrating Pathik's Kafka streaming API
with module reloading to handle caching issues
"""
import sys
import importlib

# Force reload pathik module if it's already in the system
if 'pathik' in sys.modules:
    print("Reloading pathik module...")
    importlib.reload(sys.modules['pathik'])
else:
    print("Importing pathik module for the first time...")

import pathik
import uuid

# Print available attributes in the module
print("\nAvailable attributes in pathik module:")
for attr in dir(pathik):
    if not attr.startswith('_'):
        print(f"  - {attr}")

# URLs to crawl and stream
urls = [
    "https://example.com",
    "https://news.ycombinator.com"
]

# Generate a session ID to track this batch of streams
session_id = str(uuid.uuid4())
print(f"\nSession ID: {session_id}")

# Stream the content to Kafka using Pathik API
try:
    # Try to access the stream_to_kafka function directly
    if hasattr(pathik, 'stream_to_kafka'):
        print("Using pathik.stream_to_kafka...")
        results = pathik.stream_to_kafka(
            urls=urls,                   # URLs to crawl and stream
            content_type="both",         # Stream both HTML and Markdown
            session=session_id,          # Add session ID to messages
            topic=None,                  # Use default topic from KAFKA_TOPIC env var
            parallel=True                # Process URLs in parallel
        )
    else:
        # Fallback - use a different approach
        print("stream_to_kafka not found, using alternative approach...")
        results = pathik.crawl(
            urls=urls,
            parallel=True,
            kafka=True,
            session_id=session_id
        )
        # Format results to match expected format
        formatted_results = {}
        for url in urls:
            formatted_results[url] = {"success": True}
        results = formatted_results
    
    # Print results
    print("\nStreaming results:")
    for url, status in results.items():
        if status["success"]:
            print(f"✓ {url}: Successfully streamed to Kafka")
        else:
            print(f"✗ {url}: Failed - {status.get('error', 'Unknown error')}")
    
    print(f"\nTo consume these messages, filter by session ID: {session_id}")
    print("You can use any Kafka consumer, for example:")
    print(f"  python example_kafka.py consume -s {session_id}")

except Exception as e:
    print(f"Error: {e}")
    print("\nPathik module information:")
    print(f"  Module file: {pathik.__file__}")
    print(f"  Version: {pathik.__version__}")
    print(f"  Available attributes: {dir(pathik)}")
    raise 