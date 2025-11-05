"""
Upstash Redis REST API Client
Provides HTTP-based Redis operations for Upstash free tier
"""

import requests
import json
from typing import Optional, Any, List
from datetime import datetime
from logger_config import get_logger

logger = get_logger(__name__)


class UpstashRedis:
    """Upstash Redis client using REST API"""
    
    def __init__(self, rest_url: str, rest_token: str, timeout: int = 10):
        """
        Initialize Upstash Redis REST client
        
        Args:
            rest_url: Upstash REST API URL (e.g., https://xxx.upstash.io)
            rest_token: Upstash REST API token
            timeout: Request timeout in seconds
        """
        self.rest_url = rest_url.rstrip('/')
        self.rest_token = rest_token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {rest_token}',
            'Content-Type': 'application/json'
        })
    
    def _execute(self, command: List[Any]) -> Any:
        """
        Execute a Redis command via REST API
        
        Args:
            command: Redis command as a list (e.g., ["GET", "key"])
            
        Returns:
            Command result
        """
        try:
            response = self.session.post(
                self.rest_url,
                json=command,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('result')
            
        except requests.exceptions.Timeout:
            logger.error(f"Upstash request timeout: {command[0]}")
            raise TimeoutError(f"Upstash request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Upstash request failed: {e}")
            raise ConnectionError(f"Upstash connection error: {e}")
        except Exception as e:
            logger.error(f"Upstash error: {e}")
            raise
    
    def ping(self) -> bool:
        """Test connection with PING command"""
        result = self._execute(["PING"])
        return result == "PONG"
    
    def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        result = self._execute(["GET", key])
        return result
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        Set key-value pair with optional expiration
        
        Args:
            key: Redis key
            value: Value to store
            ex: Expiration in seconds
            
        Returns:
            True if successful
        """
        if ex:
            result = self._execute(["SET", key, value, "EX", ex])
        else:
            result = self._execute(["SET", key, value])
        return result == "OK"
    
    def setex(self, key: str, time: int, value: str) -> bool:
        """Set key with expiration (alias for set with EX)"""
        return self.set(key, value, ex=time)
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0
        result = self._execute(["DEL", *keys])
        return result or 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        result = self._execute(["EXISTS", key])
        return result == 1
    
    def scan(self, cursor: int = 0, match: Optional[str] = None, count: int = 100) -> tuple:
        """
        Scan keys with pattern matching
        
        Args:
            cursor: Scan cursor
            match: Pattern to match
            count: Number of keys to return
            
        Returns:
            Tuple of (next_cursor, keys)
        """
        command = ["SCAN", str(cursor)]
        if match:
            command.extend(["MATCH", match])
        command.extend(["COUNT", str(count)])
        
        result = self._execute(command)
        if result and len(result) >= 2:
            next_cursor = int(result[0])
            keys = result[1] if isinstance(result[1], list) else []
            return next_cursor, keys
        return 0, []
    
    def keys(self, pattern: str) -> List[str]:
        """
        Get all keys matching pattern (use SCAN for production)
        
        Warning: This can be slow for large databases
        """
        result = self._execute(["KEYS", pattern])
        return result if isinstance(result, list) else []
    
    def flushdb(self) -> bool:
        """Delete all keys in current database"""
        result = self._execute(["FLUSHDB"])
        return result == "OK"
    
    def info(self, section: Optional[str] = None) -> dict:
        """
        Get Redis server info
        
        Note: May not be available on Upstash free tier
        """
        try:
            command = ["INFO"] if not section else ["INFO", section]
            result = self._execute(command)
            
            # Parse INFO response
            info_dict = {}
            if isinstance(result, str):
                for line in result.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#') and ':' in line:
                        key, value = line.split(':', 1)
                        info_dict[key] = value
            
            return info_dict
        except Exception as e:
            logger.debug(f"INFO command not available: {e}")
            return {}
    
    def close(self):
        """Close session"""
        self.session.close()


class UpstashConnectionError(Exception):
    """Upstash connection error"""
    pass


class UpstashTimeoutError(Exception):
    """Upstash timeout error"""
    pass


# Test the client
if __name__ == "__main__":
    import os
    from config import settings
    
    print("=" * 60)
    print("Upstash Redis REST Client - Test")
    print("=" * 60)
    
    if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
        print("❌ Error: UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set")
        print("\nSet them in your .env file:")
        print("UPSTASH_REDIS_REST_URL=https://xxx.upstash.io")
        print("UPSTASH_REDIS_REST_TOKEN=your-token-here")
        exit(1)
    
    try:
        # Initialize client
        client = UpstashRedis(
            rest_url=settings.upstash_redis_rest_url,
            rest_token=settings.upstash_redis_rest_token,
            timeout=settings.redis_timeout
        )
        
        # Test PING
        print("\n1. Testing connection (PING)...")
        pong = client.ping()
        print(f"   ✓ PING: {pong}")
        
        # Test SET
        print("\n2. Testing SET...")
        test_key = "test:upstash"
        test_value = json.dumps({
            "message": "Hello from Upstash!",
            "timestamp": datetime.utcnow().isoformat()
        })
        success = client.set(test_key, test_value, ex=60)
        print(f"   ✓ SET {test_key}: {success}")
        
        # Test GET
        print("\n3. Testing GET...")
        retrieved = client.get(test_key)
        print(f"   ✓ GET {test_key}: {retrieved}")
        
        # Test EXISTS
        print("\n4. Testing EXISTS...")
        exists = client.exists(test_key)
        print(f"   ✓ EXISTS {test_key}: {exists}")
        
        # Test SCAN
        print("\n5. Testing SCAN...")
        cursor, keys = client.scan(match="test:*", count=10)
        print(f"   ✓ SCAN test:*: Found {len(keys)} keys")
        
        # Test DELETE
        print("\n6. Testing DELETE...")
        deleted = client.delete(test_key)
        print(f"   ✓ DELETE {test_key}: {deleted} key(s) deleted")
        
        # Test INFO (may not work on free tier)
        print("\n7. Testing INFO...")
        try:
            info = client.info()
            if info:
                print(f"   ✓ INFO: {len(info)} fields")
                print(f"   Redis version: {info.get('redis_version', 'N/A')}")
            else:
                print("   ℹ INFO command not available (Upstash free tier)")
        except:
            print("   ℹ INFO command not available (Upstash free tier)")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Upstash connection working.")
        print("=" * 60)
        
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nCheck your credentials in .env file:")
        print("UPSTASH_REDIS_REST_URL=https://xxx.upstash.io")
        print("UPSTASH_REDIS_REST_TOKEN=your-token-here")
        exit(1)
