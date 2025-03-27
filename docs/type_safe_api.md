## Kafka Streaming with Compression Options

The `safe_stream_to_kafka` function supports several compression options to optimize message size and network bandwidth when streaming content to Kafka:

```python
from pathik.safe_api import safe_stream_to_kafka, KafkaParams

# Create parameters with compression options
params = KafkaParams(
    brokers="localhost:9092",
    topic="my_crawl_data",
    content_type="both",
    session_id="compression-test",
    username="", password="",
    compression_type="gzip",  # Specify compression algorithm
    max_message_size=15728640,  # ~15MB max message size
    buffer_memory=157286400     # ~150MB buffer memory
)

# Stream with compression
result = safe_stream_to_kafka(["https://example.com"], params)
```

### Compression Options

The following compression options are available:

| Parameter | Type | Description | Default | Valid Values |
|-----------|------|-------------|---------|--------------|
| `compression_type` | string | Compression algorithm to use | "gzip" | "gzip", "snappy", "lz4", "zstd" |
| `max_message_size` | int | Maximum message size in bytes | 1048576 (1MB) | any positive integer |
| `buffer_memory` | int | Producer buffer memory in bytes | 0 (default) | any positive integer |

### Compression Algorithms

- **gzip**: Best compression ratio but slower; good for text content
- **snappy**: Moderate compression with good speed; balanced option
- **lz4**: Fast compression with moderate ratio; good for high throughput
- **zstd**: Excellent compression ratio with good speed; best overall choice if available

### Command Line Usage

```bash
# Stream with gzip compression and increased message size
pathik kafka -c both -t pathik_data --compression gzip --max-message-size 15728640 --buffer-memory 157286400 https://example.com
```

### Choosing Compression Options

1. For very large pages, increase `max_message_size` (default is 1MB)
2. For high throughput requirements, choose faster compression like `lz4` or `snappy`
3. If bandwidth is limited, increase compression and reduce message size
4. For optimal performance with good compression, use `zstd` if available

### Performance Tuning

The `buffer_memory` option controls the amount of memory used by the Kafka producer for buffering messages 
before sending them to the broker. A larger buffer can improve throughput when streaming many URLs.

```python
# High-performance configuration for large batch processing
params = KafkaParams(
    brokers="kafka1:9092,kafka2:9092",
    topic="bulk_crawl_data",
    compression_type="zstd",
    max_message_size=20971520,  # 20MB
    buffer_memory=314572800     # 300MB
)
```

For most use cases, the default values will be sufficient, but these options provide flexibility
for high-performance or constrained environments. 