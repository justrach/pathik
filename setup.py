import os
import subprocess
import sys
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist

VERSION = '0.1.1'

def build_go_binary():
    """Build the Go binary for the current platform"""
    print("Building Go binary...")
    
    # Check if we're in the original source directory or in a temporary build directory
    if os.path.exists("go.mod"):
        # We're in the original directory with Go module files
        binary_name = "pathik_bin"
        if sys.platform == "win32":
            binary_name += ".exe"
        
        # Run go build
        build_cmd = ["go", "build", "-o", f"pathik/{binary_name}", "./main.go"]
        result = subprocess.run(build_cmd, capture_output=True)
        
        if result.returncode != 0:
            print(f"Error building Go binary: {result.stderr.decode()}")
            raise RuntimeError("Failed to build Go binary")
        
        print(f"Go binary built successfully: pathik/{binary_name}")
        return f"pathik/{binary_name}"
    else:
        # We're in a temporary build directory, can't build Go binary here
        print("Not in source directory, skipping Go binary build")
        return None

class BuildGoCommand:
    """Mixin to build Go binary before installation"""
    def run(self):
        # Build the Go binary
        try:
            binary_path = build_go_binary()
        except Exception as e:
            print(f"Warning: Failed to build Go binary: {e}")
            print("Package will be installed without the binary. Run build_binary.py manually.")
        
        # Run the original command
        super().run()

class BuildSdistWithBinary(sdist):
    """Custom sdist command that includes pre-built binary"""
    def run(self):
        # Build the binary first
        try:
            build_go_binary()
        except Exception as e:
            print(f"Warning: Failed to build Go binary: {e}")
        
        # Run the original sdist
        super().run()

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
        "pathik": ["pathik_bin*"],
    },
    cmdclass={
        'install': InstallWithGoBuild,
        'develop': DevelopWithGoBuild,
        'sdist': BuildSdistWithBinary,
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 