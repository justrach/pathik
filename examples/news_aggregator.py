#!/usr/bin/env python
"""
A simple news aggregator that crawls news sites and streams content to Kafka
using the Pathik API
"""
import pathik
import uuid
import time
import datetime
import os
from typing import List, Dict, Any

# List of news sites to crawl
NEWS_SOURCES = [
    "https://news.ycombinator.com",
    "https://lobste.rs",
    "https://www.techmeme.com",
    "https://news.google.com/technology",
    "https://techcrunch.com"
]

def stream_news_sites(sources: List[str], topic: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Crawl and stream content from news sites to Kafka
    
    Args:
        sources: List of news site URLs
        topic: Optional custom Kafka topic
        
    Returns:
        Dictionary of results
    """
    # Generate a session ID that includes timestamp for easy organization
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"news_agg_{timestamp}"
    
    print(f"=== News Aggregator - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print(f"Session ID: {session_id}")
    print(f"Processing {len(sources)} news sources")
    
    # Use Pathik to stream content to Kafka
    results = pathik.stream_to_kafka(
        urls=sources,
        content_type="both",     # Stream both HTML and markdown
        topic=topic,             # Use custom topic if provided
        session=session_id,      # Use our timestamped session ID
        parallel=True            # Crawl sites in parallel for speed
    )
    
    # Process results
    successful = []
    failed = []
    
    for url, status in results.items():
        if status.get("success", False):
            successful.append(url)
        else:
            failed.append((url, status.get("error", "Unknown error")))
    
    # Print summary
    print(f"\nSuccessfully crawled and streamed {len(successful)}/{len(sources)} sites")
    
    if failed:
        print("\nFailed sites:")
        for url, error in failed:
            print(f"  - {url}: {error}")
    
    # Print session information for consumers
    print(f"\nKafka stream information:")
    print(f"  - Session ID: {session_id}")
    print(f"  - Topic: {topic or 'default (KAFKA_TOPIC from env)'}")
    
    return {
        "session_id": session_id,
        "timestamp": timestamp,
        "successful": successful,
        "failed": failed,
        "raw_results": results
    }

def run_scheduled(interval_mins: int = 60, run_once: bool = False):
    """
    Run the news aggregator on a schedule
    
    Args:
        interval_mins: Minutes between runs
        run_once: If True, only run once then exit
    """
    topic = os.environ.get("NEWS_KAFKA_TOPIC", "pathik_news_feed")
    
    try:
        while True:
            print("\n" + "=" * 60)
            results = stream_news_sites(NEWS_SOURCES, topic=topic)
            
            if run_once:
                return results
                
            next_run = datetime.datetime.now() + datetime.timedelta(minutes=interval_mins)
            print(f"\nNext run scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print("Press Ctrl+C to exit")
            
            time.sleep(interval_mins * 60)
    except KeyboardInterrupt:
        print("\nExiting news aggregator")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="News aggregator using Pathik API")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=60, 
                      help="Interval between runs in minutes (default: 60)")
    parser.add_argument("--topic", type=str, help="Custom Kafka topic")
    
    args = parser.parse_args()
    
    if args.topic:
        os.environ["NEWS_KAFKA_TOPIC"] = args.topic
        
    run_scheduled(interval_mins=args.interval, run_once=args.once) 