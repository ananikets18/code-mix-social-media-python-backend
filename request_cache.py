"""
Request Cache Manager for /analyze Endpoint

This module provides caching functionality for the /analyze endpoint.
- Stores every request with response in JSON file
- Generates unique hash for each text to detect duplicates
- Replaces duplicate requests with latest response
- Provides cache statistics and management

Author: NLP Project Team
Created: 2025-11-03
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Cache file path
CACHE_FILE = Path(__file__).parent / "data" / "analyze_cache.json"


def get_text_hash(text: str) -> str:
    """
    Generate a unique hash for the input text.
    
    Args:
        text: Input text to hash
        
    Returns:
        MD5 hash of the text (lowercase, stripped)
    """
    # Normalize text before hashing (lowercase, strip whitespace)
    normalized_text = text.strip().lower()
    return hashlib.md5(normalized_text.encode('utf-8')).hexdigest()


def load_cache() -> Dict[str, Any]:
    """
    Load cache data from JSON file.
    
    Returns:
        Dictionary with cache_info and requests
    """
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Initialize cache if file doesn't exist
            return {
                "cache_info": {
                    "description": "Cache for /analyze endpoint requests",
                    "created": datetime.now().isoformat(),
                    "total_requests": 0,
                    "last_updated": None
                },
                "requests": {}
            }
    except Exception as e:
        logger.error(f"Error loading cache: {str(e)}")
        # Return empty cache on error
        return {
            "cache_info": {
                "description": "Cache for /analyze endpoint requests",
                "created": datetime.now().isoformat(),
                "total_requests": 0,
                "last_updated": None
            },
            "requests": {}
        }


def save_cache(cache_data: Dict[str, Any]) -> bool:
    """
    Save cache data to JSON file.
    
    Args:
        cache_data: Dictionary with cache_info and requests
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure data directory exists
        CACHE_FILE.parent.mkdir(exist_ok=True)
        
        # Update last_updated timestamp
        cache_data["cache_info"]["last_updated"] = datetime.now().isoformat()
        
        # Write to file with pretty formatting
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger.error(f"Error saving cache: {str(e)}")
        return False


