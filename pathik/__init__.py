# Print diagnostic information
import sys
import os
print(f"Loading pathik package from {__file__}")
print(f"Python path: {sys.path}")

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

    def crawl(urls: List[str], output_dir: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """Fallback implementation of crawl function"""
        print("Using fallback crawl implementation")
        # Basic implementation here
        # ...

    def crawl_to_r2(urls: List[str], uuid_str: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """Fallback implementation of crawl_to_r2 function"""
        print("Using fallback crawl_to_r2 implementation")
        # Basic implementation here
        # ...

# Export the functions
__all__ = ["crawl", "crawl_to_r2"] 