package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"pathik/crawler"
	"pathik/storage"

	"github.com/joho/godotenv"
)

// Version is set during build
var Version = "dev"

// validateURL validates that a URL is properly formatted and safe
func validateURL(url string) error {
	return crawler.ValidateURL(url)
}

// validateOutputDir ensures the output directory is safe
func validateOutputDir(dir string) error {
	// Check for directory traversal
	if strings.Contains(dir, "..") {
		return fmt.Errorf("directory traversal attempt detected: %s", dir)
	}

	// Convert to absolute path
	absPath, err := filepath.Abs(dir)
	if err != nil {
		return fmt.Errorf("invalid directory path: %v", err)
	}

	// Check if directory exists or create it
	fi, err := os.Stat(absPath)
	if os.IsNotExist(err) {
		// Try to create the directory
		err = os.MkdirAll(absPath, 0755)
		if err != nil {
			return fmt.Errorf("failed to create directory: %v", err)
		}
		return nil
	}

	// Check if it's a directory
	if err == nil && !fi.IsDir() {
		return fmt.Errorf("path exists but is not a directory: %s", absPath)
	}

	// Check write permissions by attempting to create and remove a temp file
	testFile := filepath.Join(absPath, ".pathik_test")
	f, err := os.Create(testFile)
	if err != nil {
		return fmt.Errorf("directory is not writable: %v", err)
	}
	f.Close()
	os.Remove(testFile)

	return nil
}

// validateSessionID validates the session ID format
func validateSessionID(session string) error {
	if session == "" {
		return nil
	}

	// Only allow alphanumeric and some special characters
	for _, c := range session {
		if !(c >= 'a' && c <= 'z') && !(c >= 'A' && c <= 'Z') && !(c >= '0' && c <= '9') &&
			c != '-' && c != '_' && c != '.' {
			return fmt.Errorf("invalid session ID format, only alphanumeric chars, dash, underscore and dot allowed")
		}
	}

	// Check length
	if len(session) > 64 {
		return fmt.Errorf("session ID too long (max 64 characters)")
	}

	return nil
}

func main() {
	// Load .env file if it exists
	godotenv.Load()

	// Parse command-line arguments
	versionFlag := flag.Bool("version", false, "Print version information")
	crawlFlag := flag.Bool("crawl", false, "Crawl URLs without uploading")
	parallelFlag := flag.Bool("parallel", true, "Use parallel crawling (default: true)")
	uuidFlag := flag.String("uuid", "", "UUID to prefix filenames for uploads")
	dirFlag := flag.String("dir", ".", "Directory containing files to upload")
	useR2Flag := flag.Bool("r2", false, "Upload files to Cloudflare R2 (requires uuid)")
	outDirFlag := flag.String("outdir", ".", "Directory to save crawled files")
	useKafkaFlag := flag.Bool("kafka", false, "Stream crawled content to Kafka")
	contentTypeFlag := flag.String("content", "both", "Content type to stream to Kafka: html, markdown, or both (default: both)")
	topicFlag := flag.String("topic", "", "Kafka topic to stream to (overrides KAFKA_TOPIC environment variable)")
	sessionFlag := flag.String("session", "", "Session ID to include with Kafka messages (for multi-user environments)")
	compressionFlag := flag.String("compression", "", "Compression algorithm to use for Kafka messages (gzip, snappy, lz4, zstd)")
	maxMessageSizeFlag := flag.Int("max-message-size", 0, "Maximum message size in bytes for Kafka")
	bufferMemoryFlag := flag.Int("buffer-memory", 0, "Buffer memory in bytes for Kafka producer")
	flag.Parse()

	// Print version if requested
	if *versionFlag {
		fmt.Printf("pathik version v%s\n", Version)
		return
	}

	// Validate session ID
	if *sessionFlag != "" {
		if err := validateSessionID(*sessionFlag); err != nil {
			log.Fatalf("Invalid session ID: %v", err)
		}
	}

	// Validate output directory
	if *outDirFlag != "." {
		if err := validateOutputDir(*outDirFlag); err != nil {
			log.Fatalf("Invalid output directory: %v", err)
		}
	}

	// Validate directory for uploads
	if *dirFlag != "." {
		if err := validateOutputDir(*dirFlag); err != nil {
			log.Fatalf("Invalid directory: %v", err)
		}
	}

	// Get URLs from remaining arguments
	urls := flag.Args()
	if len(urls) == 0 {
		log.Fatal("No URLs provided")
	}

	// Validate all URLs
	for _, url := range urls {
		if err := validateURL(url); err != nil {
			log.Fatalf("Invalid URL '%s': %v", url, err)
		}
	}

	// Validate content type
	if *contentTypeFlag != "both" && *contentTypeFlag != "html" && *contentTypeFlag != "markdown" {
		log.Fatalf("Invalid content type: %s (must be 'html', 'markdown', or 'both')", *contentTypeFlag)
	}

	// Kafka mode - crawl and stream to Kafka
	if *useKafkaFlag {
		streamToKafka(urls, *parallelFlag, *contentTypeFlag, *topicFlag, *sessionFlag, *compressionFlag, *maxMessageSizeFlag, *bufferMemoryFlag)
		return
	}

	// Just crawl URLs if -crawl flag is set
	if *crawlFlag {
		if *parallelFlag && len(urls) > 1 {
			// Use parallel crawling
			fmt.Printf("Crawling %d URLs in parallel...\n", len(urls))
			crawler.CrawlURLs(urls, *outDirFlag)
		} else {
			// Use sequential crawling
			for _, url := range urls {
				fmt.Printf("Crawling %s...\n", url)
				err := crawler.CrawlURL(url, "", nil, nil, *outDirFlag)
				if err != nil {
					log.Printf("Error crawling %s: %v", url, err)
				}
			}
			fmt.Println("Crawling complete!")
		}
		return
	}

	// If R2 upload is requested, UUID is required
	if *useR2Flag && *uuidFlag == "" {
		log.Fatal("UUID is required for R2 upload mode (-uuid flag)")
	}

	// Validate UUID format
	if *useR2Flag && *uuidFlag != "" {
		// Basic UUID validation
		if len(*uuidFlag) > 64 || strings.Contains(*uuidFlag, "/") || strings.Contains(*uuidFlag, "..") {
			log.Fatal("Invalid UUID format")
		}
	}

	// If R2 upload is requested, do the upload
	if *useR2Flag {
		// Load R2 configuration
		r2Config, err := storage.LoadR2Config()
		if err != nil {
			log.Fatalf("Failed to load R2 configuration: %v", err)
		}

		// Create S3 client for R2
		client, err := storage.CreateS3Client(r2Config)
		if err != nil {
			log.Fatalf("Failed to create S3 client: %v", err)
		}

		// Process each URL
		for _, url := range urls {
			// Look for files
			htmlFile, mdFile, err := storage.FindFilesForURL(*dirFlag, url)
			if err != nil {
				log.Printf("Warning: %v", err)
				continue
			}

			// Upload HTML file if found
			if htmlFile != "" {
				err = storage.UploadFileToR2(client, r2Config.BucketName, htmlFile, *uuidFlag, url, "html")
				if err != nil {
					log.Printf("Error uploading HTML file: %v", err)
				}
			}

			// Upload MD file if found
			if mdFile != "" {
				err = storage.UploadFileToR2(client, r2Config.BucketName, mdFile, *uuidFlag, url, "md")
				if err != nil {
					log.Printf("Error uploading MD file: %v", err)
				}
			}
		}

		fmt.Println("Upload process complete!")
	} else {
		fmt.Println("No action specified. Use -crawl to crawl URLs, -r2 to upload to R2, or -kafka to stream to Kafka.")
	}
}

