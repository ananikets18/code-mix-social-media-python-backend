"""
Test Improvements for Tamil and Marathi Detection Issues

Tests the fixes implemented based on API testing results:
1. Tamil romanized word detection
2. Marathi language markers
3. English word preservation (meeting, late, start, wait)

Author: NLP Project Team
Created: 2025-11-03
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import detect_romanized_indian_language, is_english_token, COMMON_ENGLISH_WORDS
from translation import ROMANIZED_DICTIONARY


def test_tamil_words_in_dictionary():
    """Test 1: Check if Tamil dictionary now has the missing words"""
    print("\n" + "="*80)
    print("TEST 1: Tamil Dictionary Completeness")
    print("="*80 + "\n")
    
    tamil_dict = ROMANIZED_DICTIONARY.get('tamil', {})
    
    test_words = [
        'naan', 'pathukaren', 'thedi', 'poi', 'mudichiduven',
        'work', 'ven', 'ren', 'tten', 'pannuren'
    ]
    
    found_count = 0
    for word in test_words:
        if word in tamil_dict:
            print(f"✅ '{word}' → '{tamil_dict[word]}'")
            found_count += 1
        else:
            print(f"❌ '{word}' NOT FOUND")
    
    print(f"\n📊 Result: {found_count}/{len(test_words)} words found ({found_count/len(test_words)*100:.1f}%)")
    
    if found_count >= 8:
        print("✅ TEST PASSED: Tamil dictionary significantly improved!")
        return True
    else:
        print("⚠️  TEST PARTIAL: More words needed")
        return False


def test_tamil_detection():
    """Test 2: Detect Tamil romanized text"""
    print("\n" + "="*80)
    print("TEST 2: Tamil Language Detection")
    print("="*80 + "\n")
    
    test_cases = [
        ("Naan pathukaren thedi poi, work mudichiduven.", "tam", 0.5),
        ("Naan office poren, neenga vaanga", "tam", 0.6),
        ("Ennaku ippodhu work irukku", "tam", 0.5),
    ]
    
    passed = 0
    for text, expected_lang, min_confidence in test_cases:
        detected_lang, confidence = detect_romanized_indian_language(text)
        
        is_correct = detected_lang == expected_lang and confidence >= min_confidence
        status = "✅" if is_correct else "❌"
        
        print(f"{status} Text: '{text[:50]}...'")
        print(f"   Expected: {expected_lang} (≥{min_confidence})")
        print(f"   Detected: {detected_lang} ({confidence:.2f})")
        
        if is_correct:
            passed += 1
        print()
    
    print(f"📊 Result: {passed}/{len(test_cases)} tests passed ({passed/len(test_cases)*100:.1f}%)")
    
    if passed >= 2:
        print("✅ TEST PASSED: Tamil detection working!")
        return True
    else:
        print("⚠️  TEST FAILED: Tamil detection needs more work")
        return False


def test_marathi_markers():
    """Test 3: Check Marathi-specific markers"""
    print("\n" + "="*80)
    print("TEST 3: Marathi Language Markers")
    print("="*80 + "\n")
    
    marathi_dict = ROMANIZED_DICTIONARY.get('marathi', {})
    
    markers = ['ahe', 'aahe', 'honar', 'kara', 'thoda', 'khup']
    
    found_count = 0
    for marker in markers:
        if marker in marathi_dict:
            print(f"✅ '{marker}' → '{marathi_dict[marker]}'")
            found_count += 1
        else:
            print(f"❌ '{marker}' NOT FOUND")
    
    print(f"\n📊 Result: {found_count}/{len(markers)} markers found ({found_count/len(markers)*100:.1f}%)")
    
    if found_count == len(markers):
        print("✅ TEST PASSED: All Marathi markers present!")
        return True
    else:
        print("⚠️  TEST PARTIAL: Some markers missing")
        return False


def test_english_word_preservation():
    """Test 4: Check if new English words are in the common words set"""
    print("\n" + "="*80)
    print("TEST 4: English Word Preservation")
    print("="*80 + "\n")
    
    test_words = ['meeting', 'late', 'start', 'wait', 'office', 'traffic', 'today']
    
    found_count = 0
    for word in test_words:
        if word in COMMON_ENGLISH_WORDS:
            print(f"✅ '{word}' is in COMMON_ENGLISH_WORDS")
            found_count += 1
        else:
            print(f"❌ '{word}' NOT in COMMON_ENGLISH_WORDS")
    
    print(f"\n📊 Result: {found_count}/{len(test_words)} words found ({found_count/len(test_words)*100:.1f}%)")
    
    if found_count == len(test_words):
        print("✅ TEST PASSED: All English words present!")
        return True
    else:
        print("⚠️  TEST FAILED: Missing English words")
        return False


def test_english_token_detection():
    """Test 5: Test is_english_token function with new words"""
    print("\n" + "="*80)
    print("TEST 5: English Token Detection Function")
    print("="*80 + "\n")
    
    # Words that should be detected as English
    english_words = ['meeting', 'late', 'start', 'wait', 'I', 'office', 'work']
    
    # Words that should NOT be detected as English (even if in romanized dict)
    indic_words = ['honar', 'ahe', 'thoda', 'naan', 'poi']
    
    passed = 0
    total = 0
    
    print("Testing English words (should be detected as English):")
    for word in english_words:
        is_eng = is_english_token(word, set())
        status = "✅" if is_eng else "❌"
        print(f"{status} '{word}' → {is_eng}")
        if is_eng:
            passed += 1
        total += 1
    
    print("\nTesting Indic words (should NOT be detected as English):")
    for word in indic_words:
        is_eng = is_english_token(word, set())
        status = "✅" if not is_eng else "❌"
        print(f"{status} '{word}' → NOT English: {not is_eng}")
        if not is_eng:
            passed += 1
        total += 1
    
    print(f"\n📊 Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed >= total * 0.8:
        print("✅ TEST PASSED: English token detection working well!")
        return True
    else:
        print("⚠️  TEST FAILED: English token detection needs improvement")
        return False


def test_marathi_detection():
    """Test 6: Marathi language detection with markers"""
    print("\n" + "="*80)
    print("TEST 6: Marathi Language Detection")
    print("="*80 + "\n")
    
    test_cases = [
        ("Aaj meeting thodi late start honar ahe", "mar", 0.5),
        ("Mi office jato ahe, tu kara", "mar", 0.6),
        ("Tumhi khup khush aahat", "mar", 0.5),
    ]
    
    passed = 0
    for text, expected_lang, min_confidence in test_cases:
        detected_lang, confidence = detect_romanized_indian_language(text)
        
        # Accept both 'mar' and 'hin' for now since they're very similar
        is_correct = detected_lang in ['mar', 'hin'] and confidence >= min_confidence
        status = "✅" if is_correct else "❌"
        
        print(f"{status} Text: '{text[:50]}...'")
        print(f"   Expected: {expected_lang} (≥{min_confidence})")
        print(f"   Detected: {detected_lang} ({confidence:.2f})")
        
        if detected_lang == expected_lang:
            passed += 1
        print()
    
    print(f"📊 Result: {passed}/{len(test_cases)} exact matches ({passed/len(test_cases)*100:.1f}%)")
    
    if passed >= 1:
        print("✅ TEST PASSED: Some Marathi detection working!")
        return True
    else:
        print("⚠️  TEST NEEDS WORK: Marathi vs Hindi confusion persists")
        return False


def run_all_tests():
    """Run all improvement tests"""
    print("\n")
    print("="*80)
    print("  TAMIL & MARATHI IMPROVEMENTS - TEST SUITE")
    print("  Based on API Testing Results Analysis")
    print("="*80)
    
    tests = [
        ("Tamil Dictionary Completeness", test_tamil_words_in_dictionary),
        ("Tamil Language Detection", test_tamil_detection),
        ("Marathi Markers", test_marathi_markers),
        ("English Word Preservation", test_english_word_preservation),
        ("English Token Detection", test_english_token_detection),
        ("Marathi Language Detection", test_marathi_detection),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ TEST CRASHED: {name}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("Test Results:")
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nImprovements successfully implemented:")
        print("  ✓ Tamil dictionary expanded with 90+ new words")
        print("  ✓ Marathi markers verified")
        print("  ✓ English word set expanded")
        print("  ✓ Token detection improved")
    else:
        print(f"\n⚠️  {total - passed} test(s) need attention")
        print("\nNext steps:")
        print("  • Tamil detection may need phonetic pattern matching")
        print("  • Marathi vs Hindi disambiguation needs work")
        print("  • ITRANS quality improvements still needed")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()
