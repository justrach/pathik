#!/usr/bin/env python
"""
Script to build the Go binary for pathik
"""
import os
import subprocess
import sys
import platform

def main():
    print("Building Go binary for Pathik...")
    
    # Determine the binary name based on platform
    binary_name = "pathik_bin"
    if platform.system() == "Windows":
        binary_name += ".exe"
    
    # Ensure the pathik directory exists
    os.makedirs("pathik", exist_ok=True)
    
    # Build the Go binary
    cmd = ["go", "build", "-o", f"pathik/{binary_name}", "./main.go"]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode != 0:
        print(f"Error building Go binary: {result.stderr.decode()}")
        sys.exit(1)
    
    print(f"Go binary built successfully: pathik/{binary_name}")
    print("You can now install the Python package with:")
    print("  pip install -e .")

if __name__ == "__main__":
    main() 