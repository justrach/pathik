# Changelog

All notable changes to Pathik will be documented in this file.

## [0.3.1] - 2023-10-28

### Added
- New example scripts for Kafka streaming: `native_kafka_demo.py` and `safe_kafka_demo.py`
- Improved documentation for Kafka integration
- Added more compression options (gzip, snappy, lz4, zstd) for Kafka streaming
- Added max message size and buffer memory controls for Kafka performance tuning

### Changed
- Fixed command line flags to align with Go binary expectations
- Corrected argument ordering for Kafka flags
- Simplified Kafka streaming interface in `__init__.py`
- Updated Go binary to support compression parameters
- Modified stream_to_kafka to support compression options in Python SDK

### Fixed
- Fixed binary command flag format issues in CLI module
- Fixed argument mismatches between Python wrapper and Go binary
- Fixed session ID handling in Kafka streaming functions
- Addressed compression codec selection in Kafka producer configuration
- Fixed missing compression flags in Go binary for Kafka streaming

## [0.3.0] - 2023-10-28

### Added
- Enhanced URL validation to prevent security vulnerabilities
- Support for customizable buffer sizes in Kafka streaming
- Improved error handling for crawler operations
- New `kafka_consumer_direct.py` script with better security
- Configurable compression options (Gzip and Snappy support)
- Added Snappy compression library installation instructions

### Changed
- Updated Kafka producer to use Gzip compression instead of Snappy by default
- Improved input validation across all user-provided parameters
- Enhanced session ID tracking for better multi-user support
- Refactored code for better security and performance

### Fixed
- Fixed URL validation to properly handle invalid URLs
- Fixed command execution when arguments are missing
- Fixed UnsupportedCodecError by adding proper compression library support
- Resolved buffer size issues when streaming large web pages
- Fixed message encoding problems in Kafka consumer

## [0.2.6] - 2025-03-27

### Added
- Kafka streaming functionality
- Session-based message tracking
- Support for R2 storage integration
- Binary version management system
- Parallel URL processing

### Changed
- Refactored crawler implementation for better performance
- Improved HTML content extraction
- Enhanced Markdown conversion quality

### Fixed
- Fixed memory leaks in long-running operations
- Resolved concurrent processing issues
