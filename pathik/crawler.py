import os
import subprocess
import tempfile
import uuid
from typing import List, Dict, Tuple, Optional, Union
import sys
import json
import platform

# Add debugging output
print("Loading pathik.crawler module")
print("Current directory:", os.getcwd())
print("Module path:", __file__)

class CrawlerError(Exception):
    """Exception raised for errors in the crawler."""
    pass


def get_binary_path():
    """Get the path to the pathik binary"""
    # First, check if running from source or installed package
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine binary name based on platform
    binary_name = "pathik_bin"
    if platform.system() == "Windows":
        binary_name += ".exe"
    
    # Check if binary exists in the package directory
    binary_path = os.path.join(current_dir, binary_name)
    
    if os.path.exists(binary_path):
        return binary_path
    
    # If not found in package directory, it could be in site-packages
    if hasattr(sys, 'prefix'):
        site_packages_binary = os.path.join(sys.prefix, 'lib', 
                                            f'python{sys.version_info.major}.{sys.version_info.minor}', 
                                            'site-packages', 'pathik', binary_name)
        if os.path.exists(site_packages_binary):
            return site_packages_binary
    
    # As a fallback, check if it's in the same directory as the module
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    module_dir_binary = os.path.join(current_file_dir, binary_name)
    if os.path.exists(module_dir_binary):
        return module_dir_binary
    
    raise FileNotFoundError(f"Pathik binary not found at {current_dir}")


