package crawler

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"math/rand"
	"net"
	"net/url"
	"os"
	"pathik/storage"
	"strings"
	"sync"
	"time"

	md "github.com/JohannesKaufmann/html-to-markdown"
	"github.com/go-rod/rod"
	"github.com/go-shiori/go-readability"
	"golang.org/x/time/rate"
)

// Configuration parameters
var (
	// Rate limiter to prevent DOS attacks - default 1 request per second
	rateLimiter = rate.NewLimiter(rate.Limit(1), 3) // 1 req/sec with burst of 3

	userAgents = []string{ // User-agents for rotation
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
	}
	maxRetries            = 3                // Number of retries for failed fetches
	retryDelay            = 2 * time.Second  // Delay between retries
	maxConcurrent         = 5                // Max concurrent crawls
	minContentLength      = 5000             // Min HTML length to assume page is complete
	stabilityCheckTimeout = 3 * time.Second  // Timeout for dynamic content stability wait
	maxContentLength      = 20 * 1024 * 1024 // 20 MB max content size
)

// LoadProxies loads proxies from environment variables
func LoadProxies() []string {
	// Check environment variable for proxy list
	proxyEnv := strings.TrimSpace(os.Getenv("PATHIK_PROXIES"))
	if proxyEnv == "" {
		return []string{}
	}

	// Split by commas
	proxies := strings.Split(proxyEnv, ",")

	// Validate proxy URLs
	var validProxies []string
	for _, p := range proxies {
		if strings.HasPrefix(p, "ws://") || strings.HasPrefix(p, "wss://") {
			validProxies = append(validProxies, strings.TrimSpace(p))
		} else {
			log.Printf("Warning: Invalid proxy format for %s, must start with ws:// or wss://", p)
		}
	}

	return validProxies
}

// getRandomProxy returns a random proxy from the loaded list
func getRandomProxy() string {
	proxies := LoadProxies()
	if len(proxies) == 0 {
		return ""
	}
	return proxies[rand.Intn(len(proxies))]
}

// getRandomUserAgent returns a random user-agent from the list
func getRandomUserAgent() string {
	return userAgents[rand.Intn(len(userAgents))]
}

// isPrivateIP checks if an IP address is private
func isPrivateIP(ipStr string) bool {
	ip := net.ParseIP(ipStr)
	if ip == nil {
		return false
	}

	// Get the IPv4 representation
	ipv4 := ip.To4()
	if ipv4 == nil {
		// Not an IPv4 address
		return false
	}

	// Check for private IP ranges
	privateRanges := []struct {
		start net.IP
		end   net.IP
	}{
		{net.ParseIP("10.0.0.0").To4(), net.ParseIP("10.255.255.255").To4()},
		{net.ParseIP("172.16.0.0").To4(), net.ParseIP("172.31.255.255").To4()},
		{net.ParseIP("192.168.0.0").To4(), net.ParseIP("192.168.255.255").To4()},
		{net.ParseIP("127.0.0.0").To4(), net.ParseIP("127.255.255.255").To4()},
	}

	for _, r := range privateRanges {
		if r.start == nil || r.end == nil {
			continue
		}

		if ipv4[0] == r.start[0] &&
			ipv4[1] >= r.start[1] &&
			ipv4[1] <= r.end[1] {
			return true
		}
	}

	return false
}

// ValidateURL checks if a URL is safe to crawl
func ValidateURL(rawURL string) error {
	parsedURL, err := url.Parse(rawURL)
	if err != nil {
		return fmt.Errorf("invalid URL format: %v", err)
	}

	// Check for allowed schemes
	if parsedURL.Scheme != "http" && parsedURL.Scheme != "https" {
		return fmt.Errorf("only HTTP and HTTPS schemes are allowed")
	}

	// Some URLs might not need IP resolution (e.g., localhost)
	if parsedURL.Hostname() == "localhost" || parsedURL.Hostname() == "127.0.0.1" {
		return fmt.Errorf("localhost access is restricted for security")
	}

	// Resolve hostname to IP
	host := parsedURL.Hostname()
	ips, err := net.LookupIP(host)
	if err != nil {
		// If we can't resolve the hostname, allow it (might be temporary DNS issue)
		log.Printf("Warning: Could not resolve hostname %s: %v", host, err)
		return nil
	}

	// No IPs found
	if len(ips) == 0 {
		log.Printf("Warning: No IPs found for hostname %s", host)
		return nil
	}

	// Check if any of the IPs are private
	for _, ip := range ips {
		if isPrivateIP(ip.String()) {
			return fmt.Errorf("crawling private IP addresses is not allowed")
		}
	}

	return nil
}

