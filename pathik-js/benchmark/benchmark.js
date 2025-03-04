/**
 * Benchmark comparing pathik vs Playwright for web crawling in JavaScript
 */

const pathik = require('../src/index');
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

// More reliable test websites
const TEST_SITES = [
    "https://example.com",                   // Simple static site
    "https://httpbin.org/html",              // Simple HTML test page
    "https://jsonplaceholder.typicode.com",  // Simple API test site
    "https://books.toscrape.com",            // Book catalog site for scraping tests
    "https://quotes.toscrape.com"            // Quotes site for scraping tests
];

// Constants
const TIMEOUT = 30000; // 30 seconds timeout for each crawl
const OUTPUT_DIR = path.join(__dirname, 'results');
const PATHIK_DIR = path.join(OUTPUT_DIR, 'pathik');
const PLAYWRIGHT_DIR = path.join(OUTPUT_DIR, 'playwright');

// Create output directories
fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.mkdirSync(PATHIK_DIR, { recursive: true });
fs.mkdirSync(PLAYWRIGHT_DIR, { recursive: true });

// Memory snapshot utility
function getMemoryUsage() {
    const used = process.memoryUsage();
    return used.rss / 1024 / 1024; // Convert to MB
}

/**
 * Crawl a URL using pathik and measure performance
 */
async function benchmarkPathik(url) {
    console.log(`\nBenchmarking pathik on ${url}...`);
    
    const initialMemory = getMemoryUsage();
    const startTime = Date.now();
    
    try {
        // Crawl with pathik with timeout
        const crawlPromise = pathik.crawl(url, { outputDir: PATHIK_DIR });
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Timeout after ${TIMEOUT/1000}s`)), TIMEOUT)
        );
        
        const results = await Promise.race([crawlPromise, timeoutPromise]);
        
        const endTime = Date.now();
        const peakMemory = getMemoryUsage() - initialMemory;
        
        // Get content size
        const filePath = results[url]?.markdown;
        const contentSize = (filePath && fs.existsSync(filePath)) ? fs.statSync(filePath).size / 1024 : 0;
        
        return {
            crawler: 'pathik',
            url,
            time: (endTime - startTime) / 1000, // in seconds
            memory: peakMemory,
            contentSize,
            success: filePath && fs.existsSync(filePath)
        };
    } catch (error) {
        console.error(`Error with pathik: ${error.message}`);
        return {
            crawler: 'pathik',
            url,
            time: (Date.now() - startTime) / 1000,
            memory: getMemoryUsage() - initialMemory,
            contentSize: 0,
            success: false,
            error: error.message
        };
    }
}

/**
 * Crawl a URL using Playwright and measure performance
 */
async function benchmarkPlaywright(url) {
    console.log(`\nBenchmarking Playwright on ${url}...`);
    
    const initialMemory = getMemoryUsage();
    const startTime = Date.now();
    let browser = null;
    
    try {
        // Launch browser
        browser = await chromium.launch();
        const context = await browser.newContext();
        const page = await context.newPage();
        
        // Set timeout for navigation
        page.setDefaultTimeout(TIMEOUT);
        
        // Navigate to URL - use 'domcontentloaded' instead of 'networkidle' for more reliable navigation
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: TIMEOUT });
        
        // Wait a bit for any dynamic content to load
        await page.waitForTimeout(1000);
        
        // Extract content
        const html = await page.content();
        
        // Get readable content similar to readability
        const mainContent = await page.evaluate(() => {
            // Simple content extraction - in production you'd use Readability
            const article = document.querySelector('article') || 
                           document.querySelector('main') || 
                           document.querySelector('.content') || 
                           document.body;
            return article.innerHTML;
        });
        
        // Save files
        const urlObj = new URL(url);
        const filename = urlObj.hostname.replace(/\./g, '_');
        const date = new Date().toISOString().slice(0, 10);
        
        const htmlPath = path.join(PLAYWRIGHT_DIR, `${filename}_${date}.html`);
        const contentPath = path.join(PLAYWRIGHT_DIR, `${filename}_${date}.txt`);
        
        fs.writeFileSync(htmlPath, html);
        fs.writeFileSync(contentPath, mainContent);
        
        const endTime = Date.now();
        const peakMemory = getMemoryUsage() - initialMemory;
        
        // Get content size
        const contentSize = fs.existsSync(contentPath) ? fs.statSync(contentPath).size / 1024 : 0;
        
        return {
            crawler: 'playwright',
            url,
            time: (endTime - startTime) / 1000, // in seconds
            memory: peakMemory,
            contentSize,
            success: true
        };
    } catch (error) {
        console.error(`Error with Playwright on ${url}: ${error.message}`);
        return {
            crawler: 'playwright',
            url,
            time: (Date.now() - startTime) / 1000,
            memory: getMemoryUsage() - initialMemory,
            contentSize: 0,
            success: false,
            error: error.message
        };
    } finally {
        // Ensure browser is closed
        if (browser) {
            await browser.close().catch(() => {});
        }
    }
}

/**
 * Benchmark a batch of URLs using pathik
 */
async function benchmarkPathikBatch(urls) {
    console.log(`\nBenchmarking pathik batch crawl of ${urls.length} URLs...`);
    
    const initialMemory = getMemoryUsage();
    const startTime = Date.now();
    const results = {};
    let successCount = 0;
    
    try {
        // Process URLs individually but in parallel - this better matches
        // how the Go code's CrawlURLs function works with concurrency
        const crawlPromises = urls.map(url => 
            pathik.crawl(url, { outputDir: PATHIK_DIR })
                .then(result => {
                    if (result[url]?.markdown) successCount++;
                    return result;
                })
                .catch(error => {
                    console.error(`Error crawling ${url}: ${error.message}`);
                    return { [url]: { error: error.message } };
                })
        );
        
        // Wait for all promises with a timeout
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Batch timeout after ${TIMEOUT/1000}s`)), TIMEOUT)
        );
        
        // Wait for all crawls to complete or timeout
        const batchResults = await Promise.race([
            Promise.all(crawlPromises),
            timeoutPromise
        ]);
        
        // Merge results
        batchResults.forEach(result => {
            Object.assign(results, result);
        });
    } catch (error) {
        console.error(`Error in pathik batch: ${error.message}`);
    }
    
    const endTime = Date.now();
    const peakMemory = getMemoryUsage() - initialMemory;
    const totalTime = (endTime - startTime) / 1000;
    
    return {
        crawler: 'pathik',
        totalTime,
        avgTimePerUrl: totalTime / urls.length,
        memory: peakMemory,
        memoryPerUrl: peakMemory / urls.length,
        successRate: (successCount / urls.length) * 100,
        throughput: successCount / totalTime,
        urlCount: urls.length,
        successCount
    };
}

