#!/usr/bin/env python
"""
Type-safe API interface for pathik.

This module provides a type-safe wrapper around the pathik API functions,
ensuring that inputs and outputs are properly validated.
"""
from typing import List, Dict, Optional, Union, Any
import sys
import os
import json

# Import the schema validation
from pathik.schema import (
    CrawlParams,
    CrawlResult,
    PathikFileResult,
    KafkaStreamParams,
    KafkaStreamResult,
    validate_crawl_params,
    validate_crawl_result,
    validate_kafka_stream_params,
    validate_kafka_stream_result
)

# Import the actual implementation
from pathik.cli import crawl as _cli_crawl
from pathik.crawler import stream_to_kafka as _stream_to_kafka

def safe_crawl(
    urls: Union[str, List[str]], 
    output_dir: Optional[str] = None,
    parallel: bool = False,
    selector: Optional[str] = None,
    selector_files: bool = False,
    num_workers: int = 4,
    timeout: int = 60,
    limit: int = 1000,
    validate: bool = False,
    skip_tls: bool = False,
    delay: int = 0,
    chrome_path: Optional[str] = None,
    hostname: Optional[str] = None,
    r2: bool = False,
    r2_account_id: Optional[str] = None,
    r2_access_key_id: Optional[str] = None,
    r2_access_key_secret: Optional[str] = None,
    r2_bucket_name: Optional[str] = None,
    r2_public: bool = False,
    generate_uuid: bool = False,
    content_type: Optional[str] = None,
    kafka: bool = False,
    kafka_brokers: Optional[str] = None,
    kafka_topic: Optional[str] = None,
    kafka_username: Optional[str] = None,
    kafka_password: Optional[str] = None,
    kafka_client_id: Optional[str] = None,
    kafka_use_tls: bool = False,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Type-safe wrapper for the pathik crawl function.
    
    This function validates all inputs against a schema before passing them
    to the actual implementation, and validates the output before returning it.
    
    Args:
        urls: URL or list of URLs to crawl
        output_dir: Directory to save crawled files
        parallel: Process URLs in parallel
        selector: CSS selector to extract specific content
        selector_files: Save selector output to separate files
        num_workers: Number of workers for parallel crawling
        timeout: Timeout in seconds for each request
        limit: Maximum number of pages to crawl
        validate: Validate URLs before crawling
        skip_tls: Skip TLS certificate validation
        delay: Delay between requests in milliseconds
        chrome_path: Path to Chrome/Chromium executable
        hostname: Hostname for filtering URLs
        r2: Upload to R2
        r2_account_id: R2 account ID
        r2_access_key_id: R2 access key ID
        r2_access_key_secret: R2 access key secret
        r2_bucket_name: R2 bucket name
        r2_public: Make R2 objects public
        generate_uuid: Generate UUID for each crawled URL
        content_type: Filter content by type
        kafka: Stream to Kafka
        kafka_brokers: Kafka brokers
        kafka_topic: Kafka topic
        kafka_username: Kafka username
        kafka_password: Kafka password
        kafka_client_id: Kafka client ID
        kafka_use_tls: Use TLS for Kafka
        session_id: Session ID for grouping crawls
    
    Returns:
        Dictionary mapping URLs to their crawl results
    
    Raises:
        ValueError: If any input parameters fail validation
    """
    # Construct the parameters dictionary
    params = {
        "urls": urls,
        "output_dir": output_dir,
        "parallel": parallel,
        "selector": selector,
        "selector_files": selector_files,
        "num_workers": num_workers,
        "timeout": timeout,
        "limit": limit,
        "validate": validate,
        "skip_tls": skip_tls,
        "delay": delay,
        "chrome_path": chrome_path,
        "hostname": hostname,
        "r2": r2,
        "r2_account_id": r2_account_id,
        "r2_access_key_id": r2_access_key_id,
        "r2_access_key_secret": r2_access_key_secret,
        "r2_bucket_name": r2_bucket_name,
        "r2_public": r2_public,
        "generate_uuid": generate_uuid,
        "content_type": content_type,
        "kafka": kafka,
        "kafka_brokers": kafka_brokers,
        "kafka_topic": kafka_topic,
        "kafka_username": kafka_username,
        "kafka_password": kafka_password,
        "kafka_client_id": kafka_client_id,
        "kafka_use_tls": kafka_use_tls,
        "session_id": session_id,
    }
    
    # Validate input parameters
    try:
        validate_crawl_params(params)
    except ValueError as e:
        raise ValueError(f"Parameter validation failed: {e}")
    
    # Call the actual implementation
    try:
        result = _cli_crawl(**params)
        
        # Validate the result
        validated_result = validate_crawl_result(result)
        
        # Return the original result since it passed validation
        return result
    except Exception as e:
        # If an error occurs, create a structured error result
        if isinstance(urls, list):
            error_result = {url: {"success": False, "error": str(e)} for url in urls}
        else:
            error_result = {urls: {"success": False, "error": str(e)}}
        
        if session_id:
            error_result["session_id"] = session_id
            
        return error_result

def safe_stream_to_kafka(
    params_or_urls: Union[KafkaStreamParams, Union[str, List[str]]],
    content_type: Optional[str] = None,
    topic: Optional[str] = None,
    session_id: Optional[str] = None,
    parallel: bool = True,
    compression_type: Optional[str] = None,
    max_message_size: Optional[int] = None,
    buffer_memory: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Type-safe wrapper for streaming content to Kafka.
    
    Args:
        params_or_urls: Either a KafkaStreamParams object or a URL/list of URLs
        content_type: Type of content to stream ('html', 'markdown', or 'both')
        topic: Kafka topic to stream to
        session_id: Session ID for grouping messages
        parallel: Process URLs in parallel
        compression_type: Compression type ('gzip', 'snappy', 'lz4', 'zstd')
        max_message_size: Maximum message size in bytes
        buffer_memory: Buffer memory in bytes
        
    Returns:
        Dictionary with streaming results
        
    Raises:
        ValueError: If any input parameters fail validation
    """
    # Check if the input is a KafkaStreamParams object
    if isinstance(params_or_urls, KafkaStreamParams):
        # Extract parameters from the object
        urls = params_or_urls.urls
        content_type = params_or_urls.content_type
        topic = params_or_urls.topic
        session_id = params_or_urls.session_id
        parallel = params_or_urls.parallel
        compression_type = getattr(params_or_urls, 'compression_type', None)
        max_message_size = getattr(params_or_urls, 'max_message_size', None)
        buffer_memory = getattr(params_or_urls, 'buffer_memory', None)
    else:
        # Use the parameters directly
        urls = params_or_urls
    
    # Build the parameters dictionary
    params = {
        "urls": urls,
        "content_type": content_type,
        "topic": topic,
        "session": session_id,
        "parallel": parallel
    }
    
    # Add compression options if provided
    if compression_type:
        params["compression_type"] = compression_type
    if max_message_size:
        params["max_message_size"] = max_message_size
    if buffer_memory:
        params["buffer_memory"] = buffer_memory
    
    # Validate parameters
    try:
        validate_kafka_stream_params(params)
    except ValueError as e:
        raise ValueError(f"Parameter validation failed: {e}")
    
    # Call the actual implementation
    try:
        result = _stream_to_kafka(**params)
        
        # Add session_id to result if it's not already there
        if session_id and "session_id" not in result:
            result["session_id"] = session_id
            
        # Return the result
        return result
    except Exception as e:
        # Create a structured error result
        if isinstance(urls, list):
            error_result = {url: {"success": False, "error": str(e)} for url in urls}
        else:
            error_result = {urls: {"success": False, "error": str(e)}}
        
        # Add session_id if available
        if session_id:
            error_result["session_id"] = session_id
        
        return error_result 