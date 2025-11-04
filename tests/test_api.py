"""
Quick API Test Script
Run this after starting the API server to verify it works
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing /health endpoint...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        result = response.json()
        
        print(f"Status: {result['status']}")
        print(f"Version: {result['version']}")
        print(f"Features Available:")
        for feature, available in result['features'].items():
            status = "✓" if available else "✗"
            print(f"  [{status}] {feature}")
        
        assert response.status_code == 200
        print("\n✓ Health check passed!")
        return True
    except Exception as e:
        print(f"\n✗ Health check failed: {e}")
        return False


def test_comprehensive_analysis():
    """Test comprehensive analysis endpoint"""
    print("\n2. Testing /analyze endpoint (Comprehensive Analysis)...")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={
                "text": "This is a wonderful product! I highly recommend it.",
                "check_profanity": True,
                "detect_domains": True
            }
        )
        
        result = response.json()
        
        print(f"Text: {result['original_text']}")
        print(f"Language: {result['language']['language']} ({result['language']['confidence']:.2%})")
        print(f"Sentiment: {result['sentiment']['label']} ({result['sentiment']['confidence']:.2%})")
        print(f"Profanity: {'Detected' if result['profanity']['has_profanity'] else 'Clean'}")
        print(f"Domains: {', '.join([d for d, v in result['domains'].items() if v]) or 'General'}")
        
        assert response.status_code == 200
        assert 'sentiment' in result
        assert 'profanity' in result
        assert 'domains' in result
        print("\n✓ Comprehensive analysis passed!")
        return True
    except Exception as e:
        print(f"\n✗ Comprehensive analysis failed: {e}")
        return False


def test_profanity():
    """Test profanity detection endpoint"""
    print("\n3. Testing /profanity endpoint...")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/profanity",
            json={"text": "This fucking product is shit!"}
        )
        
        result = response.json()
        
        print(f"Text: {result['text']}")
        print(f"Has Profanity: {result['has_profanity']}")
        print(f"Severity: {result['severity']} (score: {result['severity_score']})")
        print(f"Detected Words: {result['detected_words']}")
        print(f"Censored: {result['censored_text']}")
        
        assert response.status_code == 200
        assert result['has_profanity'] == True
        print("\n✓ Profanity detection passed!")
        return True
    except Exception as e:
        print(f"\n✗ Profanity detection failed: {e}")
        return False


def test_sentiment():
    """Test sentiment analysis endpoint"""
    print("\n4. Testing /sentiment endpoint...")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/sentiment",
            json={"text": "This movie is absolutely amazing! I loved every moment."}
        )
        
        result = response.json()
        
        print(f"Text: {result['text']}")
        print(f"Language: {result['language']}")
        print(f"Sentiment: {result['sentiment']['label']} ({result['sentiment']['confidence']:.2%})")
        print(f"Model: {result['sentiment']['model_used']}")
        
        assert response.status_code == 200
        assert result['sentiment']['label'] == 'positive'
        print("\n✓ Sentiment analysis passed!")
        return True
    except Exception as e:
        print(f"\n✗ Sentiment analysis failed: {e}")
        return False


def test_domains():
    """Test domain detection endpoint"""
    print("\n5. Testing /domains endpoint...")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/domains",
            json={"text": "The stock price increased by $50. Meeting tomorrow at 3 PM."}
        )
        
        result = response.json()
        
        print(f"Text: {result['text']}")
        print(f"Detected Domains:")
        for domain, detected in result['domains'].items():
            status = "✓" if detected else "✗"
            print(f"  [{status}] {domain}")
        
        if result['domains']['financial']:
            print(f"Financial Entities: {result['entities']['financial']}")
        if result['domains']['temporal']:
            print(f"Temporal Entities: {result['entities']['temporal']}")
        
        assert response.status_code == 200
        print("\n✓ Domain detection passed!")
        return True
    except Exception as e:
        print(f"\n✗ Domain detection failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("FASTAPI NLP API - QUICK TEST SUITE")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print("\nMake sure the API is running:")
    print("  python api.py")
    print("\nOr:")
    print("  uvicorn api:app --reload")
    print("=" * 60)
    
    # Wait for user confirmation
    input("\nPress Enter when API is running... ")
    
    results = []
    
    # Run all tests
    results.append(("Health Check", test_health()))
    results.append(("Comprehensive Analysis", test_comprehensive_analysis()))
    results.append(("Profanity Detection", test_profanity()))
    results.append(("Sentiment Analysis", test_sentiment()))
    results.append(("Domain Detection", test_domains()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print("=" * 60)
    print(f"Results: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! API is working correctly.")
        print("\nNext steps:")
        print("  1. Open http://localhost:8000/docs for interactive API docs")
        print("  2. Try the /analyze endpoint with your own text")
        print("  3. Integrate the API into your application")
    else:
        print("\n⚠ Some tests failed. Check the error messages above.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
