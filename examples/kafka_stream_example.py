#!/usr/bin/env python
"""
Simple example demonstrating Pathik's Kafka streaming API
"""
import pathik
import uuid

# URLs to crawl and stream
urls = [
    "https://example.com",
    "https://news.ycombinator.com"
]

# Generate a session ID to track this batch of streams
session_id = str(uuid.uuid4())
print(f"Session ID: {session_id}")

# Stream the content to Kafka using Pathik API
results = pathik.stream_to_kafka(
    urls=urls,                   # URLs to crawl and stream
    content_type="both",         # Stream both HTML and Markdown
    session=session_id,          # Add session ID to messages
    topic=None,                  # Use default topic from KAFKA_TOPIC env var
    parallel=True                # Process URLs in parallel
)

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