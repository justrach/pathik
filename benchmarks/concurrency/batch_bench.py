#!/usr/bin/env python
"""
Simplified benchmark script comparing pathik vs Playwright for batch web crawling.
Tests batch sizes of 5 and 10 URLs to showcase concurrent performance.
"""

import pathik
import asyncio
import time
import os
import psutil
import platform
import pandas as pd
import matplotlib.pyplot as plt
from playwright.async_api import async_playwright
from tabulate import tabulate
import argparse
import traceback
from datetime import datetime

# Test websites for batch processing
BATCH_SITES = [
    "https://example.com",
    "https://news.ycombinator.com",
    "https://www.wikipedia.org",
    "https://github.com",
    "https://www.nytimes.com",
    "https://www.reddit.com", 
    "https://stackoverflow.com",
    "https://www.cnn.com",
    "https://www.bbc.com",
    "https://www.theverge.com"
]

class BenchmarkResult:
    def __init__(self):
        self.results = {
            "batch_size": [],
            "crawler": [],
            "total_time_seconds": [],
            "urls_per_second": [],
            "memory_mb": [],
            "success_count": []
        }
    
    def add_result(self, batch_size, crawler, time_seconds, memory_mb, success_count):
        self.results["batch_size"].append(batch_size)
        self.results["crawler"].append(crawler)
        self.results["total_time_seconds"].append(time_seconds)
        self.results["urls_per_second"].append(success_count / time_seconds if time_seconds > 0 else 0)
        self.results["memory_mb"].append(memory_mb)
        self.results["success_count"].append(success_count)
    
    def get_dataframe(self):
        return pd.DataFrame(self.results)


def measure_memory():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def batch_crawl_with_pathik(urls, output_dir):
    """
    Crawl a batch of URLs using pathik's built-in concurrent crawling.
    This uses the Pythonic approach shown in the example.
    """
    print(f"Crawling {len(urls)} URLs with pathik...")
    
    # Measure starting memory
    start_memory = measure_memory()
    
    # Record start time
    start_time = time.time()
    
    try:
        # Use pathik's built-in concurrency by passing a list of URLs
        results = pathik.crawl(urls, output_dir=output_dir)
        
        # Measure time and memory
        elapsed_time = time.time() - start_time
        memory_used = measure_memory() - start_memory
        
        # Count successful crawls
        success_count = sum(1 for url in results if url in results and 
                           results[url].get("html") and os.path.exists(results[url]["html"]))
        
        print(f"  Pathik completed in {elapsed_time:.2f} seconds")
        print(f"  Successfully crawled {success_count}/{len(urls)} URLs")
        print(f"  Memory used: {memory_used:.2f} MB")
        print(f"  Throughput: {success_count/elapsed_time:.2f} URLs/second")
        
        return {
            "time": elapsed_time,
            "memory": memory_used,
            "success_count": success_count
        }
    
    except Exception as e:
        print(f"Error in pathik batch crawling: {e}")
        traceback.print_exc()
        elapsed_time = time.time() - start_time
        return {
            "time": elapsed_time,
            "memory": 0,
            "success_count": 0
        }


async def batch_crawl_with_playwright(urls, output_dir, concurrency=5):
    """
    Crawl a batch of URLs using Playwright with async/await concurrency.
    """
    print(f"Crawling {len(urls)} URLs with Playwright (concurrency={concurrency})...")
    
    # Measure starting memory
    start_memory = measure_memory()
    
    # Record start time
    start_time = time.time()
    
    # Track successful crawls
    success_count = 0
    
    try:
        async with async_playwright() as p:
            # Limit concurrency
            semaphore = asyncio.Semaphore(concurrency)
            
            async def crawl_url(url):
                """Crawl a single URL with Playwright"""
                async with semaphore:
                    try:
                        browser = await p.chromium.launch()
                        page = await browser.new_page()
                        
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        html_content = await page.content()
                        
                        # Save content
                        domain = url.replace("https://", "").replace("http://", "").replace("/", "_")
                        filename = f"{domain}_playwright_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        
                        await browser.close()
                        return True, filepath
                    except Exception as e:
                        print(f"  Error crawling {url}: {e}")
                        return False, None
            
            # Create tasks for all URLs
            tasks = [crawl_url(url) for url in urls]
            results = await asyncio.gather(*tasks)
            
            # Count successful crawls
            success_count = sum(1 for success, _ in results if success)
    
    except Exception as e:
        print(f"Error in Playwright batch crawling: {e}")
        traceback.print_exc()
    
    # Calculate metrics
    elapsed_time = time.time() - start_time
    memory_used = measure_memory() - start_memory
    
    print(f"  Playwright completed in {elapsed_time:.2f} seconds")
    print(f"  Successfully crawled {success_count}/{len(urls)} URLs")
    print(f"  Memory used: {memory_used:.2f} MB")
    print(f"  Throughput: {success_count/elapsed_time:.2f} URLs/second")
    
    return {
        "time": elapsed_time,
        "memory": memory_used,
        "success_count": success_count
    }


