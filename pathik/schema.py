#!/usr/bin/env python
"""
Type-safe schema definitions for the pathik API using Satya.

This module defines validation schemas for inputs and outputs of the pathik API,
ensuring type safety and proper validation of parameters and results.
"""
from typing import List, Dict, Optional, Union, Literal, Any
from enum import Enum
from datetime import datetime
from satya import Model, Field

class PathikFlag(str, Enum):
    """Supported flag types for pathik commands"""
    PARALLEL = "parallel"
    SELECTOR = "selector"
    SELECTOR_FILES = "selector_files"
    WORKERS = "workers"
    TIMEOUT = "timeout"
    LIMIT = "limit"
    VALIDATE = "validate"
    SKIP_TLS = "skip_tls"
    DELAY = "delay"
    CHROME_PATH = "chrome_path"
    HOSTNAME = "hostname"
    R2 = "r2"
    R2_ACCOUNT_ID = "r2_account_id"
    R2_ACCESS_KEY_ID = "r2_access_key_id"
    R2_ACCESS_KEY_SECRET = "r2_access_key_secret"
    R2_BUCKET_NAME = "r2_bucket_name"
    R2_PUBLIC = "r2_public"
    GENERATE_UUID = "generate_uuid"
    CONTENT_TYPE = "content_type"
    KAFKA = "kafka"
    KAFKA_BROKERS = "kafka_brokers"
    KAFKA_TOPIC = "kafka_topic"
    KAFKA_USERNAME = "kafka_username"
    KAFKA_PASSWORD = "kafka_password"
    KAFKA_CLIENT_ID = "kafka_client_id"
    KAFKA_USE_TLS = "kafka_use_tls"
    SESSION_ID = "session_id"

class PathikFileResult(Model):
    """Represents file outputs from a crawl operation"""
    html: Optional[str] = Field(
        required=False,
        description="Path to the HTML file",
        pattern=r'^\/.*\.html$'
    )
    markdown: Optional[str] = Field(
        required=False,
        description="Path to the Markdown file",
        pattern=r'^\/.*\.md$'
    )
    success: bool = Field(
        default=True,
        description="Whether the operation was successful"
    )
    error: Optional[str] = Field(
        required=False,
        description="Error message if the operation failed"
    )
    raw_output: Optional[str] = Field(
        required=False,
        description="Raw command output for debugging"
    )

class CrawlParams(Model):
    """Input parameters for the crawl operation"""
    urls: str = Field(
        description="URL or list of URLs to crawl"
    )
    output_dir: Optional[str] = Field(
        required=False,
        description="Directory to save crawled files"
    )
    parallel: bool = Field(
        default=False,
        description="Process URLs in parallel"
    )
    selector: Optional[str] = Field(
        required=False,
        description="CSS selector to extract specific content"
    )
    selector_files: bool = Field(
        default=False,
        description="Save selector output to separate files"
    )
    num_workers: int = Field(
        default=4,
        min_value=1,
        max_value=20,
        description="Number of workers for parallel crawling"
    )
    timeout: int = Field(
        default=60,
        min_value=1,
        max_value=300,
        description="Timeout in seconds for each request"
    )
    limit: int = Field(
        default=1000,
        min_value=1,
        max_value=10000,
        description="Maximum number of pages to crawl"
    )
    validate: bool = Field(
        default=False,
        description="Validate URLs before crawling"
    )
    skip_tls: bool = Field(
        default=False,
        description="Skip TLS certificate validation"
    )
    delay: int = Field(
        default=0,
        min_value=0,
        max_value=10000,
        description="Delay between requests in milliseconds"
    )
    chrome_path: Optional[str] = Field(
        required=False,
        description="Path to Chrome/Chromium executable"
    )
    hostname: Optional[str] = Field(
        required=False,
        description="Hostname for filtering URLs"
    )
    r2: bool = Field(
        default=False,
        description="Upload to R2"
    )
    r2_account_id: Optional[str] = Field(
        required=False,
        description="R2 account ID"
    )
    r2_access_key_id: Optional[str] = Field(
        required=False,
        description="R2 access key ID"
    )
    r2_access_key_secret: Optional[str] = Field(
        required=False,
        description="R2 access key secret"
    )
    r2_bucket_name: Optional[str] = Field(
        required=False,
        description="R2 bucket name"
    )
    r2_public: bool = Field(
        default=False,
        description="Make R2 objects public"
    )
    generate_uuid: bool = Field(
        default=False,
        description="Generate UUID for each crawled URL"
    )
    content_type: Optional[str] = Field(
        required=False,
        description="Filter content by type",
        enum=["html", "markdown", "both"]
    )
    kafka: bool = Field(
        default=False,
        description="Stream to Kafka"
    )
    kafka_brokers: Optional[str] = Field(
        required=False,
        description="Kafka brokers"
    )
    kafka_topic: Optional[str] = Field(
        required=False,
        description="Kafka topic"
    )
    kafka_username: Optional[str] = Field(
        required=False,
        description="Kafka username"
    )
    kafka_password: Optional[str] = Field(
        required=False,
        description="Kafka password"
    )
    kafka_client_id: Optional[str] = Field(
        required=False,
        description="Kafka client ID"
    )
    kafka_use_tls: bool = Field(
        default=False,
        description="Use TLS for Kafka"
    )
    session_id: Optional[str] = Field(
        required=False,
        description="Session ID for grouping crawls"
    )