// FetchPage retrieves HTML from a URL with retries and smart dynamic content handling
func FetchPage(url string, proxy string) (string, error) {
	// Validate URL before fetching
	if err := ValidateURL(url); err != nil {
		return "", err
	}

	// Apply rate limiting
	if err := rateLimiter.Wait(context.Background()); err != nil {
		return "", fmt.Errorf("rate limit error: %v", err)
	}

	for attempt := 0; attempt < maxRetries; attempt++ {
		browser := rod.New()
		if proxy != "" {
			browser = browser.ControlURL(proxy)
		}
		browser = browser.MustConnect()
		defer browser.MustClose()

		page := browser.MustPage(url)
		page.MustEval(`() => { navigator.userAgent = "` + getRandomUserAgent() + `" }`)
		page.MustWaitLoad() // Wait for initial page load

		// Get initial HTML
		html, err := page.HTML()
		if err != nil {
			log.Printf("Attempt %d failed to get HTML for %s: %v", attempt+1, url, err)
			time.Sleep(retryDelay)
			continue
		}

		// Check content length limit
		if len(html) > maxContentLength {
			log.Printf("Content length exceeds limit (%d > %d bytes), truncating",
				len(html), maxContentLength)
			html = html[:maxContentLength]
		}

		// If HTML is long enough, assume it's complete and return
		if len(html) >= minContentLength {
			return html, nil
		}

		// HTML is short; wait for dynamic content
		err = page.WaitStable(stabilityCheckTimeout)
		if err != nil {
			log.Printf("Stability timeout for %s after %v; using current HTML", url, stabilityCheckTimeout)
		}

		// Get final HTML after stability check
		html, err = page.HTML()
		if err == nil {
			// Check content length limit again
			if len(html) > maxContentLength {
				log.Printf("Content length exceeds limit (%d > %d bytes), truncating",
					len(html), maxContentLength)
				html = html[:maxContentLength]
			}
			return html, nil
		}
		log.Printf("Attempt %d failed for %s: %v", attempt+1, url, err)
		time.Sleep(retryDelay)
	}
	return "", fmt.Errorf("failed to fetch %s after %d attempts", url, maxRetries)
}

// ExtractHTMLContent extracts main content HTML using Readability
func ExtractHTMLContent(htmlStr, urlStr string) (string, error) {
	parsedURL, err := url.Parse(urlStr)
	if err != nil {
		return "", fmt.Errorf("failed to parse URL %s: %v", urlStr, err)
	}
	article, err := readability.FromReader(strings.NewReader(htmlStr), parsedURL)
	if err != nil {
		return "", fmt.Errorf("failed to extract content from %s: %v", urlStr, err)
	}
	return article.Content, nil
}

// ConvertToMarkdown converts HTML content to Markdown
func ConvertToMarkdown(htmlStr string) (string, error) {
	converter := md.NewConverter("", true, nil)
	markdown, err := converter.ConvertString(htmlStr)
	if err != nil {
		return "", fmt.Errorf("failed to convert HTML to Markdown: %v", err)
	}
	return markdown, nil
}

// GetDomainName generates a unique filename from the URL
func GetDomainName(pageURL string) string {
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

// saveToMarkdownFile saves content to a Markdown file
func saveToMarkdownFile(content, url string) error {
	domain := GetDomainName(url)
	date := time.Now().Format("2006-01-02")
	filename := fmt.Sprintf("%s_%s.md", domain, date)

	err := ioutil.WriteFile(filename, []byte(content), 0644)
	if err != nil {
		return fmt.Errorf("failed to save file %s: %v", filename, err)
	}
	fmt.Printf("✅ Saved to %s\n", filename)
	return nil
}

// saveToHTMLFile saves raw HTML content to a file
func saveToHTMLFile(content, url string) error {
	domain := GetDomainName(url)
	date := time.Now().Format("2006-01-02")
	filename := fmt.Sprintf("%s_%s.html", domain, date)

	err := ioutil.WriteFile(filename, []byte(content), 0644)
	if err != nil {
		return fmt.Errorf("failed to save HTML file %s: %v", filename, err)
	}
	fmt.Printf("✅ Saved raw HTML to %s\n", filename)
	return nil
}

// CrawlURL processes a single URL
func CrawlURL(url string, proxy string, sem chan struct{}, wg *sync.WaitGroup, outputDir string) error {
	// Handle semaphore and waitgroup if provided
	if sem != nil && wg != nil {
		defer func() {
			<-sem
			wg.Done()
		}()
	}

	if proxy == "" {
		fmt.Printf("Fetching %s without proxy...\n", url)
	} else {
		fmt.Printf("Fetching %s with proxy %s...\n", url, proxy)
	}

	// Fetch page content
	html, err := FetchPage(url, proxy)
	if err != nil {
		log.Printf("Error fetching %s: %v", url, err)
		return err
	}

	// Save raw HTML
	_, err = storage.SaveToLocalFile(html, url, "html", outputDir)
	if err != nil {
		log.Printf("Error saving raw HTML for %s: %v", url, err)
		return err
	}

	// Extract main content
	contentHTML, err := ExtractHTMLContent(html, url)
	if err != nil {
		log.Printf("Error extracting content from %s: %v", url, err)
		return err
	}

	// Convert to Markdown
	markdown, err := ConvertToMarkdown(contentHTML)
	if err != nil {
		log.Printf("Error converting %s to Markdown: %v", url, err)
		return err
	}

	// Save to file
	_, err = storage.SaveToLocalFile(markdown, url, "md", outputDir)
	if err != nil {
		log.Printf("Error saving %s: %v", url, err)
		return err
	}

	return nil
}

// CrawlURLs crawls multiple URLs concurrently
func CrawlURLs(urls []string, outputDir string) {
	sem := make(chan struct{}, maxConcurrent)
	var wg sync.WaitGroup

	for _, url := range urls {
		wg.Add(1)
		sem <- struct{}{} // Acquire semaphore
		go CrawlURL(url, getRandomProxy(), sem, &wg, outputDir)
	}

	wg.Wait()
	fmt.Println("Crawling complete!")
}
