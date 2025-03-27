# Pathik Examples

This directory contains example code to demonstrate how to use Pathik.

## Kafka Consumer Examples

These examples show how to consume data that Pathik has streamed to Kafka.

### Prerequisites

To run the Kafka examples, you'll need:

1. A running Kafka broker (see setup options below)
2. Data streamed to Kafka using Pathik's Kafka feature

### Go Example

#### Requirements

```bash
# Install dependencies
go get github.com/segmentio/kafka-go
go get github.com/joho/godotenv
```

#### Usage

```bash
# Run with default settings (localhost:9092, topic: pathik_crawl_data)
go run kafka_consumer.go

# Specify brokers and topic
go run kafka_consumer.go --brokers=localhost:9092 --topic=my-topic

# Filter by content type
go run kafka_consumer.go --type=html
go run kafka_consumer.go --type=markdown

# With authentication
go run kafka_consumer.go --username=user --password=pass
```

### Python Example

#### Requirements

```bash
# Install dependencies
pip install kafka-python python-dotenv
```

#### Usage

```bash
# Run with default settings (localhost:9092, topic: pathik_crawl_data)
python kafka_consumer.py

# Specify brokers and topic
python kafka_consumer.py --brokers=localhost:9092 --topic=my-topic

# Filter by content type
python kafka_consumer.py --type=html
python kafka_consumer.py --type=markdown

# Filter by session ID (useful for multi-user environments)
python kafka_consumer.py --session=user123

# Combine filters
python kafka_consumer.py --type=html --session=user123

# Consume from the beginning of the topic
python kafka_consumer.py --from-beginning

# With authentication
python kafka_consumer.py --username=user --password=pass
```

## Setting Up Kafka for Local Development

There are several ways to run Kafka locally:

### Option 1: Using Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

Then start the containers:

```bash
docker-compose up -d
```

### Option 2: Using Redpanda

[Redpanda](https://redpanda.com/) is a Kafka API-compatible streaming platform that's easier to set up.

```bash
docker run -d --name=redpanda --net=host \
  -e REDPANDA_RPC_SERVER_LISTEN_ADDR=0.0.0.0 \
  -e REDPANDA_ADVERTISED_KAFKA_ADDR=127.0.0.1:9092 \
  -e REDPANDA_SEED_SERVERS='[]' \
  docker.redpanda.com/vectorized/redpanda:latest
```

### Option 3: Kafka on Kubernetes with Strimzi

If you're using Kubernetes (e.g., with minikube, kind, or k3s), you can use [Strimzi](https://strimzi.io/):

```bash
# Install Strimzi operator
kubectl create namespace kafka
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka'

# Deploy a Kafka cluster
kubectl apply -f https://strimzi.io/examples/latest/kafka/kafka-persistent-single.yaml -n kafka
```

## Workflow Example

1. Start Kafka locally:
   ```bash
   docker-compose up -d
   ```

2. Stream content to Kafka using Pathik:
   ```bash
   ./pathik -kafka https://example.com
   ```

3. Consume the streamed data:
   ```bash
   go run kafka_consumer.go
   # or
   python kafka_consumer.py
   ```

### Crawling Multiple URLs in Parallel

Pathik uses parallel crawling by default when multiple URLs are provided:

```bash
# Crawling multiple sites in parallel (default behavior)
pathik kafka https://example.com https://huewheel.com https://ycombinator.com

# For Go binary direct usage:
# Explicitly enable parallel crawling (redundant, as it's on by default)
./pathik -kafka -parallel https://example.com https://huewheel.com https://ycombinator.com

# Disable parallel crawling in Go binary
./pathik -kafka -parallel=false https://example.com https://huewheel.com https://ycombinator.com

# For Python CLI:
# Disable parallel crawling with -s/--sequential flag
pathik kafka -s https://example.com https://huewheel.com https://ycombinator.com
```