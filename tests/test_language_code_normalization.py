"""
FIX #6: Test Language Code Normalization
Tests the robust language code mapping system that normalizes
GLotLID variants (hif, urd, snd) to canonical forms (hin, mar, etc.)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from preprocessing import normalize_language_code, get_language_display_name, detect_language

def test_normalization_mapping():
    """Test the LANGUAGE_CODE_NORMALIZATION mapping"""
    print("\n" + "="*80)
    print("TEST 1: Normalization Mapping")
    print("="*80)
    
    test_cases = [
        # Hindi variants
        ('hif', 'hin', 'Fiji Hindi → Hindi'),
        ('bho', 'hin', 'Bhojpuri → Hindi'),
        ('urd', 'hin', 'Urdu → Hindi'),
        ('ur', 'hin', 'Urdu (2-letter) → Hindi'),
        
        # Marathi variants
        ('mr', 'mar', 'Marathi 2-letter → 3-letter'),
        
        # Sindhi variants
        ('sd', 'sin', 'Sindhi 2-letter → 3-letter'),
        ('snd', 'sin', 'Sindhi variant → 3-letter'),
        
        # Obscure languages → unknown
        ('ido', 'unknown', 'Ido (constructed) → unknown'),
        ('jbo', 'unknown', 'Lojban → unknown'),
        ('luo', 'unknown', 'Luo (rare) → unknown'),
        ('zxx', 'unknown', 'No linguistic content → unknown'),
        ('und', 'unknown', 'Undetermined → unknown'),
        
        # Already canonical
        ('hin', 'hin', 'Hindi already canonical'),
        ('eng', 'eng', 'English already canonical'),
        ('mar', 'mar', 'Marathi already canonical'),
    ]
    
    passed = 0
    failed = 0
    
    for input_code, expected, description in test_cases:
        result = normalize_language_code(input_code, keep_suffixes=False)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"   Input: '{input_code}' → Expected: '{expected}', Got: '{result}'")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0

def test_normalization_with_suffixes():
    """Test normalization with suffixes like _mixed, _roman"""
    print("\n" + "="*80)
    print("TEST 2: Normalization with Suffixes")
    print("="*80)
    
    test_cases = [
        # Keep suffixes
        ('hif_mixed', 'hin_mixed', True, 'Fiji Hindi mixed → Hindi mixed (keep suffix)'),
        ('urd_roman', 'hin_roman', True, 'Urdu roman → Hindi roman (keep suffix)'),
        ('hin_mixed', 'hin_mixed', True, 'Hindi mixed → Hindi mixed (no change)'),
        
        # Remove suffixes
        ('hif_mixed', 'hin', False, 'Fiji Hindi mixed → Hindi (remove suffix)'),
        ('urd_roman', 'hin', False, 'Urdu roman → Hindi (remove suffix)'),
        ('hin_eng_mixed', 'hin', False, 'Hindi-English mixed → Hindi (remove suffix)'),
    ]
    
    passed = 0
    failed = 0
    
    for input_code, expected, keep_suffixes, description in test_cases:
        result = normalize_language_code(input_code, keep_suffixes=keep_suffixes)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"   Input: '{input_code}' (keep_suffixes={keep_suffixes}) → Expected: '{expected}', Got: '{result}'")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0

def test_display_names():
    """Test language display name generation"""
    print("\n" + "="*80)
    print("TEST 3: Display Name Generation")
    print("="*80)
    
    test_cases = [
        ('hin', 'Hindi'),
        ('hif', 'Hindi'),  # Normalized first
        ('urd', 'Hindi'),  # Normalized first
        ('mar', 'Marathi'),
        ('eng', 'English'),
        ('unknown', 'Unknown'),
        ('ido', 'Unknown'),  # Obscure → unknown → Unknown
    ]
    
    passed = 0
    failed = 0
    
    for input_code, expected_name in test_cases:
        result = get_language_display_name(input_code)
        status = "✅ PASS" if result == expected_name else "❌ FAIL"
        
        if result == expected_name:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | '{input_code}' → Expected: '{expected_name}', Got: '{result}'")
    
    print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0

def test_end_to_end_detection():
    """Test full detection pipeline with normalization"""
    print("\n" + "="*80)
    print("TEST 4: End-to-End Detection with Normalization")
    print("="*80)
    
    test_cases = [
        # These would require actual GLotLID model to test properly
        # For now, we test that the API doesn't break
        ("Hello world", "Basic English text"),
        ("नमस्ते दुनिया", "Hindi Devanagari text"),
        ("आपण कसे आहात?", "Marathi Devanagari text"),
    ]
    
    print("\nℹ️  Note: This test verifies API doesn't break with normalization.")
    print("   Actual GLotLID variant detection requires model to be loaded.\n")
    
    passed = 0
    
    for text, description in test_cases:
        try:
            result = detect_language(text, detailed=True)
            
            print(f"✅ PASS | {description}")
            print(f"   Text: '{text}'")
            print(f"   Detected: {result['language']} (confidence: {result['confidence']:.2f})")
            
            # Verify result has required keys
            assert 'language' in result, "Missing 'language' key"
            assert 'original_language' in result, "Missing 'original_language' key (FIX #6)"
            assert 'confidence' in result, "Missing 'confidence' key"
            assert 'language_info' in result, "Missing 'language_info' key"
            
            passed += 1
            
        except Exception as e:
            print(f"❌ FAIL | {description}")
            print(f"   Error: {str(e)}")
    
    print(f"\n📊 Results: {passed} passed out of {len(test_cases)} tests")
    return passed == len(test_cases)

def run_all_tests():
    """Run all normalization tests"""
    print("\n" + "="*80)
    print("FIX #6: LANGUAGE CODE NORMALIZATION TEST SUITE")
    print("="*80)
    print("Testing robust mapping of GLotLID variants to canonical codes")
    print("="*80)
    
    results = []
    
    results.append(("Normalization Mapping", test_normalization_mapping()))
    results.append(("Normalization with Suffixes", test_normalization_with_suffixes()))
    results.append(("Display Name Generation", test_display_names()))
    results.append(("End-to-End Detection", test_end_to_end_detection()))
    
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} | {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Language code normalization is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the output above.")
    print("="*80)
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
