#!/bin/bash
# Test the pathik command line interface to verify command ordering fix

# Install pathik in development mode if needed
cd "$(dirname "$0")/.."
if ! pip show pathik >/dev/null 2>&1; then
  echo "Installing pathik in development mode..."
  pip install -e .
fi

# Create output directory
OUTPUT_DIR="$HOME/projects/pathik/test/cli_test_output"
mkdir -p "$OUTPUT_DIR"

echo "===== TESTING PATHIK CLI WITH COMMAND ORDERING FIX ====="
echo "Using output directory: $OUTPUT_DIR"

# Test 1: Basic crawl with output directory
echo -e "\n[TEST 1] Basic crawl with output directory"
echo "Running: pathik crawl https://example.com -o $OUTPUT_DIR"
pathik crawl https://example.com -o "$OUTPUT_DIR"

# Check if HTML and MD files were created
HTML_COUNT=$(find "$OUTPUT_DIR" -name "*.html" | wc -l)
MD_COUNT=$(find "$OUTPUT_DIR" -name "*.md" | wc -l)

if [ "$HTML_COUNT" -gt 0 ] && [ "$MD_COUNT" -gt 0 ]; then
  echo -e "\n✅ TEST PASSED: Files were created successfully"
  echo "HTML files: $HTML_COUNT"
  echo "Markdown files: $MD_COUNT"
  
  # List the files
  echo -e "\nFiles created:"
  find "$OUTPUT_DIR" -type f | while read -r file; do
    SIZE=$(stat -f%z "$file")
    echo "  - $file ($SIZE bytes)"
  done
else
  echo -e "\n❌ TEST FAILED: Files were not created"
  echo "HTML files: $HTML_COUNT"
  echo "Markdown files: $MD_COUNT"
fi

# Test 2: Multiple URLs with parallel flag
echo -e "\n[TEST 2] Multiple URLs with parallel flag"
echo "Running: pathik crawl https://example.com https://httpbin.org/html -o $OUTPUT_DIR -p"
pathik crawl https://example.com https://httpbin.org/html -o "$OUTPUT_DIR" -p

# Check if more HTML and MD files were created
NEW_HTML_COUNT=$(find "$OUTPUT_DIR" -name "*.html" | wc -l)
NEW_MD_COUNT=$(find "$OUTPUT_DIR" -name "*.md" | wc -l)

if [ "$NEW_HTML_COUNT" -gt "$HTML_COUNT" ] && [ "$NEW_MD_COUNT" -gt "$MD_COUNT" ]; then
  echo -e "\n✅ TEST PASSED: Additional files were created successfully"
  echo "Total HTML files: $NEW_HTML_COUNT (added $(($NEW_HTML_COUNT - $HTML_COUNT)))"
  echo "Total Markdown files: $NEW_MD_COUNT (added $(($NEW_MD_COUNT - $MD_COUNT)))"
else
  echo -e "\n❌ TEST FAILED: Additional files were not created"
  echo "HTML files: $NEW_HTML_COUNT (previously $HTML_COUNT)"
  echo "Markdown files: $NEW_MD_COUNT (previously $MD_COUNT)"
fi

echo -e "\n===== ALL TESTS COMPLETED =====" 