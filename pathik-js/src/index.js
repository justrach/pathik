/**
 * Pathik - High-Performance Web Crawler
 * JavaScript bindings for the Pathik Go crawler
 */

const crawler = require('./crawler');

/**
 * Crawl a URL or list of URLs and save the content locally
 * 
 * @param {string|string[]} urls - A single URL or array of URLs to crawl
 * @param {Object} options - Crawl options
 * @param {string} [options.outputDir=null] - Directory to save output (uses temp dir if null)
 * @returns {Promise<Object>} Result mapping URLs to file paths
 */
function crawl(urls, options = {}) {
  return crawler.crawl(urls, options);
}

/**
 * Crawl a URL or list of URLs and upload the content to R2
 * 
 * @param {string|string[]} urls - A single URL or array of URLs to crawl 
 * @param {Object} options - R2 crawl options
 * @param {string} [options.uuid=null] - UUID to prefix filenames (generates random UUID if null)
 * @returns {Promise<Object>} Result mapping URLs to R2 keys
 */
function crawlToR2(urls, options = {}) {
  return crawler.crawlToR2(urls, options);
}

module.exports = {
  crawl,
  crawlToR2
}; 