/**
 * Benchmark a batch of URLs using Playwright with concurrency
 */
async function benchmarkPlaywrightBatch(urls, concurrency = 3) {
    console.log(`\nBenchmarking Playwright batch crawl of ${urls.length} URLs with concurrency ${concurrency}...`);
    
    const initialMemory = getMemoryUsage();
    const startTime = Date.now();
    let successCount = 0;
    
    try {
        // Process in batches with concurrency limit
        const batches = [];
        for (let i = 0; i < urls.length; i += concurrency) {
            batches.push(urls.slice(i, i + concurrency));
        }
        
        for (const batch of batches) {
            // Create a promise for each URL in the batch
            const batchPromises = batch.map(url => {
                return benchmarkPlaywright(url)
                    .then(result => {
                        if (result.success) successCount++;
                        return result;
                    })
                    .catch(error => {
                        console.error(`Unhandled error for ${url}: ${error.message}`);
                        return { success: false };
                    });
            });
            
            // Wait for all promises in this batch
            await Promise.all(batchPromises);
        }
    } catch (error) {
        console.error(`Error in Playwright batch: ${error.message}`);
    }
    
    const endTime = Date.now();
    const peakMemory = getMemoryUsage() - initialMemory;
    const totalTime = (endTime - startTime) / 1000;
    
    return {
        crawler: 'playwright',
        totalTime,
        avgTimePerUrl: totalTime / urls.length,
        memory: peakMemory,
        memoryPerUrl: peakMemory / urls.length,
        successRate: (successCount / urls.length) * 100,
        throughput: successCount / totalTime,
        urlCount: urls.length,
        successCount
    };
}

