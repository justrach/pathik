# Pathik for Node.js

High-performance web crawler implemented in Go with JavaScript bindings.

## Installation

```bash
npm install pathik
```

## Prerequisites

- Node.js 14+
- Go 1.16+ (for building the binary)

## Usage

### Basic Crawling

```javascript
const pathik = require('pathik');
const path = require('path');
const fs = require('fs');

// Create output directory
const outputDir = path.resolve('./output_data');
fs.mkdirSync(outputDir, { recursive: true });

// List of URLs to crawl
const urls = [
  'https://example.com',
  'https://news.ycombinator.com'
];

// Crawl the URLs
pathik.crawl(urls, { outputDir })
  .then(results => {
    console.log('Crawling results:');
    
    for (const [url, files] of Object.entries(results)) {
      console.log(`URL: ${url}`);
      console.log(`HTML file: ${files.html}`);
      console.log(`Markdown file: ${files.markdown}`);
    }
  })
  .catch(error => {
    console.error(`Error during crawling: ${error.message}`);
  });
```

### Parallel Crawling

Pathik supports parallel crawling by default, making it very efficient for batch processing:

```javascript
const pathik = require('pathik');

// List of many URLs to crawl in parallel
const urls = [
  'https://example.com',
  'https://news.ycombinator.com',
  'https://github.com',
  'https://developer.mozilla.org',
  'https://wikipedia.org'
];

// Crawl multiple URLs in parallel (default behavior)
pathik.crawl(urls, { outputDir: './output' })
  .then(results => {
    console.log(`Successfully crawled ${Object.keys(results).length} URLs`);
  });

// Disable parallel crawling if needed
pathik.crawl(urls, { 
  outputDir: './output',
  parallel: false  // Process sequentially
})
  .then(results => {
    console.log(`Successfully crawled ${Object.keys(results).length} URLs sequentially`);
  });
```

### R2 Upload

```javascript
const pathik = require('pathik');

// Crawl and upload to R2
pathik.crawlToR2(['https://example.com'], { uuid: 'my-unique-id' })
  .then(results => {
    console.log('R2 Upload results:');
    
    for (const [url, info] of Object.entries(results)) {
      console.log(`URL: ${url}`);
      console.log(`R2 HTML key: ${info.r2_html_key}`);
      console.log(`R2 Markdown key: ${info.r2_markdown_key}`);
    }
  })
  .catch(error => {
    console.error(`Error during R2 upload: ${error.message}`);
  });
```

### Command-line Interface

```bash
# Install globally
npm install -g pathik

# Crawl URLs
pathik crawl https://example.com https://news.ycombinator.com -o ./output

# Crawl multiple URLs in parallel (default)
pathik crawl https://example.com https://news.ycombinator.com https://github.com -o ./output

# Disable parallel crawling
pathik crawl https://example.com https://news.ycombinator.com --no-parallel -o ./output

# Crawl and upload to R2
pathik r2 https://example.com -u my-unique-id
```

## API

### pathik.crawl(urls, options)

Crawl URLs and save content locally.

- `urls`: String or array of URLs to crawl
- `options`: Object with crawl options
  - `outputDir`: Directory to save output (uses temp dir if null)
  - `parallel`: Boolean to enable/disable parallel crawling (default: true)
- Returns: Promise resolving to an object mapping URLs to file paths

### pathik.crawlToR2(urls, options)

Crawl URLs and upload content to R2.

- `urls`: String or array of URLs to crawl
- `options`: Object with R2 options
  - `uuid`: UUID to prefix filenames (generates random UUID if null)
  - `parallel`: Boolean to enable/disable parallel crawling (default: true)
- Returns: Promise resolving to an object mapping URLs to R2 keys

## Building the Binary

If the Go binary isn't built automatically during installation:

```bash
npm run build-binary
```

## Troubleshooting

### Missing Binary

```bash
npm run build-binary
```

### Import Errors

```bash
npm uninstall -y pathik
cd pathik-js && npm install
```

## Performance

Pathik's concurrent crawling is powered by Go's goroutines, making it significantly more memory-efficient than browser automation tools:

- Uses ~10x less memory than Playwright
- Efficiently processes large batches of URLs
- Parallelism controlled by the Go binary (default: 5 concurrent crawls)

## License

Apache 2.0 