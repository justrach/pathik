"""
Simple implementation of the pathik functions that doesn't rely on Go.
"""
import os
import requests
import tempfile
import uuid
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import markdownify

def crawl(urls: List[str], output_dir: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """Simple Python-based crawler that doesn't use Go"""
    if not urls:
        raise ValueError("No URLs provided")
    
    # Create output directory if it doesn't exist
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="pathik_")
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    for url in urls:
        print(f"Crawling {url}...")
        try:
            # Fetch HTML
            response = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            })
            response.raise_for_status()
            html = response.text
            
            # Save HTML
            domain = url.replace("https://", "").replace("http://", "").replace("/", "_")
            html_file = os.path.join(output_dir, f"{domain}.html")
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)
            
            # Extract content and convert to markdown
            soup = BeautifulSoup(html, "html.parser")
            content = soup.find("body")
            markdown = markdownify.markdownify(str(content)) if content else ""
            
            # Save markdown
            md_file = os.path.join(output_dir, f"{domain}.md")
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(markdown)
            
            results[url] = {"html": html_file, "markdown": md_file}
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            results[url] = {"html": "", "markdown": ""}
    
    return results

def crawl_to_r2(urls: List[str], uuid_str: Optional[str] = None) -> Dict[str, Dict[str, str]]:
    """Simple version that just uses local storage"""
    if uuid_str is None:
        uuid_str = str(uuid.uuid4())
    
    results = crawl(urls)
    # Just return local paths since we're not using R2
    return {url: {
        "uuid": uuid_str,
        "r2_html_key": "",
        "r2_markdown_key": "",
        "local_html_file": files["html"],
        "local_markdown_file": files["markdown"]
    } for url, files in results.items()} 