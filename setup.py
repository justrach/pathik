import os
import subprocess
import sys
import shutil
import platform
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist
from setuptools.command.bdist_wheel import bdist_wheel

VERSION = '0.2.2'

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

def build_go_binary(target_os=None, target_arch=None):
    """Build the Go binary for the specified platform or current platform if not specified"""
    # If no platform specified, use current
    if target_os is None or target_arch is None:
        current_os, current_arch = detect_platform()
        target_os = target_os or current_os
        target_arch = target_arch or current_arch
    
    print(f"Building Go binary for {target_os}_{target_arch}...")
    
    # Check if we're in the original source directory or in a temporary build directory
    if os.path.exists("go.mod"):
        # We're in the original directory with Go module files
        binary_name = "pathik_bin"
        if target_os == "windows":
            binary_name += ".exe"
        
        # Setup environment for cross-compilation if needed
        env = os.environ.copy()
        env["GOOS"] = target_os
        env["GOARCH"] = target_arch
        output_path = f"pathik/bin/{target_os}_{target_arch}/{binary_name}"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Run go build
        build_cmd = ["go", "build", "-o", output_path, "./main.go"]
        result = subprocess.run(build_cmd, capture_output=True, env=env)
        
        if result.returncode != 0:
            print(f"Error building Go binary: {result.stderr.decode()}")
            raise RuntimeError("Failed to build Go binary")
        
        print(f"Go binary built successfully: {output_path}")
        
        # For the current platform, also copy to the main directory
        current_os, current_arch = detect_platform()
        if target_os == current_os and target_arch == current_arch:
            main_binary_path = f"pathik/{binary_name}"
            shutil.copy2(output_path, main_binary_path)
            print(f"Copied current platform binary to {main_binary_path}")
            
            # Make sure it's executable
            if target_os != "windows":
                os.chmod(main_binary_path, 0o755)
                
        return output_path
    else:
        # We're in a temporary build directory, can't build Go binary here
        print("Not in source directory, skipping Go binary build")
        return None

def build_all_binaries():
    """Build binaries for all supported platforms"""
    platforms = [
        ("darwin", "amd64"),  # Intel Mac
        ("darwin", "arm64"),  # Apple Silicon Mac
        ("linux", "amd64"),   # Linux x86_64
        ("linux", "arm64"),   # Linux ARM64
        ("windows", "amd64"), # Windows x86_64
    ]
    
    built_binaries = []
    for target_os, target_arch in platforms:
        try:
            binary = build_go_binary(target_os, target_arch)
            if binary:
                built_binaries.append(binary)
        except Exception as e:
            print(f"Warning: Failed to build for {target_os}_{target_arch}: {e}")
    
    return built_binaries

class BuildGoCommand:
    """Mixin to build Go binary before installation"""
    def run(self):
        # Build the Go binary for the current platform
        try:
            current_os, current_arch = detect_platform()
            build_go_binary(current_os, current_arch)
        except Exception as e:
            print(f"Warning: Failed to build Go binary: {e}")
            print("Package will be installed without the binary. Run build_binary.py manually.")
        
        # Run the original command
        super().run()

class BuildSdistWithBinary(sdist):
    """Custom sdist command that includes pre-built binaries for all platforms"""
    def run(self):
        # Build the binaries for all platforms
        try:
            build_all_binaries()
        except Exception as e:
            print(f"Warning: Failed to build Go binaries: {e}")
        
        # Run the original sdist
        super().run()

class BuildWheel(bdist_wheel):
    """Custom wheel command that includes binary for all platforms"""
    def run(self):
        # Build binaries for all platforms
        try:
            build_all_binaries()
        except Exception as e:
            print(f"Warning: Failed to build Go binaries: {e}")
            
        # Run the original wheel build
        super().run()
    
    def finalize_options(self):
        # Mark the wheel as platform independent since we include
        # binaries for all platforms
        super().finalize_options()
        self.root_is_pure = True

class InstallWithGoBuild(BuildGoCommand, install):
    """Custom install command that builds Go binary first"""
    pass

class DevelopWithGoBuild(BuildGoCommand, develop):
    """Custom develop command that builds Go binary first"""
    pass

# Read the README.md file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pathik",
    version=VERSION,
    description="A web crawler implemented in Go with Python bindings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/justrach/pathik",
    packages=find_packages(),
    package_data={
        "pathik": ["pathik_bin*", "bin/**/*"],
    },
    cmdclass={
        'install': InstallWithGoBuild,
        'develop': DevelopWithGoBuild,
        'sdist': BuildSdistWithBinary,
        'bdist_wheel': BuildWheel,
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    # Add entry points for command-line usage
    entry_points={
        'console_scripts': [
            'pathik=pathik.cli:main',
        ],
    },
) 