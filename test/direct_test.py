#!/usr/bin/env python
"""
Direct test for pathik binary to verify correct command ordering.

This test script runs the pathik Go binary directly with different
command ordering patterns to determine which one works correctly.
"""
import os
import sys
import subprocess
import json
import tempfile
import shutil

def run_command(cmd, show_output=True):
    """Run a command and return the result with exit code"""
    if show_output:
        print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if show_output:
            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout[:500] + ("..." if len(result.stdout) > 500 else ""))
            if result.stderr:
                print("STDERR:")
                print(result.stderr[:500] + ("..." if len(result.stderr) > 500 else ""))
        
        return result
    except Exception as e:
        if show_output:
            print(f"Error executing command: {e}")
        return None

def find_pathik_binary():
    """Find the pathik binary location"""
    # Try to find the binary in the Python package
    try:
        import pathik
        path_parts = os.path.abspath(pathik.__file__).split(os.sep)
        
        # Look for the bin directory
        package_dir = os.sep.join(path_parts[:-1])  # Directory containing the package
        
        # Try to determine the platform
        import platform
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Map to expected directory names
        if system == 'darwin':
            system = 'darwin'
        elif system.startswith('linux'):
            system = 'linux'
        elif system.startswith('win'):
            system = 'windows'
            
        if machine in ('x86_64', 'amd64'):
            machine = 'amd64'
        elif machine in ('arm64', 'aarch64'):
            machine = 'arm64'
        
        platform_dir = f"{system}_{machine}"
        
        # Check if bin directory exists with platform subdirectory
        bin_dir = os.path.join(package_dir, 'bin', platform_dir)
        if os.path.exists(bin_dir):
            binary_name = 'pathik_bin.exe' if system == 'windows' else 'pathik_bin'
            binary_path = os.path.join(bin_dir, binary_name)
            if os.path.exists(binary_path):
                return binary_path
    except:
        pass
    
    # Try to locate it in the project structure
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Check common locations
    possible_locations = [
        os.path.join(project_root, 'pathik', 'bin', 'darwin_arm64', 'pathik_bin'),
        os.path.join(project_root, 'pathik', 'bin', 'darwin_amd64', 'pathik_bin'),
        os.path.join(project_root, 'pathik', 'bin', 'linux_amd64', 'pathik_bin'),
        os.path.join(project_root, 'pathik_bin'),
        os.path.join(project_root, 'bin', 'pathik_bin'),
    ]
    
    for location in possible_locations:
        if os.path.exists(location) and os.access(location, os.X_OK):
            return location
    
    # If not found, try using 'which'
    try:
        result = subprocess.run(['which', 'pathik_bin'], stdout=subprocess.PIPE, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    return None

def test_binary_command_orders():
    """Test different command orderings with the pathik binary"""
    binary_path = find_pathik_binary()
    if not binary_path:
        print("❌ ERROR: Could not find pathik binary")
        return False
    
    print(f"Found pathik binary at: {binary_path}")
    
    # Check binary version
    version_result = run_command([binary_path, '-version'])
    if version_result.returncode != 0:
        print("❌ ERROR: Failed to get binary version")
        return False
    
    # Create output directory
    output_dir = tempfile.mkdtemp(prefix="pathik_direct_test_")
    print(f"Using output directory: {output_dir}")
    
    try:
        test_url = "https://example.com"
        
        print("\n=== Testing different command orderings ===")
        
        # Test 1: flags before -crawl (CORRECT ORDER)
        print("\n[TEST 1] flags before -crawl (CORRECT ORDER)")
        cmd1 = [binary_path, "-outdir", output_dir, "-crawl", test_url]
        result1 = run_command(cmd1)
        passed1 = result1.returncode == 0
        
        if passed1:
            print("✅ PASSED: Flags before -crawl works correctly")
            # Check if files were created
            html_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
            if html_files:
                print(f"HTML file created: {html_files[0]}")
        else:
            print("❌ FAILED: Flags before -crawl failed")
        
        # Clean output directory
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
        
        # Test 2: -crawl before URLs before flags (INCORRECT ORDER)
        print("\n[TEST 2] -crawl before URLs before flags (INCORRECT ORDER)")
        cmd2 = [binary_path, "-crawl", test_url, "-outdir", output_dir]
        result2 = run_command(cmd2)
        passed2 = result2.returncode == 0
        
        if passed2:
            print("⚠️ UNEXPECTED PASS: -crawl before URLs before flags works (should fail)")
            # Check if files were created
            html_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
            if html_files:
                print(f"HTML file created: {html_files[0]}")
        else:
            print("✅ EXPECTED FAILURE: -crawl before URLs before flags failed (correct behavior)")
            print(f"Error message: {result2.stderr.strip()}")
        
        # Clean output directory
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
        
        # Test 3: -crawl before flags before URLs (MIXED ORDER)
        print("\n[TEST 3] -crawl before flags before URLs (MIXED ORDER)")
        cmd3 = [binary_path, "-crawl", "-outdir", output_dir, test_url]
        result3 = run_command(cmd3)
        passed3 = result3.returncode == 0
        
        if passed3:
            print("⚠️ UNEXPECTED PASS: -crawl before flags before URLs works (unexpected)")
            # Check if files were created
            html_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
            if html_files:
                print(f"HTML file created: {html_files[0]}")
        else:
            print("✅ EXPECTED FAILURE: -crawl before flags before URLs failed (expected)")
            print(f"Error message: {result3.stderr.strip()}")
        
        print("\n=== Test Results Summary ===")
        print(f"Test 1 (Correct Order): {'✅ PASSED' if passed1 else '❌ FAILED'}")
        print(f"Test 2 (Incorrect Order): {'❌ FAILED' if not passed2 else '⚠️ UNEXPECTED PASS'}")
        print(f"Test 3 (Mixed Order): {'❌ FAILED' if not passed3 else '⚠️ UNEXPECTED PASS'}")
        
        if passed1 and not passed2:
            print("\n✅ OVERALL: Command ordering behavior is correct!")
            print("The binary requires flags to come before -crawl, and URLs to come after -crawl")
            return True
        else:
            print("\n⚠️ OVERALL: Command ordering behavior is not as expected!")
            return False
    
    finally:
        # Clean up
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    test_binary_command_orders() 