class CrawlResult(Model):
    """Type-safe result from a crawl operation"""
    results: Dict[str, PathikFileResult] = Field(
        description="Mapping of URLs to their file results"
    )
    session_id: Optional[str] = Field(
        required=False,
        description="Session ID for multi-URL crawls"
    )

# Helper functions to validate inputs and outputs
def validate_crawl_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate crawl parameters against the schema"""
    # Make a copy of params to avoid modifying the original
    params_copy = params.copy()
    
    # Special handling for the 'urls' parameter
    if 'urls' in params_copy:
        urls = params_copy['urls']
        
        # Validate URL or list of URLs
        if isinstance(urls, str):
            # For single URL, just check if it looks like a URL
            if not urls.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL format: {urls} - must start with http:// or https://")
        elif isinstance(urls, list):
            # For list of URLs, validate each one
            for url in urls:
                if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                    raise ValueError(f"Invalid URL in list: {url} - must be a string starting with http:// or https://")
        else:
            raise ValueError(f"URLs must be a string or list of strings, got {type(urls)}")
    else:
        raise ValueError("Missing required parameter: urls")
    
    # Validate the rest of the parameters
    # Check num_workers
    if 'num_workers' in params_copy and (not isinstance(params_copy['num_workers'], int) or params_copy['num_workers'] < 1):
        raise ValueError(f"num_workers must be a positive integer, got {params_copy['num_workers']}")
    
    # Check timeout
    if 'timeout' in params_copy and (not isinstance(params_copy['timeout'], int) or params_copy['timeout'] < 1):
        raise ValueError(f"timeout must be a positive integer, got {params_copy['timeout']}")
    
    # Check limit
    if 'limit' in params_copy and (not isinstance(params_copy['limit'], int) or params_copy['limit'] < 1):
        raise ValueError(f"limit must be a positive integer, got {params_copy['limit']}")
    
    # Check delay
    if 'delay' in params_copy and (not isinstance(params_copy['delay'], int) or params_copy['delay'] < 0):
        raise ValueError(f"delay must be a non-negative integer, got {params_copy['delay']}")
    
    # Check content_type
    if 'content_type' in params_copy and params_copy['content_type'] is not None:
        if params_copy['content_type'] not in ["html", "markdown", "both"]:
            raise ValueError(f"content_type must be one of 'html', 'markdown', or 'both', got {params_copy['content_type']}")
    
    # All validation passed
    return params

def validate_crawl_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Validate crawl results against the schema"""
    # Transform the result into the expected format if needed
    if not isinstance(result, dict):
        raise ValueError(f"Expected dict result, got {type(result)}")
    
    # Extract session ID if present
    session_id = None
    if "session_id" in result:
        session_id = result.pop("session_id")
    
    # Validate each URL result
    for url, data in result.items():
        if not isinstance(url, str):
            raise ValueError(f"URL keys must be strings, got {type(url)}")
            
        if not isinstance(data, dict):
            raise ValueError(f"URL values must be dictionaries, got {type(data)} for URL {url}")
        
        # Required fields
        if "success" not in data:
            # If success field is missing, add it based on presence of error
            data["success"] = "error" not in data
        
        # Validate types of common fields if present
        if "html" in data and data["html"] is not None and not isinstance(data["html"], str):
            raise ValueError(f"html path must be a string, got {type(data['html'])} for URL {url}")
            
        if "markdown" in data and data["markdown"] is not None and not isinstance(data["markdown"], str):
            raise ValueError(f"markdown path must be a string, got {type(data['markdown'])} for URL {url}")
            
        if "error" in data and data["error"] is not None and not isinstance(data["error"], str):
            raise ValueError(f"error message must be a string, got {type(data['error'])} for URL {url}")
    
    # Add back session ID if it was present
    if session_id is not None:
        result["session_id"] = session_id
    
    return result 