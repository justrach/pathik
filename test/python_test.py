#!/usr/bin/env python
"""
Test script for the pathik Python API with the command ordering fix.
"""
import os
import sys
import json
import subprocess
from pprint import pprint

# Add parent directory to the path
sys.path.insert(0, os.path.abspath('..'))

# Import logging to see what's happening
import logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# First test is just to import pathik
print("Importing pathik...")
import pathik
print(f"Successfully imported pathik version {pathik.__version__}")

# Monkey patch subprocess.run to see the actual commands being run
original_run = subprocess.run
commands_run = []

def mock_run(*args, **kwargs):
    commands_run.append(args[0] if args else kwargs.get('args', ''))
    print(f"Mock subprocess.run called with: {' '.join(args[0] if args else kwargs.get('args', []))}")
    # Pass through to the original function
    return original_run(*args, **kwargs)

# Apply the monkey patch
subprocess.run = mock_run

# Now test the crawl function
print("\n=== Testing pathik.crawl ===")
output_dir = "/tmp/pathik_python_test"
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory: {output_dir}")

# Try using the crawler directly 
print("\n=== Testing direct import from pathik.crawler ===")
from pathik.crawler import crawl as direct_crawl
from pathik.crawler import get_binary_path

# Get the binary path
binary_path = get_binary_path()
print(f"Binary path: {binary_path}")

# Test the command directly to verify behavior
def test_direct_command(cmd):
    print(f"\nTesting direct command: {' '.join(cmd)}")
    result = original_run(cmd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    print(f"Output: {result.stdout[:200]}...")
    print(f"Error: {result.stderr[:200]}..." if result.stderr else "No errors")
    return result

# Test both command orders
test_direct_command([binary_path, "-outdir", output_dir, "-crawl", "https://example.com"])
test_direct_command([binary_path, "-crawl", "https://example.com", "-outdir", output_dir])

# Test crawler directly
print("\n=== Testing crawler module directly ===")
try:
    result = direct_crawl("https://example.com", output_dir=output_dir)
    print("Command(s) executed:")
    for cmd in commands_run:
        print(f"  {' '.join(cmd)}")
    print("\nCrawler direct result:")
    pprint(result)
except Exception as e:
    print(f"Error: {e}")

# Clear the commands list
commands_run.clear()

# Test the CLI crawl
print("\n=== Testing cli.crawl ===")
from pathik.cli import crawl as cli_crawl
try:
    result = cli_crawl("https://example.com", output_dir=output_dir)
    print("Command(s) executed:")
    for cmd in commands_run:
        print(f"  {' '.join(cmd)}")
    print("\nCLI crawl result:")
    pprint(result) 
except Exception as e:
    print(f"Error: {e}")

# Restore the original subprocess.run
subprocess.run = original_run

print("\n=== Test complete ===")
print("Commands executed during test:")
for i, cmd in enumerate(commands_run):
    print(f"{i+1}: {' '.join(cmd)}")

# Check files that were created
print("\nFiles created:")
created_files = os.listdir(output_dir)
for file in created_files:
    file_path = os.path.join(output_dir, file)
    print(f"  - {file} ({os.path.getsize(file_path)} bytes)")

print("\nSummary:")
print(f"Number of commands executed: {len(commands_run)}")
print(f"Number of files created: {len(created_files)}")
if "https://example.com" in result and "html" in result["https://example.com"]:
    print("✅ JSON result contains expected URL and HTML file")
else:
    print("❌ JSON result does not contain expected structure")
    print(f"Keys in result: {list(result.keys())}")
    if "raw_output" in result:
        print(f"Raw output: {result['raw_output']}") 