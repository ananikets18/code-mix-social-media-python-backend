"""
Redis Cache Manager for NLP API
Provides caching functionality for API responses and intermediate results
"""

import redis
import json
import hashlib
from typing import Optional, Dict, Any, Union
from datetime import datetime
from logger_config import get_logger
from config import settings

logger = get_logger(__name__)


class RedisCache:
    """Redis cache manager with automatic serialization and TTL"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = None
        self.enabled = settings.redis_enabled
        
        if self.enabled:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✓ Redis connected: {settings.redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
                self.redis_client = None
    
    def _generate_key(self, prefix: str, data: Union[str, Dict]) -> str:
        """Generate a unique cache key from data"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 chars
        
        return f"{prefix}:{hash_hex}"
    
    def get(self, key: str) -> Optional[Dict]:
        """
        Get cached value by key
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        """
        Set cache value with optional TTL
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (default: from settings)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or settings.redis_ttl
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete cached value
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            deleted = self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key} (deleted: {deleted})")
            return deleted > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    def cache_analysis_result(self, text: str, params: Dict, result: Dict) -> str:
        """
        Cache comprehensive analysis result
        
        Args:
            text: Input text
            params: Request parameters
            result: Analysis result
            
        Returns:
            Cache key
        """
        cache_data = {
            "text": text,
            "params": params
        }
        key = self._generate_key("analysis", cache_data)
        
        # Add metadata
        cached_result = {
            **result,
            "_cache_metadata": {
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": settings.redis_ttl
            }
        }
        
        self.set(key, cached_result)
        return key
    
    def get_cached_analysis(self, text: str, params: Dict) -> Optional[Dict]:
        """
        Get cached analysis result
        
        Args:
            text: Input text
            params: Request parameters
            
        Returns:
            Cached result or None
        """
        cache_data = {
            "text": text,
            "params": params
        }
        key = self._generate_key("analysis", cache_data)
        return self.get(key)
    
    def cache_language_detection(self, text: str, result: Dict, ttl: int = 7200) -> str:
        """
        Cache language detection result (longer TTL as it's deterministic)
        
        Args:
            text: Input text
            result: Detection result
            ttl: TTL in seconds (default: 2 hours)
            
        Returns:
            Cache key
        """
        key = self._generate_key("lang_detect", text)
        self.set(key, result, ttl)
        return key
    
    def get_cached_language_detection(self, text: str) -> Optional[Dict]:
        """Get cached language detection result"""
        key = self._generate_key("lang_detect", text)
        return self.get(key)
    
    def cache_sentiment(self, text: str, language: str, result: Dict) -> str:
        """
        Cache sentiment analysis result
        
        Args:
            text: Input text
            language: Language code
            result: Sentiment result
            
        Returns:
            Cache key
        """
        cache_data = f"{language}:{text}"
        key = self._generate_key("sentiment", cache_data)
        self.set(key, result)
        return key
    
    def get_cached_sentiment(self, text: str, language: str) -> Optional[Dict]:
        """Get cached sentiment result"""
        cache_data = f"{language}:{text}"
        key = self._generate_key("sentiment", cache_data)
        return self.get(key)
    
    def cache_translation(self, text: str, source: str, target: str, result: Dict, ttl: int = 86400) -> str:
        """
        Cache translation result (24 hour TTL as translations are stable)
        
        Args:
            text: Input text
            source: Source language
            target: Target language
            result: Translation result
            ttl: TTL in seconds (default: 24 hours)
            
        Returns:
            Cache key
        """
        cache_data = f"{source}:{target}:{text}"
        key = self._generate_key("translation", cache_data)
        self.set(key, result, ttl)
        return key
    
    def get_cached_translation(self, text: str, source: str, target: str) -> Optional[Dict]:
        """Get cached translation result"""
        cache_data = f"{source}:{target}:{text}"
        key = self._generate_key("translation", cache_data)
        return self.get(key)
    
    def get_stats(self) -> Dict:
        """
        Get Redis cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "status": "disabled"
            }
        
        try:
            info = self.redis_client.info()
            
            # Count keys by prefix
            key_counts = {}
            for prefix in ["analysis", "lang_detect", "sentiment", "translation"]:
                pattern = f"{prefix}:*"
                keys = self.redis_client.keys(pattern)
                key_counts[prefix] = len(keys)
            
            return {
                "enabled": True,
                "status": "connected",
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": sum(key_counts.values()),
                "keys_by_type": key_counts,
                "ttl": settings.redis_ttl,
                "url": settings.redis_url.replace(settings.redis_url.split("@")[-1] if "@" in settings.redis_url else "", "***")
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }
    
    def clear_all(self) -> bool:
        """
        Clear all cached data (USE WITH CAUTION)
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Redis cache cleared (all keys deleted)")
            return True
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return False
    
    def clear_by_pattern(self, pattern: str) -> int:
        """
        Clear keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., "analysis:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing keys by pattern: {e}")
            return 0
    
    def health_check(self) -> Dict:
        """
        Check Redis health
        
        Returns:
            Health status dictionary
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Redis caching is disabled"
            }
        
        if not self.redis_client:
            return {
                "status": "error",
                "message": "Redis client not initialized"
            }
        
        try:
            self.redis_client.ping()
            return {
                "status": "healthy",
                "message": "Redis is connected and responsive",
                "url": settings.redis_url
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Redis connection error: {str(e)}"
            }


# Global cache instance
redis_cache = RedisCache()


# Convenience functions
def get_cache() -> RedisCache:
    """Get the global Redis cache instance"""
    return redis_cache


def is_cache_enabled() -> bool:
    """Check if Redis caching is enabled and working"""
    return redis_cache.enabled


if __name__ == "__main__":
    # Test Redis connection
    print("=" * 60)
    print("Redis Cache Manager - Test")
    print("=" * 60)
    
    cache = RedisCache()
    
    # Health check
    health = cache.health_check()
    print(f"Health Status: {health}")
    
    if cache.enabled:
        # Test operations
        print("\nTesting cache operations...")
        
        # Set test value
        test_key = "test:key"
        test_value = {"message": "Hello Redis!", "timestamp": datetime.utcnow().isoformat()}
        cache.set(test_key, test_value, ttl=60)
        print(f"✓ Set test key: {test_key}")
        
        # Get test value
        retrieved = cache.get(test_key)
        print(f"✓ Retrieved: {retrieved}")
        
        # Delete test value
        cache.delete(test_key)
        print(f"✓ Deleted test key")
        
        # Stats
        stats = cache.get_stats()
        print(f"\nCache Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    print("=" * 60)
