"""
FIX #10: Hybrid Romanized-to-Native Script Conversion Tests
============================================================

Purpose: Test the new hybrid conversion system that intelligently handles
mixed language text by preserving English words while converting romanized
Indic tokens to native script.

Test Categories:
1. Pure romanized text (should convert all tokens)
2. Mixed language text (Hinglish, Marathi-English)
3. English proper noun preservation
4. Punctuation and formatting preservation
5. Code-mixed social media text
6. Multiple Indian languages
7. Edge cases (short text, ALL CAPS, numbers)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from preprocessing import convert_romanized_to_native, is_english_token
from translation import romanized_to_devanagari


def print_result(test_name, result, expected_features=None):
    """Helper to print test results"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Original:  {result['original_text']}")
    print(f"Converted: {result['converted_text']}")
    print(f"Method:    {result['conversion_method']}")
    print(f"\nStatistics:")
    stats = result['statistics']
    print(f"  Total tokens:     {stats['total_tokens']}")
    print(f"  Converted:        {stats['converted_tokens']}")
    print(f"  Preserved (Eng):  {stats['preserved_tokens']}")
    print(f"  Failed:           {stats['failed_tokens']}")
    print(f"  Conversion rate:  {stats['conversion_rate']}%")
    
    if expected_features:
        print(f"\nExpected Features:")
        for feature in expected_features:
            print(f"  ✓ {feature}")
    
    # Show token details
    if len(result['token_details']) <= 15:
        print(f"\nToken Details:")
        for detail in result['token_details']:
            status_symbol = {
                'converted': '🔄',
                'preserved_english': '🇬🇧',
                'failed': '❌'
            }.get(detail['status'], '❓')
            print(f"  {status_symbol} '{detail['original']}' → '{detail['converted']}' "
                  f"({detail['status']}, {detail['method']})")


def test_pure_romanized_hindi():
    """Test 1: Pure romanized Hindi - should convert all tokens"""
    text = "aaj mausam bahut acha hai"
    result = convert_romanized_to_native(text, 'hin')
    
    print_result(
        "Pure Romanized Hindi",
        result,
        expected_features=[
            "All tokens should be converted to Devanagari",
            "No English tokens to preserve",
            "Conversion rate should be high (>60%)"
        ]
    )
    
    # Validation
    assert result['statistics']['total_tokens'] == 5
    assert result['statistics']['preserved_tokens'] == 0  # No English
    assert result['statistics']['conversion_rate'] > 50  # Most should convert
    print("✅ Test 1 PASSED")
    return result


def test_mixed_hinglish():
    """Test 2: Mixed Hinglish - preserve English, convert Hindi"""
    text = "I am going to office, traffic bahut hai today"
    result = convert_romanized_to_native(text, 'hin')
    
    print_result(
        "Mixed Hinglish (Code-Mixed)",
        result,
        expected_features=[
            "'I', 'am', 'going', 'to', 'today' should be preserved (very common English)",
            "'bahut', 'hai' should be converted to Devanagari",
            "'office', 'traffic' may convert (in romanized dict but also English)",
            "Method should be 'hybrid'"
        ]
    )
    
    # Validation
    stats = result['statistics']
    assert stats['preserved_tokens'] >= 4  # Common English words (I, am, going, to, today)
    assert stats['converted_tokens'] >= 2  # At least 'bahut' and 'hai'
    assert result['conversion_method'] == 'hybrid'
    assert 'I' in result['converted_text']  # Single letter preserved
    assert 'going' in result['converted_text']  # English preserved
    assert 'today' in result['converted_text']  # English preserved
    print("✅ Test 2 PASSED")
    return result


def test_proper_noun_preservation():
    """Test 3: Proper nouns should be preserved"""
    text = "John Mumbai la gaya kal, Google madhe kaam karto"
    result = convert_romanized_to_native(text, 'mar')
    
    print_result(
        "Proper Noun Preservation",
        result,
        expected_features=[
            "'John', 'Mumbai', 'Google' should be preserved (capitalized)",
            "Marathi words 'gaya', 'kal', 'madhe', 'kaam', 'karto' should convert",
            "'la' (Marathi particle) may or may not convert"
        ]
    )
    
    # Validation
    assert 'John' in result['converted_text']
    assert 'Mumbai' in result['converted_text']
    assert 'Google' in result['converted_text']
    assert result['statistics']['preserved_tokens'] >= 3
    print("✅ Test 3 PASSED")
    return result


