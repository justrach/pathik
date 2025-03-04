/**
 * Basic example of using Pathik
 */

const pathik = require('../src/index');
const path = require('path');
const fs = require('fs');

// Create output directory
const outputDir = path.resolve('./output_data');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}
console.log(`Output directory: ${outputDir}`);

// List of URLs to crawl
const urls = [
  'https://example.com',
  'https://news.ycombinator.com'
];

// Crawl the URLs
console.log(`Crawling ${urls.length} URLs...`);

pathik.crawl(urls, { outputDir })
  .then(results => {
    console.log('\nCrawling results:');
    
    for (const [url, files] of Object.entries(results)) {
      console.log(`\nURL: ${url}`);
      console.log(`HTML file: ${files.html}`);
      console.log(`Markdown file: ${files.markdown}`);
      
      // Print sample content from markdown file
      if (files.markdown && fs.existsSync(files.markdown)) {
        const content = fs.readFileSync(files.markdown, 'utf-8').slice(0, 500);
        console.log('\nSample markdown content:');
        console.log(`${content}...`);
      } else {
        console.log('WARNING: Markdown file not found or empty!');
      }
    }
  })
  .catch(error => {
    console.error(`Error during crawling: ${error.message}`);
  }); 