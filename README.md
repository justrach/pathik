# Pathik

A powerful web crawling tool with Go implementation and Python bindings. Supports local storage and optional Cloudflare R2 storage.

## INSTALLATION

### Prerequisites

- Go 1.16+
- Python 3.6+

### Install Python Package

```sh
pip install pathik
```

### Clone Repository

```sh
git clone https://github.com/yourusername/pathik.git
cd pathik
```

### Install in Development Mode

```sh
pip install -e .
```

## BUILDING GO BINARY

### Navigate to Pathik Directory

```sh
cd pathik
```

### Build Binary Using Script

```sh
python build_binary.py
```

### Expected Output:

```
Building Go binary in /path/to/pathik
Build successful!
Binary located at: /path/to/pathik/pathik_bin
Testing binary...
Binary output: [Help text from binary]
```

## USAGE

### Python Usage

#### Basic Crawling

```python
import pathik
import os

output_dir = os.path.abspath("output_data")
os.makedirs(output_dir, exist_ok=True)

urls = ["https://example.com"]
results = pathik.crawl(urls, output_dir)

for url, files in results.items():
    print(f"URL: {url}")
    print(f"HTML: {files['html']}")
    print(f"Markdown: {files['markdown']}")
```

#### R2 Upload (Optional)

```python
results = pathik.crawl_to_r2(
    ["https://example.com"],
    uuid_str="my-id"
)

for url, info in results.items():
    print(f"R2 HTML Key: {info['r2_html_key']}")
    print(f"Local File: {info['local_html_file']}")
```

### Direct Go Usage

#### Local Crawling

```sh
./pathik_bin -crawl -outdir ./output https://example.com
```

#### R2 Upload

```sh
./pathik_bin -r2 -uuid my-id -dir ./output https://example.com
```

## TROUBLESHOOTING

### Missing Binary

```sh
cd pathik
python build_binary.py
```

### Path Issues

```python
# Use absolute paths
output_dir = os.path.abspath("./output")
```

### Import Errors

```sh
pip uninstall -y pathik
cd pathik && pip install -e .
```

## PROJECT STRUCTURE

- `main.go` - CLI interface
- `crawler/` - Web crawling logic
- `storage/` - File storage handlers
- `pathik/` - Python bindings
- `__init__.py` - Package setup
- `crawler.py` - Go integration
- `simple.py` - Python fallback

## CONFIGURATION

Configure R2 credentials in `storage.go` or through environment variables.

## LICENSE

MIT License
