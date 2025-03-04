#!/usr/bin/env node
/**
 * Post-installation script for pathik
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Determine binary name based on platform
const binaryName = os.platform() === 'win32' ? 'pathik_bin.exe' : 'pathik_bin';
const binDir = path.join(__dirname, '..', 'bin');
const binaryPath = path.join(binDir, binaryName);

// Create bin directory if it doesn't exist
if (!fs.existsSync(binDir)) {
  fs.mkdirSync(binDir, { recursive: true });
}

console.log('Pathik post-installation setup...');

// Check if binary already exists
if (fs.existsSync(binaryPath)) {
  console.log(`Binary already exists at: ${binaryPath}`);
  process.exit(0);
}

try {
  // Look for the Go binary in parent directory
  const mainGoPath = path.join(__dirname, '..', '..', 'main.go');
  
  if (!fs.existsSync(mainGoPath)) {
    console.log(`Info: main.go not found at expected location: ${mainGoPath}`);
    console.log('You may need to build the binary manually with "npm run build-binary"');
    process.exit(0);
  }

  // Build the Go binary
  console.log('Building Go binary...');
  const buildCommand = `go build -o "${binaryPath}" "${mainGoPath}"`;
  execSync(buildCommand, { stdio: 'inherit' });
  
  console.log(`Go binary built successfully: ${binaryPath}`);
} catch (error) {
  console.log('Note: Could not automatically build the Go binary.');
  console.log('This is normal if Go is not installed or the source is not available.');
  console.log('You can build it manually by running "npm run build-binary"');
} 