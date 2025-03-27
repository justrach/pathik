#!/usr/bin/env node
/**
 * Command-line interface for Pathik
 */

const { program } = require('commander');
const path = require('path');
const fs = require('fs');
const pathik = require('../src/index');

program
  .name('pathik')
  .description('High-performance web crawler implemented in Go')
  .version('0.3.0');

program
  .command('crawl')
  .description('Crawl URLs and save content locally')
  .argument('<urls...>', 'URLs to crawl')
  .option('-o, --output <dir>', 'Output directory', './output')
  .option('-p, --parallel', 'Use parallel crawling (default: true)')
  .option('--no-parallel', 'Disable parallel crawling')
  .action(async (urls, options) => {
    try {
      console.log(`Crawling ${urls.length} URLs to ${options.output}...`);
      
      // Ensure output directory exists
      fs.mkdirSync(options.output, { recursive: true });
      
      // Crawl URLs
      const results = await pathik.crawl(urls, { 
        outputDir: options.output,
        parallel: options.parallel !== false
      });
      
      // Print results
      console.log('\nCrawling results:');
      for (const [url, files] of Object.entries(results)) {
        console.log(`\nURL: ${url}`);
        
        if (files.error) {
          console.log(`Error: ${files.error}`);
          continue;
        }
        
        console.log(`HTML file: ${files.html || 'Not found'}`);
        console.log(`Markdown file: ${files.markdown || 'Not found'}`);
        
        // Print sample markdown content
        if (files.markdown && fs.existsSync(files.markdown)) {
          const content = fs.readFileSync(files.markdown, 'utf-8').slice(0, 500);
          console.log('\nSample markdown content:');
          console.log(`${content}...`);
        } else {
          console.log('WARNING: Markdown file not found or empty!');
        }
      }
    } catch (error) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
  });

program
  .command('r2')
  .description('Crawl URLs and upload content to R2')
  .argument('<urls...>', 'URLs to crawl')
  .option('-u, --uuid <uuid>', 'UUID for R2 upload')
  .option('-p, --parallel', 'Use parallel crawling (default: true)')
  .option('--no-parallel', 'Disable parallel crawling')
  .action(async (urls, options) => {
    try {
      console.log(`Crawling and uploading ${urls.length} URLs to R2...`);
      
      // Crawl and upload
      const results = await pathik.crawlToR2(urls, {
        uuid: options.uuid,
        parallel: options.parallel !== false
      });
      
      // Print results
      console.log('\nR2 Upload results:');
      for (const [url, info] of Object.entries(results)) {
        console.log(`\nURL: ${url}`);
        
        if (info.error) {
          console.log(`Error: ${info.error}`);
          continue;
        }
        
        console.log(`UUID: ${info.uuid}`);
        console.log(`R2 HTML key: ${info.r2_html_key}`);
        console.log(`R2 Markdown key: ${info.r2_markdown_key}`);
        console.log(`Local HTML file: ${info.local_html_file || 'Not found'}`);
        console.log(`Local Markdown file: ${info.local_markdown_file || 'Not found'}`);
      }
    } catch (error) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
  });

program
  .command('kafka')
  .description('Crawl URLs and stream content to Kafka')
  .argument('<urls...>', 'URLs to crawl and stream')
  .option('-c, --content <type>', 'Content type to stream: html, markdown, or both', 'both')
  .option('-t, --topic <topic>', 'Kafka topic to stream to')
  .option('-s, --session <id>', 'Session ID for multi-user environments')
  .option('-p, --parallel', 'Use parallel crawling (default: true)')
  .option('--no-parallel', 'Disable parallel crawling')
  .action(async (urls, options) => {
    try {
      // Validate content type
      if (!['html', 'markdown', 'both'].includes(options.content)) {
        console.error('Error: Content type must be "html", "markdown", or "both"');
        process.exit(1);
      }
      
      console.log(`Streaming ${urls.length} URLs to Kafka...`);
      console.log(`Content type: ${options.content}`);
      
      if (options.topic) {
        console.log(`Topic: ${options.topic}`);
      }
      
      if (options.session) {
        console.log(`Session ID: ${options.session}`);
      }
      
      // Stream to Kafka
      const results = await pathik.streamToKafka(urls, {
        contentType: options.content,
        topic: options.topic,
        session: options.session,
        parallel: options.parallel !== false
      });
      
      // Print results
      console.log('\nKafka streaming results:');
      let successCount = 0;
      let failCount = 0;
      
      for (const [url, result] of Object.entries(results)) {
        if (result.success) {
          console.log(`✓ ${url}: Successfully streamed to Kafka`);
          successCount++;
        } else {
          console.log(`✗ ${url}: Failed to stream to Kafka - ${result.error}`);
          failCount++;
        }
      }
      
      console.log(`\nSummary: ${successCount} succeeded, ${failCount} failed`);
      
      if (options.session) {
        console.log(`\nTo consume these messages, filter by session ID: ${options.session}`);
      }
    } catch (error) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
  });

program.parse(); 