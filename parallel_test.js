const pathik = require('pathik');
const path = require('path');
const fs = require('fs');

async function main() {
  // Create output directories
  const baseDir = path.resolve('./output_test_js');
  const parallelDir = path.join(baseDir, 'parallel');
  const sequentialDir = path.join(baseDir, 'sequential');
  
  fs.mkdirSync(parallelDir, { recursive: true });
  fs.mkdirSync(sequentialDir, { recursive: true });
  
  // Test URLs - mix of different sites
  const urls = [
    'https://example.com',
    'https://httpbin.org/html',
    'https://jsonplaceholder.typicode.com',
    'https://books.toscrape.com',
    'https://quotes.toscrape.com'
  ];
  
  console.log(`Testing with ${urls.length} URLs...`);
  
  // Test parallel crawling
  console.log('\n=== PARALLEL CRAWLING ===');
  const parallelStart = Date.now();
  
  try {
    const parallelResults = await pathik.crawl(urls, { 
      outputDir: parallelDir,
      parallel: true
    });
    
    const parallelTime = (Date.now() - parallelStart) / 1000;
    console.log(`Parallel crawling completed in ${parallelTime.toFixed(2)} seconds`);
    
    // Print results summary
    for (const [url, info] of Object.entries(parallelResults)) {
      const status = info.html && info.markdown ? '✅ Success' : '❌ Failed';
      console.log(`  ${url}: ${status}`);
    }
    
    // Test sequential crawling
    console.log('\n=== SEQUENTIAL CRAWLING ===');
    const sequentialStart = Date.now();
    
    try {
      const sequentialResults = await pathik.crawl(urls, { 
        outputDir: sequentialDir,
        parallel: false
      });
      
      const sequentialTime = (Date.now() - sequentialStart) / 1000;
      console.log(`Sequential crawling completed in ${sequentialTime.toFixed(2)} seconds`);
      
      // Print results summary
      for (const [url, info] of Object.entries(sequentialResults)) {
        const status = info.html && info.markdown ? '✅ Success' : '❌ Failed';
        console.log(`  ${url}: ${status}`);
      }
      
      // Compare performance
      console.log('\n=== PERFORMANCE COMPARISON ===');
      if (parallelTime < sequentialTime) {
        const speedup = sequentialTime / parallelTime;
        console.log(`Parallel crawling was ${speedup.toFixed(2)}x faster than sequential crawling`);
      } else {
        console.log(`Warning: Parallel crawling was not faster in this test`);
      }
      
      console.log(`Parallel: ${parallelTime.toFixed(2)}s vs Sequential: ${sequentialTime.toFixed(2)}s`);
      console.log(`\nOutput files are located in: ${baseDir}`);
    } catch (error) {
      console.error(`Error during sequential crawling: ${error.message}`);
      process.exit(1);
    }
  } catch (error) {
    console.error(`Error during parallel crawling: ${error.message}`);
    process.exit(1);
  }
}

main().catch(console.error); 