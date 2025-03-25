#!/usr/bin/env python
"""
Script to build and publish the pathik package to PyPI
"""
import os
import sys
import subprocess
import shutil
import argparse

def run_command(cmd, description=None):
    """Run a command and exit on failure"""
    if description:
        print(f"\n=== {description} ===")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"Error: Command failed with code {result.returncode}")
        sys.exit(1)
    
    return result

def main():
    """Main function to build and publish the package"""
    parser = argparse.ArgumentParser(description="Build and publish pathik to PyPI")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI instead of PyPI")
    parser.add_argument("--skip-build-binary", action="store_true", help="Skip building Go binaries")
    parser.add_argument("--skip-clean", action="store_true", help="Skip cleaning build directories")
    args = parser.parse_args()
    
    # Clean build directories if needed
    if not args.skip_clean:
        print("\n=== Cleaning build directories ===")
        dirs_to_clean = ["build", "dist", "pathik.egg-info"]
        for dir_name in dirs_to_clean:
            if os.path.exists(dir_name):
                print(f"Removing {dir_name}")
                shutil.rmtree(dir_name)
    
    # Build Go binaries if needed
    if not args.skip_build_binary:
        run_command(
            ["python", "build_binary.py", "--all"],
            "Building Go binaries for all platforms"
        )
    
    # Build Python package
    run_command(
        ["python", "setup.py", "sdist", "bdist_wheel"],
        "Building source distribution and wheel"
    )
    
    # Check package with twine
    run_command(
        ["twine", "check", "dist/*"],
        "Checking package with twine"
    )
    
    # Upload to PyPI or TestPyPI
    if args.test:
        run_command(
            ["twine", "upload", "--repository-url", "https://test.pypi.org/legacy/", "dist/*"],
            "Uploading to TestPyPI"
        )
        print("\nPackage uploaded to TestPyPI. Install with:")
        print("pip install --index-url https://test.pypi.org/simple/ pathik")
    else:
        run_command(
            ["twine", "upload", "dist/*"],
            "Uploading to PyPI"
        )
        print("\nPackage uploaded to PyPI. Install with:")
        print("pip install pathik")
    
    print("\nDone!")

if __name__ == "__main__":
    main() 