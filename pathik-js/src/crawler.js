/**
 * Pathik crawler implementation
 */

const path = require('path');
const fs = require('fs');
const { exec, execSync } = require('child_process');
const os = require('os');
const { v4: uuidv4 } = require('uuid');
const { getBinaryPath } = require('./utils');

/**
 * Crawl a URL or list of URLs and save content locally
 * 
 * @param {string|string[]} urls - URL or array of URLs to crawl
 * @param {Object} options - Crawl options
 * @param {string} [options.outputDir=null] - Directory to save output (uses temp dir if null)
 * @returns {Promise<Object>} Result mapping URLs to file paths
 */
async function crawl(urls, options = {}) {
  // Normalize inputs
  const urlList = Array.isArray(urls) ? urls : [urls];
  if (urlList.length === 0) {
    throw new Error('No URLs provided');
  }

  // Setup output directory
  let outputDir = options.outputDir;
  let isTempDir = false;
  
  if (!outputDir) {
    outputDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pathik-'));
    isTempDir = true;
    console.log(`Created temporary directory: ${outputDir}`);
  } else {
    // Ensure output directory exists
    fs.mkdirSync(outputDir, { recursive: true });
    console.log(`Using provided directory: ${outputDir}`);
  }

  // Get binary path
  const binaryPath = await getBinaryPath();
  console.log(`Using binary at: ${binaryPath}`);

  // Process each URL
  const results = {};
  
  for (const url of urlList) {
    try {
      console.log(`Crawling ${url}...`);
      
      // Prepare command
      const command = `"${binaryPath}" -crawl -outdir "${outputDir}" "${url}"`;
      
      // Execute command
      const { error, stdout, stderr } = await execPromise(command);
      
      if (error) {
        console.error(`Error crawling ${url}: ${stderr}`);
        throw new Error(`Command failed: ${stderr}`);
      }
      
      // Find files for this URL
      const { htmlFile, mdFile } = findFilesForUrl(outputDir, url);
      
      results[url] = {
        html: htmlFile,
        markdown: mdFile
      };
      
      console.log(`Successfully crawled ${url}`);
    } catch (err) {
      console.error(`Failed to crawl ${url}: ${err.message}`);
      results[url] = {
        error: err.message
      };
    }
  }

  return results;
}

/**
 * Crawl a URL or list of URLs and upload to R2
 * 
 * @param {string|string[]} urls - URL or array of URLs to crawl
 * @param {Object} options - R2 crawl options
 * @param {string} [options.uuid=null] - UUID to prefix filenames (generates if null)
 * @returns {Promise<Object>} Result mapping URLs to R2 keys
 */
async function crawlToR2(urls, options = {}) {
  // Normalize inputs
  const urlList = Array.isArray(urls) ? urls : [urls];
  if (urlList.length === 0) {
    throw new Error('No URLs provided');
  }
  
  // Generate UUID if not provided
  const uuidStr = options.uuid || uuidv4();
  
  // Create temporary directory for files
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pathik-'));
  
  try {
    // First crawl URLs locally
    const crawlResults = await crawl(urlList, { outputDir: tempDir });
    
    // Get binary path
    const binaryPath = await getBinaryPath();
    
    // Process each URL for R2 upload
    const results = {};
    
    for (const url of urlList) {
      try {
        console.log(`Uploading ${url} to R2...`);
        
        // Prepare command
        const command = `"${binaryPath}" -r2 -uuid "${uuidStr}" -dir "${tempDir}" "${url}"`;
        
        // Execute command
        const { error, stdout, stderr } = await execPromise(command);
        
        if (error) {
          console.error(`Error uploading ${url}: ${stderr}`);
          throw new Error(`R2 upload failed: ${stderr}`);
        }
        
        // Add result
        results[url] = {
          uuid: uuidStr,
          r2_html_key: `${uuidStr}+${sanitizeUrl(url)}.html`,
          r2_markdown_key: `${uuidStr}+${sanitizeUrl(url)}.md`,
          local_html_file: crawlResults[url].html,
          local_markdown_file: crawlResults[url].markdown
        };
        
        console.log(`Successfully uploaded ${url} to R2`);
      } catch (err) {
        console.error(`Failed to upload ${url}: ${err.message}`);
        results[url] = {
          error: err.message
        };
      }
    }
    
    return results;
  } finally {
    // Keep temp directory for debugging
    console.log(`Temporary directory with files: ${tempDir}`);
  }
}

/**
 * Sanitize a URL for use in filenames
 * 
 * @param {string} url - URL to sanitize
 * @returns {string} Sanitized string
 */
function sanitizeUrl(url) {
  try {
    const parsedUrl = new URL(url);
    let result = parsedUrl.hostname + parsedUrl.pathname;
    
    // Replace unsafe characters
    return result.replace(/[/:?&=#]/g, '_');
  } catch (err) {
    // If parsing fails, just replace unsafe characters
    return url.replace(/[/:?&=#]/g, '_');
  }
}

/**
 * Find HTML and MD files for a given URL
 * 
 * @param {string} directory - Directory to search in
 * @param {string} url - URL to find files for
 * @returns {Object} Object with htmlFile and mdFile paths
 */
function findFilesForUrl(directory, url) {
  console.log(`Looking for files in ${directory} for URL ${url}`);
  
  // Check if directory exists
  if (!fs.existsSync(directory)) {
    console.warn(`Directory ${directory} does not exist!`);
    return { htmlFile: '', mdFile: '' };
  }
  
  // List directory contents for debugging
  console.log(`Directory contents: ${fs.readdirSync(directory).join(', ')}`);
  
  const domain = getDomainNameForFile(url);
  console.log(`Domain name for file: ${domain}`);
  
  let htmlFile = '';
  let mdFile = '';
  
  // Find matching files
  fs.readdirSync(directory).forEach(filename => {
    console.log(`Checking file: ${filename}`);
    
    const domainParts = domain.split('_');
    const baseDomain = domainParts[0];
    
    if (filename.startsWith(domain) || filename.startsWith(baseDomain.replace('.', '_'))) {
      if (filename.endsWith('.html')) {
        htmlFile = path.join(directory, filename);
        console.log(`Found HTML file: ${htmlFile}`);
      } else if (filename.endsWith('.md')) {
        mdFile = path.join(directory, filename);
        console.log(`Found MD file: ${mdFile}`);
      }
    }
  });
  
  return { htmlFile, mdFile };
}

/**
 * Generate a filename prefix from a URL
 * 
 * @param {string} url - URL to generate filename from
 * @returns {string} Formatted domain name for filename
 */
function getDomainNameForFile(url) {
  try {
    const parsedUrl = new URL(url);
    const domain = parsedUrl.hostname.replace(/\./g, '_');
    const path = parsedUrl.pathname.trim('/');
    
    if (!path) {
      return domain;
    }
    
    const formattedPath = path.replace(/\//g, '_');
    return `${domain}_${formattedPath}`;
  } catch (err) {
    return 'unknown';
  }
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
  crawl,
  crawlToR2
}; 