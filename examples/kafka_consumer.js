#!/usr/bin/env node
/**
 * Example Kafka consumer for Pathik-streamed content in JavaScript/Node.js
 * 
 * Requirements:
 * npm install kafkajs dotenv yargs
 */

const { Kafka } = require('kafkajs');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// Load environment variables from .env file
dotenv.config();

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('brokers', {
    description: 'Kafka brokers (comma-separated)',
    default: process.env.KAFKA_BROKERS || 'localhost:9092',
    type: 'string'
  })
  .option('topic', {
    description: 'Kafka topic to consume from',
    default: process.env.KAFKA_TOPIC || 'pathik_crawl_data',
    type: 'string'
  })
  .option('username', {
    description: 'SASL username',
    default: process.env.KAFKA_USERNAME,
    type: 'string'
  })
  .option('password', {
    description: 'SASL password',
    default: process.env.KAFKA_PASSWORD,
    type: 'string'
  })
  .option('type', {
    description: 'Filter by content type (html or markdown)',
    choices: ['html', 'markdown'],
    type: 'string'
  })
  .option('session', {
    description: 'Filter by session ID',
    type: 'string'
  })
  .option('from-beginning', {
    description: 'Consume from the beginning of the topic',
    type: 'boolean',
    default: false
  })
  .help()
  .alias('help', 'h')
  .argv;

async function run() {
  // Log connection info
  console.log(`Connecting to Kafka brokers: ${argv.brokers}`);
  console.log(`Consuming from topic: ${argv.topic}`);
  if (argv.type) {
    console.log(`Filtering for content type: ${argv.type}`);
  }
  console.log(`Starting from: ${argv['from-beginning'] ? 'beginning' : 'most recent'}`);

  // Configure Kafka client
  const kafkaConfig = {
    clientId: 'pathik-example-consumer',
    brokers: argv.brokers.split(','),
  };

  // Add SASL authentication if credentials provided
  if (argv.username && argv.password) {
    kafkaConfig.sasl = {
      mechanism: 'plain',
      username: argv.username,
      password: argv.password
    };
    kafkaConfig.ssl = true;
    console.log('Using SASL authentication');
  }

  const kafka = new Kafka(kafkaConfig);
  const consumer = kafka.consumer({ 
    groupId: 'pathik-example-consumer-js',
    maxWaitTimeInMs: 500 
  });
  
  // Handle graceful shutdown
  const errorTypes = ['unhandledRejection', 'uncaughtException'];
  const signalTraps = ['SIGTERM', 'SIGINT', 'SIGUSR2'];
  
  errorTypes.forEach(type => {
    process.on(type, async e => {
      try {
        console.log(`Process.on ${type}`);
        console.error(e);
        await consumer.disconnect();
        process.exit(0);
      } catch (_) {
        process.exit(1);
      }
    });
  });
  
  signalTraps.forEach(type => {
    process.once(type, async () => {
      try {
        console.log('\nShutting down gracefully...');
        await consumer.disconnect();
        process.exit(0);
      } catch (_) {
        process.exit(1);
      }
    });
  });

  // Connect and subscribe
  await consumer.connect();
  await consumer.subscribe({ 
    topic: argv.topic, 
    fromBeginning: argv['from-beginning'] 
  });
  
  // Display messages
  console.log('Consumer started. Press Ctrl+C to exit.');
  console.log('-----------------------------------------');
  
  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      // Extract headers
      const headers = {};
      if (message.headers) {
        Object.entries(message.headers).forEach(([key, value]) => {
          headers[key] = value ? value.toString() : null;
        });
      }
      
      const contentType = headers.contentType || '';
      const sessionId = headers.sessionID || '';
      
      // Skip if content type filter is set and doesn't match
      if (argv.type && !contentType.toLowerCase().includes(argv.type.toLowerCase())) {
        return;
      }
      
      // Skip if session ID filter is set and doesn't match
      if (argv.session && sessionId !== argv.session) {
        return;
      }
      
      // Display message
      console.log('-----------------------------------------');
      console.log(`Partition: ${partition}, Offset: ${message.offset}`);
      console.log(`Key: ${message.key ? message.key.toString() : 'null'}`);
      console.log(`URL: ${headers.url || 'unknown'}`);
      console.log(`Content Type: ${contentType}`);
      console.log(`Timestamp: ${headers.timestamp || 'unknown'}`);
      if (sessionId) {
        console.log(`Session ID: ${sessionId}`);
      }
      
      // Print preview of content
      const content = message.value ? message.value.toString() : '';
      const contentLen = content.length;
      const preview = contentLen > 200 ? `${content.substring(0, 200)}... [truncated]` : content;
      console.log(`Content Preview (${contentLen} bytes total):`);
      console.log(preview);
    },
  });
}

run().catch(e => {
  console.error(`Error: ${e.message}`);
  process.exit(1);
}); 