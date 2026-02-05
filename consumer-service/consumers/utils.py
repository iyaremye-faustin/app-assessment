"""
Utility classes for consumer service.
Includes idempotency, data merging, and analytics client.
"""
import hashlib
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import redis
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ============= IDEMPOTENCY =============

class IdempotencyHandler:
    """Handles message deduplication using Redis."""
    
    def __init__(self):
        redis_config = settings.REDIS_CONFIG
        self.redis_client = redis.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            db=redis_config['db'],
            password=redis_config['password'] if redis_config['password'] else None,
            decode_responses=True
        )
        self.ttl = redis_config['ttl']
    
    def generate_message_hash(self, message_data: dict) -> str:
        """Generate unique hash for message."""
        message_str = json.dumps(message_data, sort_keys=True)
        return hashlib.sha256(message_str.encode()).hexdigest()
    
    def is_duplicate(self, message_hash: str) -> bool:
        """Check if message already processed."""
        try:
            return self.redis_client.exists(f"processed:{message_hash}") == 1
        except redis.RedisError as e:
            logger.error(f"Redis error checking duplicate: {e}")
            return False
    
    def mark_as_processed(self, message_hash: str, metadata: Optional[dict] = None) -> bool:
        """Mark message as processed with TTL."""
        try:
            key = f"processed:{message_hash}"
            value = json.dumps(metadata) if metadata else "processed"
            self.redis_client.setex(key, self.ttl, value)
            return True
        except redis.RedisError as e:
            logger.error(f"Redis error marking as processed: {e}")
            return False


# ============= DATA MERGER =============

class DataMerger:
    """Merges customer and inventory data."""
    
    def __init__(self):
        self.customer_cache: Dict[str, dict] = {}
        self.inventory_cache: Dict[str, dict] = {}
    
    def add_customer_data(self, customer_data: dict) -> None:
        """Add customer data to cache."""
        customer_id = customer_data.get('id')
        if customer_id:
            self.customer_cache[customer_id] = customer_data
    
    def add_inventory_data(self, inventory_data: dict) -> None:
        """Add inventory data to cache."""
        inventory_id = inventory_data.get('id')
        if inventory_id:
            self.inventory_cache[inventory_id] = inventory_data
    
    def merge_data(self) -> Optional[Dict[str, Any]]:
        """Merge cached data into unified JSON."""
        if not self.customer_cache and not self.inventory_cache:
            return None
        
        merged_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "customers": self._format_customers(),
            "inventory": self._format_inventory(),
            "summary": {
                "total_customers": len(self.customer_cache),
                "total_products": len(self.inventory_cache)
            }
        }
        
        logger.info(f"Merged data: {merged_data['summary']}")
        return merged_data
    
    def _format_customers(self) -> List[dict]:
        """Format customer data."""
        customers = []
        for customer_id, data in self.customer_cache.items():
            customer_entry = {
                "id": customer_id,
                "name": data.get('name'),
                "email": data.get('email'),
            }
            if 'additional' in data and data['additional']:
                customer_entry['additional_info'] = data['additional']
            customers.append(customer_entry)
        return customers
    
    def _format_inventory(self) -> List[dict]:
        """Format inventory data."""
        inventory = []
        for inventory_id, data in self.inventory_cache.items():
            inventory_entry = {
                "id": inventory_id,
                "name": data.get('name'),
                "stock": data.get('stock'),
            }
            if 'additional' in data and data['additional']:
                inventory_entry['additional_info'] = data['additional']
            inventory.append(inventory_entry)
        return inventory
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.customer_cache.clear()
        self.inventory_cache.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "customers_cached": len(self.customer_cache),
            "inventory_cached": len(self.inventory_cache)
        }


# ============= ANALYTICS CLIENT =============

class AnalyticsClient:
    """Client for Analytics System with retry logic."""
    
    def __init__(self):
        analytics_config = settings.ANALYTICS_CONFIG
        self.base_url = analytics_config['base_url']
        self.endpoint = analytics_config['endpoint']
        self.retry_attempts = analytics_config['retry_attempts']
        self.retry_backoff = analytics_config['retry_backoff']
        self.full_url = f"{self.base_url}{self.endpoint}"
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """Send data with exponential backoff retry."""
        for attempt in range(1, self.retry_attempts + 1):
            try:
                logger.info(f"Sending data to Analytics (attempt {attempt}/{self.retry_attempts})")
                
                response = requests.post(
                    self.full_url,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code in (200, 201, 202):
                    logger.info(f"Successfully sent data: {response.status_code}")
                    return True
                else:
                    logger.warning(f"Non-success status: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Timeout (attempt {attempt})")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error (attempt {attempt})")
            except Exception as e:
                logger.error(f"Error: {e} (attempt {attempt})")
            
            if attempt < self.retry_attempts:
                backoff_time = self.retry_backoff ** attempt
                logger.info(f"Retrying in {backoff_time}s...")
                time.sleep(backoff_time)
        
        logger.error(f"Failed after {self.retry_attempts} attempts")
        return False
