#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print messages with color
print_message() {
  echo -e "${GREEN}$1${NC}"
}

print_warning() {
  echo -e "${YELLOW}$1${NC}"
}

print_error() {
  echo -e "${RED}$1${NC}"
}

# Get the latest tag
get_latest_tag() {
  git fetch --tags
  latest_tag=$(git tag -l "v*" --sort=-v:refname | head -n 1)
  
  if [ -z "$latest_tag" ]; then
    print_warning "No existing version tags found. Starting with v0.1.0."
    latest_tag="v0.1.0"
  else
    print_message "Latest version tag: $latest_tag"
  fi
  
  # Strip the 'v' prefix for version calculations
  latest_version=${latest_tag#v}
}

# Increment version
increment_version() {
  # Split version into parts
  IFS='.' read -r -a version_parts <<< "$latest_version"
  
  major=${version_parts[0]}
  minor=${version_parts[1]}
  patch=${version_parts[2]}
  
  case $1 in
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    patch|*)
      patch=$((patch + 1))
      ;;
  esac
  
  new_version="$major.$minor.$patch"
  new_tag="v$new_version"
}

# Main script

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  print_error "Not in a git repository!"
  exit 1
fi

# Get the latest tag
get_latest_tag

# Process command line arguments
if [ $# -eq 0 ]; then
  # No arguments - show interactive menu
  echo "Current version: $latest_tag"
  echo "What would you like to do?"
  echo "1) Increment patch version (default)"
  echo "2) Increment minor version"
  echo "3) Increment major version"
  echo "4) Specify exact version"
  
  read -p "Select option [1-4] (default: 1): " option
  
  case $option in
    2) increment_version minor ;;
    3) increment_version major ;;
    4) 
      read -p "Enter version (without 'v' prefix): " user_version
      new_version=$user_version
      new_tag="v$new_version"
      ;;
    *) increment_version patch ;;
  esac
else
  # Version provided as command line argument
  if [[ $1 == v* ]]; then
    new_tag=$1
    new_version=${new_tag#v}
  else
    new_version=$1
    new_tag="v$new_version"
  fi
fi

print_message "Creating new version tag: $new_tag"

# Check if there are uncomitted changes
if [ -n "$(git status --porcelain)" ]; then
  print_warning "You have uncommitted changes. It's recommended to commit them before creating a new release."
  read -p "Continue anyway? (y/n): " continue_choice
  if [[ $continue_choice != "y" && $continue_choice != "Y" ]]; then
    print_message "Aborting. Please commit your changes first."
    exit 0
  fi
fi

# Create and push the tag
print_message "Creating tag $new_tag with message 'Release $new_tag'..."
git tag -a "$new_tag" -m "Release $new_tag"

print_message "Pushing tag to remote..."
git push origin "$new_tag"

print_message "Version $new_tag has been created and pushed!"
print_message "GitHub Actions workflow should start automatically."
print_message "Check the progress at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\).git/\1/')/actions" 