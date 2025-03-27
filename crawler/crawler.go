package crawler

import (
	"fmt"
	"io/ioutil"
	"log"
	"math/rand"
	"net/url"
	"pathik/storage"
	"strings"
	"sync"
	"time"

	md "github.com/JohannesKaufmann/html-to-markdown"
	"github.com/go-rod/rod"
	"github.com/go-shiori/go-readability"
)

// Configuration parameters
var (
	proxies = []string{ // Proxy URLs for rotation (leave empty for no proxies)
		"ws://proxy1:9222",
		"ws://proxy2:9222",
		"ws://proxy3:9222",
	}
	useProxies = false     // Enable/disable proxy rotation
	userAgents = []string{ // User-agents for rotation
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
	}
	maxRetries            = 3               // Number of retries for failed fetches
	retryDelay            = 2 * time.Second // Delay between retries
	maxConcurrent         = 5               // Max concurrent crawls
	minContentLength      = 5000            // Min HTML length to assume page is complete
	stabilityCheckTimeout = 3 * time.Second // Timeout for dynamic content stability wait
)

// getRandomProxy returns a random proxy from the list or empty string if disabled
func getRandomProxy() string {
	if !useProxies || len(proxies) == 0 {
		return ""
	}
	return proxies[rand.Intn(len(proxies))]
}

// getRandomUserAgent returns a random user-agent from the list
func getRandomUserAgent() string {
	return userAgents[rand.Intn(len(userAgents))]
}

// fetchPage retrieves HTML from a URL with retries and smart dynamic content handling
func fetchPage(url string, proxy string) (string, error) {
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
			return html, nil
		}
		log.Printf("Attempt %d failed for %s: %v", attempt+1, url, err)
		time.Sleep(retryDelay)
	}
	return "", fmt.Errorf("failed to fetch %s after %d attempts", url, maxRetries)
}

// extractHTMLContent extracts main content HTML using Readability
func extractHTMLContent(htmlStr, urlStr string) (string, error) {
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

// convertToMarkdown converts HTML content to Markdown
func convertToMarkdown(htmlStr string) (string, error) {
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
	html, err := fetchPage(url, proxy)
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
	contentHTML, err := extractHTMLContent(html, url)
	if err != nil {
		log.Printf("Error extracting content from %s: %v", url, err)
		return err
	}

	// Convert to Markdown
	markdown, err := convertToMarkdown(contentHTML)
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

// Export fetchPage as FetchPage for use by other packages
func FetchPage(url string, proxy string) (string, error) {
	return fetchPage(url, proxy)
}

// Export extractHTMLContent as ExtractHTMLContent for use by other packages
func ExtractHTMLContent(htmlStr, urlStr string) (string, error) {
	return extractHTMLContent(htmlStr, urlStr)
}

// Export convertToMarkdown as ConvertToMarkdown for use by other packages
func ConvertToMarkdown(htmlStr string) (string, error) {
	return convertToMarkdown(htmlStr)
}
