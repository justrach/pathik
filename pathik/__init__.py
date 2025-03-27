# Print diagnostic information
import sys
import os
print(f"Loading pathik package from {__file__}")
print(f"Python path: {sys.path}")

# Set version
__version__ = "0.2.13"

# Import the crawler functions
try:
    from pathik.crawler import crawl, crawl_to_r2
    print(f"Successfully imported crawl and crawl_to_r2 functions")
except ImportError as e:
    print(f"Error importing crawler functions: {e}")
    # Fallback direct definition
    import subprocess
    import tempfile
    import uuid
    from typing import List, Dict, Optional

    def crawl(urls: List[str], output_dir: Optional[str] = None, parallel: bool = True) -> Dict[str, Dict[str, str]]:
        """Crawl function that uses the binary to crawl the given URLs"""
        from .crawler import get_binary_path
        
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

    def crawl_to_r2(urls: List[str], uuid_str: Optional[str] = None, parallel: bool = True) -> Dict[str, Dict[str, str]]:
        """Upload to R2 function that uses the binary to upload the given URLs"""
        from .crawler import get_binary_path
        
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

# Export the functions
__all__ = ["crawl", "crawl_to_r2", "__version__"] 