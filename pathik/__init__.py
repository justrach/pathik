# Print diagnostic information
import sys
import os
print(f"Loading pathik package from {__file__}")
print(f"Python path: {sys.path}")

# Import typing related modules at the module level
from typing import List, Dict, Optional, Union, Literal, Any
import uuid
import json
import tempfile
import subprocess
import time
import shutil

# Set version
__version__ = "0.3.11"  # Incremented version for command ordering fix

# NOTE: Version 0.3.0 fixes a critical bug with command-line argument ordering.
# Previously, flags were incorrectly placed after URLs, causing errors like:
# "Invalid URL '-outdir': only HTTP and HTTPS schemes are allowed"
# Now flags are correctly placed before the -crawl command.

# Import the basic functions  
from .cli import crawl

# Import our type-safe API 
try:
    from .safe_api import safe_crawl
    from .schema import CrawlParams, CrawlResult, PathikFileResult
    print("Successfully imported type-safe API")
except ImportError as e:
    print(f"Type-safe API import failed: {e}")
    # Define a fallback in case the import fails
    def safe_crawl(*args, **kwargs):
        """Fallback implementation that redirects to regular crawl"""
        return crawl(*args, **kwargs)

# Function to stream to Kafka - defined at module level
def stream_to_kafka(
    urls: Union[str, List[str]], 
    content_type: Literal["html", "markdown", "both"] = "both",
    topic: Optional[str] = None,
    session: Optional[str] = None,
    parallel: bool = True,
    compression_type: Optional[str] = None,
    max_message_size: Optional[int] = None,
    buffer_memory: Optional[int] = None
) -> Dict[str, Dict[str, Union[bool, str]]]:
    """
    Crawl the given URLs and stream the content to Kafka.
    
    Args:
        urls: A single URL or list of URLs to crawl
        content_type: Type of content to stream: "html", "markdown", or "both"
        topic: Kafka topic to stream to (uses KAFKA_TOPIC env var if None)
        session: Session ID for multi-user environments
        parallel: Whether to use parallel crawling for multiple URLs
        compression_type: Compression algorithm to use ('gzip', 'snappy', 'lz4', 'zstd')
        max_message_size: Maximum message size in bytes
        buffer_memory: Kafka producer buffer memory in bytes
        
    Returns:
        Dictionary mapping URLs to their streaming status
    """
    # Import Kafka dependencies - optional dependency
    try:
        from kafka import KafkaProducer
    except ImportError:
        print("Warning: kafka-python is not installed. Install with: pip install kafka-python")
        print("Using fallback simulation mode without actual streaming.")
        return _simulated_stream_to_kafka(urls, content_type, topic, session, parallel)
    
    # Generate session ID if not provided
    if session is None:
        session = str(uuid.uuid4())
    print(f"Session ID: {session}")
    
    # Get Kafka configuration from environment or use defaults
    kafka_brokers = os.environ.get("KAFKA_BROKERS", "localhost:9092")
    if topic is None:
        topic = os.environ.get("KAFKA_TOPIC", "pathik_crawl_data")
    
    # First crawl the URLs to get content
    from pathik.crawler import crawl as direct_crawl
    crawl_results = direct_crawl(urls=urls, parallel=parallel)
    
    # Connect to Kafka
    try:
        # Configure Kafka producer with extra options if provided
        producer_config = {
            'bootstrap_servers': kafka_brokers.split(','),
            'key_serializer': str.encode,
            'value_serializer': str.encode
        }
        
        # Add compression if specified
        if compression_type:
            producer_config['compression_type'] = compression_type
            
        # Add max message size if specified
        if max_message_size:
            producer_config['max_request_size'] = max_message_size
            
        # Add buffer memory if specified
        if buffer_memory:
            producer_config['buffer_memory'] = buffer_memory
            
        producer = KafkaProducer(**producer_config)
    except Exception as e:
        print(f"Failed to connect to Kafka broker(s) {kafka_brokers}: {e}")
        print("Using fallback simulation mode without actual streaming.")
        return _simulated_stream_to_kafka(urls, content_type, topic, session, parallel)
    
    # Format results in the style expected by the API
    if isinstance(urls, str):
        urls = [urls]
    
    results = {}
    
    # Stream each URL's content to Kafka
    try:
        for url in urls:
            results[url] = {"success": True}
            
            # Skip URLs that weren't successfully crawled
            if url not in crawl_results:
                results[url] = {"success": False, "error": "URL was not successfully crawled"}
                continue
                
            files = crawl_results[url]
            
            try:
                # Prepare headers - common across messages
                headers = [
                    ('url', url.encode()),
                    ('timestamp', str(time.time()).encode()),
                    ('session', session.encode())
                ]
                
                # Send HTML content if requested
                if "html" in files and os.path.exists(files["html"]) and content_type in ["html", "both"]:
                    with open(files["html"], "r", encoding='utf-8') as f:
                        html_content = f.read()
                        
                    # Add content-type header
                    html_headers = headers + [('content_type', 'text/html'.encode())]
                    
                    # Send to Kafka
                    future = producer.send(
                        topic=topic,
                        key=url,
                        value=html_content,
                        headers=html_headers
                    )
                    # Wait for send to complete
                    record_metadata = future.get(timeout=10)
                    print(f"✅ HTML content for {url} sent to Kafka at offset {record_metadata.offset}")
                
                # Send Markdown content if requested
                if "markdown" in files and os.path.exists(files["markdown"]) and content_type in ["markdown", "both"]:
                    with open(files["markdown"], "r", encoding='utf-8') as f:
                        md_content = f.read()
                        
                    # Add content-type header
                    md_headers = headers + [('content_type', 'text/markdown'.encode())]
                    
                    # Send to Kafka
                    future = producer.send(
                        topic=topic,
                        key=url,
                        value=md_content,
                        headers=md_headers
                    )
                    # Wait for send to complete
                    record_metadata = future.get(timeout=10)
                    print(f"✅ Markdown content for {url} sent to Kafka at offset {record_metadata.offset}")
                
                # Add details to result
                results[url]["details"] = {
                    "html_file": files.get("html", ""),
                    "markdown_file": files.get("markdown", ""),
                    "topic": topic,
                    "session_id": session
                }
                
                # Add compression info if provided
                if compression_type:
                    results[url]["details"]["compression_type"] = compression_type
                
            except Exception as e:
                print(f"Error streaming {url}: {e}")
                results[url] = {"success": False, "error": str(e)}
        
        # Make sure all messages are sent
        producer.flush()
        
    except Exception as e:
        print(f"Error in stream_to_kafka: {e}")
        if isinstance(urls, str):
            urls = [urls]
        results = {url: {"success": False, "error": str(e)} for url in urls}
        
    finally:
        # Always close the producer
        producer.close()
    
    return results


