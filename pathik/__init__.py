# Print diagnostic information
import sys
import os
print(f"Loading pathik package from {__file__}")
print(f"Python path: {sys.path}")

# Set version
__version__ = "0.2.13"

# Import the crawler functions
try:
    from pathik.crawler import get_binary_path, _run_go_command
    from pathik.cli import crawl
    print(f"Successfully imported crawl function")
except ImportError as e:
    print(f"Error importing crawler functions: {e}")
    # Fallback direct definition
    import subprocess
    import tempfile
    import uuid
    import json
    from typing import List, Dict, Optional, Union, Literal, Any

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
        from .crawler import get_binary_path, get_binary_version, _run_go_command
        
        # Check if binary version matches package version
        binary_path = get_binary_path()
        binary_version = get_binary_version(binary_path)
        if binary_version != __version__:
            print(f"Binary version ({binary_version}) does not match package version ({__version__}), attempting to update...")
            binary_path = get_binary_path(force_download=True)
        
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
            # Prepare command arguments
            args = []
            
            # URL arguments - these should always come before option flags
            args.extend(urls)
            
            # Basic crawl options
            args.extend(["-o", output_dir])
            if parallel:
                args.append("-p")
            if selector:
                args.extend(["-s", selector])
            if selector_files:
                args.append("-sf")
            if num_workers != 4:
                args.extend(["-w", str(num_workers)])
            if timeout != 60:
                args.extend(["-t", str(timeout)])
            if limit != 1000:
                args.extend(["-l", str(limit)])
            if validate:
                args.append("-v")
            if skip_tls:
                args.append("-k")
            if delay > 0:
                args.extend(["-d", str(delay)])
            if chrome_path:
                args.extend(["-c", chrome_path])
            if hostname:
                args.extend(["-h", hostname])
            
            # R2 options
            if r2:
                args.append("-r2")
                
                if r2_account_id:
                    args.extend(["--r2-account-id", r2_account_id])
                if r2_access_key_id:
                    args.extend(["--r2-access-key-id", r2_access_key_id])
                if r2_access_key_secret:
                    args.extend(["--r2-access-key-secret", r2_access_key_secret])
                if r2_bucket_name:
                    args.extend(["--r2-bucket-name", r2_bucket_name])
                if r2_public:
                    args.append("--r2-public")
            
            # UUID option
            if generate_uuid:
                args.append("-uuid")
            
            # Content type option
            if content_type:
                args.extend(["--content-type", content_type])
            
            # Kafka options
            if kafka:
                args.append("-kafka")
                
                if kafka_brokers:
                    args.extend(["--kafka-brokers", kafka_brokers])
                if kafka_topic:
                    args.extend(["--kafka-topic", kafka_topic])
                if kafka_username:
                    args.extend(["--kafka-username", kafka_username])
                if kafka_password:
                    args.extend(["--kafka-password", kafka_password])
                if kafka_client_id:
                    args.extend(["--kafka-client-id", kafka_client_id])
                if kafka_use_tls:
                    args.append("--kafka-use-tls")
            
            # Session ID option
            if session_id:
                args.extend(["--session-id", session_id])

            # Run the command
            result = _run_go_command(binary_path, args)
            
            # Parse JSON result
            try:
                crawl_result = json.loads(result)
                
                # Add session ID to result if it was generated
                if session_id and 'session_id' not in crawl_result:
                    crawl_result['session_id'] = session_id
                    
                return crawl_result
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw result
                return {"raw_output": result, "session_id": session_id if session_id else None}
        
        finally:
            # Clean up temporary directory if we created one
            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    print(f"Warning: Failed to remove temporary directory: {temp_dir}")

# Export the functions
__all__ = ["crawl", "__version__"] 