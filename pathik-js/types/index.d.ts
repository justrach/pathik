/**
 * Type definitions for pathik package
 */

declare module 'pathik' {
  /**
   * Result object for crawled URL
   */
  export interface CrawlResult {
    html: string;
    markdown: string;
    error?: string;
  }

  /**
   * Result object for R2 upload
   */
  export interface R2UploadResult {
    uuid: string;
    r2_html_key: string;
    r2_markdown_key: string;
    local_html_file: string;
    local_markdown_file: string;
    error?: string;
  }

  /**
   * Result object for Kafka streaming operation
   */
  export interface KafkaStreamResult {
    success: boolean;
    error?: string;
  }

  /**
   * Options for crawl function
   */
  export interface CrawlOptions {
    outputDir?: string;
    parallel?: boolean;
  }

  /**
   * Options for crawlToR2 function
   */
  export interface R2Options {
    uuid?: string;
    outputDir?: string;
    parallel?: boolean;
  }

  /**
   * Options for streamToKafka function
   */
  export interface KafkaOptions {
    parallel?: boolean;
    contentType?: 'html' | 'markdown' | 'both';
    topic?: string;
    session?: string;
  }

  /**
   * Crawl a URL or list of URLs and save the content locally
   * 
   * @param urls - A single URL or array of URLs to crawl
   * @param options - Crawl options
   * @returns Promise resolving to an object mapping URLs to file paths
   */
  export function crawl(
    urls: string | string[],
    options?: CrawlOptions
  ): Promise<Record<string, CrawlResult>>;

  /**
   * Crawl a URL or list of URLs and upload the content to R2
   * 
   * @param urls - A single URL or array of URLs to crawl 
   * @param options - R2 crawl options
   * @returns Promise resolving to an object mapping URLs to R2 keys
   */
  export function crawlToR2(
    urls: string | string[],
    options?: R2Options
  ): Promise<Record<string, R2UploadResult>>;

  /**
   * Stream crawled content from a URL or list of URLs to Kafka
   * 
   * @param urls - A single URL or array of URLs to crawl and stream
   * @param options - Kafka streaming options
   * @returns Promise resolving to an object mapping URLs to streaming status
   */
  export function streamToKafka(
    urls: string | string[],
    options?: KafkaOptions
  ): Promise<Record<string, KafkaStreamResult>>;
} 