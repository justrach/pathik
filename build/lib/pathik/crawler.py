import os
import subprocess
import tempfile
import uuid
from typing import List, Dict, Tuple, Optional, Union
import sys

# Add debugging output
print("Loading pathik.crawler module")
print("Current directory:", os.getcwd())
print("Module path:", __file__)

class CrawlerError(Exception):
    """Exception raised for errors in the crawler."""
    pass


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


def crawl(urls: List[str], output_dir: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """
    Crawl the specified URLs and return paths to the downloaded files.
    
    Args:
        urls: A list of URLs to crawl
        output_dir: Directory to save the crawled files (uses temp dir if None)
    
    Returns:
        A dictionary mapping URLs to file paths: 
        {url: {"html": html_path, "markdown": markdown_path}}
    """
    print(f"crawl() called with urls={urls}, output_dir={output_dir}")
    
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
    package_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(package_dir)
    binary_path = os.path.join(root_dir, "pathik_bin")
    
    if not os.path.exists(binary_path):
        raise FileNotFoundError(f"Pathik binary not found at {binary_path}")
    
    print(f"Using binary at: {binary_path}")
    
    # Use binary directly instead of "go run"
    command = [binary_path, "-crawl", "-outdir", output_dir]
    command.extend(urls)
    
    # Run the command from the directory containing the Go code
    current_dir = os.getcwd()
    print(f"Current directory before: {current_dir}")
    try:
        os.chdir(root_dir)
        print(f"Changed to directory: {os.getcwd()}")
        stdout, stderr = _run_go_command(command)
    finally:
        os.chdir(current_dir)
        print(f"Changed back to directory: {os.getcwd()}")
    
    # Parse the results to get file paths
    result = {}
    for url in urls:
        print(f"Finding files for URL: {url} in directory {output_dir}")
        html_file, md_file = _find_files_for_url(output_dir, url)
        print(f"Found HTML file: {html_file}")
        print(f"Found MD file: {md_file}")
        result[url] = {
            "html": html_file,
            "markdown": md_file
        }
    
    return result


def crawl_to_r2(urls: List[str], uuid_str: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """
    Crawl the specified URLs and upload the results to R2.
    
    Args:
        urls: A list of URLs to crawl
        uuid_str: UUID to prefix filenames (generates one if None)
    
    Returns:
        A dictionary with upload information
    """
    if not urls:
        raise ValueError("No URLs provided")
    
    # Generate UUID if not provided
    if uuid_str is None:
        uuid_str = str(uuid.uuid4())
    
    # Create a temporary directory for the crawled files
    temp_dir = tempfile.mkdtemp(prefix="pathik_")
    
    try:
        # First crawl the URLs with local storage
        crawl_result = crawl(urls, output_dir=temp_dir)
        
        # Then upload to R2
        command = ["go", "run", ".", "-r2", "-uuid", uuid_str, "-dir", temp_dir]
        command.extend(urls)
        
        current_dir = os.getcwd()
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Navigate to the directory with the Go code
            stdout, stderr = _run_go_command(command)
        finally:
            os.chdir(current_dir)
        
        # Build result with R2 upload information
        result = {}
        for url in urls:
            result[url] = {
                "uuid": uuid_str,
                "r2_html_key": f"{uuid_str}+{_sanitize_url(url)}.html",
                "r2_markdown_key": f"{uuid_str}+{_sanitize_url(url)}.md",
                "local_html_file": crawl_result[url]["html"],
                "local_markdown_file": crawl_result[url]["markdown"]
            }
        
        return result
    finally:
        # Do not clean up temporary directory so the local files remain available
        pass


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