#!/usr/bin/env python
"""
Benchmark script comparing pathik vs Playwright for web crawling performance.
"""

import pathik
import asyncio
import time
import os
import psutil
import platform
import pandas as pd
import matplotlib.pyplot as plt
from playwright.sync_api import sync_playwright
from tabulate import tabulate
import argparse
import tempfile

# Test websites (varying complexity and size)
TEST_SITES = [
    "https://example.com",                  # Simple static site
    "https://news.ycombinator.com",         # Moderately complex
    "https://www.wikipedia.org",            # Multiple languages, medium complexity
    "https://github.com",                   # Complex, dynamic content
    "https://www.nytimes.com"               # News site with lots of content
]

class PerformanceMetrics:
    def __init__(self, name):
        self.name = name
        self.metrics = {
            "website": [],
            "time_seconds": [],
            "peak_memory_mb": [],
            "content_size_kb": []
        }
    
    def add_result(self, website, time_seconds, peak_memory_mb, content_size_kb):
        self.metrics["website"].append(website)
        self.metrics["time_seconds"].append(time_seconds)
        self.metrics["peak_memory_mb"].append(peak_memory_mb)
        self.metrics["content_size_kb"].append(content_size_kb)
    
    def get_dataframe(self):
        return pd.DataFrame(self.metrics)