/**
 * Print benchmark results in a nice table
 */
function printResults(singleResults, batchResults) {
    console.log('\n===== SINGLE URL RESULTS =====');
    console.log('\nTime (seconds):');
    
    // Group by URL
    const siteResults = {};
    for (const result of singleResults) {
        if (!siteResults[result.url]) {
            siteResults[result.url] = {};
        }
        siteResults[result.url][result.crawler] = result;
    }
    
    // Print tables comparing each URL for both crawlers
    for (const [url, results] of Object.entries(siteResults)) {
        const pathikResult = results.pathik || {};
        const playwrightResult = results.playwright || {};
        
        console.log(`\n${url}:`);
        console.log('Metric           | Pathik    | Playwright | Difference');
        console.log('-----------------|-----------|------------|------------');
        console.log(`Time (s)         | ${pathikResult.time?.toFixed(2) || 'N/A'} | ${playwrightResult.time?.toFixed(2) || 'N/A'} | ${(pathikResult.time && playwrightResult.time) ? (playwrightResult.time - pathikResult.time).toFixed(2) : 'N/A'}`);
        console.log(`Memory (MB)      | ${pathikResult.memory?.toFixed(2) || 'N/A'} | ${playwrightResult.memory?.toFixed(2) || 'N/A'} | ${(pathikResult.memory && playwrightResult.memory) ? (playwrightResult.memory - pathikResult.memory).toFixed(2) : 'N/A'}`);
        console.log(`Content Size (KB)| ${pathikResult.contentSize?.toFixed(2) || 'N/A'} | ${playwrightResult.contentSize?.toFixed(2) || 'N/A'} | ${(pathikResult.contentSize && playwrightResult.contentSize) ? (playwrightResult.contentSize - pathikResult.contentSize).toFixed(2) : 'N/A'}`);
        console.log(`Success          | ${pathikResult.success ? '✓' : '✗'} | ${playwrightResult.success ? '✓' : '✗'} | `);
    }
    
    // Print batch results
    console.log('\n===== BATCH PROCESSING RESULTS =====');
    const pathikBatch = batchResults.find(r => r.crawler === 'pathik') || {};
    const playwrightBatch = batchResults.find(r => r.crawler === 'playwright') || {};
    
    console.log('\nBatch Crawling:');
    console.log('Metric            | Pathik    | Playwright | Difference');
    console.log('------------------|-----------|------------|------------');
    console.log(`Total Time (s)    | ${pathikBatch.totalTime?.toFixed(2) || 'N/A'} | ${playwrightBatch.totalTime?.toFixed(2) || 'N/A'} | ${(pathikBatch.totalTime && playwrightBatch.totalTime) ? (playwrightBatch.totalTime - pathikBatch.totalTime).toFixed(2) : 'N/A'}`);
    console.log(`Avg Time/URL (s)  | ${pathikBatch.avgTimePerUrl?.toFixed(2) || 'N/A'} | ${playwrightBatch.avgTimePerUrl?.toFixed(2) || 'N/A'} | ${(pathikBatch.avgTimePerUrl && playwrightBatch.avgTimePerUrl) ? (playwrightBatch.avgTimePerUrl - pathikBatch.avgTimePerUrl).toFixed(2) : 'N/A'}`);
    console.log(`Memory (MB)       | ${pathikBatch.memory?.toFixed(2) || 'N/A'} | ${playwrightBatch.memory?.toFixed(2) || 'N/A'} | ${(pathikBatch.memory && playwrightBatch.memory) ? (playwrightBatch.memory - pathikBatch.memory).toFixed(2) : 'N/A'}`);
    console.log(`Memory/URL (MB)   | ${pathikBatch.memoryPerUrl?.toFixed(2) || 'N/A'} | ${playwrightBatch.memoryPerUrl?.toFixed(2) || 'N/A'} | ${(pathikBatch.memoryPerUrl && playwrightBatch.memoryPerUrl) ? (playwrightBatch.memoryPerUrl - pathikBatch.memoryPerUrl).toFixed(2) : 'N/A'}`);
    console.log(`Success Rate      | ${(pathikBatch.successRate * 100)?.toFixed(1) || 'N/A'}% | ${(playwrightBatch.successRate * 100)?.toFixed(1) || 'N/A'}% | ${(pathikBatch.successRate && playwrightBatch.successRate) ? ((playwrightBatch.successRate - pathikBatch.successRate) * 100).toFixed(1) + '%' : 'N/A'}`);
    console.log(`Throughput (URL/s)| ${pathikBatch.throughput?.toFixed(2) || 'N/A'} | ${playwrightBatch.throughput?.toFixed(2) || 'N/A'} | ${(pathikBatch.throughput && playwrightBatch.throughput) ? (pathikBatch.throughput - playwrightBatch.throughput).toFixed(2) : 'N/A'}`);
}

