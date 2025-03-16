# Pathik

<p align="center">
  <img src="assets/pathik_logo.png" alt="Pathik Logo">
</p>

A high-performance web crawler implemented in Go with Python and JavaScript bindings.

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

## Python Installation

```bash
pip install pathik
```

## JavaScript Installation

```bash
npm install pathik
```

## Python Usage

```python
import pathik
import os

# Create an output directory with an absolute path
output_dir = os.path.abspath("output_data")
os.makedirs(output_dir, exist_ok=True)

# Crawl a single URL
result = pathik.crawl('https://example.com', output_dir=output_dir)
print(f"HTML file: {result['https://example.com']['html']}")
print(f"Markdown file: {result['https://example.com']['markdown']}")

# Crawl multiple URLs in parallel (default behavior)
urls = [
    "https://example.com",
    "https://news.ycombinator.com",
    "https://github.com",
    "https://wikipedia.org"
]
results = pathik.crawl(urls, output_dir=output_dir)

# Crawl URLs sequentially (parallel disabled)
results = pathik.crawl(urls, output_dir=output_dir, parallel=False)

# Crawl and upload to R2
r2_results = pathik.crawl_to_r2(urls, uuid_str='my-unique-id', parallel=True)
```

## JavaScript Usage

```javascript
const pathik = require('pathik');
const path = require('path');
const fs = require('fs');

// Create output directory
const outputDir = path.resolve('./output_data');
fs.mkdirSync(outputDir, { recursive: true });

// Crawl a single URL
pathik.crawl('https://example.com', { outputDir })
  .then(results => {
    console.log(`HTML file: ${results['https://example.com'].html}`);
  });

// Crawl multiple URLs in parallel (default behavior)
const urls = [
  'https://example.com',
  'https://news.ycombinator.com',
  'https://github.com'
];

pathik.crawl(urls, { outputDir })
  .then(results => {
    console.log(`Crawled ${Object.keys(results).length} URLs`);
  });

// Crawl URLs sequentially
pathik.crawl(urls, { outputDir, parallel: false })
  .then(results => {
    console.log(`Crawled ${Object.keys(results).length} URLs sequentially`);
  });

// Upload to R2
pathik.crawlToR2(urls, { uuid: 'my-unique-id' })
  .then(results => {
    console.log('R2 Upload complete');
  });
```

## Python API

### pathik.crawl(urls, output_dir=None, parallel=True)

Crawl URLs and save the content locally.

**Parameters:**
- `urls`: A single URL string or a list of URLs to crawl
- `output_dir`: Directory to save crawled files (uses a temporary directory if None)
- `parallel`: Whether to use parallel crawling (default: True)

**Returns:**
- A dictionary mapping URLs to file paths: `{url: {"html": html_path, "markdown": markdown_path}}`

### pathik.crawl_to_r2(urls, uuid_str=None, parallel=True)

Crawl URLs and upload the content to Cloudflare R2.

**Parameters:**
- `urls`: A single URL string or a list of URLs to crawl
- `uuid_str`: UUID to prefix filenames for uploads (generates one if None)
- `parallel`: Whether to use parallel crawling (default: True)

**Returns:**
- A dictionary with R2 upload information

## JavaScript API

### pathik.crawl(urls, options)

Crawl URLs and save content locally.

**Parameters:**
- `urls`: String or array of URLs to crawl
- `options`: Object with crawl options
  - `outputDir`: Directory to save output (uses temp dir if null)
  - `parallel`: Enable/disable parallel crawling (default: true)

**Returns:**
- Promise resolving to an object mapping URLs to file paths

### pathik.crawlToR2(urls, options)

Crawl URLs and upload content to R2.

**Parameters:**
- `urls`: String or array of URLs to crawl
- `options`: Object with R2 options
  - `uuid`: UUID to prefix filenames (generates random UUID if null)
  - `parallel`: Enable/disable parallel crawling (default: true)

**Returns:**
- Promise resolving to an object mapping URLs to R2 keys

## Requirements

- Go 1.18+ (for building the binary)
- Python 3.6+ or Node.js 14+

## Building from Source

For Python:
```bash
python build_binary.py
pip install -e .
```

For JavaScript:
```bash
npm run build-binary
npm install
```

## License

Apache 2.0 