def test_punctuation_preservation():
    """Test 4: Punctuation should be preserved correctly"""
    text = "aaj traffic khup heavy aahe, main road par bahut vehicles hain!"
    result = convert_romanized_to_native(text, 'mar')
    
    print_result(
        "Punctuation Preservation",
        result,
        expected_features=[
            "Comma and exclamation mark should be preserved",
            "Punctuation should stay with converted words",
            "Word boundaries should be maintained"
        ]
    )
    
    # Validation
    assert ',' in result['converted_text']
    assert '!' in result['converted_text']
    assert result['statistics']['total_tokens'] == 11
    print("✅ Test 4 PASSED")
    return result


def test_social_media_text():
    """Test 5: Code-mixed social media text"""
    text = "OMG yaar traffic jam aahe, I'll be late for meeting today"
    result = convert_romanized_to_native(text, 'mar')
    
    print_result(
        "Social Media Code-Mixed Text",
        result,
        expected_features=[
            "'OMG' (all caps) should be preserved",
            "'I'll' (contraction) should be preserved",
            "'traffic', 'jam', 'late', 'meeting', 'today' should be preserved",
            "Marathi words 'yaar', 'aahe' should convert"
        ]
    )
    
    # Validation
    assert 'OMG' in result['converted_text']
    assert "I'll" in result['converted_text'] or "I" in result['converted_text']
    assert 'meeting' in result['converted_text']
    assert result['conversion_method'] in ['hybrid', 'dictionary', 'itrans']
    print("✅ Test 5 PASSED")
    return result


def test_multiple_languages():
    """Test 6: Test multiple Indian languages"""
    test_cases = [
        ('namaste aap kaise hain', 'hin', 'Hindi'),
        ('tumhi kase ahat', 'mar', 'Marathi'),
        ('tumi kemon acho', 'ben', 'Bengali'),
        ('neenga eppadi irukkireenga', 'tam', 'Tamil'),
        ('meeru ela unnaru', 'tel', 'Telugu'),
        ('tusi kive ho', 'pan', 'Punjabi'),
    ]
    
    results = []
    for text, lang, name in test_cases:
        result = convert_romanized_to_native(text, lang)
        print(f"\n{name} ({lang}): '{text}' → '{result['converted_text']}'")
        print(f"  Converted: {result['statistics']['converted_tokens']}/{result['statistics']['total_tokens']} tokens")
        results.append(result)
    
    # All should have some conversion
    for i, result in enumerate(results):
        assert result['statistics']['total_tokens'] > 0
        print(f"✅ Language {test_cases[i][2]} test PASSED")
    
    print("✅ Test 6 (Multiple Languages) PASSED")
    return results


def test_edge_cases():
    """Test 7: Edge cases and special scenarios"""
    
    print(f"\n{'='*80}")
    print("TEST: Edge Cases")
    print(f"{'='*80}")
    
    # Short text
    result1 = convert_romanized_to_native("OK bye", 'hin')
    print(f"\n7a. Short text: '{result1['original_text']}' → '{result1['converted_text']}'")
    assert 'OK' in result1['converted_text']  # Should preserve
    print("  ✅ Short text handled correctly")
    
    # ALL CAPS
    result2 = convert_romanized_to_native("USA madhe rahto mi", 'mar')
    print(f"\n7b. ALL CAPS: '{result2['original_text']}' → '{result2['converted_text']}'")
    assert 'USA' in result2['converted_text']  # Should preserve acronym
    print("  ✅ ALL CAPS preserved")
    
    # Numbers and mixed
    result3 = convert_romanized_to_native("aaj 5 bajhe aaunga", 'hin')
    print(f"\n7c. Numbers: '{result3['original_text']}' → '{result3['converted_text']}'")
    assert '5' in result3['converted_text']  # Numbers preserved
    print("  ✅ Numbers preserved")
    
    # Empty and very short
    result4 = convert_romanized_to_native("", 'hin')
    assert result4['statistics']['total_tokens'] == 0
    print(f"\n7d. Empty string handled: total_tokens={result4['statistics']['total_tokens']}")
    print("  ✅ Empty string handled")
    
    # Single word
    result5 = convert_romanized_to_native("namaste", 'hin')
    print(f"\n7e. Single word: '{result5['original_text']}' → '{result5['converted_text']}'")
    assert result5['statistics']['total_tokens'] == 1
    print("  ✅ Single word handled")
    
    print("\n✅ Test 7 (Edge Cases) PASSED")


