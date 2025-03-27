#!/usr/bin/env python
"""
Real Kafka test that sends actual crawled content to Kafka and verifies reception
"""
import sys
import os
import uuid
import time
import threading
from queue import Queue

# Ensure we're using the local pathik module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from kafka import KafkaProducer, KafkaConsumer
    import pathik
    from pathik.crawler import crawl
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    sys.exit(1)

# Configuration (can be overridden with environment variables)
KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "pathik.test")
TEST_URLS = [
    "https://example.com",
    "https://httpbin.org/html"
]

# Globals for capturing results
received_messages = []
consumer_queue = Queue()
consumer_running = True

def kafka_consumer_thread():
    """Thread that consumes messages from Kafka"""
    global consumer_running
    
    try:
        print(f"\nStarting Kafka consumer for topic: {KAFKA_TOPIC}")
        
        # Create consumer 
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKERS.split(','),
            auto_offset_reset='latest',
            group_id=f'pathik-test-{uuid.uuid4()}',
            consumer_timeout_ms=10000  # 10 seconds
        )
        
        print(f"Consumer connected to {KAFKA_BROKERS}, waiting for messages...")
        
        # Loop consuming messages
        while consumer_running:
            # Poll for messages with 2 second timeout
            message_pack = consumer.poll(timeout_ms=2000, max_records=10)
            
            if not message_pack:
                continue
                
            # Process messages
            for tp, messages in message_pack.items():
                for message in messages:
                    # Process message
                    url = message.key.decode('utf-8') if message.key else "unknown"
                    content_length = len(message.value) if message.value else 0
                    content_type = None
                    session_id = None
                    
                    # Extract headers
                    if message.headers:
                        for key, value in message.headers:
                            if key == 'content_type':
                                content_type = value.decode('utf-8')
                            elif key == 'session':
                                session_id = value.decode('utf-8')
                    
                    # Add to received messages
                    received_messages.append({
                        'url': url,
                        'content_length': content_length,
                        'content_type': content_type,
                        'session_id': session_id,
                        'topic': tp.topic,
                        'partition': tp.partition,
                        'offset': message.offset
                    })
                    
                    print(f"Received message: URL={url}, Type={content_type}, Length={content_length}")
                    
                    # Signal the queue that we got a message
                    consumer_queue.put(True)
        
        consumer.close()
        print("Consumer thread stopped")
    
    except Exception as e:
        print(f"Error in consumer thread: {e}")

def crawl_and_stream_to_kafka():
    """Actually crawl URLs and stream to Kafka"""
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    print(f"Streaming content from {TEST_URLS} to Kafka topic {KAFKA_TOPIC}")
    
    # First crawl the URLs
    print("Crawling URLs...")
    crawl_results = crawl(urls=TEST_URLS, parallel=True)
    
    # Connect to Kafka
    try:
        print(f"Connecting to Kafka broker(s): {KAFKA_BROKERS}")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS.split(','),
            key_serializer=str.encode,
            value_serializer=str.encode
        )
        print("Connected to Kafka")
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return False
    
    # Success flag
    success = True
    
    # Stream content to Kafka
    try:
        for url, files in crawl_results.items():
            # Prepare headers
            headers = [
                ('url', url.encode()),
                ('timestamp', str(time.time()).encode()),
                ('session', session_id.encode())
            ]
            
            # Send HTML content
            if "html" in files and os.path.exists(files["html"]):
                try:
                    with open(files["html"], "r", encoding='utf-8') as f:
                        html_content = f.read()
                        
                    # Add content-type header
                    html_headers = headers + [('content_type', 'text/html'.encode())]
                    
                    # Send to Kafka
                    future = producer.send(
                        topic=KAFKA_TOPIC,
                        key=url,
                        value=html_content,
                        headers=html_headers
                    )
                    # Wait for send to complete
                    record_metadata = future.get(timeout=10)
                    print(f"✅ HTML for {url} sent to Kafka at offset {record_metadata.offset}")
                except Exception as e:
                    print(f"❌ Error sending HTML for {url}: {e}")
                    success = False
            
            # Send Markdown content
            if "markdown" in files and os.path.exists(files["markdown"]):
                try:
                    with open(files["markdown"], "r", encoding='utf-8') as f:
                        md_content = f.read()
                        
                    # Add content-type header
                    md_headers = headers + [('content_type', 'text/markdown'.encode())]
                    
                    # Send to Kafka
                    future = producer.send(
                        topic=KAFKA_TOPIC,
                        key=url,
                        value=md_content,
                        headers=md_headers
                    )
                    # Wait for send to complete
                    record_metadata = future.get(timeout=10)
                    print(f"✅ Markdown for {url} sent to Kafka at offset {record_metadata.offset}")
                except Exception as e:
                    print(f"❌ Error sending Markdown for {url}: {e}")
                    success = False
        
        # Make sure all messages are sent
        producer.flush()
        print("All messages sent to Kafka")
    
    except Exception as e:
        print(f"Error in streaming to Kafka: {e}")
        success = False
    
    finally:
        producer.close()
    
    return success

def run_kafka_test():
    """Run the complete test"""
    # Start consumer thread
    global consumer_running
    consumer_thread = threading.Thread(target=kafka_consumer_thread)
    consumer_running = True
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Wait a bit for consumer to connect
    time.sleep(2)
    
    # Stream to Kafka
    success = crawl_and_stream_to_kafka()
    
    if success:
        print("\nSuccessfully sent messages to Kafka")
    else:
        print("\nFailed to send some messages to Kafka")
    
    # Wait for messages to be consumed (timeout after 10 seconds)
    print("Waiting for messages to be consumed...")
    try:
        # Wait up to 10 seconds to receive a message
        consumer_queue.get(timeout=10)
        print("✅ Received at least one message from Kafka")
    except:
        print("❌ No messages received from Kafka within timeout")
    
    # Stop consumer thread
    consumer_running = False
    consumer_thread.join(timeout=2)
    
    # Print consumer results
    print("\nMessages received from Kafka:")
    print("===========================")
    if not received_messages:
        print("No messages received")
    else:
        for i, msg in enumerate(received_messages):
            print(f"{i+1}. URL: {msg['url']}")
            print(f"   Content Type: {msg['content_type']}")
            print(f"   Content Length: {msg['content_length']} bytes")
            print(f"   Topic: {msg['topic']}, Partition: {msg['partition']}, Offset: {msg['offset']}")
            print(f"   Session ID: {msg['session_id']}")
            print()
    
    # Verify all expected messages were received
    expected_count = len(TEST_URLS) * 2  # HTML and Markdown
    if len(received_messages) >= expected_count:
        print(f"✅ SUCCESS: All {expected_count} expected messages were received")
        return True
    else:
        print(f"❌ FAILURE: Only {len(received_messages)} of {expected_count} expected messages were received")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("REAL KAFKA END-TO-END TEST")
    print("=" * 60)
    print(f"Kafka Broker(s): {KAFKA_BROKERS}")
    print(f"Kafka Topic: {KAFKA_TOPIC}")
    print(f"Test URLs: {', '.join(TEST_URLS)}")
    print("=" * 60)
    
    try:
        result = run_kafka_test()
        if result:
            print("\nTEST PASSED ✅")
            sys.exit(0)
        else:
            print("\nTEST FAILED ❌")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        consumer_running = False
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        consumer_running = False
        sys.exit(1) 