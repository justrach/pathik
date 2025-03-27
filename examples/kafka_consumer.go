package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	"github.com/segmentio/kafka-go"
	"github.com/segmentio/kafka-go/sasl/plain"
)

func main() {
	// Load .env file if it exists
	godotenv.Load()

	// Command line flags
	brokers := flag.String("brokers", getEnvWithDefault("KAFKA_BROKERS", "localhost:9092"), "Kafka brokers (comma-separated)")
	topic := flag.String("topic", getEnvWithDefault("KAFKA_TOPIC", "pathik_crawl_data"), "Kafka topic to consume from")
	username := flag.String("username", os.Getenv("KAFKA_USERNAME"), "SASL username")
	password := flag.String("password", os.Getenv("KAFKA_PASSWORD"), "SASL password")
	contentType := flag.String("type", "", "Filter by content type (html or markdown)")
	sessionID := flag.String("session", "", "Filter by session ID")
	flag.Parse()

	// Setup signal handling for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-signals
		fmt.Println("\nShutting down gracefully...")
		cancel()
	}()

	// Create Kafka reader
	brokerList := strings.Split(*brokers, ",")
	fmt.Printf("Connecting to Kafka brokers: %s\n", *brokers)
	fmt.Printf("Consuming from topic: %s\n", *topic)
	if *contentType != "" {
		fmt.Printf("Filtering for content type: %s\n", *contentType)
	}
	if *sessionID != "" {
		fmt.Printf("Filtering for session ID: %s\n", *sessionID)
	}

	// Configure reader
	readerConfig := kafka.ReaderConfig{
		Brokers:     brokerList,
		Topic:       *topic,
		MinBytes:    10e3, // 10KB
		MaxBytes:    10e6, // 10MB
		StartOffset: kafka.LastOffset,
		Logger:      kafka.LoggerFunc(logKafkaInfo),
		ErrorLogger: kafka.LoggerFunc(logKafkaError),
	}

	// Add SASL authentication if credentials provided
	if *username != "" && *password != "" {
		dialer := &kafka.Dialer{
			Timeout:   10 * time.Second,
			DualStack: true,
			SASLMechanism: plain.Mechanism{
				Username: *username,
				Password: *password,
			},
		}
		readerConfig.Dialer = dialer
		fmt.Println("Using SASL authentication")
	}

	reader := kafka.NewReader(readerConfig)
	defer reader.Close()

	fmt.Println("Consumer started. Press Ctrl+C to exit.")
	fmt.Println("-----------------------------------------")

	// Consume messages
	for {
		select {
		case <-ctx.Done():
			return
		default:
			m, err := reader.ReadMessage(ctx)
			if err != nil {
				if ctx.Err() != context.Canceled {
					log.Printf("Error reading message: %v", err)
				}
				continue
			}

			// Extract headers
			var msgURL, msgContentType, msgTimestamp, msgSessionID string
			for _, header := range m.Headers {
				switch header.Key {
				case "url":
					msgURL = string(header.Value)
				case "contentType":
					msgContentType = string(header.Value)
				case "timestamp":
					msgTimestamp = string(header.Value)
				case "sessionID":
					msgSessionID = string(header.Value)
				}
			}

			// Skip if content type filter is set and doesn't match
			if *contentType != "" && !strings.Contains(msgContentType, *contentType) {
				continue
			}

			// Skip if session ID filter is set and doesn't match
			if *sessionID != "" && msgSessionID != *sessionID {
				continue
			}

			// Display message
			fmt.Println("-----------------------------------------")
			fmt.Printf("Message received at partition %d, offset %d\n", m.Partition, m.Offset)
			fmt.Printf("Key: %s\n", string(m.Key))
			fmt.Printf("URL: %s\n", msgURL)
			fmt.Printf("Content Type: %s\n", msgContentType)
			fmt.Printf("Timestamp: %s\n", msgTimestamp)
			if msgSessionID != "" {
				fmt.Printf("Session ID: %s\n", msgSessionID)
			}

			// Print preview of the content (first 200 chars)
			content := string(m.Value)
			preview := content
			if len(content) > 200 {
				preview = content[:200] + "... [truncated]"
			}
			fmt.Printf("Content Preview (%d bytes total):\n%s\n", len(content), preview)
		}
	}
}

func getEnvWithDefault(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func logKafkaInfo(msg string, args ...interface{}) {
	// Uncomment to see verbose Kafka client logs
	// log.Printf("INFO: "+msg, args...)
}

func logKafkaError(msg string, args ...interface{}) {
	log.Printf("ERROR: "+msg, args...)
}