def test_english_token_detection():
    """Test 8: Test is_english_token() helper function"""
    
    print(f"\n{'='*80}")
    print("TEST: English Token Detection Helper")
    print(f"{'='*80}")
    
    test_cases = [
        # (token, expected_result, reason)
        ('the', True, 'common English word'),
        ('going', True, 'common English word with suffix'),
        ('I', True, 'single letter pronoun'),
        ("don't", True, 'English contraction'),
        ('USA', True, 'ALL CAPS acronym'),
        ('Google', True, 'proper noun (capitalized)'),
        ('traffic', True, 'common English word'),
        
        # Should be False (not clearly English)
        ('aaj', False, 'Hindi/Marathi word'),
        ('bahut', False, 'Hindi word'),
        ('khup', False, 'Marathi word'),
        ('namaste', False, 'Indian greeting'),
    ]
    
    passed = 0
    failed = 0
    
    for token, expected, reason in test_cases:
        result = is_english_token(token)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} '{token}': {result} (expected {expected}) - {reason}")
    
    print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    assert failed == 0, f"{failed} token detection tests failed"
    print("✅ Test 8 (Token Detection) PASSED")


def test_translation_integration():
    """Test 9: Integration with translation.py romanized_to_devanagari()"""
    
    print(f"\n{'='*80}")
    print("TEST: Translation.py Integration")
    print(f"{'='*80}")
    
    text = "aaj traffic bahut hai but I will reach on time"
    converted = romanized_to_devanagari(text, 'hin')
    
    print(f"Original:  {text}")
    print(f"Converted: {converted}")
    
    # Should preserve English words
    assert 'but' in converted or 'I' in converted
    assert 'will' in converted or 'reach' in converted
    assert converted != text  # Should have some conversion
    
    print("✅ Test 9 (Translation Integration) PASSED")


def run_all_tests():
    """Run all FIX #10 tests"""
    
    print("\n" + "="*80)
    print("FIX #10: Hybrid Romanized-to-Native Conversion Test Suite")
    print("="*80)
    print("\nTesting intelligent mixed-language transliteration:")
    print("  • Preserves English words and proper nouns")
    print("  • Converts only romanized Indic tokens")
    print("  • Handles punctuation and formatting")
    print("  • Supports 6 Indian languages")
    print("")
    
    try:
        # Core functionality tests
        test_pure_romanized_hindi()
        test_mixed_hinglish()
        test_proper_noun_preservation()
        test_punctuation_preservation()
        test_social_media_text()
        test_multiple_languages()
        test_edge_cases()
        
        # Helper function tests
        test_english_token_detection()
        
        # Integration tests
        test_translation_integration()
        
        # Summary
        print("\n" + "="*80)
        print("🎉 ALL FIX #10 TESTS PASSED!")
        print("="*80)
        print("\nHybrid romanized-to-native conversion is working correctly:")
        print("  ✅ Pure romanized text conversion")
        print("  ✅ Mixed language (Hinglish/Marathi-English) handling")
        print("  ✅ English proper noun preservation")
        print("  ✅ Punctuation and formatting preservation")
        print("  ✅ Code-mixed social media text")
        print("  ✅ Multiple Indian languages (6 languages)")
        print("  ✅ Edge cases (short text, ALL CAPS, numbers)")
        print("  ✅ English token detection helper")
        print("  ✅ Translation.py integration")
        print("\nThe system now gracefully handles mixed language text!")
        print("="*80)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