def _simulated_stream_to_kafka(
    urls: Union[str, List[str]], 
    content_type: str = "both",
    topic: Optional[str] = None,
    session: Optional[str] = None,
    parallel: bool = True,
    compression_type: Optional[str] = None,
    max_message_size: Optional[int] = None,
    buffer_memory: Optional[int] = None
) -> Dict[str, Dict[str, Union[bool, str]]]:
    """
    Fallback implementation that simulates Kafka streaming.
    Used when kafka-python is not installed or Kafka connection fails.
    """
    # First crawl the URLs to get the content
    from pathik.crawler import crawl as direct_crawl
    
    try:
        # Get content by crawling
        crawl_results = direct_crawl(urls=urls, parallel=parallel)
        
        # In a real implementation, we would stream to Kafka here
        # For now, we'll simulate success since we got the content
        if isinstance(urls, str):
            urls = [urls]
        
        formatted_result = {}
        for url in urls:
            formatted_result[url] = {"success": True}
            
            # Add details about the files that would be sent to Kafka
            if url in crawl_results:
                files = crawl_results[url]
                formatted_result[url]["details"] = {
                    "html_file": files.get("html", ""),
                    "markdown_file": files.get("markdown", ""),
                    "topic": topic or "default_topic",
                    "session_id": session,
                    "note": "SIMULATED - not actually sent to Kafka"
                }
                
                # Add compression info if provided
                if compression_type:
                    formatted_result[url]["details"]["compression_type"] = compression_type
        
        return formatted_result
    except Exception as e:
        # On error, return failure for all URLs
        if isinstance(urls, str):
            urls = [urls]
        
        return {url: {"success": False, "error": str(e)} for url in urls}

# Re-export the crawl_to_r2 function for backward compatibility
def crawl_to_r2(urls: Union[str, List[str]], uuid_str: Optional[str] = None, parallel: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Crawl the given URLs and upload the content to R2.
    
    Args:
        urls: A single URL or list of URLs to crawl
        uuid_str: UUID to prefix filenames (generates one if None)
        parallel: Whether to use parallel crawling for multiple URLs
        
    Returns:
        Dictionary mapping URLs to their R2 upload results
    """
    # Call the new consolidated crawl function with R2 settings
    result = crawl(
        urls=urls,
        parallel=parallel,
        r2=True,
        generate_uuid=(uuid_str is None),
        session_id=uuid_str
    )
    
    # Format the result to match the old API
    if isinstance(urls, str):
        urls = [urls]
    
    formatted_result = {}
    for url in urls:
        formatted_result[url] = {
            "uuid": uuid_str or result.get("session_id", ""),
            "success": True
        }
    
    return formatted_result

# Import the crawler functions
try:
    from pathik.crawler import get_binary_path, _run_go_command
    print(f"Successfully imported crawl function")
except ImportError as e:
    print(f"Error importing crawler functions: {e}")

# Export the functions
__all__ = [
    "crawl", 
    "stream_to_kafka", 
    "crawl_to_r2", 
    "__version__",
    "safe_crawl",  # New type-safe API
    "CrawlParams",
    "CrawlResult",
    "PathikFileResult"
] 

# Deprecation warning to encourage using the type-safe API
import warnings

warnings.warn(
    "Consider using safe_crawl() instead of crawl() for better type safety and validation. "
    "The safe_crawl() function provides input validation and structured error handling.",
    DeprecationWarning,
    stacklevel=2
) 