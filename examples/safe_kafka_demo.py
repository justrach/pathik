#!/usr/bin/env python3
"""
Type-safe Kafka Demo using pathik's validation-enabled streaming capabilities

This script demonstrates how to use pathik's type-safe Kafka streaming functionality
which provides input validation and structured error handling.
"""
import os
import sys
import uuid
import argparse
from typing import Dict, Any, List, Optional

# Add the parent directory to the path to ensure we can import pathik
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Import safe_stream_to_kafka from local module
    from pathik.safe_api import safe_stream_to_kafka
    from pathik.schema import KafkaStreamParams, KafkaStreamResult
except ImportError:
    try:
        # Fall back to importing from installed module
        from pathik import safe_stream_to_kafka
        from pathik.schema import KafkaStreamParams, KafkaStreamResult
    except ImportError:
        print("Error: Cannot import pathik modules. Make sure pathik is installed.")
        print("Install with: pip install pathik")
        sys.exit(1)

def stream_urls_with_validation(
    urls: List[str],
    kafka_brokers: str = "localhost:9092",
    kafka_topic: str = "pathik_crawl_data",
    content_type: str = "both",
    session_id: Optional[str] = None,
    compression_type: Optional[str] = None,
    max_message_size: Optional[int] = None,
    buffer_memory: Optional[int] = None
) -> Dict[str, Any]:
    """
    Stream URLs to Kafka with parameter validation.
    
    Args:
        urls: List of URLs to crawl and stream
        kafka_brokers: Comma-separated list of Kafka brokers
        kafka_topic: Kafka topic to stream to
        content_type: Type of content to stream ('html', 'markdown', or 'both')
        session_id: Optional session ID (generated if not provided)
        compression_type: Compression algorithm ('gzip', 'snappy', 'lz4', 'zstd')
        max_message_size: Maximum message size in bytes
        buffer_memory: Kafka producer buffer memory in bytes
        
    Returns:
        Dictionary with streaming results
    """
    # Set environment variables for Kafka configuration
    os.environ["KAFKA_BROKERS"] = kafka_brokers
    os.environ["KAFKA_TOPIC"] = kafka_topic
    
    # Generate a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    print(f"Streaming {len(urls)} URLs to Kafka with validation:")
    print(f"Kafka Brokers: {kafka_brokers}")
    print(f"Kafka Topic: {kafka_topic}")
    print(f"Content Type: {content_type}")
    print(f"Session ID: {session_id}")
    if compression_type:
        print(f"Compression: {compression_type}")
    if max_message_size:
        print(f"Max Message Size: {max_message_size} bytes")
    if buffer_memory:
        print(f"Buffer Memory: {buffer_memory} bytes")
    print("="*50)
    
    try:
        # Create params dictionary
        params_dict = {
            "urls": urls,
            "content_type": content_type,
            "topic": kafka_topic,
            "session_id": session_id,
            "parallel": True
        }
        
        # Add compression options if provided
        if compression_type:
            params_dict["compression_type"] = compression_type
        if max_message_size:
            params_dict["max_message_size"] = max_message_size
        if buffer_memory:
            params_dict["buffer_memory"] = buffer_memory
        
        # Create validated parameters
        params = KafkaStreamParams(**params_dict)
        
        # Stream with validation
        result = safe_stream_to_kafka(params)
        
        # Process and return results
        return result
        
    except ValueError as e:
        print(f"Validation error: {e}")
        return {"success": False, "error": str(e)}

def print_validated_results(result):
    """
    Print formatted results of the validation-enabled Kafka streaming operation.
    
    Args:
        result: Result object from safe_stream_to_kafka
    """
    print("\nStreaming Results:")
    print("="*50)
    
    if not isinstance(result, dict):
        print(f"Error: Unexpected result type: {type(result)}")
        return
        
    # Check for error structure
    if "success" in result and result["success"] is False:
        print(f"❌ Operation failed: {result.get('error', 'Unknown error')}")
        return
    
    # Count successes and failures
    successful = 0
    failed = 0
    
    # Process results
    for url, info in result.items():
        if not isinstance(info, dict):
            continue
            
        if info.get("success", False):
            successful += 1
            print(f"✅ {url}: Success")
            
            # Extract details from the info dictionary
            if "details" in info:
                details = info["details"]
                if "topic" in details:
                    print(f"  Topic: {details['topic']}")
                if "compression_type" in details:
                    print(f"  Compression: {details['compression_type']}")
                if "html_file" in details:
                    print(f"  HTML File: {os.path.basename(details['html_file'])}")
                if "markdown_file" in details:
                    print(f"  Markdown File: {os.path.basename(details['markdown_file'])}")
                if "session_id" in details:
                    print(f"  Session ID: {details['session_id']}")
            # Handle flat structure for backward compatibility 
            else:
                if "topic" in info:
                    print(f"  Topic: {info['topic']}")
                if "html" in info:
                    html_file = info.get('html', 'N/A')
                    print(f"  HTML File: {os.path.basename(html_file) if html_file != 'N/A' else 'N/A'}")
                if "markdown" in info:
                    md_file = info.get('markdown', 'N/A')
                    print(f"  Markdown File: {os.path.basename(md_file) if md_file != 'N/A' else 'N/A'}")
        else:
            failed += 1
            print(f"❌ {url}: Failed - {info.get('error', 'Unknown error')}")
    
    # Print summary
    print("\nSummary:")
    print(f"Successfully streamed: {successful}/{successful + failed}")
    print(f"Failed to stream: {failed}/{successful + failed}")
    
    # Get session ID if available
    session_id = None
    
    # Try to get session_id from result directly
    if "session_id" in result:
        session_id = result["session_id"]
    else:
        # Look in details section of first successful result
        for info in result.values():
            if isinstance(info, dict) and info.get("success", False) and "details" in info:
                if "session_id" in info["details"]:
                    session_id = info["details"]["session_id"]
                    break
    
    if session_id:
        print("\nTo consume these messages from Kafka:")
        print(f"  python examples/kafka_consumer.py --session={session_id}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Stream web content to Kafka using pathik's type-safe streaming API"
    )
    parser.add_argument("--urls", type=str, required=True, help="Comma-separated list of URLs to stream")
    parser.add_argument("--brokers", type=str, default="localhost:9092", help="Kafka broker list (comma-separated)")
    parser.add_argument("--topic", type=str, default="pathik_crawl_data", help="Kafka topic to stream to")
    parser.add_argument("--content", type=str, choices=["html", "markdown", "both"], default="both", 
                        help="Type of content to stream")
    parser.add_argument("--session", type=str, help="Session ID (generated if not provided)")
    parser.add_argument("--compression", type=str, choices=["gzip", "snappy", "lz4", "zstd"], 
                        help="Compression algorithm to use")
    parser.add_argument("--max-message-size", type=int, help="Maximum message size in bytes")
    parser.add_argument("--buffer-memory", type=int, help="Kafka producer buffer memory in bytes")
    
    args = parser.parse_args()
    
    # Parse URLs
    url_list = [url.strip() for url in args.urls.split(",")]
    
    # Stream URLs to Kafka with validation
    result = stream_urls_with_validation(
        urls=url_list,
        kafka_brokers=args.brokers,
        kafka_topic=args.topic,
        content_type=args.content,
        session_id=args.session,
        compression_type=args.compression,
        max_message_size=args.max_message_size,
        buffer_memory=args.buffer_memory
    )
    
    # Print results
    print_validated_results(result)

if __name__ == "__main__":
    main() 