"""
Pathik - A Python package for web crawling with Go backend capabilities.
"""
print("Loading pathik package root")

# Try importing from the subpackage
try:
    from pathik.pathik.crawler import crawl, crawl_to_r2
    print("Successfully imported functions from pathik.pathik.crawler")
except ImportError as e:
    print(f"Failed to import from pathik.pathik.crawler: {e}")
    # Try importing from the simple implementation
    try:
        from pathik.pathik.simple import crawl, crawl_to_r2
        print("Using simple Python implementation")
    except ImportError as e:
        print(f"Failed to import from pathik.pathik.simple: {e}")
        # Fallback implementation
        import tempfile
        import os
        import uuid
        from typing import List, Dict, Optional
        
        print("Using fallback implementation")
        
        def crawl(urls: List[str], output_dir: Optional[str] = None) -> Dict[str, Dict[str, str]]:
            """Emergency fallback crawler implementation"""
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="pathik_")
            else:
                os.makedirs(output_dir, exist_ok=True)
                
            print(f"FALLBACK CRAWLER - Would crawl: {urls} to {output_dir}")
            
            # Just create empty files as placeholders
            results = {}
            for url in urls:
                domain = url.replace("https://", "").replace("http://", "").replace("/", "_")
                html_file = os.path.join(output_dir, f"{domain}.html")
                md_file = os.path.join(output_dir, f"{domain}.md")
                
                # Create empty files
                open(html_file, 'w').close()
                open(md_file, 'w').close()
                
                results[url] = {"html": html_file, "markdown": md_file}
                
            return results
            
        def crawl_to_r2(urls: List[str], uuid_str: Optional[str] = None) -> Dict[str, Dict[str, str]]:
            """Emergency fallback R2 implementation"""
            if uuid_str is None:
                uuid_str = str(uuid.uuid4())
                
            results = crawl(urls)
            return {
                url: {
                    "uuid": uuid_str,
                    "r2_html_key": "",
                    "r2_markdown_key": "",
                    "local_html_file": files["html"],
                    "local_markdown_file": files["markdown"]
                } for url, files in results.items()
            }

# Export the functions
__all__ = ["crawl", "crawl_to_r2"] 