def store_request(text: str, response: Dict[str, Any], request_params: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Store or update a request in the cache.
    
    If the same text was requested before, it will be replaced with the new response.
    
    Args:
        text: Original input text
        response: API response to cache
        request_params: Optional request parameters (normalization_level, etc.)
        
    Returns:
        Tuple of (is_duplicate, text_hash)
        - is_duplicate: True if this text was cached before (replaced)
        - text_hash: The hash used to identify this request
    """
    try:
        # Load current cache
        cache_data = load_cache()
        
        # Generate hash for the text
        text_hash = get_text_hash(text)
        
        # Check if this text was already cached
        is_duplicate = text_hash in cache_data["requests"]
        
        # Prepare cache entry
        cache_entry = {
            "text": text,
            "text_hash": text_hash,
            "response": response,
            "request_params": request_params or {},
            "timestamp": datetime.now().isoformat(),
            "request_count": cache_data["requests"].get(text_hash, {}).get("request_count", 0) + 1
        }
        
        # Store or replace
        cache_data["requests"][text_hash] = cache_entry
        
        # Update metadata
        cache_data["cache_info"]["total_requests"] = len(cache_data["requests"])
        
        # Save to file
        save_cache(cache_data)
        
        # Log the operation
        if is_duplicate:
            logger.info(f"[CACHE] Replaced duplicate request: hash={text_hash}, "
                       f"count={cache_entry['request_count']}, text_preview='{text[:50]}...'")
        else:
            logger.info(f"[CACHE] Stored new request: hash={text_hash}, text_preview='{text[:50]}...'")
        
        return is_duplicate, text_hash
        
    except Exception as e:
        logger.error(f"Error storing request in cache: {str(e)}")
        return False, ""


def get_cached_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a cached response for the given text.
    
    Args:
        text: Input text to look up
        
    Returns:
        Cached response if found, None otherwise
    """
    try:
        # Load cache
        cache_data = load_cache()
        
        # Generate hash
        text_hash = get_text_hash(text)
        
        # Look up in cache
        if text_hash in cache_data["requests"]:
            cached_entry = cache_data["requests"][text_hash]
            logger.info(f"[CACHE] Cache hit: hash={text_hash}, "
                       f"cached_at={cached_entry.get('timestamp')}, "
                       f"request_count={cached_entry.get('request_count', 1)}")
            return cached_entry.get("response")
        
        logger.info(f"[CACHE] Cache miss: hash={text_hash}")
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving cached response: {str(e)}")
        return None


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        cache_data = load_cache()
        
        # Calculate statistics
        total_requests = len(cache_data["requests"])
        total_hits = sum(
            entry.get("request_count", 1) - 1 
            for entry in cache_data["requests"].values()
        )
        
        # Most requested texts
        top_requests = sorted(
            cache_data["requests"].values(),
            key=lambda x: x.get("request_count", 1),
            reverse=True
        )[:5]
        
        return {
            "cache_info": cache_data["cache_info"],
            "total_unique_requests": total_requests,
            "total_duplicate_hits": total_hits,
            "cache_hit_rate": round(total_hits / max(total_requests, 1), 2),
            "top_requested": [
                {
                    "text": req["text"][:50] + "..." if len(req["text"]) > 50 else req["text"],
                    "request_count": req.get("request_count", 1),
                    "last_timestamp": req.get("timestamp")
                }
                for req in top_requests
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            "error": str(e),
            "cache_info": {},
            "total_unique_requests": 0,
            "total_duplicate_hits": 0
        }


def clear_cache() -> bool:
    """
    Clear all cached requests.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        cache_data = {
            "cache_info": {
                "description": "Cache for /analyze endpoint requests",
                "created": datetime.now().isoformat(),
                "total_requests": 0,
                "last_updated": None
            },
            "requests": {}
        }
        
        save_cache(cache_data)
        logger.info("[CACHE] Cache cleared successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False


def remove_request(text: str) -> bool:
    """
    Remove a specific request from the cache.
    
    Args:
        text: Text to remove from cache
        
    Returns:
        True if removed, False if not found or error
    """
    try:
        cache_data = load_cache()
        text_hash = get_text_hash(text)
        
        if text_hash in cache_data["requests"]:
            del cache_data["requests"][text_hash]
            cache_data["cache_info"]["total_requests"] = len(cache_data["requests"])
            save_cache(cache_data)
            logger.info(f"[CACHE] Removed request: hash={text_hash}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error removing request from cache: {str(e)}")
        return False


# Test function
if __name__ == "__main__":
    # Test the cache system
    print("Testing Request Cache System...")
    
    # Test 1: Store a request
    test_text = "Hello, this is a test message!"
    test_response = {"language": "en", "sentiment": "positive"}
    is_dup, hash_val = store_request(test_text, test_response)
    print(f"\n1. Stored request: is_duplicate={is_dup}, hash={hash_val}")
    
    # Test 2: Store same request again (should be duplicate)
    is_dup2, hash_val2 = store_request(test_text, test_response)
    print(f"2. Stored same request: is_duplicate={is_dup2}, hash={hash_val2}")
    
    # Test 3: Retrieve cached response
    cached = get_cached_response(test_text)
    print(f"3. Retrieved cached response: {cached}")
    
    # Test 4: Get statistics
    stats = get_cache_stats()
    print(f"\n4. Cache Statistics:")
    print(f"   - Total unique requests: {stats['total_unique_requests']}")
    print(f"   - Total duplicate hits: {stats['total_duplicate_hits']}")
    print(f"   - Cache hit rate: {stats['cache_hit_rate']}")
    
    # Test 5: Different text (same content, different case)
    test_text2 = "HELLO, THIS IS A TEST MESSAGE!"
    cached2 = get_cached_response(test_text2)
    print(f"\n5. Same text (different case) - Cache hit: {cached2 is not None}")
    
    print("\nTest completed! Check data/analyze_cache.json")
