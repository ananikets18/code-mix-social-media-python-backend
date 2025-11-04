"""
Test Request Cache System for /analyze Endpoint

This test file demonstrates and validates the request caching functionality.

Author: NLP Project Team
Created: 2025-11-03
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from request_cache import (
    store_request,
    get_cached_response,
    get_cache_stats,
    clear_cache,
    remove_request,
    get_text_hash
)


def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"{'='*80}\n")


def test_basic_caching():
    """Test 1: Basic request storage and retrieval"""
    print_separator("TEST 1: Basic Request Storage and Retrieval")
    
    # Clear cache to start fresh
    clear_cache()
    print("✓ Cache cleared")
    
    # Test request 1
    text1 = "Hello, this is a test message in English!"
    response1 = {
        "language": {"code": "en", "name": "English", "confidence": 0.99},
        "sentiment": {"label": "neutral", "score": 0.5},
        "profanity": {"detected": False}
    }
    
    is_dup, hash1 = store_request(text1, response1)
    print(f"1. Stored request: '{text1[:40]}...'")
    print(f"   - Hash: {hash1}")
    print(f"   - Is duplicate: {is_dup}")
    print(f"   - Expected: is_duplicate=False ✓" if not is_dup else "   - ERROR: Should not be duplicate!")
    
    # Retrieve it
    cached = get_cached_response(text1)
    print(f"\n2. Retrieved cached response:")
    print(f"   - Language: {cached['language']['code']}")
    print(f"   - Sentiment: {cached['sentiment']['label']}")
    print(f"   - Match: {'✓' if cached == response1 else '✗'}")
    
    return is_dup == False and cached == response1


def test_duplicate_detection():
    """Test 2: Duplicate request detection and replacement"""
    print_separator("TEST 2: Duplicate Request Detection and Replacement")
    
    text = "Mi aaj khup khush ahe!"
    
    # First request
    response1 = {
        "language": {"code": "mar", "name": "Marathi", "confidence": 0.85},
        "sentiment": {"label": "positive", "score": 0.75}
    }
    
    is_dup1, hash1 = store_request(text, response1)
    print(f"1. First request: '{text}'")
    print(f"   - Is duplicate: {is_dup1} (Expected: False) {'✓' if not is_dup1 else '✗'}")
    
    # Second request (same text, different response)
    response2 = {
        "language": {"code": "mar", "name": "Marathi", "confidence": 0.90},
        "sentiment": {"label": "positive", "score": 0.80},
        "translation": "I am very happy today!"
    }
    
    is_dup2, hash2 = store_request(text, response2)
    print(f"\n2. Second request (same text): '{text}'")
    print(f"   - Is duplicate: {is_dup2} (Expected: True) {'✓' if is_dup2 else '✗'}")
    print(f"   - Hash match: {hash1 == hash2} {'✓' if hash1 == hash2 else '✗'}")
    
    # Retrieve - should get second response
    cached = get_cached_response(text)
    print(f"\n3. Retrieved cached response:")
    print(f"   - Confidence: {cached['language']['confidence']}")
    print(f"   - Has translation: {'translation' in cached}")
    print(f"   - Replaced correctly: {'✓' if 'translation' in cached else '✗'}")
    
    return is_dup2 and 'translation' in cached


def test_case_insensitivity():
    """Test 3: Case-insensitive duplicate detection"""
    print_separator("TEST 3: Case-Insensitive Duplicate Detection")
    
    # Clear previous tests
    clear_cache()
    
    text1 = "Hello World"
    text2 = "hello world"
    text3 = "HELLO WORLD"
    
    response = {"language": {"code": "en"}}
    
    # Store first
    is_dup1, hash1 = store_request(text1, response)
    print(f"1. Stored: '{text1}'")
    print(f"   - Hash: {hash1}")
    print(f"   - Is duplicate: {is_dup1}")
    
    # Store second (different case)
    is_dup2, hash2 = store_request(text2, response)
    print(f"\n2. Stored: '{text2}' (lowercase)")
    print(f"   - Hash: {hash2}")
    print(f"   - Is duplicate: {is_dup2} (Expected: True) {'✓' if is_dup2 else '✗'}")
    print(f"   - Hash match: {hash1 == hash2} {'✓' if hash1 == hash2 else '✗'}")
    
    # Store third (all caps)
    is_dup3, hash3 = store_request(text3, response)
    print(f"\n3. Stored: '{text3}' (uppercase)")
    print(f"   - Hash: {hash3}")
    print(f"   - Is duplicate: {is_dup3} (Expected: True) {'✓' if is_dup3 else '✗'}")
    print(f"   - Hash match: {hash1 == hash3} {'✓' if hash1 == hash3 else '✗'}")
    
    # All should have same hash
    stats = get_cache_stats()
    print(f"\n4. Cache stats:")
    print(f"   - Total unique requests: {stats['total_unique_requests']} (Expected: 1)")
    print(f"   - Total duplicates: {stats['total_duplicate_hits']} (Expected: 2)")
    
    return stats['total_unique_requests'] == 1 and stats['total_duplicate_hits'] == 2


def test_multiple_languages():
    """Test 4: Multiple language requests"""
    print_separator("TEST 4: Multiple Language Requests")
    
    # Clear cache
    clear_cache()
    
    texts = [
        ("Hello, how are you?", {"language": {"code": "en"}}),
        ("Namaste, aap kaise hain?", {"language": {"code": "hin"}}),
        ("Mi majhyat ahe", {"language": {"code": "mar"}}),
        ("Bonjour, comment allez-vous?", {"language": {"code": "fr"}}),
        ("¿Hola, cómo estás?", {"language": {"code": "es"}})
    ]
    
    print(f"Storing {len(texts)} requests in different languages...\n")
    
    for i, (text, response) in enumerate(texts, 1):
        is_dup, hash_val = store_request(text, response)
        lang = response['language']['code']
        print(f"{i}. {lang.upper()}: '{text[:40]}...' → Hash: {hash_val[:8]}...")
    
    # Get statistics
    stats = get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"   - Total unique requests: {stats['total_unique_requests']}")
    print(f"   - Expected: {len(texts)}")
    print(f"   - Match: {'✓' if stats['total_unique_requests'] == len(texts) else '✗'}")
    
    return stats['total_unique_requests'] == len(texts)


def test_cache_statistics():
    """Test 5: Cache statistics and top requests"""
    print_separator("TEST 5: Cache Statistics and Top Requests")
    
    # Clear and add some requests with duplicates
    clear_cache()
    
    # Popular request (5 times)
    popular_text = "What's the weather today?"
    for i in range(5):
        store_request(popular_text, {"language": {"code": "en"}, "sentiment": {"label": "neutral"}})
    
    # Medium popularity (3 times)
    medium_text = "I love this product!"
    for i in range(3):
        store_request(medium_text, {"language": {"code": "en"}, "sentiment": {"label": "positive"}})
    
    # One-time requests
    store_request("Unique request 1", {"language": {"code": "en"}})
    store_request("Unique request 2", {"language": {"code": "en"}})
    
    # Get statistics
    stats = get_cache_stats()
    
    print("Cache Statistics:")
    print(f"   - Total unique requests: {stats['total_unique_requests']}")
    print(f"   - Total duplicate hits: {stats['total_duplicate_hits']}")
    print(f"   - Cache hit rate: {stats['cache_hit_rate']:.2%}")
    
    print(f"\nTop Requested Texts:")
    for i, req in enumerate(stats['top_requested'], 1):
        print(f"   {i}. '{req['text'][:40]}...'")
        print(f"      - Request count: {req['request_count']}")
        print(f"      - Last timestamp: {req['last_timestamp']}")
    
    # Verify
    top_text = stats['top_requested'][0]['text']
    top_count = stats['top_requested'][0]['request_count']
    
    print(f"\nVerification:")
    print(f"   - Most requested has count {top_count} (Expected: 5) {'✓' if top_count == 5 else '✗'}")
    
    return top_count == 5


def test_remove_entry():
    """Test 6: Remove specific cache entry"""
    print_separator("TEST 6: Remove Specific Cache Entry")
    
    text_to_remove = "Remove me please"
    text_to_keep = "Keep me please"
    
    # Store both
    store_request(text_to_remove, {"language": {"code": "en"}})
    store_request(text_to_keep, {"language": {"code": "en"}})
    
    stats_before = get_cache_stats()
    print(f"Before removal:")
    print(f"   - Total requests: {stats_before['total_unique_requests']}")
    
    # Remove one
    removed = remove_request(text_to_remove)
    print(f"\nRemoved: {removed} {'✓' if removed else '✗'}")
    
    stats_after = get_cache_stats()
    print(f"\nAfter removal:")
    print(f"   - Total requests: {stats_after['total_unique_requests']}")
    print(f"   - Difference: {stats_before['total_unique_requests'] - stats_after['total_unique_requests']}")
    
    # Verify removed
    cached_removed = get_cached_response(text_to_remove)
    cached_kept = get_cached_response(text_to_keep)
    
    print(f"\nVerification:")
    print(f"   - Removed text found: {cached_removed is not None} (Expected: False) {'✓' if not cached_removed else '✗'}")
    print(f"   - Kept text found: {cached_kept is not None} (Expected: True) {'✓' if cached_kept else '✗'}")
    
    return not cached_removed and cached_kept is not None


def test_clear_cache():
    """Test 7: Clear entire cache"""
    print_separator("TEST 7: Clear Entire Cache")
    
    # Add some requests
    for i in range(10):
        store_request(f"Request {i}", {"data": i})
    
    stats_before = get_cache_stats()
    print(f"Before clearing:")
    print(f"   - Total requests: {stats_before['total_unique_requests']}")
    
    # Clear
    success = clear_cache()
    print(f"\nCache cleared: {success} {'✓' if success else '✗'}")
    
    stats_after = get_cache_stats()
    print(f"\nAfter clearing:")
    print(f"   - Total requests: {stats_after['total_unique_requests']}")
    print(f"   - Expected: 0")
    print(f"   - Match: {'✓' if stats_after['total_unique_requests'] == 0 else '✗'}")
    
    return stats_after['total_unique_requests'] == 0


def run_all_tests():
    """Run all tests and show results"""
    print("\n")
    print("="*80)
    print("  REQUEST CACHE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    tests = [
        ("Basic Caching", test_basic_caching),
        ("Duplicate Detection", test_duplicate_detection),
        ("Case Insensitivity", test_case_insensitivity),
        ("Multiple Languages", test_multiple_languages),
        ("Cache Statistics", test_cache_statistics),
        ("Remove Entry", test_remove_entry),
        ("Clear Cache", test_clear_cache)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {str(e)}")
            results.append((name, False))
    
    # Summary
    print_separator("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("Test Results:")
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe request cache system is working correctly.")
        print("Check 'data/analyze_cache.json' to see the cached data.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    print_separator()


if __name__ == "__main__":
    run_all_tests()
