package storage

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/joho/godotenv"
)

// R2Config holds the configuration for Cloudflare R2
type R2Config struct {
	AccountID       string
	AccessKeyID     string
	AccessKeySecret string
	BucketName      string
	Region          string
}

// LoadR2Config loads R2 configuration from environment variables
func LoadR2Config() (R2Config, error) {
	config := R2Config{
		AccountID:       os.Getenv("R2_ACCOUNT_ID"),
		AccessKeyID:     os.Getenv("R2_ACCESS_KEY_ID"),
		AccessKeySecret: os.Getenv("R2_ACCESS_KEY_SECRET"),
		BucketName:      os.Getenv("R2_BUCKET_NAME"),
		Region:          os.Getenv("R2_REGION"),
	}

	// Check if required values are set
	if config.AccountID == "" || config.AccessKeyID == "" ||
		config.AccessKeySecret == "" || config.BucketName == "" {
		return config, fmt.Errorf("missing required R2 configuration in environment variables")
	}

	// Set default region if not specified
	if config.Region == "" {
		config.Region = "auto" // R2 typically uses "auto" as region
	}

	return config, nil
}

// CreateS3Client creates an S3 client configured for Cloudflare R2
func CreateS3Client(cfg R2Config) (*s3.Client, error) {
	r2Resolver := aws.EndpointResolverWithOptionsFunc(func(service, region string, options ...interface{}) (aws.Endpoint, error) {
		return aws.Endpoint{
			URL: fmt.Sprintf("https://%s.r2.cloudflarestorage.com", cfg.AccountID),
		}, nil
	})

	awsCfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithEndpointResolverWithOptions(r2Resolver),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(
			cfg.AccessKeyID,
			cfg.AccessKeySecret,
			"",
		)),
		config.WithRegion(cfg.Region),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to load AWS config: %v", err)
	}

	return s3.NewFromConfig(awsCfg), nil
}

// SanitizeURL converts a URL to a safe filename component
func SanitizeURL(urlStr string) string {
	// Parse the URL
	parsedURL, err := url.Parse(urlStr)
	if err != nil {
		// If parsing fails, just replace unsafe characters
		return strings.ReplaceAll(urlStr, "/", "_")
	}

	// Combine host and path
	result := parsedURL.Host + parsedURL.Path

	// Remove protocol, query parameters, and fragments
	result = strings.ReplaceAll(result, ":", "_")
	result = strings.ReplaceAll(result, "/", "_")
	result = strings.ReplaceAll(result, "?", "_")
	result = strings.ReplaceAll(result, "&", "_")
	result = strings.ReplaceAll(result, "=", "_")
	result = strings.ReplaceAll(result, "#", "_")

	return result
}

// UploadFileToR2 uploads a file to R2 bucket
func UploadFileToR2(client *s3.Client, bucketName, filePath, uuid, originalURL, fileType string) error {
	// Read file content
	content, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("failed to read file %s: %v", filePath, err)
	}

	// Create key in format UUID+sanitizedURL.extension
	sanitizedURL := SanitizeURL(originalURL)
	key := fmt.Sprintf("%s+%s.%s", uuid, sanitizedURL, fileType)

	// Upload to R2
	_, err = client.PutObject(context.TODO(), &s3.PutObjectInput{
		Bucket:      aws.String(bucketName),
		Key:         aws.String(key),
		Body:        strings.NewReader(string(content)),
		ContentType: aws.String(getContentType(fileType)),
	})

	if err != nil {
		return fmt.Errorf("failed to upload %s to R2: %v", filePath, err)
	}

	fmt.Printf("Successfully uploaded %s to R2 as %s\n", filePath, key)
	return nil
}

// getContentType returns the MIME type based on file extension
func getContentType(fileType string) string {
	switch fileType {
	case "html":
		return "text/html"
	case "md":
		return "text/markdown"
	default:
		return "application/octet-stream"
	}
}

// FindFilesForURL finds HTML and MD files for a given URL
func FindFilesForURL(directory, urlStr string) (htmlFile, mdFile string, err error) {
	domain := GetDomainNameForFile(urlStr)

	files, err := ioutil.ReadDir(directory)
	if err != nil {
		return "", "", fmt.Errorf("failed to read directory %s: %v", directory, err)
	}

	for _, file := range files {
		if strings.HasPrefix(file.Name(), domain) {
			ext := filepath.Ext(file.Name())
			if ext == ".html" {
				htmlFile = filepath.Join(directory, file.Name())
			} else if ext == ".md" {
				mdFile = filepath.Join(directory, file.Name())
			}
		}
	}

	if htmlFile == "" && mdFile == "" {
		return "", "", fmt.Errorf("no files found for URL %s", urlStr)
	}

	return htmlFile, mdFile, nil
}

// GetDomainNameForFile generates a unique filename prefix from the URL
func GetDomainNameForFile(pageURL string) string {
	parsedURL, err := url.Parse(pageURL)
	if err != nil {
		log.Printf("Error parsing URL %s: %v", pageURL, err)
		return "unknown"
	}
	domain := strings.ReplaceAll(parsedURL.Hostname(), ".", "_")
	path := strings.Trim(parsedURL.Path, "/")
	if path == "" {
		return domain
	}
	path = strings.ReplaceAll(path, "/", "_")
	return fmt.Sprintf("%s_%s", domain, path)
}

// SaveToLocalFile saves content to a file with the appropriate extension
func SaveToLocalFile(content, url, fileType, outputDir string) (string, error) {
	domain := GetDomainNameForFile(url)
	date := time.Now().Format("2006-01-02")
	filename := fmt.Sprintf("%s_%s.%s", domain, date, fileType)

	// Use the specified output directory or current directory
	if outputDir != "" && outputDir != "." {
		// Create the directory if it doesn't exist
		if err := os.MkdirAll(outputDir, 0755); err != nil {
			return "", fmt.Errorf("failed to create directory %s: %v", outputDir, err)
		}
		filename = filepath.Join(outputDir, filename)
	}

	err := ioutil.WriteFile(filename, []byte(content), 0644)
	if err != nil {
		return "", fmt.Errorf("failed to save file %s: %v", filename, err)
	}
	fmt.Printf("✅ Saved to %s\n", filename)
	return filename, nil
}

// InitEnv loads environment variables from .env file
func InitEnv() error {
	return godotenv.Load()
}
