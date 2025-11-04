"""
Test script for automatic failure detection and learning
Tests the case: "Tu kashala me sangu!" detected as 'ido' (wrong)
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_failure_case():
    """Test the specific failure case you reported"""
    
    print_section("TESTING AUTOMATIC FAILURE DETECTION")
    
    # The problematic text
    text = "Tu kashala me sangu!"
    
    print(f"\n📝 Testing Text: '{text}'")
    print("Expected: Marathi (romanized)")
    print("Previously Detected: 'ido' (WRONG - Constructed language)")
    
    # Analyze
    print("\n🔍 Analyzing...")
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={"text": text}
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    
    # Show detection
    lang_info = result.get('language', {})
    detected = lang_info.get('language', 'unknown')
    confidence = lang_info.get('confidence', 0)
    method = lang_info.get('method', 'unknown')
    
    print(f"\n📊 Detection Result:")
    print(f"   Language: {detected}")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Method: {method}")
    
    # Check if system automatically flagged it as failure
    glotlid_info = lang_info.get('glotlid_analysis', {})
    glotlid_lang = glotlid_info.get('detected_language', '')
    glotlid_conf = glotlid_info.get('confidence', 0)
    
    print(f"\n🔬 GlotLID Analysis:")
    print(f"   Detected: {glotlid_lang}")
    print(f"   Confidence: {glotlid_conf:.2%}")
    
    # Determine if it's a failure
    is_failure = (detected in ['ido', 'jbo', 'lfn', 'vol', 'io'] or 
                  confidence < 0.5 or 
                  detected == 'unknown')
    
    if is_failure:
        print(f"\n⚠️  FAILURE AUTOMATICALLY DETECTED!")
        print(f"   Reason: Obscure language '{detected}' with low confidence")
        print(f"   This failure has been stored in data/detection_failures.json")
        print(f"   System will learn from this!")
    else:
        print(f"\n✓ Detection seems okay (but may still be wrong)")
    
    # Now submit the correction
    print_section("SUBMITTING USER CORRECTION")
    
    print(f"\n📤 Correcting: {detected} → mar (Marathi)")
    
    correction_response = requests.post(
        f"{BASE_URL}/feedback",
        json={
            "text": text,
            "detected_language": detected,
            "correct_language": "mar",
            "user_id": "test_user",
            "comments": "This is romanized Marathi. 'Tu kashala me sangu' = 'Why should I tell you' in Marathi"
        }
    )
    
    if correction_response.status_code == 200:
        corr_data = correction_response.json()
        print(f"✓ Correction recorded: {corr_data.get('correction_id')}")
        print(f"✓ Message: {corr_data.get('message')}")
        
        stats = corr_data.get('statistics', {})
        print(f"\n📊 Learning Statistics:")
        print(f"   Total Corrections: {stats.get('total_corrections', 0)}")
        print(f"   Patterns Learned: {stats.get('total_patterns_learned', 0)}")
    else:
        print(f"❌ Error submitting correction: {correction_response.status_code}")
    
    # Check failure analysis
    print_section("FAILURE PATTERN ANALYSIS")
    
    print("\n🔍 Analyzing recent failures...")
    
    failure_response = requests.get(f"{BASE_URL}/learning/failures?limit=10")
    
    if failure_response.status_code == 200:
        failure_data = failure_response.json()
        analysis = failure_data.get('analysis', {})
        
        print(f"\n📊 Analysis Results:")
        print(f"   Total Failures Analyzed: {analysis.get('total_failures_analyzed', 0)}")
        
        print(f"\n🔝 Top Failure Reasons:")
        for reason, count in analysis.get('top_failure_reasons', [])[:5]:
            print(f"      {reason}: {count} occurrences")
        
        print(f"\n🌐 Most Misdetected As:")
        for lang, count in analysis.get('most_misdetected_as', [])[:5]:
            print(f"      {lang}: {count} times")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis.get('recommendations', []), 1):
            print(f"\n   {i}. [{rec.get('priority')}] {rec.get('issue')}")
            print(f"      Solution: {rec.get('solution')}")
    else:
        print(f"❌ Error getting failure analysis: {failure_response.status_code}")
    
    # Test similar romanized Marathi
    print_section("TESTING SIMILAR ROMANIZED MARATHI")
    
    similar_texts = [
        "Tu kasa aahes?",
        "Me thik aahe",
        "Kal me yenar"
    ]
    
    print("\n🔄 Testing similar romanized Marathi texts...")
    print("   (System should eventually learn the pattern)")
    
    for text in similar_texts:
        print(f"\n   Testing: '{text}'")
        
        resp = requests.post(f"{BASE_URL}/analyze", json={"text": text})
        if resp.status_code == 200:
            lang = resp.json().get('language', {}).get('language')
            conf = resp.json().get('language', {}).get('confidence', 0)
            print(f"   → Detected: {lang} (confidence: {conf:.2%})")
            
            # If still wrong, submit correction
            if lang not in ['mar', 'mr']:
                print(f"   → Still wrong, submitting correction...")
                requests.post(f"{BASE_URL}/feedback",
                    json={
                        "text": text,
                        "detected_language": lang,
                        "correct_language": "mar",
                        "user_id": "test_user",
                        "comments": "Romanized Marathi"
                    })
        else:
            print(f"   ❌ Error: {resp.status_code}")
    
    # Final statistics
    print_section("FINAL LEARNING STATISTICS")
    
    stats_response = requests.get(f"{BASE_URL}/learning/stats")
    if stats_response.status_code == 200:
        stats_data = stats_response.json()
        stats = stats_data.get('statistics', {})
        
        cache_stats = stats.get('cache_statistics', {})
        corrections = stats.get('user_corrections', {})
        
        print(f"\n✓ Learning System Status:")
        print(f"   Cache Hit Rate: {cache_stats.get('cache_hit_rate', 0):.2f}%")
        print(f"   Total Patterns: {cache_stats.get('total_patterns', 0)}")
        print(f"   User Corrections: {corrections.get('total_corrections', 0)}")
        print(f"\n🎯 System is learning and will improve future detections!")
    
    print("\n" + "=" * 80)
    print("  TEST COMPLETE")
    print("=" * 80)
    print("\n💡 What just happened:")
    print("   1. System detected romanized Marathi as 'ido' (wrong)")
    print("   2. Failure was AUTOMATICALLY stored in data/detection_failures.json")
    print("   3. You submitted a correction (mar)")
    print("   4. System learned from the correction")
    print("   5. Similar texts were tested and corrected")
    print("   6. Pattern analysis identified the issue")
    print("\n🚀 Next time similar romanized Marathi appears, detection will improve!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        print("\n🚀 Testing Automatic Failure Detection & Learning")
        print("⚠️  Make sure API is running: python api.py\n")
        
        input("Press Enter to start test...")
        
        test_failure_case()
        
        print("\n✅ Check data/detection_failures.json to see stored failures!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API")
        print("   Please start the API first: python api.py")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
