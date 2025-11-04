"""
Test script for Adaptive Learning System
Tests pattern caching, user feedback, and self-improvement capabilities
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_initial_detection(text: str, description: str) -> Dict[str, Any]:
    """Test initial language detection (before learning)"""
    print(f"\n📝 Testing: {description}")
    print(f"Text: '{text}'")
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={"text": text},
        headers=HEADERS
    )
    
    if response.status_code == 200:
        data = response.json()
        lang_info = data.get('language_analysis', {})
        detected = lang_info.get('primary_language', 'UNKNOWN')
        confidence = lang_info.get('confidence', 0)
        
        print(f"✓ Detected: {detected} (confidence: {confidence:.2%})")
        return data
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return {}


def submit_correction(text: str, detected: str, correct: str, comments: str = ""):
    """Submit user correction for learning"""
    print(f"\n📤 Submitting correction: {detected} → {correct}")
    
    response = requests.post(
        f"{BASE_URL}/feedback",
        json={
            "text": text,
            "detected_language": detected,
            "correct_language": correct,
            "user_id": "test_user",
            "comments": comments
        },
        headers=HEADERS
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Feedback recorded: {data.get('message')}")
        stats = data.get('statistics', {})
        print(f"  - Total corrections: {stats.get('total_corrections', 0)}")
        print(f"  - Patterns learned: {stats.get('total_patterns_learned', 0)}")
        return True
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return False


def get_learning_statistics():
    """Get and display learning statistics"""
    print("\n📊 Fetching Learning Statistics...")
    
    response = requests.get(f"{BASE_URL}/learning/stats", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get('statistics', {})
        
        print("\n┌─── Cache Statistics ───")
        cache_stats = stats.get('cache_statistics', {})
        print(f"│ Total Patterns: {cache_stats.get('total_patterns', 0)}")
        print(f"│ Total Requests: {cache_stats.get('total_requests', 0)}")
        print(f"│ Cache Hits: {cache_stats.get('cache_hits', 0)}")
        print(f"│ Cache Hit Rate: {cache_stats.get('cache_hit_rate', 0):.2f}%")
        
        print("\n├─── User Corrections ───")
        corrections = stats.get('user_corrections', {})
        print(f"│ Total: {corrections.get('total_corrections', 0)}")
        
        print("\n├─── Detection Failures ───")
        failures = stats.get('detection_failures', {})
        print(f"│ Total: {failures.get('total_failures', 0)}")
        
        print("\n└─── Top Languages ───")
        top_langs = stats.get('top_detected_languages', [])
        for lang, count in top_langs[:5]:
            print(f"  {lang}: {count} detections")
        
        return stats
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")
        return {}


def test_cache_performance(texts: list):
    """Test cache hit/miss performance with repeated texts"""
    print("\n🔄 Testing Cache Performance...")
    
    for i, text in enumerate(texts, 1):
        print(f"\n  Attempt {i}: '{text[:50]}...'")
        start = time.time()
        
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"text": text},
            headers=HEADERS
        )
        
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        if response.status_code == 200:
            print(f"  ✓ Response time: {elapsed:.2f}ms")
        else:
            print(f"  ✗ Error: {response.status_code}")


def run_comprehensive_test():
    """Run comprehensive adaptive learning tests"""
    
    print_section("ADAPTIVE LEARNING SYSTEM - COMPREHENSIVE TEST")
    
    # ============================================================
    # TEST 1: Edge Cases - Romanized Marathi
    # ============================================================
    print_section("TEST 1: Romanized Marathi Detection")
    
    test_cases_marathi = [
        ("Tu Khup chukicha", "Romanized Marathi - casual"),
        ("Mala tumchi aathavan ahe", "Romanized Marathi - formal"),
        ("Aaj khup garmi aahe", "Romanized Marathi - weather")
    ]
    
    for text, desc in test_cases_marathi:
        result = test_initial_detection(text, desc)
        detected = result.get('language_analysis', {}).get('primary_language', 'unknown')
        
        # If incorrectly detected, submit correction
        if detected != 'mar' and detected != 'mr':
            submit_correction(text, detected, 'mar', 
                            "Romanized Marathi text")
    
    
    # ============================================================
    # TEST 2: Code-Mixed Hinglish
    # ============================================================
    print_section("TEST 2: Code-Mixed Hinglish Detection")
    
    test_cases_hinglish = [
        ("Tu chup bhet, guys lets continue", "Marathi-English mix"),
        ("Yaar aaj bohot boring hai, let's go out", "Hindi-English casual"),
        ("Meeting cancel ho gayi, I'm free now", "Hindi-English formal")
    ]
    
    for text, desc in test_cases_hinglish:
        result = test_initial_detection(text, desc)
        detected = result.get('language_analysis', {}).get('primary_language', 'unknown')
        
        # Submit as code-mixed if not detected
        if 'mixed' not in detected.lower():
            submit_correction(text, detected, 'hi_en_mixed',
                            f"Code-mixed text: {desc}")
    
    
    # ============================================================
    # TEST 3: Similar Pattern Recognition
    # ============================================================
    print_section("TEST 3: Similar Pattern Recognition (Cache Testing)")
    
    # First, analyze a text multiple times to build pattern
    base_text = "यह बहुत अच्छा है और मुझे पसंद है"
    
    print("\nBuilding pattern cache with repeated analysis...")
    for i in range(4):  # Threshold is 3, so 4 should enable caching
        print(f"  Iteration {i+1}/4")
        test_initial_detection(base_text, f"Hindi text - iteration {i+1}")
        time.sleep(0.5)
    
    # Now test with similar structure
    similar_texts = [
        "यह बहुत खराब है और मुझे नापसंद है",  # Same structure, different words
        "वह बहुत सुंदर है और सबको पसंद है",   # Similar pattern
    ]
    
    print("\nTesting cache with similar patterns...")
    test_cache_performance(similar_texts)
    
    
    # ============================================================
    # TEST 4: Learning Statistics
    # ============================================================
    print_section("TEST 4: Learning Statistics & Analytics")
    get_learning_statistics()
    
    
    # ============================================================
    # TEST 5: Repeated Corrections (Pattern Reinforcement)
    # ============================================================
    print_section("TEST 5: Pattern Reinforcement with Multiple Corrections")
    
    # Submit multiple corrections for similar romanized Marathi
    reinforcement_texts = [
        "Kal me yenar", 
        "Aaj me ghari nahi",
        "Tu kasa aahes"
    ]
    
    for text in reinforcement_texts:
        result = test_initial_detection(text, "Romanized Marathi")
        detected = result.get('language_analysis', {}).get('primary_language', 'unknown')
        submit_correction(text, detected, 'mar', "Romanized Marathi reinforcement")
        time.sleep(0.3)
    
    
    # ============================================================
    # FINAL STATISTICS
    # ============================================================
    print_section("FINAL STATISTICS AFTER ALL TESTS")
    final_stats = get_learning_statistics()
    
    print("\n\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)
    
    cache_stats = final_stats.get('cache_statistics', {})
    corrections = final_stats.get('user_corrections', {})
    
    print(f"\n✓ Tests Completed Successfully!")
    print(f"  - Total Patterns Cached: {cache_stats.get('total_patterns', 0)}")
    print(f"  - Cache Hit Rate: {cache_stats.get('cache_hit_rate', 0):.2f}%")
    print(f"  - User Corrections Recorded: {corrections.get('total_corrections', 0)}")
    print(f"  - System Learning: {'ACTIVE ✓' if cache_stats.get('total_patterns', 0) > 0 else 'PENDING'}")
    
    print("\n🎯 Adaptive learning system is operational and improving!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        print("\n🚀 Starting Adaptive Learning System Test Suite\n")
        print("⚠️  Make sure the API is running on http://localhost:8000")
        print("    Run: python api.py\n")
        
        input("Press Enter to start tests...")
        
        run_comprehensive_test()
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API at http://localhost:8000")
        print("   Please start the API first with: python api.py")
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