def get_file_size_kb(file_path):
    """Get file size in KB"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / 1024
    return 0


def crawl_with_pathik(url, output_dir):
    """Crawl using pathik and return metrics"""
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    start_time = time.time()
    result = pathik.crawl(url, output_dir=output_dir)
    end_time = time.time()
    
    end_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Get file path from result
    html_file = result[url]["html"] if url in result and "html" in result[url] else ""
    md_file = result[url]["markdown"] if url in result and "markdown" in result[url] else ""
    
    # Get file sizes
    html_size = get_file_size_kb(html_file)
    md_size = get_file_size_kb(md_file)
    content_size = html_size + md_size
    
    return {
        "time": end_time - start_time,
        "peak_memory": max(end_memory - start_memory, 0),  # Ensure positive value
        "content_size": content_size
    }


def crawl_with_playwright(url, output_dir):
    """Crawl using Playwright and return metrics"""
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    start_time = time.time()
    
    html_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html_content = page.content()
        browser.close()
    
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Save the HTML content
    domain = url.replace("https://", "").replace("http://", "").replace("/", "_")
    html_file = os.path.join(output_dir, f"{domain}_playwright.html")
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    content_size = get_file_size_kb(html_file)
    
    return {
        "time": end_time - start_time,
        "peak_memory": max(end_memory - start_memory, 0),  # Ensure positive value
        "content_size": content_size
    }


def plot_comparison(pathik_metrics, playwright_metrics, output_file=None):
    """Create comparison plots for the benchmark results"""
    # Prepare data
    pathik_df = pathik_metrics.get_dataframe()
    playwright_df = playwright_metrics.get_dataframe()
    
    # Create a figure with 3 subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
    
    # Plot execution time
    bar_width = 0.35
    x = range(len(pathik_df["website"]))
    
    ax1.bar([i - bar_width/2 for i in x], pathik_df["time_seconds"], bar_width, label='Pathik', color='blue')
    ax1.bar([i + bar_width/2 for i in x], playwright_df["time_seconds"], bar_width, label='Playwright', color='orange')
    ax1.set_ylabel('Time (seconds)')
    ax1.set_title('Execution Time Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels([url.replace("https://", "").split("/")[0] for url in pathik_df["website"]], rotation=45)
    ax1.legend()
    
    # Plot memory usage
    ax2.bar([i - bar_width/2 for i in x], pathik_df["peak_memory_mb"], bar_width, label='Pathik', color='blue')
    ax2.bar([i + bar_width/2 for i in x], playwright_df["peak_memory_mb"], bar_width, label='Playwright', color='orange')
    ax2.set_ylabel('Memory (MB)')
    ax2.set_title('Peak Memory Usage Comparison')
    ax2.set_xticks(x)
    ax2.set_xticklabels([url.replace("https://", "").split("/")[0] for url in pathik_df["website"]], rotation=45)
    ax2.legend()
    
    # Plot content size
    ax3.bar([i - bar_width/2 for i in x], pathik_df["content_size_kb"], bar_width, label='Pathik', color='blue')
    ax3.bar([i + bar_width/2 for i in x], playwright_df["content_size_kb"], bar_width, label='Playwright', color='orange')
    ax3.set_ylabel('Content Size (KB)')
    ax3.set_title('Content Size Comparison')
    ax3.set_xticks(x)
    ax3.set_xticklabels([url.replace("https://", "").split("/")[0] for url in pathik_df["website"]], rotation=45)
    ax3.legend()
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    plt.show()

def print_summary(pathik_metrics, playwright_metrics):
    """Print a summary table of the benchmark results"""
    pathik_df = pathik_metrics.get_dataframe()
    playwright_df = playwright_metrics.get_dataframe()
    
    # Calculate averages
    pathik_avg_time = pathik_df["time_seconds"].mean()
    playwright_avg_time = playwright_df["time_seconds"].mean()
    time_diff_pct = ((playwright_avg_time - pathik_avg_time) / playwright_avg_time) * 100
    
    pathik_avg_memory = pathik_df["peak_memory_mb"].mean()
    playwright_avg_memory = playwright_df["peak_memory_mb"].mean()
    memory_diff_pct = ((playwright_avg_memory - pathik_avg_memory) / playwright_avg_memory) * 100
    
    # Create summary table
    summary = [
        ["Crawler", "Avg Time (s)", "Avg Memory (MB)", "Sites Crawled"],
        ["Pathik", f"{pathik_avg_time:.2f}", f"{pathik_avg_memory:.2f}", len(pathik_df)],
        ["Playwright", f"{playwright_avg_time:.2f}", f"{playwright_avg_memory:.2f}", len(playwright_df)]
    ]
    
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(tabulate(summary, headers="firstrow", tablefmt="grid"))
    print("\n")
    
    if time_diff_pct > 0:
        print(f"Pathik is {time_diff_pct:.1f}% faster than Playwright")
    else:
        print(f"Playwright is {-time_diff_pct:.1f}% faster than Pathik")
    
    if memory_diff_pct > 0:
        print(f"Pathik uses {memory_diff_pct:.1f}% less memory than Playwright")
    else:
        print(f"Playwright uses {-memory_diff_pct:.1f}% less memory than Pathik")
    
    # Detailed results table
    detailed = []
    headers = ["Website", "Pathik Time (s)", "Playwright Time (s)", "Pathik Memory (MB)", "Playwright Memory (MB)"]
    detailed.append(headers)
    
    for i in range(len(pathik_df)):
        website = pathik_df["website"][i].replace("https://", "").split("/")[0]
        detailed.append([
            website,
            f"{pathik_df['time_seconds'][i]:.2f}",
            f"{playwright_df['time_seconds'][i]:.2f}",
            f"{pathik_df['peak_memory_mb'][i]:.2f}",
            f"{playwright_df['peak_memory_mb'][i]:.2f}"
        ])
    
    print("\n" + "="*100)
    print("DETAILED RESULTS")
    print("="*100)
    print(tabulate(detailed, headers="firstrow", tablefmt="grid"))


def main():
    parser = argparse.ArgumentParser(description="Benchmark pathik vs Playwright for web crawling")
    parser.add_argument("--sites", type=int, default=3, help="Number of test sites to use (max 5)")
    parser.add_argument("--output", type=str, default="benchmark_results", help="Output directory")
    parser.add_argument("--plot", type=str, default="benchmark_plot.png", help="Output plot file")
    parser.add_argument("--no-plot", action="store_true", help="Disable plotting")
    args = parser.parse_args()
    
    # Limit number of sites
    num_sites = min(args.sites, len(TEST_SITES))
    sites_to_test = TEST_SITES[:num_sites]
    
    # Create output directory
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    # Print system info
    print("="*60)
    print(f"BENCHMARK: PATHIK vs PLAYWRIGHT")
    print("="*60)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Testing {num_sites} websites")
    print("="*60)
    
    # Initialize metrics
    pathik_metrics = PerformanceMetrics("Pathik")
    playwright_metrics = PerformanceMetrics("Playwright")
    
    # Run benchmarks
    for url in sites_to_test:
        print(f"\nBenchmarking {url}...")
        
        # Create subdirectories for each crawler
        pathik_dir = os.path.join(output_dir, "pathik")
        playwright_dir = os.path.join(output_dir, "playwright")
        os.makedirs(pathik_dir, exist_ok=True)
        os.makedirs(playwright_dir, exist_ok=True)
        
        # Pathik crawl
        print("Running pathik crawler...")
        try:
            pathik_result = crawl_with_pathik(url, pathik_dir)
            pathik_metrics.add_result(
                url, 
                pathik_result["time"], 
                pathik_result["peak_memory"],
                pathik_result["content_size"]
            )
            print(f"  Time: {pathik_result['time']:.2f} seconds")
            print(f"  Memory: {pathik_result['peak_memory']:.2f} MB")
        except Exception as e:
            print(f"  Error with Pathik: {e}")
        
        # Playwright crawl
        print("Running Playwright crawler...")
        try:
            playwright_result = crawl_with_playwright(url, playwright_dir)
            playwright_metrics.add_result(
                url, 
                playwright_result["time"], 
                playwright_result["peak_memory"],
                playwright_result["content_size"]
            )
            print(f"  Time: {playwright_result['time']:.2f} seconds")
            print(f"  Memory: {playwright_result['peak_memory']:.2f} MB")
        except Exception as e:
            print(f"  Error with Playwright: {e}")
    
    # Print summary
    print_summary(pathik_metrics, playwright_metrics)
    
    # Generate plot
    if not args.no_plot:
        plot_comparison(pathik_metrics, playwright_metrics, args.plot)
        print(f"\nPlot saved to {args.plot}")

if __name__ == "__main__":
    main() 