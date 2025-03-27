#!/bin/bash
# Run all Pathik command ordering tests

set -e  # Exit on any error

echo "===== PATHIK COMMAND ORDERING TESTS ====="
echo "Running tests to verify the command ordering fix"
echo

# Navigate to test directory
cd "$(dirname "$0")"

# Print current directory and Python environment
echo "Current directory: $(pwd)"
echo "Python interpreter: $(which python)"
echo

# Run the command construction test first (dry run without actual API calls)
echo "Running command construction tests..."
python test_command_ordering.py
echo

# Run the full implementation test (actual API calls)
echo "Running full implementation tests..."
python test_fixed_impl.py
echo

echo "===== ALL TESTS COMPLETED =====" 