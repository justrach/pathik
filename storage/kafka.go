package storage

import (
	"context"
	"crypto/tls"
	"errors"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/segmentio/kafka-go"
	"github.com/segmentio/kafka-go/sasl/plain"
)

// KafkaConfig holds configuration for Kafka
type KafkaConfig struct {
	Brokers  []string
	Topic    string
	Username string
	Password string
	ClientID string
	UseTLS   bool
	MaxRetry int
}

// LoadKafkaConfig loads Kafka configuration from environment variables
func LoadKafkaConfig() (KafkaConfig, error) {
	brokersStr := os.Getenv("KAFKA_BROKERS")
	if brokersStr == "" {
		brokersStr = "localhost:9092" // Default broker
	}

	topic := os.Getenv("KAFKA_TOPIC")
	if topic == "" {
		topic = "pathik_crawl_data" // Default topic
	}

	maxRetryStr := os.Getenv("KAFKA_MAX_RETRY")
	maxRetry := 3 // Default max retry
	if maxRetryStr != "" {
		var err error
		maxRetry, err = strconv.Atoi(maxRetryStr)
		if err != nil {
			return KafkaConfig{}, err
		}
	}

	useTLSStr := os.Getenv("KAFKA_USE_TLS")
	useTLS := false
	if useTLSStr != "" {
		var err error
		useTLS, err = strconv.ParseBool(useTLSStr)
		if err != nil {
			return KafkaConfig{}, err
		}
	}

	config := KafkaConfig{
		Brokers:  strings.Split(brokersStr, ","),
		Topic:    topic,
		Username: os.Getenv("KAFKA_USERNAME"),
		Password: os.Getenv("KAFKA_PASSWORD"),
		ClientID: os.Getenv("KAFKA_CLIENT_ID"),
		UseTLS:   useTLS,
		MaxRetry: maxRetry,
	}

	return config, nil
}

// CreateKafkaWriter creates a Kafka writer from the provided configuration
func CreateKafkaWriter(config KafkaConfig) (*kafka.Writer, error) {
	if len(config.Brokers) == 0 {
		return nil, errors.New("no Kafka brokers specified")
	}

	if config.Topic == "" {
		return nil, errors.New("no Kafka topic specified")
	}

	dialer := &kafka.Dialer{
		Timeout:   10 * time.Second,
		DualStack: true,
	}

	// Setup SASL authentication if username and password are provided
	if config.Username != "" && config.Password != "" {
		mechanism := plain.Mechanism{
			Username: config.Username,
			Password: config.Password,
		}
		dialer.SASLMechanism = mechanism
	}

	// Setup TLS if enabled
	if config.UseTLS {
		dialer.TLS = &tls.Config{
			MinVersion: tls.VersionTLS12,
		}
	}

	// Create the writer with custom buffer configurations
	writer := &kafka.Writer{
		Addr:         kafka.TCP(config.Brokers...),
		Topic:        config.Topic,
		Balancer:     &kafka.LeastBytes{},
		MaxAttempts:  config.MaxRetry,
		BatchSize:    1,                    // Default to sending immediately
		BatchTimeout: 1 * time.Millisecond, // Almost no delay
		RequiredAcks: kafka.RequireAll,     // Wait for all replicas
		Compression:  kafka.Gzip,           // Use Gzip instead of Snappy compression
		Transport: &kafka.Transport{
			SASL: dialer.SASLMechanism,
			TLS:  dialer.TLS,
		},
	}

	// Set client ID if provided
	if config.ClientID != "" {
		dialer.ClientID = config.ClientID
	}

	return writer, nil
}

// SendToKafka sends content to Kafka
func SendToKafka(writer *kafka.Writer, key string, value []byte, headers ...kafka.Header) error {
	// Add timestamp to headers
	timestamp := time.Now().UTC().Format(time.RFC3339)
	headers = append(headers, kafka.Header{
		Key:   "timestamp",
		Value: []byte(timestamp),
	})

	// Create message
	message := kafka.Message{
		Key:     []byte(key),
		Value:   value,
		Headers: headers,
		Time:    time.Now(),
	}

	// Write message with retry logic
	ctx := context.Background()
	err := writer.WriteMessages(ctx, message)
	if err != nil {
		return err
	}

	return nil
}

// ContentType represents the type of content to stream
type ContentType string

const (
	// HTMLContent is the HTML content type
	HTMLContent ContentType = "html"
	// MarkdownContent is the Markdown content type
	MarkdownContent ContentType = "markdown"
)

// StreamToKafka streams content to Kafka based on the specified content types
// If contentTypes is empty, both HTML and Markdown will be streamed
// If sessionID is provided, it will be included in message headers
func StreamToKafka(writer interface{}, url string, htmlContent string, markdownContent string, sessionID string, contentTypes ...ContentType) error {
	kafkaWriter, ok := writer.(*kafka.Writer)
	if !ok {
		return errors.New("invalid Kafka writer provided")
	}

	// If no content types specified, stream both
	if len(contentTypes) == 0 {
		contentTypes = []ContentType{HTMLContent, MarkdownContent}
	}

	// Create common headers
	headers := []kafka.Header{
		{Key: "url", Value: []byte(url)},
	}

	// Add session ID if provided
	if sessionID != "" {
		headers = append(headers, kafka.Header{
			Key:   "sessionID",
			Value: []byte(sessionID),
		})
	}

	// Check if HTML should be streamed
	if containsContentType(contentTypes, HTMLContent) {
		htmlHeaders := append(headers, kafka.Header{
			Key:   "contentType",
			Value: []byte("text/html"),
		})

		err := SendToKafka(
			kafkaWriter,
			url,
			[]byte(htmlContent),
			htmlHeaders...,
		)
		if err != nil {
			return err
		}
	}

	// Check if Markdown should be streamed
	if containsContentType(contentTypes, MarkdownContent) {
		markdownHeaders := append(headers, kafka.Header{
			Key:   "contentType",
			Value: []byte("text/markdown"),
		})

		err := SendToKafka(
			kafkaWriter,
			url,
			[]byte(markdownContent),
			markdownHeaders...,
		)
		if err != nil {
			return err
		}
	}

	return nil
}

// Helper function to check if a content type is in the list
func containsContentType(types []ContentType, target ContentType) bool {
	for _, t := range types {
		if t == target {
			return true
		}
	}
	return false
}

// CloseKafkaWriter safely closes the Kafka writer
func CloseKafkaWriter(writer interface{}) {
	if kafkaWriter, ok := writer.(*kafka.Writer); ok {
		kafkaWriter.Close()
	}
}
