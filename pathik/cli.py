#!/usr/bin/env python
"""
Command-line interface for the pathik crawler
"""
import argparse
import sys
import os
import json
import subprocess
import tempfile
import datetime
import uuid
import shutil
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

# Fix the import to use direct import instead of relative
import pathik
from pathik.crawler import get_binary_path, _run_go_command, CrawlerError
from pathik import __version__

def check_binary_version():
    """Check if the binary version matches the package version and update if needed"""
    try:
        # This will automatically check version and download if needed
        get_binary_path(force_download=False)
    except Exception as e:
        print(f"Warning: Error checking binary version: {e}")

def crawl(urls: Union[str, List[str]], 
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
    Crawl URLs and save the results
    
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
        Dictionary with crawl results
    """
    # First ensure we have the correct binary version
    check_binary_version()
    
    # If session_id is not provided, generate a unique one
    if not session_id and (kafka or r2):
        session_id = str(uuid.uuid4())
        print(f"Generated session ID: {session_id}")
    
    if isinstance(urls, str):
        urls = [urls]
    
    # Create a temporary directory for output if none provided
    temp_dir = None
    if not output_dir:
        temp_dir = tempfile.mkdtemp(prefix="pathik_crawl_")
        output_dir = temp_dir
    
    try:
        # Get the binary path
        binary_path = get_binary_path()
        
        # FIXED: Prepare the command with correct order:
        # binary [options] -crawl URLs
        command = [binary_path]
        
        # Add output directory BEFORE -crawl
        command.extend(["-outdir", output_dir])
        
        # Add basic options BEFORE -crawl
        if parallel:
            command.append("-parallel")
        if selector:
            command.extend(["-s", selector])
        if selector_files:
            command.append("-sf")
        if num_workers != 4:
            command.extend(["-w", str(num_workers)])
        if timeout != 60:
            command.extend(["-t", str(timeout)])
        if limit != 1000:
            command.extend(["-l", str(limit)])
        if validate:
            command.append("-v")
        if skip_tls:
            command.append("-k")
        if delay > 0:
            command.extend(["-d", str(delay)])
        if chrome_path:
            command.extend(["-c", chrome_path])
        if hostname:
            command.extend(["-h", hostname])
        
        # R2 options
        if r2:
            command.append("-r2")
            
            if r2_account_id:
                command.extend(["--r2-account-id", r2_account_id])
            if r2_access_key_id:
                command.extend(["--r2-access-key-id", r2_access_key_id])
            if r2_access_key_secret:
                command.extend(["--r2-access-key-secret", r2_access_key_secret])
            if r2_bucket_name:
                command.extend(["--r2-bucket-name", r2_bucket_name])
            if r2_public:
                command.append("--r2-public")
        
        # UUID option
        if generate_uuid:
            command.append("-uuid")
        
        # Content type option
        if content_type:
            command.extend(["-content", content_type])
        
        # Kafka options
        if kafka:
            command.append("-kafka")
            
            if kafka_brokers:
                command.extend(["--kafka-brokers", kafka_brokers])
            if kafka_topic:
                command.extend(["--kafka-topic", kafka_topic])
            if kafka_username:
                command.extend(["--kafka-username", kafka_username])
            if kafka_password:
                command.extend(["--kafka-password", kafka_password])
            if kafka_client_id:
                command.extend(["--kafka-client-id", kafka_client_id])
            if kafka_use_tls:
                command.append("--kafka-use-tls")
        
        # Session ID option
        if session_id:
            command.extend(["--session-id", session_id])
            
        # Add -crawl flag AFTER options
        command.append("-crawl")
        
        # Add URLs AFTER -crawl
        command.extend(urls)
        
        # Run the command
        print(f"Running command: {' '.join(command)}")
        stdout, stderr = _run_go_command(command)
        
        # Parse JSON result
        try:
            crawl_result = json.loads(stdout)
            
            # Add session ID to result if it was generated
            if session_id and 'session_id' not in crawl_result:
                crawl_result['session_id'] = session_id
                
            return crawl_result
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured result from raw output
            # Format: map URLs to file paths found in the output
            result = {}
            
            import re
            
            if urls:
                # Try to extract URLs and file paths from the output
                for url in urls:
                    url_result = {
                        "success": "Saved to" in stdout,
                        "raw_output": stdout
                    }
                    
                    # Extract file paths from stdout
                    html_pattern = re.compile(r"Saved to (\S+\.html)")
                    md_pattern = re.compile(r"Saved to (\S+\.m)")
                    
                    html_matches = html_pattern.findall(stdout)
                    md_matches = md_pattern.findall(stdout)
                    
                    if html_matches:
                        url_result["html"] = html_matches[0]
                    if md_matches:
                        # Add the "d" back to the ".m..." extension
                        url_result["markdown"] = md_matches[0] + "d"
                    
                    # If no matches found but output directory exists, check for files
                    if not html_matches and not md_matches and output_dir and os.path.exists(output_dir):
                        from pathik.crawler import _find_files_for_url
                        html_file, md_file = _find_files_for_url(output_dir, url)
                        if html_file:
                            url_result["html"] = html_file
                        if md_file:
                            url_result["markdown"] = md_file
                    
                    result[url] = url_result
            
            # Include the raw output as an internal value
            if session_id:
                result["session_id"] = session_id
                
            return result
    
    finally:
        # Clean up temporary directory if we created one
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                print(f"Warning: Failed to remove temporary directory: {temp_dir}")

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(
        description="""Pathik - Web Crawler CLI
        
Examples:
  pathik crawl https://example.com -o ./output
  pathik r2 https://example.com --r2-bucket-name my-bucket
  pathik kafka https://example.com --kafka-brokers localhost:9092
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', 
                      version=f'Pathik {__version__}')
    parser.add_argument('--check-binary', action='store_true',
                      help='Check if binary is up to date and update if needed')
    parser.add_argument('--force-update-binary', action='store_true',
                      help='Force update of the pathik binary')
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create subparser for the 'crawl' command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl URLs")
    crawl_parser.add_argument("urls", nargs="+", help="URLs to crawl")
    crawl_parser.add_argument("-o", "--output-dir", help="Output directory")
    crawl_parser.add_argument("-p", "--parallel", action="store_true", help="Process URLs in parallel")
    crawl_parser.add_argument("-s", "--selector", help="CSS selector to extract specific content")
    crawl_parser.add_argument("-sf", "--selector-files", action="store_true", help="Save selector output to separate files")
    crawl_parser.add_argument("-w", "--workers", type=int, default=4, help="Number of workers for parallel crawling")
    crawl_parser.add_argument("-t", "--timeout", type=int, default=60, help="Timeout in seconds for each request")
    crawl_parser.add_argument("-l", "--limit", type=int, default=1000, help="Maximum number of pages to crawl")
    crawl_parser.add_argument("-v", "--validate", action="store_true", help="Validate URLs before crawling")
    crawl_parser.add_argument("-k", "--skip-tls", action="store_true", help="Skip TLS certificate validation")
    crawl_parser.add_argument("-d", "--delay", type=int, default=0, help="Delay between requests in milliseconds")
    crawl_parser.add_argument("-c", "--chrome-path", help="Path to Chrome/Chromium executable")
    crawl_parser.add_argument("-h", "--hostname", help="Hostname for filtering URLs")
    crawl_parser.add_argument("--uuid", action="store_true", help="Generate UUID for each crawled URL")
    crawl_parser.add_argument("--content-type", help="Filter by content type")
    crawl_parser.add_argument("--session-id", help="Session ID for grouping crawls")
    
    # Create subparser for the 'r2' command (crawl + R2 upload)
    r2_parser = subparsers.add_parser("r2", help="Crawl URLs and upload to R2")
    r2_parser.add_argument("urls", nargs="+", help="URLs to crawl")
    r2_parser.add_argument("-o", "--output-dir", help="Output directory")
    r2_parser.add_argument("-p", "--parallel", action="store_true", help="Process URLs in parallel")
    r2_parser.add_argument("-s", "--selector", help="CSS selector to extract specific content")
    r2_parser.add_argument("-sf", "--selector-files", action="store_true", help="Save selector output to separate files")
    r2_parser.add_argument("-w", "--workers", type=int, default=4, help="Number of workers for parallel crawling")
    r2_parser.add_argument("-t", "--timeout", type=int, default=60, help="Timeout in seconds for each request")
    r2_parser.add_argument("-l", "--limit", type=int, default=1000, help="Maximum number of pages to crawl")
    r2_parser.add_argument("-v", "--validate", action="store_true", help="Validate URLs before crawling")
    r2_parser.add_argument("-k", "--skip-tls", action="store_true", help="Skip TLS certificate validation")
    r2_parser.add_argument("-d", "--delay", type=int, default=0, help="Delay between requests in milliseconds")
    r2_parser.add_argument("-c", "--chrome-path", help="Path to Chrome/Chromium executable")
    r2_parser.add_argument("-h", "--hostname", help="Hostname for filtering URLs")
    r2_parser.add_argument("--uuid", action="store_true", help="Generate UUID for each crawled URL")
    r2_parser.add_argument("--content-type", help="Filter by content type")
    r2_parser.add_argument("--r2-account-id", help="R2 account ID")
    r2_parser.add_argument("--r2-access-key-id", help="R2 access key ID")
    r2_parser.add_argument("--r2-access-key-secret", help="R2 access key secret")
    r2_parser.add_argument("--r2-bucket-name", help="R2 bucket name")
    r2_parser.add_argument("--r2-public", action="store_true", help="Make R2 objects public")
    r2_parser.add_argument("--session-id", help="Session ID for grouping crawls")
    
    # Create subparser for the 'kafka' command (crawl + Kafka streaming)
    kafka_parser = subparsers.add_parser("kafka", help="Crawl URLs and stream to Kafka")
    kafka_parser.add_argument("urls", nargs="+", help="URLs to crawl")
    kafka_parser.add_argument("-o", "--output-dir", help="Output directory")
    kafka_parser.add_argument("-p", "--parallel", action="store_true", help="Process URLs in parallel")
    kafka_parser.add_argument("-s", "--selector", help="CSS selector to extract specific content")
    kafka_parser.add_argument("-sf", "--selector-files", action="store_true", help="Save selector output to separate files")
    kafka_parser.add_argument("-w", "--workers", type=int, default=4, help="Number of workers for parallel crawling")
    kafka_parser.add_argument("-t", "--timeout", type=int, default=60, help="Timeout in seconds for each request")
    kafka_parser.add_argument("-l", "--limit", type=int, default=1000, help="Maximum number of pages to crawl")
    kafka_parser.add_argument("-v", "--validate", action="store_true", help="Validate URLs before crawling")
    kafka_parser.add_argument("-k", "--skip-tls", action="store_true", help="Skip TLS certificate validation")
    kafka_parser.add_argument("-d", "--delay", type=int, default=0, help="Delay between requests in milliseconds")
    kafka_parser.add_argument("-c", "--chrome-path", help="Path to Chrome/Chromium executable")
    kafka_parser.add_argument("-h", "--hostname", help="Hostname for filtering URLs")
    kafka_parser.add_argument("--uuid", action="store_true", help="Generate UUID for each crawled URL")
    kafka_parser.add_argument("--content-type", help="Filter by content type")
    kafka_parser.add_argument("--kafka-brokers", help="Kafka brokers")
    kafka_parser.add_argument("--kafka-topic", help="Kafka topic")
    kafka_parser.add_argument("--kafka-username", help="Kafka username")
    kafka_parser.add_argument("--kafka-password", help="Kafka password")
    kafka_parser.add_argument("--kafka-client-id", help="Kafka client ID")
    kafka_parser.add_argument("--kafka-use-tls", action="store_true", help="Use TLS for Kafka connection")
    kafka_parser.add_argument("--session-id", help="Session ID for grouping crawls")
    kafka_parser.add_argument("--compression", choices=["gzip", "snappy", "lz4", "zstd"], 
                         help="Compression algorithm to use for Kafka messages")
    kafka_parser.add_argument("--max-message-size", type=int, 
                         help="Maximum message size in bytes (default: 10MB)")
    kafka_parser.add_argument("--buffer-memory", type=int, 
                         help="Kafka producer buffer memory in bytes (default: 100MB)")
    
    # Create subparser for the 'version' command
    version_parser = subparsers.add_parser("version", help="Print version information")
    
    args = parser.parse_args()
    
    # If version check or binary update is requested, handle it and exit
    if args.check_binary:
        try:
            check_binary_version()
            print("Binary is up to date.")
            return 0
        except Exception as e:
            print(f"Error checking binary: {e}")
            return 1
            
    if args.force_update_binary:
        try:
            binary_path = get_binary_path(force_download=True)
            print(f"Binary updated successfully at: {binary_path}")
            return 0
        except Exception as e:
            print(f"Error updating binary: {e}")
            return 1
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "crawl":
            result = crawl(
                urls=args.urls, 
                output_dir=args.output_dir, 
                parallel=args.parallel,
                selector=args.selector,
                selector_files=args.selector_files,
                num_workers=args.workers,
                timeout=args.timeout,
                limit=args.limit,
                validate=args.validate,
                skip_tls=args.skip_tls,
                delay=args.delay,
                chrome_path=args.chrome_path,
                hostname=args.hostname,
                r2=args.r2,
                r2_account_id=args.r2_account_id,
                r2_access_key_id=args.r2_access_key_id,
                r2_access_key_secret=args.r2_access_key_secret,
                r2_bucket_name=args.r2_bucket_name,
                r2_public=args.r2_public,
                generate_uuid=args.uuid,
                content_type=args.content_type,
                kafka=args.kafka,
                kafka_brokers=args.kafka_brokers,
                kafka_topic=args.kafka_topic,
                kafka_username=args.kafka_username,
                kafka_password=args.kafka_password,
                kafka_client_id=args.kafka_client_id,
                kafka_use_tls=args.kafka_use_tls,
                session_id=args.session_id
            )
            
            # Print results summary
            print("\nCrawl Results:")
            print("--------------")
            for url, info in result.items():
                if "error" in info:
                    print(f"❌ {url}: Error - {info['error']}")
                else:
                    print(f"✅ {url}: Success")
                    print(f"   HTML: {info.get('html', 'Not found')}")
                    print(f"   Markdown: {info.get('markdown', 'Not found')}")
            
            # Also write results to a JSON file if output directory is specified
            if args.output_dir:
                results_file = os.path.join(args.output_dir, "pathik_results.json")
                with open(results_file, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"\nResults saved to: {results_file}")
        
        elif args.command == "r2":
            result = crawl(
                urls=args.urls,
                output_dir=args.output_dir,
                parallel=args.parallel,
                selector=args.selector,
                selector_files=args.selector_files,
                num_workers=args.workers,
                timeout=args.timeout,
                limit=args.limit,
                validate=args.validate,
                skip_tls=args.skip_tls,
                delay=args.delay,
                chrome_path=args.chrome_path,
                hostname=args.hostname,
                r2=True,
                r2_account_id=args.r2_account_id,
                r2_access_key_id=args.r2_access_key_id,
                r2_access_key_secret=args.r2_access_key_secret,
                r2_bucket_name=args.r2_bucket_name,
                r2_public=args.r2_public,
                generate_uuid=args.uuid,
                content_type=args.content_type,
                kafka=False,
                session_id=args.session_id
            )
            
            # Print results summary
            print("\nR2 Upload Results:")
            print("-----------------")
            for url, info in result.items():
                print(f"✅ {url}")
                print(f"   UUID: {info.get('uuid')}")
                print(f"   HTML Key: {info.get('r2_html_key')}")
                print(f"   Markdown Key: {info.get('r2_markdown_key')}")
        
        elif args.command == "kafka":
            # Import the stream_to_kafka function directly for Kafka streaming
            from pathik.crawler import stream_to_kafka
            
            try:
                # Use the stream_to_kafka function directly
                result = stream_to_kafka(
                    urls=args.urls,
                    content_type=args.content_type,
                    topic=args.kafka_topic,
                    session=args.session_id,
                    parallel=args.parallel,
                    compression_type=args.compression,
                    max_message_size=args.max_message_size,
                    buffer_memory=args.buffer_memory
                )
                
                print("\nKafka Streaming Results:")
                print("-----------------------")
                
                success_count = 0
                failure_count = 0
                
                for url, info in result.items():
                    if info.get("success", False):
                        success_count += 1
                        print(f"✅ {url}: Successfully streamed")
                        # Print details if available
                        if "details" in info:
                            details = info["details"]
                            if "topic" in details:
                                print(f"   Topic: {details['topic']}")
                            if "compression_type" in details:
                                print(f"   Compression: {details['compression_type']}")
                            if "html_file" in details:
                                print(f"   HTML content: {os.path.basename(details['html_file'])}")
                            if "markdown_file" in details:
                                print(f"   Markdown content: {os.path.basename(details['markdown_file'])}")
                    else:
                        failure_count += 1
                        print(f"❌ {url}: Failed - {info.get('error', 'Unknown error')}")
                
                print(f"\nSuccessfully streamed {success_count} out of {len(args.urls)} URLs")
                if failure_count > 0:
                    print(f"Failed to stream {failure_count} URLs")
            except Exception as e:
                print(f"❌ Error streaming to Kafka: {e}")
                return 1
        
        elif args.command == "version":
            print(f"Pathik v{pathik.__version__}")
            return 0
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 