# Pathik

<p align="center">
  <img src="assets/pathik_logo.png" alt="Pathik Logo">
</p>

A high-performance web crawler implemented in Go with Python and JavaScript bindings. It converts web pages to both HTML and Markdown formats.

## Features

- Fast crawling with Go's concurrency model
- Clean content extraction
- Markdown conversion
- Parallel URL processing
- Cloudflare R2 integration
- Kafka streaming support with configurable buffer sizes
- Enhanced security with URL and IP validation
- Memory-efficient (uses ~10x less memory than browser automation tools)
- Automatic binary version management
- Customizable compression options (Gzip and Snappy support)
- Session-based message tracking for multi-user environments
- Type-safe API with validation using satya
- Improved error handling and structured outputs

## Performance Benchmarks

### Memory Usage Comparison

Pathik is significantly more memory-efficient than browser automation tools like Playwright:

<p align="center">
  <img src="assets/PathikvPlaywright.png" alt="Memory Usage Comparison">
</p>

### Parallel Crawling Performance

Parallel crawling significantly improves performance when processing multiple URLs. Our benchmarks show:

#### Python Performance

```
Testing with 5 URLs:
- Parallel crawling completed in 7.78 seconds
- Sequential crawling completed in 18.52 seconds
- Performance improvement: 2.38x faster with parallel crawling
```

#### JavaScript Performance

```
Testing with 5 URLs:
- Parallel crawling completed in 6.96 seconds
- Sequential crawling completed in 21.07 seconds
- Performance improvement: 3.03x faster with parallel crawling
```

Parallel crawling is enabled by default when processing multiple URLs, but you can explicitly control it with the `parallel` parameter.

## Installation

```bash
pip install pathik
```

The package will automatically download the correct binary for your platform from GitHub releases on first use.

### Binary Version Management

Pathik now automatically handles binary version checking and updates:

- When you install or upgrade the Python package, it will check if the binary matches the package version
- If the versions don't match, it will automatically download the correct binary
- You can manually check and update the binary with:
  ```python
  # Force binary update
  import pathik
  from pathik.crawler import get_binary_path
  binary_path = get_binary_path(force_download=True)
  ```

- Command line options:
  ```bash
  # Check if binary is up to date
  pathik --check-binary
  
  # Force update of the binary
  pathik --force-update-binary
  ```

This ensures you always have the correct binary version with all the latest features, especially when using new functionality like Kafka streaming with session IDs.

## Usage

### Python API

#### Standard API

```python
import pathik
from pathik.crawler import CrawlerError

try:
    # Crawl a single URL with named parameters
    result = pathik.crawl(urls="https://example.com")
    
    # Check result
    if "https://example.com" in result:
        url_result = result["https://example.com"]
        if url_result.get("success", False):
            print(f"HTML saved to: {url_result.get('html')}")
            print(f"Markdown saved to: {url_result.get('markdown')}")
        else:
            print(f"Error: {url_result.get('error')}")
    
    # Crawl multiple URLs in parallel
    results = pathik.crawl(
        urls=["https://example.com", "https://httpbin.org/html"],
        parallel=True  # This is the default
    )
    
    # To disable parallel crawling
    results = pathik.crawl(
        urls=["https://example.com", "https://httpbin.org/html"],
        parallel=False
    )
    
    # To specify output directory
    results = pathik.crawl(
        urls="https://example.com",
        output_dir="./output"
    )
    
except CrawlerError as e:
    print(f"Crawler error: {e}")
```

#### Type-Safe API (Recommended)

The type-safe API provides enhanced validation, better error messages, and structured outputs:

```python
import pathik
from pathik import safe_crawl
from pathik.schema import CrawlParams

# Crawl a single URL with validation
try:
    # Create structured parameters
    params = CrawlParams(
        urls="https://example.com",
        output_dir="./output"
    )
    
    # Use the safe API
    result = safe_crawl(
        urls="https://example.com",
        output_dir="./output"
    )
    
    # Access the validated results
    for url, data in result.items():
        print(f"URL: {url}")
        print(f"HTML file: {data.get('html')}")
        print(f"Markdown file: {data.get('markdown')}")
        
except ValueError as e:
    print(f"Validation error: {e}")
    
# Alternatively, use keyword arguments directly
try:
    result = safe_crawl(
        urls=["https://example.com", "https://httpbin.org/html"],
        parallel=True,
        output_dir="./output"
    )
    
    # Access results
    for url, data in result.items():
        print(f"URL: {url}")
        print(f"Success: {data.get('success', False)}")
        if data.get('success', False):
            print(f"Files: {data.get('html')}, {data.get('markdown')}")
        else:
            print(f"Error: {data.get('error')}")
            
except ValueError as e:
    print(f"Validation error: {e}")
```

#### R2 Upload

```python
import pathik
import uuid
from pathik.crawler import CrawlerError

try:
    # Generate a UUID or use your own
    my_uuid = str(uuid.uuid4())
    
    # Crawl and upload to R2
    results = pathik.crawl_to_r2(
        urls="https://example.com",
        uuid_str=my_uuid
    )
    
    if "https://example.com" in results:
        r2_result = results["https://example.com"]
        print(f"UUID: {r2_result.get('uuid')}")
        print(f"R2 HTML key: {r2_result.get('r2_html_key')}")
        print(f"R2 Markdown key: {r2_result.get('r2_markdown_key')}")
    
    # Upload multiple URLs
    results = pathik.crawl_to_r2(
        urls=["https://example.com", "https://httpbin.org/html"],
        uuid_str=my_uuid
    )
    
except CrawlerError as e:
    print(f"Crawler error: {e}")
```

#### Kafka Streaming

##### Standard API

```python
import pathik
import uuid

# Generate a session ID for tracking
session_id = str(uuid.uuid4())

# Stream a single URL to Kafka
result = pathik.stream_to_kafka(
    urls="https://example.com",
    session=session_id
)

if "https://example.com" in result:
    if result["https://example.com"].get("success", False):
        print(f"Successfully streamed")

# Stream multiple URLs
results = pathik.stream_to_kafka(
    urls=["https://example.com", "https://httpbin.org/html"],
    content_type="both",     # Options: "html", "markdown", or "both"
    topic="pathik_data",     # Optional custom topic
    session=session_id,      # Optional session ID
    parallel=True            # Process URLs in parallel (default)
)

# Check results
for url, status in results.items():
    if status.get("success", False):
        print(f"Successfully streamed {url}")
        if "details" in status:
            details = status["details"]
            print(f"  Topic: {details.get('topic')}")
            print(f"  HTML Content: {details.get('html_file')}")
            print(f"  Markdown Content: {details.get('markdown_file')}")
    else:
        print(f"Failed to stream {url}: {status.get('error')}")
```

##### Type-Safe API for Kafka Streaming (Recommended)

For applications requiring robust input validation and error handling:

```python
import pathik
from pathik.safe_api import safe_stream_to_kafka
from pathik.schema import KafkaStreamParams
import uuid

try:
    # Create structured parameters
    params = KafkaStreamParams(
        urls=["https://example.com", "https://httpbin.org/html"],
        content_type="both",
        topic="pathik_data",
        session_id=str(uuid.uuid4()),
        parallel=True,
        # Compression options
        compression_type="gzip",       # Options: gzip, snappy, lz4, zstd
        max_message_size=15728640,     # 15MB message size limit (default: 10MB)
        buffer_memory=157286400        # 150MB buffer memory (default: 100MB)
    )
    
    # Stream content with validation
    result = safe_stream_to_kafka(params)
    
    # Process validated results
    if result.success:
        print(f"Successfully streamed {len(result.results)} URLs")
        print(f"Session ID: {result.session_id}")
        
        for url, stream_info in result.results.items():
            if stream_info.success:
                print(f"✅ {url}: Success")
                print(f"  Topic: {stream_info.topic}")
                print(f"  Content types: {stream_info.content_types}")
            else:
                print(f"❌ {url}: Failed - {stream_info.error}")
    else:
        print(f"Streaming operation failed: {result.error}")
        
except ValueError as e:
    print(f"Validation error: {e}")
```

