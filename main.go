package main

import (
	"flag"
	"fmt"
	"log"
	"strings"
	"sync"

	"pathik/crawler"
	"pathik/storage"

	"github.com/joho/godotenv"
)

// Version is set during build
var Version = "dev"

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
	flag.Parse()

	// Print version if requested
	if *versionFlag {
		fmt.Printf("pathik version v%s\n", Version)
		return
	}

	// Get URLs from remaining arguments
	urls := flag.Args()
	if len(urls) == 0 {
		log.Fatal("No URLs provided")
	}

	// Kafka mode - crawl and stream to Kafka
	if *useKafkaFlag {
		streamToKafka(urls, *parallelFlag, *contentTypeFlag, *topicFlag, *sessionFlag)
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

func streamToKafka(urls []string, parallel bool, contentType string, topic string, session string) {
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
