#!/usr/bin/env python
"""
Example of using Pathik to crawl websites and stream content to Kafka,
and then consuming that content from Kafka.
"""
import pathik
import uuid
import time
import argparse
import json
from typing import Optional


def stream_to_kafka(urls, content_type="both", topic=None, parallel=True):
    """
    Stream crawled content to Kafka
    """
    # Generate a unique session ID to identify this streaming batch
    session_id = str(uuid.uuid4())
    print(f"Generated session ID: {session_id}")
    
    print(f"\nStreaming {len(urls)} URLs to Kafka...")
    print(f"Content type: {content_type}")
    if topic:
        print(f"Topic: {topic}")
    print(f"Parallel processing: {parallel}")
    
    # Stream content to Kafka
    results = pathik.stream_to_kafka(
        urls=urls,
        content_type=content_type,
        topic=topic,
        session=session_id,
        parallel=parallel
    )
    
    # Print results
    success_count = 0
    for url, status in results.items():
        if status.get("success", False):
            print(f"✓ {url}: Successfully streamed to Kafka")
            success_count += 1
        else:
            print(f"✗ {url}: Failed to stream - {status.get('error', 'Unknown error')}")
    
    print(f"\n{success_count}/{len(urls)} URLs successfully streamed to Kafka")
    print(f"Session ID: {session_id} (use this to filter messages when consuming)")
    
    return session_id


def consume_from_kafka(topic="pathik_crawl_data", session_id=None, 
                       content_type=None, max_messages=10, timeout=30):
    """
    Consume messages from Kafka with filtering options
    """
    try:
        # Import Kafka consumer - requires kafka-python package
        from kafka import KafkaConsumer
    except ImportError:
        print("\nERROR: kafka-python package not installed.")
        print("Install it with: pip install kafka-python")
        return
    
    print(f"\nConnecting to Kafka topic: {topic}")
    if session_id:
        print(f"Filtering by session ID: {session_id}")
    if content_type:
        print(f"Filtering by content type: {content_type}")
    print(f"Will show up to {max_messages} messages or stop after {timeout} seconds")
    
    # Create consumer
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers='localhost:9092',  # Change if your server is different
            auto_offset_reset='earliest',        # Start from beginning of topic
            enable_auto_commit=True,
            group_id='pathik-example-consumer',
            consumer_timeout_ms=timeout * 1000   # Convert seconds to milliseconds
        )
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        print("\nMake sure Kafka is running and properly configured in .env file")
        return
    
    # Process messages with filtering
    print("\nWaiting for messages...")
    count = 0
    try:
        for message in consumer:
            # Extract message details
            msg_key = message.key.decode('utf-8') if message.key else None
            
            # Process headers
            headers = {}
            for key, value in message.headers:
                headers[key] = value.decode('utf-8') if value else None
            
            # Apply filters
            if session_id and headers.get('session') != session_id:
                continue
                
            msg_content_type = headers.get('contentType', '')
            if content_type:
                if content_type == 'html' and 'html' not in msg_content_type:
                    continue
                if content_type == 'markdown' and 'markdown' not in msg_content_type:
                    continue
            
            # Print message details
            print("\n" + "-" * 60)
            print(f"URL: {msg_key}")
            print(f"Content Type: {msg_content_type}")
            print(f"Session ID: {headers.get('session', 'N/A')}")
            print(f"Timestamp: {headers.get('timestamp', 'N/A')}")
            
            # Print a sample of the content
            content = message.value.decode('utf-8')
            content_preview = content[:500] + "..." if len(content) > 500 else content
            print("\nContent Preview:")
            print(content_preview)
            
            count += 1
            if count >= max_messages:
                print(f"\nReached maximum message count ({max_messages})")
                break
                
    except Exception as e:
        print(f"Error consuming messages: {e}")
    finally:
        consumer.close()
    
    if count == 0:
        print("\nNo messages received. Possible reasons:")
        print("- No messages matching your filters")
        print("- Kafka topic is empty")
        print("- Timeout reached before messages arrived")
    else:
        print(f"\nReceived {count} messages from Kafka")


def main():
    """
    Main function to parse arguments and run the example
    """
    parser = argparse.ArgumentParser(
        description="Pathik Kafka streaming example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stream content to Kafka:
  python example_kafka.py stream https://example.com https://news.ycombinator.com
  
  # Stream only HTML content:
  python example_kafka.py stream -c html https://example.com
  
  # Stream to a custom topic:
  python example_kafka.py stream -t custom_topic https://example.com
  
  # Consume from Kafka:
  python example_kafka.py consume
  
  # Consume with session filter:
  python example_kafka.py consume -s your-session-id
  
  # Consume only markdown content:
  python example_kafka.py consume -c markdown
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Stream command
    stream_parser = subparsers.add_parser("stream", help="Stream content to Kafka")
    stream_parser.add_argument("urls", nargs="+", help="URLs to crawl and stream")
    stream_parser.add_argument("-c", "--content", choices=["html", "markdown", "both"], 
                              default="both", help="Content type to stream")
    stream_parser.add_argument("-t", "--topic", help="Kafka topic to use")
    stream_parser.add_argument("-s", "--sequential", action="store_true", 
                              help="Use sequential (non-parallel) crawling")
    
    # Consume command
    consume_parser = subparsers.add_parser("consume", help="Consume content from Kafka")
    consume_parser.add_argument("-t", "--topic", default="pathik_crawl_data",
                               help="Kafka topic to consume from")
    consume_parser.add_argument("-s", "--session", help="Filter by session ID")
    consume_parser.add_argument("-c", "--content", choices=["html", "markdown"],
                               help="Filter by content type")
    consume_parser.add_argument("-m", "--max", type=int, default=10,
                              help="Maximum number of messages to consume")
    consume_parser.add_argument("--timeout", type=int, default=30,
                              help="Timeout in seconds")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "stream":
        session_id = stream_to_kafka(
            urls=args.urls,
            content_type=args.content,
            topic=args.topic,
            parallel=not args.sequential
        )
        
        # Offer to consume the messages just streamed
        choice = input("\nDo you want to consume the messages you just streamed? (y/n): ")
        if choice.lower() in ['y', 'yes']:
            consume_from_kafka(
                topic=args.topic or "pathik_crawl_data",
                session_id=session_id,
                content_type=args.content if args.content != "both" else None
            )
    
    elif args.command == "consume":
        consume_from_kafka(
            topic=args.topic,
            session_id=args.session,
            content_type=args.content,
            max_messages=args.max,
            timeout=args.timeout
        )


if __name__ == "__main__":
    main() 