def plot_results(results_df, output_file=None):
    """Create bar plots comparing pathik and Playwright across batch sizes"""
    # Convert results to pivot format for easier plotting
    pathik_results = results_df[results_df["crawler"] == "pathik"]
    playwright_results = results_df[results_df["crawler"] == "playwright"]
    
    batch_sizes = sorted(results_df["batch_size"].unique())
    
    # Create figure with 2x2 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Total time
    ax1 = axes[0, 0]
    ax1.bar(
        [x - 0.2 for x in batch_sizes], 
        pathik_results["total_time_seconds"], 
        width=0.4, 
        label="pathik"
    )
    ax1.bar(
        [x + 0.2 for x in batch_sizes], 
        playwright_results["total_time_seconds"], 
        width=0.4, 
        label="playwright"
    )
    ax1.set_title("Total Crawl Time")
    ax1.set_xlabel("Batch Size")
    ax1.set_ylabel("Time (seconds)")
    ax1.set_xticks(batch_sizes)
    ax1.legend()
    ax1.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Plot 2: Throughput (URLs/second)
    ax2 = axes[0, 1]
    ax2.bar(
        [x - 0.2 for x in batch_sizes], 
        pathik_results["urls_per_second"], 
        width=0.4, 
        label="pathik"
    )
    ax2.bar(
        [x + 0.2 for x in batch_sizes], 
        playwright_results["urls_per_second"], 
        width=0.4, 
        label="playwright"
    )
    ax2.set_title("Throughput")
    ax2.set_xlabel("Batch Size")
    ax2.set_ylabel("URLs per second")
    ax2.set_xticks(batch_sizes)
    ax2.legend()
    ax2.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Plot 3: Memory usage
    ax3 = axes[1, 0]
    ax3.bar(
        [x - 0.2 for x in batch_sizes], 
        pathik_results["memory_mb"], 
        width=0.4, 
        label="pathik"
    )
    ax3.bar(
        [x + 0.2 for x in batch_sizes], 
        playwright_results["memory_mb"], 
        width=0.4, 
        label="playwright"
    )
    ax3.set_title("Memory Usage")
    ax3.set_xlabel("Batch Size")
    ax3.set_ylabel("Memory (MB)")
    ax3.set_xticks(batch_sizes)
    ax3.legend()
    ax3.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Plot 4: Success rate
    ax4 = axes[1, 1]
    ax4.bar(
        [x - 0.2 for x in batch_sizes], 
        pathik_results["success_count"] / pathik_results["batch_size"] * 100, 
        width=0.4, 
        label="pathik"
    )
    ax4.bar(
        [x + 0.2 for x in batch_sizes], 
        playwright_results["success_count"] / playwright_results["batch_size"] * 100, 
        width=0.4, 
        label="playwright"
    )
    ax4.set_title("Success Rate")
    ax4.set_xlabel("Batch Size")
    ax4.set_ylabel("Success Rate (%)")
    ax4.set_xticks(batch_sizes)
    ax4.legend()
    ax4.grid(axis="y", linestyle="--", alpha=0.7)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    plt.show()