func streamToKafka(urls []string, parallel bool, contentType string, topic string, session string, compression string, maxMessageSize int, bufferMemory int) {
	// Create a Kafka writer
	kafkaConfig, err := storage.LoadKafkaConfig()
	if err != nil {
		fmt.Printf("Error loading Kafka configuration: %v\n", err)
		return
	}

	// Override topic if specified on command line
	if topic != "" {
		kafkaConfig.Topic = topic
		fmt.Printf("Using command-line specified Kafka topic: %s\n", topic)
	}

	// Add compression options if provided
	if compression != "" {
		kafkaConfig.CompressionType = compression
		fmt.Printf("Using compression: %s\n", compression)
	}

	// Add message size if provided
	if maxMessageSize > 0 {
		kafkaConfig.MaxMessageSize = maxMessageSize
		fmt.Printf("Using max message size: %d bytes\n", maxMessageSize)
	}

	// Add buffer memory if provided
	if bufferMemory > 0 {
		kafkaConfig.BufferMemory = bufferMemory
		fmt.Printf("Using buffer memory: %d bytes\n", bufferMemory)
	}

	writer, err := storage.CreateKafkaWriter(kafkaConfig)
	if err != nil {
		fmt.Printf("Error creating Kafka writer: %v\n", err)
		return
	}
	defer storage.CloseKafkaWriter(writer)

	fmt.Printf("Streaming content to Kafka topic %s at %s\n",
		kafkaConfig.Topic, strings.Join(kafkaConfig.Brokers, ","))

	// Determine content types to stream
	var contentTypes []storage.ContentType
	switch contentType {
	case "html":
		contentTypes = []storage.ContentType{storage.HTMLContent}
		fmt.Println("Streaming HTML content only")
	case "markdown":
		contentTypes = []storage.ContentType{storage.MarkdownContent}
		fmt.Println("Streaming Markdown content only")
	default:
		// Empty slice means both will be streamed
		fmt.Println("Streaming both HTML and Markdown content")
	}

	if parallel && len(urls) > 1 {
		var wg sync.WaitGroup
		for _, url := range urls {
			wg.Add(1)
			go func(u string) {
				defer wg.Done()
				processURLForKafka(u, writer, contentTypes, session)
			}(url)
		}
		wg.Wait()
	} else {
		for _, url := range urls {
			processURLForKafka(url, writer, contentTypes, session)
		}
	}

	fmt.Println("Completed streaming to Kafka")
}

func processURLForKafka(url string, writer interface{}, contentTypes []storage.ContentType, session string) {
	fmt.Printf("Streaming content from %s to Kafka\n", url)

	// Fetch the page
	htmlContent, err := crawler.FetchPage(url, "")
	if err != nil {
		fmt.Printf("Error fetching %s: %v\n", url, err)
		return
	}

	// Extract HTML content
	extractedHTML, err := crawler.ExtractHTMLContent(htmlContent, url)
	if err != nil {
		fmt.Printf("Error extracting content from %s: %v\n", url, err)
		return
	}

	// Convert to markdown
	markdown, err := crawler.ConvertToMarkdown(extractedHTML)
	if err != nil {
		fmt.Printf("Error converting to Markdown: %v\n", err)
		return
	}

	// Stream to Kafka with specified content types
	err = storage.StreamToKafka(writer, url, htmlContent, markdown, session, contentTypes...)
	if err != nil {
		fmt.Printf("Error streaming content to Kafka for %s: %v\n", url, err)
		return
	}

	fmt.Printf("Successfully streamed content from %s to Kafka\n", url)
}
