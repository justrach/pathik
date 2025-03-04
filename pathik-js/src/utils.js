/**
 * Pathik utility functions
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const os = require('os');

/**
 * Get the path to the pathik binary
 * 
 * @returns {Promise<string>} Path to the binary
 */
async function getBinaryPath() {
  // Determine binary name based on platform
  const binaryName = os.platform() === 'win32' ? 'pathik_bin.exe' : 'pathik_bin';
  
  // Check in the package's bin directory first
  const packageBinPath = path.join(__dirname, '..', 'bin', binaryName);
  if (fs.existsSync(packageBinPath)) {
    return packageBinPath;
  }
  
  // Check in node_modules/.bin
  const nodeModulesBinPath = path.join(__dirname, '..', '..', '.bin', binaryName);
  if (fs.existsSync(nodeModulesBinPath)) {
    return nodeModulesBinPath;
  }
  
  // Check if it's available in PATH
  try {
    const { error, stdout } = await execPromise(`which ${binaryName}`);
    if (!error && stdout) {
      return stdout.trim();
    }
  } catch (err) {
    // Ignore and try next location
  }
  
  // If binary not found, try to build it
  console.log('Binary not found, attempting to build it...');
  try {
    await buildBinary();
    
    // Check if build was successful
    if (fs.existsSync(packageBinPath)) {
      return packageBinPath;
    }
  } catch (err) {
    console.error('Failed to build binary:', err);
  }
  
  throw new Error(`Pathik binary not found. Please run 'npm run build-binary' first.`);
}

/**
 * Build the Go binary
 * 
 * @returns {Promise<void>}
 */
async function buildBinary() {
  return new Promise((resolve, reject) => {
    exec('node scripts/build.js', (error, stdout, stderr) => {
      if (error) {
        console.error(`Build error: ${stderr}`);
        return reject(error);
      }
      console.log(stdout);
      resolve();
    });
  });
}

/**
 * Promisified exec function
 * 
 * @param {string} command - Command to execute
 * @returns {Promise<Object>} Object with stdout and stderr
 */
function execPromise(command) {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      resolve({ error, stdout, stderr });
    });
  });
}

module.exports = {
  getBinaryPath,
  buildBinary
}; 