/**
 * Generate an HTML report with benchmark results
 */
function generateHtmlReport(singleResults, batchResults) {
    const pathikSingle = singleResults.filter(r => r.crawler === 'pathik');
    const playwrightSingle = singleResults.filter(r => r.crawler === 'playwright');
    
    const urlLabels = [...new Set(singleResults.map(r => new URL(r.url).hostname))];
    const pathikTime = urlLabels.map(url => {
        const result = pathikSingle.find(r => new URL(r.url).hostname === url);
        return result?.time || 0;
    });
    const playwrightTime = urlLabels.map(url => {
        const result = playwrightSingle.find(r => new URL(r.url).hostname === url);
        return result?.time || 0;
    });
    
    const pathikMemory = urlLabels.map(url => {
        const result = pathikSingle.find(r => new URL(r.url).hostname === url);
        return result?.memory || 0;
    });
    const playwrightMemory = urlLabels.map(url => {
        const result = playwrightSingle.find(r => new URL(r.url).hostname === url);
        return result?.memory || 0;
    });
    
    // Batch data
    const pathikBatch = batchResults.find(r => r.crawler === 'pathik') || {};
    const playwrightBatch = batchResults.find(r => r.crawler === 'playwright') || {};
    
    const batchLabels = ['Total Time', 'Avg Time/URL', 'Memory/URL', 'Throughput'];
    const pathikBatchData = [
        pathikBatch.totalTime || 0,
        pathikBatch.avgTimePerUrl || 0,
        pathikBatch.memoryPerUrl || 0,
        pathikBatch.throughput || 0
    ];
    const playwrightBatchData = [
        playwrightBatch.totalTime || 0,
        playwrightBatch.avgTimePerUrl || 0,
        playwrightBatch.memoryPerUrl || 0,
        playwrightBatch.throughput || 0
    ];
    
    // Create report
    const reportPath = path.join(OUTPUT_DIR, 'benchmark_report.html');
    
    const html = `<!DOCTYPE html>
<html>
<head>
    <title>Pathik vs Playwright Benchmark</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .chart-container { display: flex; flex-wrap: wrap; justify-content: space-between; }
        .chart { width: 48%; margin-bottom: 30px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .winner { background-color: #d4edda; }
        .summary { margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pathik vs Playwright Benchmark Results</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>
                <strong>System:</strong> ${os.platform()} ${os.release()}<br>
                <strong>Node.js:</strong> ${process.version}<br>
                <strong>CPUs:</strong> ${os.cpus().length}<br>
                <strong>Memory:</strong> ${Math.round(os.totalmem() / (1024 * 1024 * 1024))}GB<br>
                <strong>Test Date:</strong> ${new Date().toISOString().slice(0, 10)}
            </p>
        </div>
        
        <h2>Single URL Performance</h2>
        <div class="chart-container">
            <div class="chart">
                <canvas id="timeChart"></canvas>
            </div>
            <div class="chart">
                <canvas id="memoryChart"></canvas>
            </div>
        </div>
        
        <h2>Batch Processing Performance</h2>
        <div class="chart">
            <canvas id="batchChart"></canvas>
        </div>
        
        <h2>Detailed Results</h2>
        <table>
            <tr>
                <th>URL</th>
                <th>Crawler</th>
                <th>Time (s)</th>
                <th>Memory (MB)</th>
                <th>Content Size (KB)</th>
                <th>Success</th>
            </tr>
            ${singleResults.map(r => `
                <tr>
                    <td>${r.url}</td>
                    <td>${r.crawler}</td>
                    <td>${r.time?.toFixed(2) || 'N/A'}</td>
                    <td>${r.memory?.toFixed(2) || 'N/A'}</td>
                    <td>${r.contentSize?.toFixed(2) || 'N/A'}</td>
                    <td>${r.success ? '✓' : '✗'}</td>
                </tr>
            `).join('')}
        </table>
        
        <h2>Batch Results</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Pathik</th>
                <th>Playwright</th>
                <th>Difference</th>
            </tr>
            <tr>
                <td>Total Time (s)</td>
                <td>${pathikBatch.totalTime?.toFixed(2) || 'N/A'}</td>
                <td>${playwrightBatch.totalTime?.toFixed(2) || 'N/A'}</td>
                <td>${(pathikBatch.totalTime && playwrightBatch.totalTime) ? (playwrightBatch.totalTime - pathikBatch.totalTime).toFixed(2) : 'N/A'}</td>
            </tr>
            <tr>
                <td>Avg Time/URL (s)</td>
                <td>${pathikBatch.avgTimePerUrl?.toFixed(2) || 'N/A'}</td>
                <td>${playwrightBatch.avgTimePerUrl?.toFixed(2) || 'N/A'}</td>
                <td>${(pathikBatch.avgTimePerUrl && playwrightBatch.avgTimePerUrl) ? (playwrightBatch.avgTimePerUrl - pathikBatch.avgTimePerUrl).toFixed(2) : 'N/A'}</td>
            </tr>
            <tr>
                <td>Memory (MB)</td>
                <td>${pathikBatch.memory?.toFixed(2) || 'N/A'}</td>
                <td>${playwrightBatch.memory?.toFixed(2) || 'N/A'}</td>
                <td>${(pathikBatch.memory && playwrightBatch.memory) ? (playwrightBatch.memory - pathikBatch.memory).toFixed(2) : 'N/A'}</td>
            </tr>
            <tr>
                <td>Memory/URL (MB)</td>
                <td>${pathikBatch.memoryPerUrl?.toFixed(2) || 'N/A'}</td>
                <td>${playwrightBatch.memoryPerUrl?.toFixed(2) || 'N/A'}</td>
                <td>${(pathikBatch.memoryPerUrl && playwrightBatch.memoryPerUrl) ? (playwrightBatch.memoryPerUrl - pathikBatch.memoryPerUrl).toFixed(2) : 'N/A'}</td>
            </tr>
            <tr>
                <td>Success Rate</td>
                <td>${(pathikBatch.successRate * 100)?.toFixed(1) || 'N/A'}%</td>
                <td>${(playwrightBatch.successRate * 100)?.toFixed(1) || 'N/A'}%</td>
                <td>${(pathikBatch.successRate && playwrightBatch.successRate) ? ((playwrightBatch.successRate - pathikBatch.successRate) * 100).toFixed(1) + '%' : 'N/A'}</td>
            </tr>
            <tr>
                <td>Throughput (URL/s)</td>
                <td>${pathikBatch.throughput?.toFixed(2) || 'N/A'}</td>
                <td>${playwrightBatch.throughput?.toFixed(2) || 'N/A'}</td>
                <td>${(pathikBatch.throughput && playwrightBatch.throughput) ? (pathikBatch.throughput - playwrightBatch.throughput).toFixed(2) : 'N/A'}</td>
            </tr>
        </table>
    </div>
    
    <script>
        // Time Chart
        const timeCtx = document.getElementById('timeChart').getContext('2d');
        new Chart(timeCtx, {
            type: 'bar',
            data: {
                labels: ${JSON.stringify(urlLabels)},
                datasets: [
                    {
                        label: 'Pathik Time (s)',
                        data: ${JSON.stringify(pathikTime)},
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Playwright Time (s)',
                        data: ${JSON.stringify(playwrightTime)},
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Time Comparison (lower is better)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Time (seconds)'
                        }
                    }
                }
            }
        });
        
        // Memory Chart
        const memoryCtx = document.getElementById('memoryChart').getContext('2d');
        new Chart(memoryCtx, {
            type: 'bar',
            data: {
                labels: ${JSON.stringify(urlLabels)},
                datasets: [
                    {
                        label: 'Pathik Memory (MB)',
                        data: ${JSON.stringify(pathikMemory)},
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Playwright Memory (MB)',
                        data: ${JSON.stringify(playwrightMemory)},
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Memory Usage Comparison (lower is better)'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Memory (MB)'
                        }
                    }
                }
            }
        });
        
        // Batch Chart
        const batchCtx = document.getElementById('batchChart').getContext('2d');
        new Chart(batchCtx, {
            type: 'bar',
            data: {
                labels: ${JSON.stringify(batchLabels)},
                datasets: [
                    {
                        label: 'Pathik',
                        data: ${JSON.stringify(pathikBatchData)},
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Playwright',
                        data: ${JSON.stringify(playwrightBatchData)},
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Batch Processing Performance'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>`;
    
    fs.writeFileSync(reportPath, html);
    console.log(`HTML report saved to ${reportPath}`);
    
    return reportPath;
}

