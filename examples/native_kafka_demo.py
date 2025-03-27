#!/usr/bin/env python3
"""
Native Kafka Demo using pathik's built-in streaming capabilities

This script demonstrates real-world usage of pathik's native Kafka
streaming functionality without additional implementation.
"""
import os
import sys
import uuid
import argparse
from typing import List, Optional, Dict, Any

# Add the parent directory to the path to ensure we can import pathik
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pathik import stream_to_kafka

def stream_urls_to_kafka(
    urls: List[str], 
    kafka_brokers: str = "localhost:9092", 
    kafka_topic: str = "pathik_crawl_data", 
    content_type: str = "both",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stream a list of URLs to Kafka using pathik's native streaming functionality.
    
    Args:
        urls: List of URLs to crawl and stream
        kafka_brokers: Comma-separated list of Kafka brokers
        kafka_topic: Kafka topic to stream to
        content_type: Type of content to stream ('html', 'markdown', or 'both')
        session_id: Optional session ID (generated if not provided)
        
    Returns:
        Dictionary with streaming results
    """
    # Set environment variables for Kafka configuration
    os.environ["KAFKA_BROKERS"] = kafka_brokers
    os.environ["KAFKA_TOPIC"] = kafka_topic
    
    # Generate a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    print(f"Streaming {len(urls)} URLs to Kafka:")
    print(f"Kafka Brokers: {kafka_brokers}")
    print(f"Kafka Topic: {kafka_topic}")
    print(f"Content Type: {content_type}")
    print(f"Session ID: {session_id}")
    print("="*50)
    
    # Stream URLs to Kafka using pathik's built-in functionality
    results = stream_to_kafka(
        urls=urls,
        content_type=content_type,
        topic=kafka_topic,
        session=session_id,
        parallel=True
    )
    
    # Return results 
    return results

def print_results(results: Dict[str, Any]) -> None:
    """
    Print formatted results of the Kafka streaming operation.
    
    Args:
        results: Results dictionary from stream_to_kafka
    """
    if not results:
        print("No results returned")
        return
        
    # Print results
    print("\nStreaming Results:")
    print("="*50)
    successful = 0
    failed = 0
    
    for url, result in results.items():
        status = "✅ Success" if result.get("success", False) else "❌ Failed"
        if result.get("success", False):
            successful += 1
            print(f"{status} - {url}")
            if "details" in result:
                details = result["details"]
                print(f"  Topic: {details.get('topic')}")
                html_file = details.get('html_file', 'N/A')
                md_file = details.get('markdown_file', 'N/A')
                print(f"  HTML Content: {os.path.basename(html_file) if html_file != 'N/A' else 'N/A'}")
                print(f"  Markdown Content: {os.path.basename(md_file) if md_file != 'N/A' else 'N/A'}")
        else:
            failed += 1
            print(f"{status} - {url}")
            if "error" in result:
                print(f"  Error: {result['error']}")
    
    print("\nSummary:")
    print(f"Successfully streamed: {successful}/{len(results)}")
    print(f"Failed to stream: {failed}/{len(results)}")
    
    # Get session ID from the first successful result
    session_id = None
    for result in results.values():
        if result.get("success", False) and "details" in result:
            session_id = result["details"].get("session_id")
            break
    
    # Or get it from the first result's details if available
    if not session_id and len(results) > 0:
        url = list(results.keys())[0]
        result = results[url]
        if "details" in result:
            session_id = result["details"].get("session_id")
    
    if session_id:
        print("\nTo consume these messages from Kafka:")
        print(f"  python examples/kafka_consumer.py --session={session_id}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Stream web content to Kafka using pathik's native streaming capability")
    parser.add_argument("--urls", type=str, required=True, help="Comma-separated list of URLs to stream")
    parser.add_argument("--brokers", type=str, default="localhost:9092", help="Kafka broker list (comma-separated)")
    parser.add_argument("--topic", type=str, default="pathik_crawl_data", help="Kafka topic to stream to")
    parser.add_argument("--content", type=str, choices=["html", "markdown", "both"], default="both", 
                        help="Type of content to stream")
    parser.add_argument("--session", type=str, help="Session ID (generated if not provided)")
    
    args = parser.parse_args()
    
    # Parse URLs
    url_list = [url.strip() for url in args.urls.split(",")]
    
    # Stream URLs to Kafka
    results = stream_urls_to_kafka(
        urls=url_list,
        kafka_brokers=args.brokers,
        kafka_topic=args.topic,
        content_type=args.content,
        session_id=args.session
    )
    
    # Print results
    print_results(results)

if __name__ == "__main__":
    main() 