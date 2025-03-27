# Pathik Command Ordering Fix

## Issue Description

Pathik versions up to 0.3.0 had a critical issue with how command-line arguments were ordered when calling the Go binary. The issue caused flags to be incorrectly interpreted as URLs, resulting in errors like:

```
Invalid URL '-outdir': only HTTP and HTTPS schemes are allowed
```

## Root Cause

The Go binary expects a specific order of command-line arguments:

```
pathik_bin [flags] -crawl [urls]
```

However, the Python wrapper was incorrectly constructing commands with URLs before flags:

```
pathik_bin -crawl [urls] [flags]
```

## Fix Applied

The following files have been updated to fix the issue:

1. `pathik/cli.py`: Reordered command arguments to place all flags before `-crawl`
2. `pathik/crawler.py`: Fixed command ordering in multiple places:
   - In the `crawl()` function (both parallel and sequential modes)
   - In the `stream_to_kafka()` function

## Command-Line Arguments Order Rules

When using the Go binary directly or through the Python API, the following rules must be followed:

1. All flags MUST come BEFORE the `-crawl` flag
2. The `-crawl` flag must come immediately before the URLs
3. No flags can appear after the URLs

Correct pattern:
```
pathik_bin [flags] -crawl [urls]
```

Example:
```
pathik_bin -outdir ./output -parallel -kafka -crawl https://example.com https://example.org
```

## Testing the Fix

The fix has been tested with various flag combinations and URLs to ensure correct behavior.

```python
import pathik

# Now works correctly
result = pathik.crawl(
    urls=["https://example.com"],
    output_dir="./output",
    parallel=True
)
```

## Version Notes

This fix will be included in the next release. If you encounter any issues with the fix, please report them. 