##### Compression Options for Kafka Streaming

When streaming large web pages or handling high volumes of content, you can optimize performance by configuring compression:

```python
# Optimize for best compression ratio (slower)
params = KafkaStreamParams(
    urls=urls,
    compression_type="gzip",
    max_message_size=15728640,    # 15MB
    buffer_memory=157286400       # 150MB
)

# Optimize for speed (moderate compression)
params = KafkaStreamParams(
    urls=urls,
    compression_type="snappy",
    max_message_size=10485760,    # 10MB (default)
    buffer_memory=104857600       # 100MB (default)
)

# Optimize for throughput (fastest)
params = KafkaStreamParams(
    urls=urls,
    compression_type="lz4",
    max_message_size=10485760,
    buffer_memory=104857600
)

# Best balance of speed and compression
params = KafkaStreamParams(
    urls=urls,
    compression_type="zstd",
    max_message_size=10485760,
    buffer_memory=104857600
)
```

Choose the appropriate configuration based on your specific requirements:
- For large pages with a lot of text, use `gzip` or `zstd`
- For high-volume crawling, use `lz4` or `snappy`
- Adjust message size and buffer memory based on content size and available resources

### Command Line

```bash
# Crawl a single URL
pathik crawl https://example.com

# Crawl multiple URLs
pathik crawl https://example.com https://httpbin.org/html

# Specify output directory
pathik crawl -o ./output https://example.com

# Use sequential (non-parallel) mode
pathik crawl -s https://example.com https://httpbin.org/html

# Upload to R2 (Cloudflare)
pathik r2 https://example.com

# Stream crawled content to Kafka
pathik kafka https://example.com

# Stream only HTML content to Kafka
pathik kafka -c html https://example.com

# Stream only Markdown content to Kafka
pathik kafka -c markdown https://example.com

# Stream to a specific Kafka topic
pathik kafka -t user1_crawl_data https://example.com

# Add a session ID for multi-user environments
pathik kafka --session user123 https://example.com

# Combine options
pathik kafka -c html -t user1_data --session user123 https://example.com
```

### Sample Kafka Streaming Examples

We provide two example scripts in the examples directory to demonstrate Kafka streaming:

#### Basic Example (native_kafka_demo.py)

```python
from pathik import stream_to_kafka

# Stream a URL to Kafka
results = stream_to_kafka(
    urls="https://example.com",
    content_type="both",
    topic="pathik_crawl_data",
    session="demo-session-123",
    parallel=True
)

# Check results
for url, result in results.items():
    print(f"URL: {url}")
    print(f"Success: {result.get('success', False)}")
    if result.get('success', False) and 'details' in result:
        details = result['details']
        print(f"Topic: {details.get('topic')}")
        print(f"HTML file: {details.get('html_file')}")
        print(f"Markdown file: {details.get('markdown_file')}")
```

#### Type-Safe Example (safe_kafka_demo.py)

```python
from pathik import safe_stream_to_kafka
from pathik.schema import KafkaStreamParams

# Create validated parameters
params = KafkaStreamParams(
    urls=["https://example.com"],
    content_type="both",
    topic="pathik_crawl_data",
    session_id="safe-demo-123",
    parallel=True
)

try:
    # Stream with validation
    result = safe_stream_to_kafka(params)
    
    if result.success:
        print(f"Successfully streamed {len(result.results)} URLs")
        for url, info in result.results.items():
            if info.success:
                print(f"✅ {url}")
                print(f"  Topic: {info.topic}")
                print(f"  Files: {info.html_file}, {info.markdown_file}")
            else:
                print(f"❌ {url}: {info.error}")
    else:
        print(f"Operation failed: {result.error}")
        
except ValueError as e:
    print(f"Validation error: {e}")
```