/**
 * Save benchmark data to JSON file
 */
function saveBenchmarkData(singleResults, batchResults) {
    const data = {
        system: {
            platform: os.platform(),
            release: os.release(),
            node: process.version,
            cpus: os.cpus().length,
            memory: Math.round(os.totalmem() / (1024 * 1024 * 1024)),
            date: new Date().toISOString()
        },
        singleResults,
        batchResults
    };
    
    const jsonPath = path.join(OUTPUT_DIR, 'benchmark_data.json');
    fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2));
    console.log(`JSON data saved to ${jsonPath}`);
}

/**
 * Main benchmark function
 */
async function runBenchmark() {
    console.log('\n===== PATHIK vs PLAYWRIGHT BENCHMARK =====');
    console.log(`System: ${os.platform()} ${os.release()}`);
    console.log(`Node.js: ${process.version}`);
    console.log(`CPUs: ${os.cpus().length}`);
    console.log(`Memory: ${Math.round(os.totalmem() / (1024 * 1024 * 1024))}GB`);
    console.log('=========================================\n');
    
    // Install Playwright browsers if needed
    try {
        await execAsync('npx playwright install chromium --with-deps');
    } catch (error) {
        console.error('Error installing Playwright browser:', error);
        process.exit(1);
    }
    
    // Single URL benchmarks
    const singleResults = [];
    
    for (const url of TEST_SITES.slice(0, 3)) { // Test first 3 sites
        const pathikResult = await benchmarkPathik(url);
        singleResults.push(pathikResult);
        
        const playwrightResult = await benchmarkPlaywright(url);
        singleResults.push(playwrightResult);
    }
    
    // Batch benchmarks - test with batch of URLs
    const batchSize = Math.min(5, TEST_SITES.length);
    const batchUrls = TEST_SITES.slice(0, batchSize);
    
    const pathikBatchResult = await benchmarkPathikBatch(batchUrls);
    const playwrightBatchResult = await benchmarkPlaywrightBatch(batchUrls, 3); // concurrency of 3
    
    const batchResults = [pathikBatchResult, playwrightBatchResult];
    
    // Print results
    printResults(singleResults, batchResults);
    
    // Save results
    saveBenchmarkData(singleResults, batchResults);
    
    // Generate HTML report
    generateHtmlReport(singleResults, batchResults);
    
    console.log('\nBenchmark complete!');
}

// Run the benchmark
runBenchmark().catch(error => {
    console.error('Error running benchmark:', error);
    process.exit(1);
}); 