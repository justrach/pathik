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
		// If parsing fails, sanitize the string more aggressively
		sanitized := strings.ReplaceAll(urlStr, "/", "_")
		sanitized = strings.ReplaceAll(sanitized, "\\", "_")
		sanitized = strings.ReplaceAll(sanitized, ":", "_")
		sanitized = strings.ReplaceAll(sanitized, "*", "_")
		sanitized = strings.ReplaceAll(sanitized, "?", "_")
		sanitized = strings.ReplaceAll(sanitized, "\"", "_")
		sanitized = strings.ReplaceAll(sanitized, "<", "_")
		sanitized = strings.ReplaceAll(sanitized, ">", "_")
		sanitized = strings.ReplaceAll(sanitized, "|", "_")
		return sanitized
	}

	// Combine host and path
	result := parsedURL.Host
	if parsedURL.Path != "" && parsedURL.Path != "/" {
		// Add path but remove leading/trailing slashes
		path := strings.Trim(parsedURL.Path, "/")
		result += "_" + path
	}

	// Remove unsafe characters
	unsafe := []string{":", "/", "\\", "?", "*", "\"", "<", ">", "|", " ", "\t", "\n", "\r", "&", "=", "+", "$", ",", ";", "^", "`", "{", "}", "[", "]", "(", ")", "#", "%"}
	for _, char := range unsafe {
		result = strings.ReplaceAll(result, char, "_")
	}

	// Ensure no directory traversal is possible
	result = strings.ReplaceAll(result, "..", "_")

	// Truncate if too long (max 200 chars for filename safety)
	if len(result) > 200 {
		result = result[:200]
	}

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
	// Check for directory traversal attempts
	if strings.Contains(outputDir, "..") {
		return "", fmt.Errorf("directory traversal attempt detected")
	}

	// Limit content size to prevent denial of service
	maxContentSize := 10 * 1024 * 1024 // 10 MB
	if len(content) > maxContentSize {
		content = content[:maxContentSize]
		log.Printf("Warning: Content for URL %s truncated to %d bytes", url, maxContentSize)
	}

	domain := GetDomainNameForFile(url)
	date := time.Now().Format("2006-01-02")

	// Ensure safe file type
	safeFileType := fileType
	if fileType != "html" && fileType != "md" {
		safeFileType = "txt" // Default to txt if type is unexpected
	}

	filename := fmt.Sprintf("%s_%s.%s", domain, date, safeFileType)

	// Use the specified output directory or current directory
	if outputDir != "" && outputDir != "." {
		// Validate output directory path
		absOutputDir, err := filepath.Abs(outputDir)
		if err != nil {
			return "", fmt.Errorf("invalid output directory path: %v", err)
		}

		// Create the directory if it doesn't exist
		if err := os.MkdirAll(absOutputDir, 0755); err != nil {
			return "", fmt.Errorf("failed to create directory %s: %v", absOutputDir, err)
		}

		filename = filepath.Join(absOutputDir, filename)
	}

	// Ensure the final path doesn't go outside the intended directory
	absFilename, err := filepath.Abs(filename)
	if err != nil {
		return "", fmt.Errorf("invalid file path: %v", err)
	}

	absOutputDir, err := filepath.Abs(outputDir)
	if err != nil {
		return "", fmt.Errorf("invalid output directory path: %v", err)
	}

	if !strings.HasPrefix(absFilename, absOutputDir) {
		return "", fmt.Errorf("path traversal attempt detected")
	}

	err = ioutil.WriteFile(filename, []byte(content), 0644)
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
