#!/usr/bin/env python
"""
Diagnostic script to identify import issues with pathik
"""
import sys
import os
import importlib

# Print Python path
print("Python path:")
for p in sys.path:
    print(f"  - {p}")

# Look for pathik in site-packages
site_packages = [p for p in sys.path if 'site-packages' in p]
for sp in site_packages:
    pathik_path = os.path.join(sp, 'pathik')
    if os.path.exists(pathik_path):
        print(f"\nFound pathik in: {pathik_path}")
        print("Contents:")
        for root, dirs, files in os.walk(pathik_path):
            level = root.replace(pathik_path, '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{sub_indent}{f}")

# Try importing pathik
print("\nImporting pathik...")
try:
    import pathik
    print(f"pathik imported from: {pathik.__file__}")
    print(f"pathik version: {getattr(pathik, '__version__', 'Unknown')}")
    print("\nPathik module dir:")
    for attr in dir(pathik):
        if not attr.startswith('_'):
            print(f"  - {attr}")
except Exception as e:
    print(f"Error importing pathik: {e}")

# Try loading from local source
print("\nTrying to load from local source...")
# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to sys.path")

try:
    import pathik as local_pathik
    print(f"Local pathik imported from: {local_pathik.__file__}")
    print(f"Local pathik version: {getattr(local_pathik, '__version__', 'Unknown')}")
    
    # Forcefully reload the module
    importlib.reload(local_pathik)
    print("Reloaded local pathik module")
    
    print("\nLocal pathik module dir after reload:")
    for attr in dir(local_pathik):
        if not attr.startswith('_'):
            print(f"  - {attr}")
            
    # Try accessing stream_to_kafka
    if hasattr(local_pathik, 'stream_to_kafka'):
        print("\nstream_to_kafka function exists!")
        func_source = getattr(local_pathik.stream_to_kafka, '__code__', None)
        if func_source:
            print(f"Function defined in: {func_source.co_filename}")
    else:
        print("\nstream_to_kafka function not found in local module")
        
    # Try accessing crawl
    if hasattr(local_pathik, 'crawl'):
        print("\ncrawl function exists!")
        func_source = getattr(local_pathik.crawl, '__code__', None)
        if func_source:
            print(f"Function defined in: {func_source.co_filename}")
    else:
        print("\ncrawl function not found in local module")
        
except Exception as e:
    print(f"Error with local pathik: {e}") 