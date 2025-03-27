# Changelog

All notable changes to Pathik will be documented in this file.

## [0.3.1] - 2023-10-28

### Added
- New example scripts for Kafka streaming: `native_kafka_demo.py` and `safe_kafka_demo.py`
- Improved documentation for Kafka integration

### Changed
- Fixed command line flags to match Go binary expectations (-content instead of --content-type)
- Correct ordering of arguments for Kafka flags
- Simplified Kafka streaming interface in __init__.py

### Fixed
- Fixed binary command flag format issues in CLI module
- Resolved argument mismatch between Python wrapper and Go binary
- Fixed session ID handling in Kafka streaming functions

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
