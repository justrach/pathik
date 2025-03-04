#!/usr/bin/env node
/**
 * Script to build the Go binary for pathik
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

console.log('Building Go binary for Pathik...');

try {
  // Look for the Go binary in parent directory
  const mainGoPath = path.join(__dirname, '..', '..', 'main.go');
  
  if (!fs.existsSync(mainGoPath)) {
    console.error(`Error: main.go not found at expected location: ${mainGoPath}`);
    console.log('Please ensure you have the Go source files in the parent directory.');
    process.exit(1);
  }

  // Build the Go binary
  const buildCommand = `go build -o "${binaryPath}" "${mainGoPath}"`;
  console.log(`Running: ${buildCommand}`);
  
  execSync(buildCommand, { stdio: 'inherit' });
  
  console.log(`Go binary built successfully: ${binaryPath}`);
  console.log('You can now use the package:');
  console.log('  const pathik = require("pathik");');
} catch (error) {
  console.error('Failed to build Go binary:', error.message);
  process.exit(1);
} 