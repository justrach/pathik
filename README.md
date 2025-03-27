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
- Kafka streaming support
- Memory-efficient (uses ~10x less memory than browser automation tools)
- Automatic binary version management

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

#### Basic Crawling

```python
import pathik

# Crawl a single URL
result = pathik.crawl("https://example.com")
print(f"HTML saved to: {result['https://example.com']['html']}")
print(f"Markdown saved to: {result['https://example.com']['markdown']}")

# Crawl multiple URLs in parallel
results = pathik.crawl([
    "https://example.com",
    "https://httpbin.org/html",
    "https://jsonplaceholder.typicode.com"
])

# To disable parallel crawling
results = pathik.crawl(urls, parallel=False)

# To specify output directory
results = pathik.crawl(urls, output_dir="./output")
```

#### R2 Upload

```python
import pathik
import uuid

# Generate a UUID or use your own
my_uuid = str(uuid.uuid4())

# Crawl and upload to R2
results = pathik.crawl_to_r2("https://example.com", uuid_str=my_uuid)
print(f"UUID: {results['https://example.com']['uuid']}")
print(f"R2 HTML key: {results['https://example.com']['r2_html_key']}")
print(f"R2 Markdown key: {results['https://example.com']['r2_markdown_key']}")

# Upload multiple URLs
results = pathik.crawl_to_r2([
    "https://example.com",
    "https://httpbin.org/html"
], uuid_str=my_uuid)
```

#### Kafka Streaming

```python
import pathik
import uuid

# Generate a session ID to track this batch of streams
session_id = str(uuid.uuid4())

# URLs to crawl and stream
urls = [
    "https://www.wikipedia.org",
    "https://www.github.com",
    "https://news.ycombinator.com"
]

# Stream content to Kafka
results = pathik.stream_to_kafka(
    urls=urls,                   # URLs to crawl and stream
    content_type="both",         # Stream both HTML and Markdown
    session=session_id,          # Add session ID to messages
    topic="pathik.crawl",        # Set Kafka topic
    parallel=True                # Process URLs in parallel
)

# Print results
for url, result in results.items():
    if result["success"]:
        print(f"✅ Successfully streamed {url}")
    else:
        print(f"❌ Failed to stream {url}: {result.get('error', 'Unknown error')}")

# You can use this session ID to filter messages when consuming from Kafka
print(f"Session ID for filtering: {session_id}")
```

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

## Kafka Streaming

Pathik supports streaming crawled content directly to Kafka. This is useful for real-time processing pipelines.

### Basic Usage

```python
import pathik
import uuid

# Generate a session ID to track this batch of streams
session_id = str(uuid.uuid4())

# URLs to crawl and stream
urls = [
    "https://www.wikipedia.org",
    "https://www.github.com",
    "https://news.ycombinator.com"
]

# Stream content to Kafka
results = pathik.stream_to_kafka(
    urls=urls,                   # URLs to crawl and stream
    content_type="both",         # Stream both HTML and Markdown
    session=session_id,          # Add session ID to messages
    topic="pathik.crawl",        # Set Kafka topic
    parallel=True                # Process URLs in parallel
)

# Print results
for url, result in results.items():
    if result["success"]:
        print(f"✅ Successfully streamed {url}")
    else:
        print(f"❌ Failed to stream {url}: {result.get('error', 'Unknown error')}")

# You can use this session ID to filter messages when consuming from Kafka
print(f"Session ID for filtering: {session_id}")
```

### Kafka Configuration

Configure Kafka connection details in the `.env` file:

```
KAFKA_BROKERS=localhost:9092        # Comma-separated list of brokers
KAFKA_TOPIC=pathik_crawl_data       # Topic to publish to
KAFKA_USERNAME=                     # Optional username for SASL authentication
KAFKA_PASSWORD=                     # Optional password for SASL authentication
KAFKA_CLIENT_ID=pathik-crawler      # Client ID for Kafka
KAFKA_USE_TLS=false                 # Whether to use TLS
```

Alternatively, you can configure these settings in your code with the CLI-based approach:

```python
from pathik.cli import crawl

results = crawl(
    urls=["https://example.com"],
    kafka=True,
    kafka_brokers="localhost:9092",
    kafka_topic="my.topic",
    kafka_username="user",
    kafka_password="pass",
    kafka_client_id="pathik-client",
    kafka_use_tls=True,
    session_id="my-session-id"
)
```

### Kafka Message Format

When streaming to Kafka, Pathik sends two messages per URL:

1. HTML Content:
   - Key: URL
   - Value: Raw HTML content
   - Headers:
     - url: The original URL
     - contentType: "text/html"
     - timestamp: ISO 8601 timestamp
     - session: Session ID (if provided)

2. Markdown Content:
   - Key: URL
   - Value: Markdown content
   - Headers:
     - url: The original URL
     - contentType: "text/markdown"
     - timestamp: ISO 8601 timestamp
     - session: Session ID (if provided)

### Kafka Consumer Examples

Pathik includes example consumers for Go, Python, and JavaScript in the `examples` directory.

#### Python Consumer Example

```python
from kafka import KafkaConsumer
import json

# Connect to Kafka
consumer = KafkaConsumer(
    'pathik_crawl_data',                  # Topic
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',         # Start from beginning
    enable_auto_commit=True,
    group_id='pathik-consumer-group'
)

# Optional: filter by session ID
session_filter = "user123"  # Set to None to receive all messages

# Process messages
for message in consumer:
    # Extract headers
    headers = {k: v.decode('utf-8') for k, v in message.headers}
    
    # Filter by session if needed
    if session_filter and headers.get('session') != session_filter:
        continue
        
    # Get message details
    url = message.key.decode('utf-8')
    content_type = headers.get('contentType')
    
    print(f"Received from {url}: {content_type} content ({len(message.value)} bytes)")
    
    # Process content based on type
    if content_type == 'text/html':
        # Process HTML...
        pass
    elif content_type == 'text/markdown':
        # Process Markdown...
        pass
```

## Using in Docker

When using Pathik in a Docker container, you need to install the required dependencies for Chromium:

```dockerfile
FROM python:3.10-slim

# Install Chromium dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgtk-3-0 \
    libx11-6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libcups2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    fonts-freefont-ttf

# Install pathik
RUN pip install pathik
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/justrach/pathik.git
cd pathik

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```