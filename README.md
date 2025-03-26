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
- Memory-efficient (uses ~10x less memory than browser automation tools)

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

## Usage

### Python API

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

### Building Binaries Locally

```bash
# Build for current platform
python build_binary.py

# Build for all platforms
python build_binary.py --all

# Build for specific platform
python build_binary.py --os linux --arch amd64
```

### Release Process

Pathik uses GitHub Actions to automate the release process:

1. Create and push a new tag:
   ```bash
   git tag -a v0.2.2 -m "Release v0.2.2"
   git push origin v0.2.2
   ```

2. GitHub Actions will:
   - Build binaries for all supported platforms
   - Create a GitHub Release with the binaries
   - Build and publish the Python package to PyPI

The PyPI package will download the appropriate binary from GitHub releases when needed.

## License

Apache 2.0 