def print_results_table(results_df):
    """Print a formatted table of benchmark results"""
    # Convert to pivot format for easier comparison
    pivoted = results_df.pivot(index="batch_size", columns="crawler")
    
    # Format detailed table for raw results
    detailed_table = []
    headers = ["Batch Size", "Crawler", "Time (sec)", "URLs/sec", "Memory (MB)", "Success Rate"]
    detailed_table.append(headers)
    
    for batch_size in sorted(results_df["batch_size"].unique()):
        for crawler in ["pathik", "playwright"]:
            row_data = results_df[(results_df["batch_size"] == batch_size) & 
                                  (results_df["crawler"] == crawler)]
            if len(row_data) > 0:
                success_rate = f"{row_data['success_count'].values[0] / batch_size * 100:.1f}%"
                detailed_table.append([
                    batch_size,
                    crawler,
                    f"{row_data['total_time_seconds'].values[0]:.2f}",
                    f"{row_data['urls_per_second'].values[0]:.2f}",
                    f"{row_data['memory_mb'].values[0]:.2f}",
                    success_rate
                ])
    
    # Format summary table comparing pathik vs playwright
    summary_table = []
    summary_headers = ["Metric", "pathik", "playwright", "Ratio (pathik/playwright)"]
    summary_table.append(summary_headers)
    
    # Group by crawler and calculate averages
    avg_by_crawler = results_df.groupby("crawler").mean()
    
    # Add summary metrics
    metrics = [
        ("Avg Time (sec)", "total_time_seconds"),
        ("Avg URLs/sec", "urls_per_second"),
        ("Avg Memory (MB)", "memory_mb")
    ]
    
    for metric_name, column in metrics:
        if "playwright" in avg_by_crawler.index and "pathik" in avg_by_crawler.index:
            pathik_val = avg_by_crawler.loc["pathik", column]
            playwright_val = avg_by_crawler.loc["playwright", column]
            ratio = pathik_val / playwright_val if playwright_val != 0 else float('inf')
            
            # For time, lower is better (ratio < 1)
            # For throughput, higher is better (ratio > 1)
            better_indicator = "✅" if (column == "total_time_seconds" and ratio < 1) or \
                                       (column != "total_time_seconds" and ratio > 1) else ""
            
            summary_table.append([
                metric_name,
                f"{pathik_val:.2f}",
                f"{playwright_val:.2f}",
                f"{ratio:.2f} {better_indicator}"
            ])
    
    # Print tables
    print("\n" + "="*80)
    print("BENCHMARK SUMMARY")
    print("="*80)
    print(tabulate(summary_table, headers="firstrow", tablefmt="grid"))
    
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    print(tabulate(detailed_table, headers="firstrow", tablefmt="grid"))


async def main():
    parser = argparse.ArgumentParser(description="Benchmark pathik vs Playwright for batch crawling")
    parser.add_argument("--output", type=str, default="batch_benchmark", help="Output directory")
    parser.add_argument("--plot", type=str, default="batch_results.png", help="Output plot filename")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrency level for Playwright")
    args = parser.parse_args()
    
    # Create output directories
    os.makedirs(args.output, exist_ok=True)
    pathik_dir = os.path.join(args.output, "pathik")
    playwright_dir = os.path.join(args.output, "playwright")
    os.makedirs(pathik_dir, exist_ok=True)
    os.makedirs(playwright_dir, exist_ok=True)
    
    # Print system info
    print("\n" + "="*80)
    print("BATCH CRAWLING BENCHMARK: PATHIK vs PLAYWRIGHT")
    print("="*80)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Playwright concurrency: {args.concurrency}")
    print("="*80 + "\n")
    
    # Initialize results collector
    results = BenchmarkResult()
    
    # Run benchmarks for batch sizes 5 and 10
    batch_sizes = [5, 10]
    
    for batch_size in batch_sizes:
        print(f"\n{'='*40}")
        print(f"TESTING BATCH SIZE: {batch_size}")
        print(f"{'='*40}")
        
        # Get URLs for this batch
        urls = BATCH_SITES[:batch_size]
        
        # Run pathik benchmark
        pathik_result = batch_crawl_with_pathik(urls, pathik_dir)
        results.add_result(
            batch_size=batch_size,
            crawler="pathik",
            time_seconds=pathik_result["time"],
            memory_mb=pathik_result["memory"],
            success_count=pathik_result["success_count"]
        )
        
        # Run playwright benchmark
        playwright_result = await batch_crawl_with_playwright(
            urls, 
            playwright_dir,
            concurrency=args.concurrency
        )
        results.add_result(
            batch_size=batch_size,
            crawler="playwright",
            time_seconds=playwright_result["time"],
            memory_mb=playwright_result["memory"],
            success_count=playwright_result["success_count"]
        )
    
    # Get results as dataframe
    results_df = results.get_dataframe()
    
    # Print table of results
    print_results_table(results_df)
    
    # Generate plot
    plot_file = os.path.join(args.output, args.plot)
    plot_results(results_df, output_file=plot_file)
    print(f"\nResults plot saved to: {plot_file}")


if __name__ == "__main__":
    asyncio.run(main()) 