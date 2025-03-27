#!/usr/bin/env python3
"""
Type-Safe Kafka Demo using pathik's built-in streaming capabilities

This script demonstrates real-world usage of pathik's native Kafka
streaming functionality with type safety and validation.
"""
import os
import sys
import uuid
import argparse
from typing import List, Optional, Dict, Any, Union, Literal

# Add the parent directory to the path to ensure we can import pathik
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from pathik import stream_to_kafka, safe_crawl
    print("Successfully imported pathik modules")
except ImportError as e:
    print(f"Error importing pathik: {e}")
    print("Make sure pathik is installed or in your Python path")
    sys.exit(1)

def validate_url(url: str) -> bool:
    """
    Validate a URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if the URL is valid, False otherwise
    """
    return url.startswith(('http://', 'https://'))

def validate_kafka_brokers(brokers: str) -> bool:
    """
    Validate Kafka broker string format.
    
    Args:
        brokers: Comma-separated list of Kafka brokers
        
    Returns:
        True if the broker string is valid, False otherwise
    """
    if not brokers:
        return False
    
    for broker in brokers.split(','):
        # Check for hostname/IP:port format
        if not broker.strip() or ':' not in broker:
            return False
    
    return True

def safe_stream_urls_to_kafka(
    urls: Union[str, List[str]], 
    kafka_brokers: str = "localhost:9092", 
    kafka_topic: str = "pathik_crawl_data", 
    content_type: Literal["html", "markdown", "both"] = "both",
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stream a list of URLs to Kafka using pathik's native streaming functionality
    with added validation.
    
    Args:
        urls: URL or list of URLs to crawl and stream
        kafka_brokers: Comma-separated list of Kafka brokers
        kafka_topic: Kafka topic to stream to
        content_type: Type of content to stream ('html', 'markdown', or 'both')
        session_id: Optional session ID (generated if not provided)
        
    Returns:
        Dictionary with streaming results
        
    Raises:
        ValueError: If validation fails for any parameter
    """
    # Convert single URL to list
    if isinstance(urls, str):
        urls = [urls]
    
    # Validate inputs
    for url in urls:
        if not validate_url(url):
            raise ValueError(f"Invalid URL format: {url}")
    
    if not validate_kafka_brokers(kafka_brokers):
        raise ValueError(f"Invalid Kafka broker format: {kafka_brokers}")
        
    if content_type not in ["html", "markdown", "both"]:
        raise ValueError(f"Invalid content type: {content_type}")
    
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
    
    try:
        # Stream URLs to Kafka using the stream_to_kafka function
        results = stream_to_kafka(
            urls=urls,
            content_type=content_type,
            topic=kafka_topic,
            session=session_id,
            parallel=True
        )
        
        return results
    except Exception as e:
        # Create structured error results
        error_results = {url: {"success": False, "error": str(e)} for url in urls}
        return error_results

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
    
    urls = [key for key in results.keys() if key != "session_id"]
    
    for url in urls:
        result = results.get(url, {})
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
    print(f"Successfully streamed: {successful}/{len(urls)}")
    print(f"Failed to stream: {failed}/{len(urls)}")
    
    # Get session ID from the first successful result
    session_id = None
    for result in results.values():
        if isinstance(result, dict) and result.get("success", False) and "details" in result:
            session_id = result["details"].get("session_id")
            break
    
    if session_id:
        print("\nTo consume these messages from Kafka:")
        print(f"  python examples/kafka_consumer.py --session={session_id}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Stream web content to Kafka using pathik's type-safe streaming capability")
    parser.add_argument("--urls", type=str, required=True, help="Comma-separated list of URLs to stream")
    parser.add_argument("--brokers", type=str, default="localhost:9092", help="Kafka broker list (comma-separated)")
    parser.add_argument("--topic", type=str, default="pathik_crawl_data", help="Kafka topic to stream to")
    parser.add_argument("--content", type=str, choices=["html", "markdown", "both"], default="both", 
                        help="Type of content to stream")
    parser.add_argument("--session", type=str, help="Session ID (generated if not provided)")
    
    args = parser.parse_args()
    
    # Parse URLs
    url_list = [url.strip() for url in args.urls.split(",")]
    
    try:
        # Stream URLs to Kafka with validation
        results = safe_stream_urls_to_kafka(
            urls=url_list,
            kafka_brokers=args.brokers,
            kafka_topic=args.topic,
            content_type=args.content,
            session_id=args.session
        )
        
        # Print results
        print_results(results)
    except ValueError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 