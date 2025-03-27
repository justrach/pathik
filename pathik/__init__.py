# Print diagnostic information
import sys
import os
print(f"Loading pathik package from {__file__}")
print(f"Python path: {sys.path}")

# Set version
__version__ = "0.2.13"

# Import the crawler functions
try:
    from pathik.crawler import crawl, crawl_to_r2, stream_to_kafka
    print(f"Successfully imported crawl, crawl_to_r2, and stream_to_kafka functions")
except ImportError as e:
    print(f"Error importing crawler functions: {e}")
    # Fallback direct definition
    import subprocess
    import tempfile
    import uuid
    from typing import List, Dict, Optional, Union, Literal

    def crawl(urls: Union[str, List[str]], output_dir: Optional[str] = None, parallel: bool = True) -> Dict[str, Dict[str, str]]:
        """
        Crawl the given URLs and save the content locally.
        
        Args:
            urls: A single URL or list of URLs to crawl
            output_dir: Directory to save output (creates temp dir if None)
            parallel: Whether to use parallel crawling for multiple URLs
            
        Returns:
            Dictionary mapping URLs to their crawl results
        """
        from .crawler import get_binary_path
        
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
            
        result = {}
        temp_dir = None
        
        if not output_dir:
            # Create temporary directory if no output_dir specified
            temp_dir = tempfile.mkdtemp(prefix="pathik_")
            output_dir = temp_dir
            print(f"Created temporary directory: {temp_dir}")
        
        try:
            binary_path = get_binary_path()
            
            # Prepare command
            cmd = [binary_path, "-crawl", f"-outdir={output_dir}"]
            if not parallel:
                cmd.append("-parallel=false")
            cmd.extend(urls)
            
            print(f"crawl() called with urls={urls}, output_dir={output_dir}, parallel={parallel}")
            
            # Run command
            subprocess.run(cmd, check=True)
            
            # Collect results
            for url in urls:
                result[url] = {}
                # TODO: Add result collection logic
        except Exception as e:
            print(f"Error in crawl function: {e}")
            for url in urls:
                if url not in result:
                    result[url] = {"error": str(e)}
        
        return result

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
        from .crawler import get_binary_path
        
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
            
        result = {}
        if not uuid_str:
            uuid_str = str(uuid.uuid4())
        
        try:
            binary_path = get_binary_path()
            
            # Prepare command
            cmd = [binary_path, "-r2", f"-uuid={uuid_str}"]
            if not parallel:
                cmd.append("-parallel=false")
            cmd.extend(urls)
            
            # Run command
            subprocess.run(cmd, check=True)
            
            # Collect results
            for url in urls:
                result[url] = {
                    "uuid": uuid_str,
                    # TODO: Add more result details
                }
        except Exception as e:
            print(f"Error in crawl_to_r2 function: {e}")
            for url in urls:
                if url not in result:
                    result[url] = {"error": str(e)}
        
        return result
        
    def stream_to_kafka(
        urls: Union[str, List[str]], 
        content_type: Literal["html", "markdown", "both"] = "both",
        topic: Optional[str] = None,
        session: Optional[str] = None,
        parallel: bool = True
    ) -> Dict[str, Dict[str, Union[bool, str]]]:
        """
        Crawl the given URLs and stream the content to Kafka.
        
        Args:
            urls: A single URL or list of URLs to crawl
            content_type: Type of content to stream: "html", "markdown", or "both"
            topic: Kafka topic to stream to (uses KAFKA_TOPIC env var if None)
            session: Session ID for multi-user environments
            parallel: Whether to use parallel crawling for multiple URLs
            
        Returns:
            Dictionary mapping URLs to their streaming status
        """
        from .crawler import get_binary_path
        
        # Convert single URL to list
        if isinstance(urls, str):
            urls = [urls]
            
        result = {}
        
        try:
            binary_path = get_binary_path()
            
            # Prepare command
            cmd = [binary_path, "-kafka"]
            
            # Add parallel flag if needed
            if not parallel:
                cmd.append("-parallel=false")
            
            # Add content type if not 'both'
            if content_type != "both":
                cmd.extend(["-content", content_type])
            
            # Add topic if specified
            if topic:
                cmd.extend(["-topic", topic])
            
            # Add session ID if provided
            if session:
                cmd.extend(["-session", session])
            
            # Add URLs
            cmd.extend(urls)
            
            print(f"stream_to_kafka() called with urls={urls}, content_type={content_type}, topic={topic}, session={session}, parallel={parallel}")
            
            # Run command
            process = subprocess.run(cmd, check=True)
            
            # Process successful, mark all URLs as success
            if process.returncode == 0:
                for url in urls:
                    result[url] = {"success": True}
            else:
                # Command failed but didn't raise an exception
                for url in urls:
                    result[url] = {"success": False, "error": f"Command failed with exit code {process.returncode}"}
                    
        except Exception as e:
            print(f"Error in stream_to_kafka function: {e}")
            for url in urls:
                if url not in result:
                    result[url] = {"success": False, "error": str(e)}
        
        return result

# Export the functions
__all__ = ["crawl", "crawl_to_r2", "stream_to_kafka", "__version__"] 