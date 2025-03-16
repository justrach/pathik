import pathik
import os
import time
import sys

def main():
    # Create output directories
    base_dir = os.path.abspath("./output_test")
    parallel_dir = os.path.join(base_dir, "parallel")
    sequential_dir = os.path.join(base_dir, "sequential")
    
    os.makedirs(parallel_dir, exist_ok=True)
    os.makedirs(sequential_dir, exist_ok=True)
    
    # Test URLs - mix of different sites
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com",
        "https://books.toscrape.com",
        "https://quotes.toscrape.com"
    ]
    
    print(f"Testing with {len(urls)} URLs...")
    
    # Test parallel crawling
    print("\n=== PARALLEL CRAWLING ===")
    parallel_start = time.time()
    
    try:
        parallel_results = pathik.crawl(urls, output_dir=parallel_dir, parallel=True)
        parallel_time = time.time() - parallel_start
        
        print(f"Parallel crawling completed in {parallel_time:.2f} seconds")
        
        # Print results summary
        for url, info in parallel_results.items():
            status = "✅ Success" if info.get("html") and info.get("markdown") else "❌ Failed"
            print(f"  {url}: {status}")
    except Exception as e:
        print(f"Error during parallel crawling: {e}")
        sys.exit(1)
    
    # Test sequential crawling
    print("\n=== SEQUENTIAL CRAWLING ===")
    sequential_start = time.time()
    
    try:
        sequential_results = pathik.crawl(urls, output_dir=sequential_dir, parallel=False)
        sequential_time = time.time() - sequential_start
        
        print(f"Sequential crawling completed in {sequential_time:.2f} seconds")
        
        # Print results summary
        for url, info in sequential_results.items():
            status = "✅ Success" if info.get("html") and info.get("markdown") else "❌ Failed"
            print(f"  {url}: {status}")
    except Exception as e:
        print(f"Error during sequential crawling: {e}")
        sys.exit(1)
    
    # Compare performance
    if parallel_time < sequential_time:
        speedup = sequential_time / parallel_time
        print(f"\n=== PERFORMANCE COMPARISON ===")
        print(f"Parallel crawling was {speedup:.2f}x faster than sequential crawling")
        print(f"Parallel: {parallel_time:.2f}s vs Sequential: {sequential_time:.2f}s")
    else:
        print("\n=== PERFORMANCE COMPARISON ===")
        print(f"Warning: Parallel crawling was not faster in this test")
        print(f"Parallel: {parallel_time:.2f}s vs Sequential: {sequential_time:.2f}s")
    
    print(f"\nOutput files are located in: {base_dir}")

if __name__ == "__main__":
    main() 