# Changelog

All notable changes to Pathik will be documented in this file.

## [Unreleased] - 2025-03-28

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

## [0.3.0] - 2025-03-27

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
