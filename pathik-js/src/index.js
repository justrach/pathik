/**
 * Pathik - High-Performance Web Crawler
 * JavaScript bindings for the Pathik Go crawler
 */

const crawler = require('./crawler');

/**
 * @module pathik
 */

/**
 * Crawl a URL or list of URLs and save the content locally
 *
 * @param {string|string[]} urls - URL or array of URLs to crawl
 * @param {Object} options - Crawling options
 * @param {string} [options.output] - Output directory
 * @param {boolean} [options.parallel=true] - Whether to use parallel crawling
 * @returns {Promise<Object>} - Object mapping URLs to file paths
 */
function crawl(urls, options = {}) {
  return crawler.crawl(urls, options);
}

/**
 * Crawl a URL or list of URLs and upload content to R2
 *
 * @param {string|string[]} urls - URL or array of URLs to crawl
 * @param {Object} options - Upload options
 * @param {string} [options.uuid] - UUID for the upload
 * @param {string} [options.output] - Output directory
 * @param {boolean} [options.parallel=true] - Whether to use parallel crawling
 * @returns {Promise<Object>} - Object mapping URLs to R2 keys
 */
function crawlToR2(urls, options = {}) {
  return crawler.crawlToR2(urls, options);
}

/**
 * Stream crawled content from a URL or list of URLs to Kafka
 * 
 * @param {string|string[]} urls - URL or array of URLs to crawl and stream
 * @param {Object} options - Kafka streaming options
 * @param {boolean} [options.parallel=true] - Whether to use parallel crawling
 * @param {string} [options.contentType='both'] - Content type to stream: 'html', 'markdown', or 'both'
 * @param {string} [options.topic=null] - Kafka topic to stream to (uses KAFKA_TOPIC env var if null)
 * @param {string} [options.session=null] - Session ID for multi-user environments
 * @returns {Promise<Object>} Result mapping URLs to streaming status
 */
function streamToKafka(urls, options = {}) {
  return crawler.streamToKafka(urls, options);
}

module.exports = {
  crawl,
  crawlToR2,
  streamToKafka
}; 