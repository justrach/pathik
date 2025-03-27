#!/usr/bin/env python3
"""
Example Kafka consumer for Pathik-streamed content.
This script reads messages from a Kafka topic where Pathik has streamed crawled content.

Requirements:
pip install kafka-python python-dotenv
"""

import os
import sys
import signal
import argparse
import json
from datetime import datetime
from typing import Optional

try:
    from dotenv import load_dotenv
    from kafka import KafkaConsumer
except ImportError:
    print("Required packages not found. Install with:")
    print("pip install kafka-python python-dotenv")
    sys.exit(1)

def get_env_with_default(key: str, default: str) -> str:
    """Get environment variable with a default value."""
    return os.environ.get(key, default)

def main():
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Consume messages from Kafka topic where Pathik streamed content")
    parser.add_argument("--brokers", default=get_env_with_default("KAFKA_BROKERS", "localhost:9092"),
                        help="Kafka brokers (comma-separated)")
    parser.add_argument("--topic", default=get_env_with_default("KAFKA_TOPIC", "pathik_crawl_data"),
                        help="Kafka topic to consume from")
    parser.add_argument("--username", default=os.environ.get("KAFKA_USERNAME"),
                        help="SASL username")
    parser.add_argument("--password", default=os.environ.get("KAFKA_PASSWORD"),
                        help="SASL password")
    parser.add_argument("--type", choices=["html", "markdown"],
                        help="Filter by content type (html or markdown)")
    parser.add_argument("--from-beginning", action="store_true",
                        help="Consume from the beginning of the topic")
    parser.add_argument("--session", help="Filter messages by session ID")
    args = parser.parse_args()

    # Configure consumer
    config = {
        'bootstrap_servers': args.brokers.split(','),
        'auto_offset_reset': 'earliest' if args.from_beginning else 'latest',
        'group_id': 'pathik-example-consumer',
        'value_deserializer': lambda x: x.decode('utf-8', errors='replace'),
        'key_deserializer': lambda x: x.decode('utf-8', errors='replace'),
        'enable_auto_commit': True,
    }
    
    # Add SASL authentication if credentials provided
    if args.username and args.password:
        config.update({
            'security_protocol': 'SASL_PLAINTEXT',
            'sasl_mechanism': 'PLAIN',
            'sasl_plain_username': args.username,
            'sasl_plain_password': args.password,
        })
        print("Using SASL authentication")

    # Print connection info
    print(f"Connecting to Kafka brokers: {args.brokers}")
    print(f"Consuming from topic: {args.topic}")
    if args.type:
        print(f"Filtering for content type: {args.type}")
    print(f"Starting from: {'beginning' if args.from_beginning else 'most recent'}")

    # Set up consumer
    consumer = KafkaConsumer(args.topic, **config)

    # Setup signal handler for graceful shutdown
    def handle_signal(sig, frame):
        print("\nShutting down gracefully...")
        consumer.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Consume messages
    print("Consumer started. Press Ctrl+C to exit.")
    print("-----------------------------------------")
    
    for message in consumer:
        # Extract headers
        headers = {}
        for key, value in message.headers:
            try:
                headers[key] = value.decode('utf-8')
            except (AttributeError, UnicodeDecodeError):
                headers[key] = str(value)
        
        content_type = headers.get('contentType', '')
        session_id = headers.get('sessionID', '')
        
        # Skip if content type filter is set and doesn't match
        if args.type and args.type not in content_type.lower():
            continue
        
        # Skip if session ID filter is set and doesn't match
        if args.session and args.session != session_id:
            continue
        
        # Display message
        print("-----------------------------------------")
        print(f"Partition: {message.partition}, Offset: {message.offset}")
        print(f"Key: {message.key}")
        print(f"URL: {headers.get('url', 'unknown')}")
        print(f"Content Type: {content_type}")
        print(f"Timestamp: {headers.get('timestamp', 'unknown')}")
        
        # Print preview of content
        content = message.value
        content_len = len(content)
        preview = content[:200] + "... [truncated]" if content_len > 200 else content
        print(f"Content Preview ({content_len} bytes total):")
        print(preview)

if __name__ == "__main__":
    main() 