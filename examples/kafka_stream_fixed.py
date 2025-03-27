#!/usr/bin/env python
"""
Example demonstrating Pathik's Kafka streaming API with guaranteed local import
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

# URLs to crawl and stream
urls = [
    "https://www.wikipedia.org",
    "https://www.github.com",
    "https://news.ycombinator.com"
]

# Generate a session ID for this run
session_id = str(uuid.uuid4())
print(f"Session ID: {session_id}")

# Stream content to Kafka
results = pathik.stream_to_kafka(
    urls=urls,
    content_type="both",
    session=session_id,
    topic="pathik.crawl",
    parallel=True
)

# Print results
for url, result in results.items():
    if result["success"]:
        print(f"✅ Successfully streamed {url}")
    else:
        print(f"❌ Failed to stream {url}: {result.get('error', 'Unknown error')}")

print("\nTo consume these messages, filter by the session ID:")
print(f"  session_id = '{session_id}'") 