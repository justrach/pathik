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
import re
import ssl
from typing import Optional, Dict, Any, List

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

def validate_broker_string(broker_str: str) -> bool:
    """Validate broker string format."""
    if not broker_str:
        return False
    
    # Simple validation - check format of each broker
    for broker in broker_str.split(','):
        # Check for hostname/IP:port format
        if not re.match(r'^[a-zA-Z0-9.-]+:\d+$', broker.strip()):
            return False
    
    return True

def validate_topic_name(topic: str) -> bool:
    """Validate Kafka topic name."""
    if not topic:
        return False
    
    # Kafka topics have restrictions on characters
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', topic))

def validate_session_id(session_id: str) -> bool:
    """Validate session ID for security."""
    if not session_id:
        return True  # Empty is valid
    
    # Only allow alphanumeric and some special chars
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', session_id))

def create_ssl_context() -> ssl.SSLContext:
    """Create a secure SSL context for Kafka."""
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    
    # Optional: Load custom CA certificate if specified
    ca_path = os.environ.get('KAFKA_CA_CERT')
    if ca_path and os.path.exists(ca_path):
        context.load_verify_locations(cafile=ca_path)
    
    return context

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
    parser.add_argument("--use-ssl", action="store_true", default=(os.environ.get("KAFKA_USE_SSL", "false").lower() == "true"),
                        help="Use SSL/TLS for Kafka connection")
    parser.add_argument("--max-content-size", type=int, default=int(os.environ.get("MAX_CONTENT_SIZE", "10000")),
                        help="Maximum content size to display (in characters)")
    args = parser.parse_args()

    # Validate inputs
    if not validate_broker_string(args.brokers):
        print("Error: Invalid broker string format", file=sys.stderr)
        sys.exit(1)
    
    if not validate_topic_name(args.topic):
        print("Error: Invalid topic name", file=sys.stderr)
        sys.exit(1)
    
    if args.session and not validate_session_id(args.session):
        print("Error: Invalid session ID format", file=sys.stderr)
        sys.exit(1)
    
    if args.max_content_size < 0 or args.max_content_size > 100000:
        print("Error: Content size must be between 0 and 100000 characters", file=sys.stderr)
        sys.exit(1)

    # Configure consumer
    config: Dict[str, Any] = {
        'bootstrap_servers': args.brokers.split(','),
        'auto_offset_reset': 'earliest' if args.from_beginning else 'latest',
        'group_id': 'pathik-example-consumer',
        'value_deserializer': lambda x: x.decode('utf-8', errors='replace'),
        'key_deserializer': lambda x: x.decode('utf-8', errors='replace'),
        'enable_auto_commit': True,
        'consumer_timeout_ms': 60000,  # 60 seconds timeout
    }
    
    # Add SASL authentication if credentials provided
    if args.username and args.password:
        config.update({
            'security_protocol': 'SASL_SSL' if args.use_ssl else 'SASL_PLAINTEXT',
            'sasl_mechanism': 'PLAIN',
            'sasl_plain_username': args.username,
            'sasl_plain_password': args.password,
        })
        print("Using SASL authentication")
    
    # Add SSL if requested
    if args.use_ssl:
        ssl_context = create_ssl_context()
        config.update({
            'security_protocol': 'SSL' if not args.username else 'SASL_SSL',
            'ssl_context': ssl_context,
        })
        print("Using SSL/TLS encryption")

    # Print connection info
    print(f"Connecting to Kafka brokers: {args.brokers}")
    print(f"Consuming from topic: {args.topic}")
    if args.type:
        print(f"Filtering for content type: {args.type}")
    print(f"Starting from: {'beginning' if args.from_beginning else 'most recent'}")

    # Set up consumer
    try:
        consumer = KafkaConsumer(args.topic, **config)
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}", file=sys.stderr)
        sys.exit(1)

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
    
    try:
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
            
            # Print preview of content with size limit
            content = message.value
            content_len = len(content)
            preview_len = min(content_len, args.max_content_size)
            preview = content[:preview_len] + "... [truncated]" if content_len > preview_len else content
            print(f"Content Preview ({content_len} bytes total):")
            print(preview)
    except Exception as e:
        print(f"Error consuming messages: {e}", file=sys.stderr)
        consumer.close()
        sys.exit(1)

if __name__ == "__main__":
    main() 