def _run_go_command(command: List[str]) -> Tuple[str, str]:
    """
    Run a Go command and return stdout and stderr.
    
    Args:
        command: The command to run as a list of strings
    
    Returns:
        A tuple of (stdout, stderr)
        
    Raises:
        CrawlerError: If the command fails
    """
    print(f"Running command: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        print(f"Command stdout: {stdout[:200]}...")
        print(f"Command stderr: {stderr[:200]}...")
        
        if process.returncode != 0:
            raise CrawlerError(f"Command failed with code {process.returncode}: {stderr}")
        
        return stdout, stderr
    except Exception as e:
        raise CrawlerError(f"Failed to run command: {e}")


def crawl(urls: List[str], output_dir: Optional[str] = None, parallel: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Crawl the specified URLs and return paths to the downloaded files.
    
    Args:
        urls: A list of URLs to crawl or a single URL string
        output_dir: Directory to save the crawled files (uses temp dir if None)
        parallel: Whether to use parallel crawling (default: True)
    
    Returns:
        A dictionary mapping URLs to file paths: 
        {url: {"html": html_path, "markdown": markdown_path}}
    """
    print(f"crawl() called with urls={urls}, output_dir={output_dir}, parallel={parallel}")
    
    # Convert single URL to list
    if isinstance(urls, str):
        urls = [urls]
        
    if not urls:
        raise ValueError("No URLs provided")
    
    # Use provided output directory or create a temporary one
    use_temp_dir = output_dir is None
    if use_temp_dir:
        output_dir = tempfile.mkdtemp(prefix="pathik_")
        print(f"Created temporary directory: {output_dir}")
    else:
        # Convert to absolute path
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        print(f"Using provided directory: {output_dir}")
    
    # Find pathik binary
    binary_path = get_binary_path()
    
    print(f"Using binary at: {binary_path}")
    
    # Create the command
    result = {}
    
    # Process URLs based on parallel flag
    if parallel and len(urls) > 1:
        # Use parallel processing with -parallel flag
        try:
            command = [binary_path, "-crawl", "-parallel", "-outdir", output_dir] + urls
            print(f"Running parallel command: {' '.join(command)}")
            
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                print(f"Error: {process.stderr}")
                raise CrawlerError(f"Command failed with code {process.returncode}: {process.stderr}")
                
            print(f"Command stdout: {process.stdout[:200]}...")
            
            # Find files for each URL
            for url in urls:
                html_file, md_file = _find_files_for_url(output_dir, url)
                result[url] = {
                    "html": html_file,
                    "markdown": md_file
                }
                
                # Check for successful crawl
                if not html_file or not md_file:
                    print(f"Warning: Files not found for {url}")
        except Exception as e:
            print(f"Error during parallel crawling: {e}")
            # Fall back to sequential processing on error
            print("Falling back to sequential processing...")
            parallel = False
    
    # Process URLs sequentially if not parallel or parallel failed
    if not parallel or len(urls) == 1:
        for url in urls:
            try:
                command = [binary_path, "-crawl", "-outdir", output_dir, url]
                print(f"Running command: {' '.join(command)}")
                
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if process.returncode != 0:
                    print(f"Error: {process.stderr}")
                    result[url] = {"error": process.stderr}
                    continue
                    
                print(f"Command stdout: {process.stdout[:200]}...")
                
                # Find files for this URL
                html_file, md_file = _find_files_for_url(output_dir, url)
                result[url] = {
                    "html": html_file,
                    "markdown": md_file
                }
            except Exception as e:
                print(f"Error processing {url}: {e}")
                result[url] = {"error": str(e)}
    
    return result


def crawl_to_r2(urls: List[str], uuid_str: Optional[str] = None, parallel: bool = True) -> Dict[str, Dict[str, str]]:
    """
    Crawl the specified URLs and upload the results to R2.
    
    Args:
        urls: A list of URLs to crawl or a single URL string
        uuid_str: UUID to prefix filenames (generates one if None)
        parallel: Whether to use parallel crawling (default: True)
    
    Returns:
        A dictionary with upload information
    """
    # Convert single URL to list
    if isinstance(urls, str):
        urls = [urls]
        
    if not urls:
        raise ValueError("No URLs provided")
    
    # Generate UUID if not provided
    if uuid_str is None:
        uuid_str = str(uuid.uuid4())
    
    # Create a temporary directory for the crawled files
    temp_dir = tempfile.mkdtemp(prefix="pathik_")
    
    try:
        # First crawl the URLs with local storage using parallel flag
        crawl_result = crawl(urls, output_dir=temp_dir, parallel=parallel)
        
        # Process results
        result = {}
        
        # Upload each URL individually
        for url in urls:
            # Create the command for this URL
            binary_path = get_binary_path()
            command = [binary_path, "-r2", "-uuid", uuid_str, "-dir", temp_dir, url]
            
            current_dir = os.getcwd()
            try:
                os.chdir(os.path.dirname(os.path.abspath(__file__)))
                print(f"Running command: {' '.join(command)}")
                
                process = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if process.returncode != 0:
                    print(f"Error: {process.stderr}")
                    raise CrawlerError(f"Command failed with code {process.returncode}: {process.stderr}")
                    
                print(f"Command stdout: {process.stdout[:200]}...")
                
                # Add result for this URL
                result[url] = {
                    "uuid": uuid_str,
                    "r2_html_key": f"{uuid_str}+{_sanitize_url(url)}.html",
                    "r2_markdown_key": f"{uuid_str}+{_sanitize_url(url)}.md",
                    "local_html_file": crawl_result[url].get("html"),
                    "local_markdown_file": crawl_result[url].get("markdown")
                }
            finally:
                os.chdir(current_dir)
        
        return result
    finally:
        # Keep the temp directory for debugging
        print(f"Temporary directory with files: {temp_dir}")


def _find_files_for_url(directory: str, url: str) -> Tuple[str, str]:
    """
    Find HTML and MD files for a given URL in the specified directory.
    
    Args:
        directory: Directory to search in
        url: URL to find files for
        
    Returns:
        A tuple of (html_file_path, md_file_path)
    """
    print(f"Looking for files in {directory} for URL {url}")
    # Check if directory exists
    if not os.path.exists(directory):
        print(f"WARNING: Directory {directory} does not exist!")
        return "", ""
    
    # List directory contents to help with debugging
    print(f"Directory contents: {os.listdir(directory)}")
    
    domain = _get_domain_name_for_file(url)
    print(f"Domain name for file: {domain}")
    
    html_file = ""
    md_file = ""
    
    for filename in os.listdir(directory):
        print(f"Checking file: {filename}")
        # Check for both the Go format (example.com_2025-03-03.html) 
        # and the domain-only format (example_com.html)
        domain_parts = domain.split('_')
        base_domain = domain_parts[0]
        
        if filename.startswith(domain) or filename.startswith(base_domain.replace('.', '_')):
            if filename.endswith(".html"):
                html_file = os.path.join(directory, filename)
                print(f"Found HTML file: {html_file}")
            elif filename.endswith(".md"):
                md_file = os.path.join(directory, filename)
                print(f"Found MD file: {md_file}")
    
    return html_file, md_file


def _get_domain_name_for_file(url: str) -> str:
    """
    Generate a unique filename prefix from the URL.
    
    Args:
        url: URL to generate filename from
        
    Returns:
        A string with the domain name formatted for a filename
    """
    # This is a simplified version of the Go code's getDomainNameForFile function
    import urllib.parse
    
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.replace(".", "_")
        path = parsed_url.path.strip("/")
        
        if not path:
            return domain
        
        path = path.replace("/", "_")
        return f"{domain}_{path}"
    except Exception:
        return "unknown"


def _sanitize_url(url: str) -> str:
    """
    Convert a URL to a safe filename component.
    
    Args:
        url: URL to sanitize
        
    Returns:
        A sanitized string suitable for filenames
    """
    import urllib.parse
    
    try:
        parsed_url = urllib.parse.urlparse(url)
        result = parsed_url.netloc + parsed_url.path
        
        for char in [':', '/', '?', '&', '=', '#']:
            result = result.replace(char, '_')
        
        return result
    except Exception:
        # If parsing fails, just replace unsafe characters
        for char in [':', '/', '?', '&', '=', '#']:
            url = url.replace(char, '_')
        return url 