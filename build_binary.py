#!/usr/bin/env python
"""
Script to build the Go binary for pathik
"""
import os
import subprocess
import sys
import platform
import argparse

def detect_platform():
    """Detect the current platform more reliably"""
    # Determine OS
    os_name = platform.system().lower()
    if os_name.startswith('win'):
        os_name = 'windows'
    elif os_name.startswith('lin'):
        os_name = 'linux'
    elif os_name == 'darwin':
        os_name = 'darwin'
    
    # Docker/container detection for Linux
    if os.path.exists("/proc/1/cgroup") or os.path.exists("/.dockerenv"):
        print("Container environment detected, forcing OS to Linux")
        os_name = 'linux'
    
    # Determine architecture
    arch = platform.machine().lower()
    if arch in ('x86_64', 'amd64'):
        arch = 'amd64'
    elif arch in ('arm64', 'aarch64'):
        arch = 'arm64'
    elif arch in ('i386', 'i686', 'x86'):
        arch = '386'
    
    print(f"Detected platform: {os_name}_{arch}")
    return os_name, arch

def build_binary(target_os=None, target_arch=None):
    """Build the Go binary for the specified platform"""
    # Determine target platform
    if target_os is None or target_arch is None:
        current_os, current_arch = detect_platform()
        target_os = target_os or current_os  
        target_arch = target_arch or current_arch
    
    # Determine the binary name based on platform
    binary_name = "pathik_bin"
    if target_os == "windows":
        binary_name += ".exe"
    
    # Setup output path - always use the bin directory for organization
    output_path = f"pathik/bin/{target_os}_{target_arch}/{binary_name}"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Setup environment
    env = os.environ.copy()
    env["GOOS"] = target_os
    env["GOARCH"] = target_arch
    
    # Build the Go binary
    cmd = ["go", "build", "-o", output_path, "./main.go"]
    print(f"Building for {target_os}/{target_arch}: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, env=env)
    
    if result.returncode != 0:
        print(f"Error building Go binary: {result.stderr.decode()}")
        return False
    
    print(f"Go binary built successfully: {output_path}")
    
    # For current platform, also copy to main directory for backward compatibility
    current_os, current_arch = detect_platform()
    if target_os == current_os and target_arch == current_arch:
        os.makedirs("pathik", exist_ok=True)
        main_binary_path = f"pathik/{binary_name}"
        print(f"Copying binary to {main_binary_path} for current platform")
        import shutil
        shutil.copy2(output_path, main_binary_path)
        
        # Make sure it's executable
        if target_os != "windows":
            os.chmod(main_binary_path, 0o755)
            
    return True

def build_all():
    """Build binaries for all supported platforms"""
    platforms = [
        ("darwin", "amd64"),  # Intel Mac
        ("darwin", "arm64"),  # Apple Silicon Mac
        ("linux", "amd64"),   # Linux x86_64
        ("linux", "arm64"),   # Linux ARM64
        ("windows", "amd64"), # Windows x86_64
    ]
    
    success = True
    for target_os, target_arch in platforms:
        if not build_binary(target_os, target_arch):
            print(f"Failed to build for {target_os}/{target_arch}")
            success = False
    
    return success

def main():
    parser = argparse.ArgumentParser(description="Build pathik binaries")
    parser.add_argument("--all", action="store_true", help="Build for all supported platforms")
    parser.add_argument("--os", help="Target OS (darwin, linux, windows)")
    parser.add_argument("--arch", help="Target architecture (amd64, arm64, 386)")
    
    args = parser.parse_args()
    
    if args.all:
        print("Building for all supported platforms...")
        if build_all():
            print("All binaries built successfully.")
            print("You can now install the Python package with:")
            print("  pip install -e .")
        else:
            print("Some binaries failed to build.")
            sys.exit(1)
    else:
        if build_binary(args.os, args.arch):
            print("Binary built successfully.")
            print("You can now install the Python package with:")
            print("  pip install -e .")
        else:
            print("Failed to build binary.")
            sys.exit(1)

if __name__ == "__main__":
    main() 