#!/usr/bin/env python
"""
Advanced example demonstrating Pathik's Kafka streaming API with additional options
"""
import pathik
import uuid
import sys

def main():
    """
    Demonstrate various ways to use the Pathik Kafka streaming API
    """
    # Check command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python kafka_stream_advanced.py <url> [<url2> ...]")
        print("Example: python kafka_stream_advanced.py https://example.com")
        sys.exit(1)
    
    # Get URLs from command line
    urls = sys.argv[1:]
    
    # Generate a session ID
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print(f"Processing {len(urls)} URLs")
    
    # Example 1: Stream only HTML content
    print("\n=== Example 1: Stream only HTML content ===")
    results_html = pathik.stream_to_kafka(
        urls=urls,
        content_type="html",    # Only stream HTML content
        session=session_id,
        parallel=True
    )
    print_results("HTML streaming", results_html)
    
    # Example 2: Stream only Markdown content
    print("\n=== Example 2: Stream only Markdown content ===")
    results_md = pathik.stream_to_kafka(
        urls=urls,
        content_type="markdown",    # Only stream Markdown content
        session=session_id,
        parallel=True
    )
    print_results("Markdown streaming", results_md)
    
    # Example 3: Stream to a custom topic
    print("\n=== Example 3: Stream to a custom topic ===")
    custom_topic = "pathik_custom_topic"
    results_topic = pathik.stream_to_kafka(
        urls=urls,
        content_type="both",
        topic=custom_topic,     # Use custom topic
        session=session_id,
        parallel=True
    )
    print_results(f"Streaming to topic '{custom_topic}'", results_topic)
    
    # Example 4: Stream sequentially (not in parallel)
    print("\n=== Example 4: Stream sequentially (no parallel processing) ===")
    results_seq = pathik.stream_to_kafka(
        urls=urls,
        content_type="both",
        session=session_id,
        parallel=False          # Process URLs one at a time
    )
    print_results("Sequential streaming", results_seq)
    
    print(f"\nAll examples used session ID: {session_id}")
    print("To consume these messages, filter by this session ID in your Kafka consumer")

def print_results(description, results):
    """
    Print results of streaming operation
    """
    success_count = sum(1 for status in results.values() if status.get("success", False))
    print(f"Results for {description}:")
    print(f"  {success_count}/{len(results)} URLs successfully streamed")
    
    # Print individual results
    for url, status in results.items():
        if status.get("success", False):
            print(f"  ✓ {url}")
        else:
            print(f"  ✗ {url}: {status.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main() 