"""
Kafka consumer for processing customer and inventory messages.
Implements asynchronous consumption with idempotency and retry logic.
"""
import json
import logging
import signal
import sys
from typing import Dict, Any
from confluent_kafka import Consumer, KafkaError, KafkaException
from django.conf import settings

from .utils import IdempotencyHandler, DataMerger, AnalyticsClient

logger = logging.getLogger(__name__)


class KafkaMessageConsumer:
    """Main Kafka consumer for processing customer and inventory data."""
    
    def __init__(self):
        self.kafka_config = settings.KAFKA_CONFIG
        self.consumer = None
        self.running = False
        self.idempotency_handler = IdempotencyHandler()
        self.data_merger = DataMerger()
        self.analytics_client = AnalyticsClient()
        
        # Message counters
        self.stats = {
            'total_consumed': 0,
            'duplicates_skipped': 0,
            'successfully_processed': 0,
            'errors': 0
        }
        
    def _create_consumer(self) -> Consumer:
        """Create and configure Kafka consumer."""
        conf = {
            'bootstrap.servers': self.kafka_config['bootstrap_servers'],
            'group.id': self.kafka_config['group_id'],
            'auto.offset.reset': self.kafka_config['auto_offset_reset'],
            'enable.auto.commit': False,  # Manual commit for better control
            'session.timeout.ms': 6000,
            'max.poll.interval.ms': 300000,
        }
        
        consumer = Consumer(conf)
        logger.info(f"Kafka consumer created with config: {conf}")
        return consumer
    
    def start(self):
        """Start consuming messages from Kafka topics."""
        self.consumer = self._create_consumer()
        topics = [
            self.kafka_config['customer_topic'],
            self.kafka_config['inventory_topic']
        ]
        
        self.consumer.subscribe(topics)
        logger.info(f"Subscribed to topics: {topics}")
        
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Starting message consumption...")
        self._consume_loop()
    
    def _consume_loop(self):
        """Main consumption loop."""
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    self._handle_kafka_error(msg.error())
                    continue
                
                self._process_message(msg)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except KafkaException as e:
            logger.error(f"Kafka exception: {e}")
        finally:
            self._shutdown()
    
    def _process_message(self, msg):
        """Process a single Kafka message."""
        try:
            self.stats['total_consumed'] += 1
            
            # Decode message
            topic = msg.topic()
            key = msg.key().decode('utf-8') if msg.key() else None
            value = msg.value().decode('utf-8')
            
            # Log raw data received from Kafka
            logger.info(f"[KAFKA RAW] Topic: {topic} | Key: {key} | Data: {value}")
            
            logger.debug(f"Received message from topic '{topic}' with key '{key}'")
            
            # Parse JSON
            try:
                data = json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON message: {e}")
                self.stats['errors'] += 1
                self.consumer.commit(message=msg)
                return
            
            # Check for duplicates
            message_hash = self.idempotency_handler.generate_message_hash(data)
            if self.idempotency_handler.is_duplicate(message_hash):
                logger.info(f"Duplicate message detected (hash: {message_hash[:8]}...), skipping")
                self.stats['duplicates_skipped'] += 1
                self.consumer.commit(message=msg)
                return
            
            # Process based on topic
            if topic == self.kafka_config['customer_topic']:
                self._process_customer_message(data)
            elif topic == self.kafka_config['inventory_topic']:
                self._process_inventory_message(data)
            else:
                logger.warning(f"Unknown topic: {topic}")
            
            # Mark as processed
            self.idempotency_handler.mark_as_processed(
                message_hash,
                metadata={'topic': topic, 'key': key}
            )
            
            # Commit offset
            self.consumer.commit(message=msg)
            self.stats['successfully_processed'] += 1
            
            # Log stats periodically
            if self.stats['total_consumed'] % 10 == 0:
                logger.info(f"Consumer stats: {self.stats}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            self.stats['errors'] += 1
            # Still commit to avoid reprocessing problematic messages
            self.consumer.commit(message=msg)
    
    def _process_customer_message(self, data: Dict[str, Any]):
        """Process customer data message."""
        logger.debug(f"Processing customer data: {data.get('id')}")
        self.data_merger.add_customer_data(data)
        self._try_send_merged_data()
    
    def _process_inventory_message(self, data: Dict[str, Any]):
        """Process inventory data message."""
        logger.debug(f"Processing inventory data: {data.get('id')}")
        self.data_merger.add_inventory_data(data)
        self._try_send_merged_data()
    
    def _try_send_merged_data(self):
        """
        Attempt to merge and send data to Analytics System.
        Triggers when both customer and inventory data are available.
        """
        cache_stats = self.data_merger.get_cache_stats()
        
        # Simple strategy: send when we have data from both sources
        if cache_stats['customers_cached'] > 0 and cache_stats['inventory_cached'] > 0:
            logger.info("Both customer and inventory data available, merging...")
            
            merged_data = self.data_merger.merge_data()
            if merged_data:
                success = self.analytics_client.send_data(merged_data)
                if success:
                    logger.info("Successfully sent merged data to Analytics System")
                    self.data_merger.clear_cache()
                else:
                    logger.error("Failed to send merged data to Analytics System")
                    # Keep data in cache for retry on next message
    
    def _handle_kafka_error(self, error: KafkaError):
        """Handle Kafka errors."""
        if error.code() == KafkaError._PARTITION_EOF:
            logger.debug("Reached end of partition")
        else:
            logger.error(f"Kafka error: {error}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down consumer...")
        logger.info(f"Final stats: {self.stats}")
        
        # Try to send any remaining cached data
        if self.data_merger.get_cache_stats()['customers_cached'] > 0 or \
           self.data_merger.get_cache_stats()['inventory_cached'] > 0:
            logger.info("Attempting to send remaining cached data...")
            merged_data = self.data_merger.merge_data()
            if merged_data:
                self.analytics_client.send_data(merged_data)
        
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer closed")
