#!/usr/bin/env python
"""
Debug script to examine command construction in pathik.

This script imports the necessary functions from pathik directly
and examines the command construction to ensure flags come before
the -crawl flag and URLs come after.
"""
import os
import sys
import subprocess
from pprint import pprint

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath('..'))

# Import directly from pathik modules
from pathik.cli import crawl as cli_crawl
from pathik.crawler import get_binary_path

def debug_command_construction():
    """Debug the command construction in pathik"""
    # Replace subprocess.run to capture the command
    original_run = subprocess.run
    last_command = None
    
    def mock_run(command, *args, **kwargs):
        nonlocal last_command
        last_command = command
        
        # Create a mock result
        class MockResult:
            returncode = 0
            stdout = "{}"
            stderr = ""
        return MockResult()
    
    # Replace the run function
    subprocess.run = mock_run
    
    try:
        # Get binary path
        binary_path = get_binary_path()
        print(f"Binary path: {binary_path}")
        
        # Set up test parameters
        test_url = "https://example.com"
        output_dir = "/tmp/test_output"
        
        print("\n=== Testing command construction ===")
        print(f"URL: {test_url}")
        print(f"Output dir: {output_dir}")
        
        # Call the function that constructs the command
        cli_crawl(
            urls=test_url,
            output_dir=output_dir,
            parallel=True
        )
        
        # Analyze the command
        if last_command:
            print("\nCommand constructed:")
            print(f"{' '.join(last_command)}")
            
            # Check ordering
            binary_idx = last_command.index(binary_path)
            crawl_idx = last_command.index("-crawl") if "-crawl" in last_command else -1
            url_idx = last_command.index(test_url) if test_url in last_command else -1
            outdir_idx = last_command.index("-outdir") if "-outdir" in last_command else -1
            
            print("\nElement positions:")
            print(f"- Binary: {binary_idx}")
            print(f"- -crawl flag: {crawl_idx}")
            print(f"- URL: {url_idx}")
            print(f"- -outdir flag: {outdir_idx}")
            
            if crawl_idx > 0 and url_idx > 0 and outdir_idx > 0:
                if binary_idx < outdir_idx < crawl_idx < url_idx:
                    print("\n✅ CORRECT ORDER: binary -> flags -> -crawl -> URLs")
                else:
                    print("\n❌ INCORRECT ORDER!")
                    if outdir_idx > crawl_idx:
                        print("Problem: -outdir flag comes after -crawl")
                    if url_idx < crawl_idx:
                        print("Problem: URL comes before -crawl")
            else:
                print("\n❌ Missing critical elements in command!")
        else:
            print("\n❌ No command was constructed!")
    
    finally:
        # Restore original subprocess.run
        subprocess.run = original_run

if __name__ == "__main__":
    debug_command_construction() 