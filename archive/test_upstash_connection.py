"""
Test Upstash Redis Connection
Run this script to verify your Upstash credentials are working correctly
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("UPSTASH REDIS CONNECTION TEST")
print("=" * 70)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check configuration
from config import settings

print("\n📋 Configuration Check:")
print("-" * 70)
print(f"✓ Redis Enabled: {settings.redis_enabled}")
print(f"✓ Upstash REST URL: {settings.upstash_redis_rest_url[:50]}..." if settings.upstash_redis_rest_url else "❌ Not set")
print(f"✓ Upstash REST Token: {'*' * 20}... (hidden)" if settings.upstash_redis_rest_token else "❌ Not set")
print(f"✓ Redis TTL: {settings.redis_ttl}s")
print(f"✓ Max Retries: {settings.redis_max_retries}")
print(f"✓ Timeout: {settings.redis_timeout}s")

if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
    print("\n" + "=" * 70)
    print("❌ ERROR: Upstash credentials not configured!")
    print("=" * 70)
    print("\nPlease add the following to your .env file:")
    print("\nUPSTASH_REDIS_REST_URL=https://your-database.upstash.io")
    print("UPSTASH_REDIS_REST_TOKEN=your-token-here")
    print("\nGet your credentials from: https://console.upstash.com/")
    print("=" * 70)
    sys.exit(1)

# Test Upstash client directly
print("\n🔌 Testing Upstash REST API Client:")
print("-" * 70)

try:
    from upstash_redis import UpstashRedis
    import json
    from datetime import datetime
    
    client = UpstashRedis(
        rest_url=settings.upstash_redis_rest_url,
        rest_token=settings.upstash_redis_rest_token,
        timeout=settings.redis_timeout
    )
    
    # Test 1: PING
    print("\n1️⃣  PING test...")
    pong = client.ping()
    print(f"   ✅ PING successful: {pong}")
    
    # Test 2: SET
    print("\n2️⃣  SET test...")
    test_key = "test:connection"
    test_value = json.dumps({
        "message": "Upstash connection successful!",
        "timestamp": datetime.utcnow().isoformat(),
        "from": "test_upstash_connection.py"
    })
    success = client.set(test_key, test_value, ex=60)
    print(f"   ✅ SET successful: {success}")
    
    # Test 3: GET
    print("\n3️⃣  GET test...")
    retrieved = client.get(test_key)
    if retrieved:
        data = json.loads(retrieved)
        print(f"   ✅ GET successful")
        print(f"   📦 Retrieved: {data['message']}")
    else:
        print(f"   ❌ GET failed - no data retrieved")
    
    # Test 4: EXISTS
    print("\n4️⃣  EXISTS test...")
    exists = client.exists(test_key)
    print(f"   ✅ EXISTS: {exists}")
    
    # Test 5: DELETE
    print("\n5️⃣  DELETE test...")
    deleted = client.delete(test_key)
    print(f"   ✅ DELETE successful: {deleted} key(s) removed")
    
    client.close()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Upstash connection is working!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n" + "=" * 70)
    print("Connection failed! Please check:")
    print("  1. Your Upstash REST URL is correct")
    print("  2. Your Upstash REST Token is correct")
    print("  3. Your internet connection is working")
    print("  4. Upstash service is not down")
    print("=" * 70)
    sys.exit(1)

# Test Redis Cache Manager
print("\n🔧 Testing Redis Cache Manager:")
print("-" * 70)

try:
    from redis_cache import redis_cache
    
    # Health check
    print("\n1️⃣  Health Check...")
    health = redis_cache.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Active: {health['active']}")
    print(f"   Provider: {health.get('provider', 'N/A')}")
    print(f"   Message: {health['message']}")
    
    if health['active']:
        print("   ✅ Redis Cache Manager is healthy")
        
        # Test caching
        print("\n2️⃣  Testing cache operations...")
        test_text = "Hello from Upstash test!"
        test_result = {"sentiment": "positive", "score": 0.95}
        
        # Cache sentiment
        redis_cache.cache_sentiment(test_text, "en", test_result)
        print("   ✅ Cached sentiment result")
        
        # Retrieve cached
        cached = redis_cache.get_cached_sentiment(test_text, "en")
        if cached:
            print(f"   ✅ Retrieved cached result: {cached}")
        else:
            print("   ⚠️  Cache retrieval returned None")
        
        # Stats
        print("\n3️⃣  Cache Statistics...")
        stats = redis_cache.get_stats()
        print(f"   Provider: {stats.get('provider', 'N/A')}")
        print(f"   Status: {stats.get('status', 'N/A')}")
        print(f"   Active: {stats.get('active', False)}")
        print(f"   Client Type: {stats.get('client_type', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("✅ REDIS CACHE MANAGER IS READY!")
        print("=" * 70)
    else:
        print(f"   ❌ Redis Cache Manager is not active")
        print(f"   Error: {health.get('last_error', 'Unknown')}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("🎉 SUCCESS! Your Upstash Redis is properly configured!")
print("=" * 70)
print("\nNext steps:")
print("  1. Start your API: uvicorn api:app --reload")
print("  2. Check status: http://localhost:8000/status")
print("  3. Check Redis health: http://localhost:8000/redis/health")
print("  4. View stats: http://localhost:8000/redis/stats")
print("\n" + "=" * 70)
