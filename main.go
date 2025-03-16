package main

import (
	"flag"
	"fmt"
	"log"

	"pathik/crawler"
	"pathik/storage"
)

func main() {
	// Parse command-line arguments
	crawlFlag := flag.Bool("crawl", false, "Crawl URLs without uploading")
	parallelFlag := flag.Bool("parallel", true, "Use parallel crawling (default: true)")
	uuidFlag := flag.String("uuid", "", "UUID to prefix filenames for uploads")
	dirFlag := flag.String("dir", ".", "Directory containing files to upload")
	useR2Flag := flag.Bool("r2", false, "Upload files to Cloudflare R2 (requires uuid)")
	outDirFlag := flag.String("outdir", ".", "Directory to save crawled files")
	flag.Parse()

	// Get URLs from remaining arguments
	urls := flag.Args()
	if len(urls) == 0 {
		log.Fatal("No URLs provided")
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
		fmt.Println("No action specified. Use -crawl to crawl URLs or -r2 to upload to R2.")
	}
}
