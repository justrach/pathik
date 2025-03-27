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

#### Secure Kafka Streaming with Buffer Customization

```python
import pathik
import uuid

# Generate a session ID for tracking
session_id = str(uuid.uuid4())

# Stream a single URL to Kafka
result = pathik.stream_to_kafka("https://example.com", session=session_id)
print(f"Success: {result['https://example.com']['success']}")

# Stream multiple URLs with custom options
results = pathik.stream_to_kafka(
    urls=["https://example.com", "https://httpbin.org/html"],
    content_type="html",              # Options: "html", "markdown", or "both"
    topic="custom_topic",             # Optional custom topic
    session=session_id,               # Optional session ID
    parallel=True,                    # Process URLs in parallel (default)
    max_message_size=15728640,        # 15MB message size limit
    buffer_memory=157286400           # 150MB buffer memory
)

# Check results
for url, status in results.items():
    if status["success"]:
        print(f"Successfully streamed {url}")
    else:
        print(f"Failed to stream {url}: {status.get('error')}")
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

# Set custom buffer sizes
pathik kafka --max-message-size 15728640 --buffer-memory 157286400 https://example.com

# Combine options
pathik kafka -c html -t user1_data --session user123 --max-message-size 15728640 https://example.com
```

## Kafka Streaming

Pathik supports streaming crawled content directly to Kafka. This is useful for real-time processing pipelines.

### Kafka Configuration

Configure Kafka connection details using environment variables or `.env` file:

```
KAFKA_BROKERS=localhost:9092        # Comma-separated list of brokers
KAFKA_TOPIC=pathik_crawl_data       # Topic to publish to
KAFKA_USERNAME=                     # Optional username for SASL authentication
KAFKA_PASSWORD=                     # Optional password for SASL authentication
KAFKA_CLIENT_ID=pathik-crawler      # Client ID for Kafka
KAFKA_USE_TLS=false                 # Whether to use TLS
KAFKA_MAX_MESSAGE_SIZE=10485760     # 10MB max message size (default)
KAFKA_BUFFER_MEMORY=104857600       # 100MB buffer memory (default)
KAFKA_MAX_REQUEST_SIZE=20971520     # 20MB max request size (default)
```

### Buffer Size Customization

You can customize Kafka producer and consumer buffer sizes for handling large content:

```python
# Custom buffer sizes for producer
pathik.stream_to_kafka(
    "https://example.com",
    max_message_size=15728640,    # 15MB max message size (default: 10MB)
    buffer_memory=157286400       # 150MB buffer memory (default: 100MB)
)

# For consuming large messages
python kafka_consumer_direct.py --session=YOUR_SESSION_ID --max-bytes=20971520 --max-partition-bytes=10485760
```

For debugging or handling large web pages, you may need to increase these buffer sizes to prevent message size errors.

### Optional Kafka Dependencies

To use Kafka streaming, install the required dependencies:

```bash
# Install pathik with Kafka support
pip install "pathik[kafka]"

# Or install the dependency separately
pip install kafka-python

# For Snappy compression support (recommended)
pip install python-snappy
```

If Kafka dependencies are not available, Pathik will use a fallback simulation mode that logs the messages locally without actually sending them to Kafka.

### Kafka Message Format

When streaming to Kafka, Pathik sends two messages per URL:

1. HTML Content:
   - Key: URL
   - Value: Raw HTML content
   - Headers:
     - url: The original URL
     - contentType: "text/html"
     - timestamp: ISO 8601 timestamp
     - sessionID: Session ID (if provided)

2. Markdown Content:
   - Key: URL
   - Value: Markdown content
   - Headers:
     - url: The original URL
     - contentType: "text/markdown"
     - timestamp: ISO 8601 timestamp
     - sessionID: Session ID (if provided)

## Security Enhancements

Pathik includes several security features to ensure safe and reliable crawling:

### URL Validation

URLs are validated to prevent security issues:
- Only HTTP and HTTPS schemes are allowed
- Private IP addresses and localhost access are restricted
- Hostnames are resolved and checked against private IP ranges

### Input Sanitization

All inputs (file paths, session IDs, etc.) are sanitized to prevent injection attacks:
- File paths are checked for directory traversal attempts
- Session IDs are validated against a safe pattern (alphanumeric and some special chars)
- Topic names and other parameters are validated for safe characters

### Rate Limiting

Built-in rate limiting prevents accidentally overloading target servers:
- Default rate limit of 1 request per second with configurable burst
- Automatic retries with exponential backoff
- Delay between retries is configurable

### Error Handling

Robust error handling ensures graceful failure:
- Detailed error messages for troubleshooting
- Automatic retries for transient failures
- Graceful shutdown with proper cleanup