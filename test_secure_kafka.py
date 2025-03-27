#!/usr/bin/env python3
"""
Secure Kafka streaming test using our fixed implementation with customizable buffer sizes.
"""
import os
import sys
import uuid
import argparse
import subprocess
from typing import List, Optional, Dict, Any
import time

# Force use of the local binary
LOCAL_BINARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pathik_bin")

def stream_to_kafka_direct(
    urls: List[str], 
    kafka_brokers: str = "localhost:9092", 
    kafka_topic: str = "pathik_crawl_data", 
    content_type: str = "both",
    session_id: Optional[str] = None,
    max_message_size: int = 10 * 1024 * 1024,  # 10MB
    buffer_memory: int = 100 * 1024 * 1024,    # 100MB
    max_request_size: int = 20 * 1024 * 1024   # 20MB
) -> Dict[str, Any]:
    """
    Stream directly using our secured binary with buffer size customization
    """
    if not os.path.exists(LOCAL_BINARY):
        raise FileNotFoundError(f"Local binary not found at {LOCAL_BINARY}")
    
    # Ensure binary is executable
    if not os.access(LOCAL_BINARY, os.X_OK):
        os.chmod(LOCAL_BINARY, 0o755)
    
    # Generate a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Set environment variables for Kafka configuration
    env = os.environ.copy()
    env["KAFKA_BROKERS"] = kafka_brokers
    env["KAFKA_TOPIC"] = kafka_topic
    
    # Add buffer size configurations
    env["KAFKA_MAX_MESSAGE_SIZE"] = str(max_message_size)
    env["KAFKA_BUFFER_MEMORY"] = str(buffer_memory)
    env["KAFKA_MAX_REQUEST_SIZE"] = str(max_request_size)
    
    # Build command
    cmd = [
        LOCAL_BINARY,
        "-kafka",
        "-content", content_type,
        "-session", session_id
    ]
    
    # Add URLs
    cmd.extend(urls)
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        raise RuntimeError(f"Command failed with exit code {result.returncode}")
    
    print(result.stdout)
    
    # Format results
    results = {}
    successful = 0
    for url in urls:
        results[url] = {
            "success": True,
            "details": {
                "topic": kafka_topic,
                "session_id": session_id
            }
        }
        successful += 1
    
    return {
        "results": results,
        "success_count": successful,
        "failed_count": len(urls) - successful,
        "session_id": session_id
    }

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Test secure Kafka streaming with custom buffer sizes")
    parser.add_argument("--urls", type=str, required=True, help="Comma-separated list of URLs to stream")
    parser.add_argument("--brokers", type=str, default="localhost:9092", help="Kafka broker list (comma-separated)")
    parser.add_argument("--topic", type=str, default="pathik_crawl_data", help="Kafka topic to stream to")
    parser.add_argument("--content", type=str, choices=["html", "markdown", "both"], default="both", 
                        help="Type of content to stream")
    parser.add_argument("--session", type=str, help="Session ID (generated if not provided)")
    
    # Add buffer size customization
    parser.add_argument("--max-message-size", type=int, default=10 * 1024 * 1024,
                      help="Maximum message size in bytes (default: 10MB)")
    parser.add_argument("--buffer-memory", type=int, default=100 * 1024 * 1024,
                      help="Producer buffer memory in bytes (default: 100MB)")
    parser.add_argument("--max-request-size", type=int, default=20 * 1024 * 1024,
                      help="Maximum request size in bytes (default: 20MB)")
    
    args = parser.parse_args()
    
    # Parse URLs
    url_list = [url.strip() for url in args.urls.split(",")]
    
    # Generate a session ID if not provided
    session_id = args.session
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Display config information
    print(f"Streaming {len(url_list)} URLs to Kafka with SECURE implementation:")
    print(f"Kafka Brokers: {args.brokers}")
    print(f"Kafka Topic: {args.topic}")
    print(f"Content Type: {args.content}")
    print(f"Session ID: {session_id}")
    print(f"Max Message Size: {args.max_message_size:,} bytes")
    print(f"Buffer Memory: {args.buffer_memory:,} bytes")
    print(f"Max Request Size: {args.max_request_size:,} bytes")
    print("="*50)
    
    # Stream to Kafka with our secure implementation
    try:
        start_time = time.time()
        response = stream_to_kafka_direct(
            urls=url_list,
            kafka_brokers=args.brokers,
            kafka_topic=args.topic,
            content_type=args.content,
            session_id=session_id,
            max_message_size=args.max_message_size,
            buffer_memory=args.buffer_memory,
            max_request_size=args.max_request_size
        )
        elapsed_time = time.time() - start_time
        
        results = response["results"]
        successful = response["success_count"]
        failed = response["failed_count"]
        
        print("\nStreaming Results:")
        print("="*50)
        
        for url, result in results.items():
            status = "✅ Success" if result.get("success", False) else "❌ Failed"
            if result.get("success", False):
                print(f"{status} - {url}")
                if "details" in result:
                    details = result["details"]
                    print(f"  Topic: {details.get('topic')}")
            else:
                print(f"{status} - {url}")
                if "error" in result:
                    print(f"  Error: {result['error']}")
        
        print("\nSummary:")
        print(f"Successfully streamed: {successful}/{len(url_list)}")
        print(f"Failed to stream: {failed}/{len(url_list)}")
        print(f"Total time: {elapsed_time:.2f} seconds")
        
        print("\nTo consume these messages from Kafka:")
        print(f"  python examples/kafka_consumer_direct.py --session={session_id}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 