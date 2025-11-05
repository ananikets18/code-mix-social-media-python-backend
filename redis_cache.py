"""
Redis Cache Manager for NLP API (Upstash REST API)
Provides caching functionality for API responses and intermediate results
Supports Upstash cloud Redis via REST API
"""

import json
import hashlib
from typing import Optional, Dict, Any, Union
from datetime import datetime
from logger_config import get_logger
from config import settings

logger = get_logger(__name__)

# Import appropriate Redis client
redis_client_type = None
try:
    # Check if Upstash REST credentials are provided
    if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        from upstash_redis import UpstashRedis
        redis_client_type = "upstash"
        logger.debug("Using Upstash REST API client")
    else:
        # Fallback to traditional Redis client (for local development)
        import redis
        redis_client_type = "traditional"
        logger.debug("Using traditional Redis client")
except ImportError as e:
    logger.warning(f"Redis import error: {e}")
    redis_client_type = None


class RedisCache:
    """Redis cache manager with automatic serialization and TTL (Upstash REST API)"""
    
    def __init__(self):
        """Initialize Redis connection with Upstash REST API support"""
        self.redis_client = None
        self.enabled = settings.redis_enabled
        self.connection_status = "disabled"
        self.last_error = None
        self.connection_timestamp = None
        self.client_type = redis_client_type
        
        if self.enabled:
            self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection with Upstash REST API"""
        try:
            if self.client_type == "upstash":
                # Use Upstash REST API
                if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
                    raise ValueError("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set")
                
                logger.debug("Connecting to Upstash Redis...")
                
                from upstash_redis import UpstashRedis
                self.redis_client = UpstashRedis(
                    rest_url=settings.upstash_redis_rest_url,
                    rest_token=settings.upstash_redis_rest_token,
                    timeout=settings.redis_timeout
                )
                
            elif self.client_type == "traditional":
                # Use traditional Redis client (fallback for local development)
                logger.debug("Connecting to local Redis...")
                import redis
                
                # Fallback to local Redis URL if set in environment
                redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379')
                
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=settings.redis_timeout,
                    socket_connect_timeout=settings.redis_timeout,
                    retry_on_timeout=True,
                    max_connections=50
                )
            else:
                raise ValueError("No Redis client available")
            
            # Test connection with retries
            max_retries = settings.redis_max_retries
            for attempt in range(max_retries):
                try:
                    self.redis_client.ping()
                    self.connection_status = "connected"
                    self.connection_timestamp = datetime.utcnow().isoformat()
                    self.last_error = None
                    
                    logger.info(f"✅ Redis connected ({self.client_type})")
                    return
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Redis connection attempt {attempt + 1}/{max_retries} failed: {e}")
                        import time
                        time.sleep(1)
                    else:
                        raise e
            
        except Exception as e:
            self.connection_status = "error"
            self.last_error = str(e)
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  Caching disabled - API will work with degraded performance")
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
        Get Redis cache statistics (Upstash REST API compatible)
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "active": False,
                "status": "disabled",
                "provider": None,
                "message": "Redis is disabled"
            }
        
        try:
            # Check provider
            is_upstash = self.client_type == "upstash"
            provider = "Upstash (Cloud - REST API)" if is_upstash else "Local Redis"
            
            # Basic stats that work on both Upstash and local Redis
            stats = {
                "enabled": True,
                "active": True,
                "status": "connected",
                "provider": provider,
                "is_upstash": is_upstash,
                "client_type": self.client_type,
                "ttl": settings.redis_ttl,
                "rest_url": self._mask_url(settings.upstash_redis_rest_url) if is_upstash else None,
                "connection_time": self.connection_timestamp
            }
            
            # Try to get INFO (may not work on Upstash free tier)
            try:
                if hasattr(self.redis_client, 'info'):
                    info = self.redis_client.info()
                    if info:
                        stats.update({
                            "redis_version": info.get("redis_version", "unknown"),
                            "used_memory_human": info.get("used_memory_human", "N/A"),
                            "connected_clients": info.get("connected_clients", 0),
                        })
                    else:
                        raise Exception("INFO not available")
                else:
                    raise Exception("INFO not available")
            except Exception:
                # Upstash free tier doesn't support INFO command
                logger.debug("INFO command not available (Upstash REST API)")
                stats.update({
                    "redis_version": "Upstash (REST API)",
                    "used_memory_human": "N/A",
                    "connected_clients": "N/A",
                })
            
            # Count keys by prefix (works on Upstash)
            key_counts = {}
            try:
                for prefix in ["analysis", "lang_detect", "sentiment", "translation"]:
                    pattern = f"{prefix}:*"
                    # Use SCAN instead of KEYS for better performance
                    cursor = 0
                    count = 0
                    while True:
                        cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                        count += len(keys)
                        if cursor == 0:
                            break
                    key_counts[prefix] = count
                
                stats["total_keys"] = sum(key_counts.values())
                stats["keys_by_type"] = key_counts
                
            except Exception as e:
                logger.warning(f"Could not count keys: {e}")
                stats["total_keys"] = "N/A"
                stats["keys_by_type"] = {}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {
                "enabled": True,
                "active": False,
                "status": "error",
                "provider": "Upstash (Cloud - REST API)" if self.client_type == "upstash" else "Local Redis",
                "error": str(e),
                "message": "Failed to retrieve Redis statistics"
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
        Check Redis health with detailed status for frontend
        
        Returns:
            Health status dictionary with connection details
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "active": False,
                "message": "Redis caching is disabled",
                "provider": None,
                "connection_time": None,
                "last_error": self.last_error
            }
        
        if not self.redis_client:
            return {
                "status": "error",
                "active": False,
                "message": "Redis client not initialized",
                "provider": None,
                "connection_time": None,
                "last_error": self.last_error or "Client not initialized"
            }
        
        try:
            # Ping with timeout
            response = self.redis_client.ping()
            
            # Determine provider
            is_upstash = self.client_type == "upstash"
            provider = "Upstash (Cloud - REST API)" if is_upstash else "Local Redis"
            
            # Try to get server info (may not work on Upstash free tier)
            redis_version = "unknown"
            try:
                if hasattr(self.redis_client, 'info'):
                    info = self.redis_client.info()
                    redis_version = info.get("redis_version", "unknown") if info else "Upstash (free tier)"
                else:
                    redis_version = "Upstash (REST API)"
            except:
                redis_version = "Upstash (REST API)"
            
            return {
                "status": "healthy",
                "active": True,
                "message": f"Redis is connected and responsive",
                "provider": provider,
                "is_upstash": is_upstash,
                "client_type": self.client_type,
                "redis_version": redis_version,
                "connection_time": self.connection_timestamp,
                "connection_status": self.connection_status,
                "rest_url": self._mask_url(settings.upstash_redis_rest_url) if is_upstash else None,
                "last_error": None
            }
            
        except (ConnectionError, TimeoutError) as e:
            error_type = "ConnectionError" if isinstance(e, ConnectionError) else "TimeoutError"
            self.connection_status = "connection_error" if isinstance(e, ConnectionError) else "timeout"
            self.last_error = str(e)
            
            return {
                "status": "unhealthy",
                "active": False,
                "message": f"Redis {error_type.lower()}: {str(e)}",
                "provider": "Upstash (Cloud - REST API)" if self.client_type == "upstash" else "Local Redis",
                "connection_time": self.connection_timestamp,
                "last_error": str(e),
                "error_type": error_type
            }
            
        except Exception as e:
            self.connection_status = "error"
            self.last_error = str(e)
            return {
                "status": "unhealthy",
                "active": False,
                "message": f"Redis error: {str(e)}",
                "provider": "Upstash (Cloud - REST API)" if self.client_type == "upstash" else "Local Redis",
                "connection_time": self.connection_timestamp,
                "last_error": str(e),
                "error_type": type(e).__name__
            }
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of URL"""
        if not url:
            return "N/A"
        # For Upstash REST URLs, just mask the middle part
        if "upstash.io" in url:
            parts = url.split(".")
            if len(parts) >= 3:
                parts[0] = parts[0][:8] + "***" if len(parts[0]) > 8 else "***"
            return ".".join(parts)
        return url


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
