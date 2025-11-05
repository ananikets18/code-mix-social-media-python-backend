#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify English validation works for various cases
"""

from preprocessing.language_detection import detect_language

def test_cases():
    """Test various cases where GLotLID might fail"""
    
    test_texts = [
        ("Analyze Text", "eng", "Original failure case"),
        ("Hello World", "eng", "Common English phrase"),
        ("Test this", "eng", "Short English"),
        ("Check the status", "eng", "Common English words"),
        ("Please wait", "eng", "Polite English"),
        ("नमस्ते", "hin", "Hindi Devanagari - should NOT be English"),
        ("mi khup khush ahe", "mar", "Romanized Marathi - should NOT be English"),
        ("The quick brown fox", "eng", "English sentence"),
        ("Good morning everyone", "eng", "English greeting"),
    ]
    
    print("=" * 100)
    print("Testing English Validation for Various Cases")
    print("=" * 100)
    
    results = []
    
    for text, expected_lang, description in test_texts:
        result = detect_language(text, detailed=True)
        detected_lang = result['language']
        confidence = result['confidence']
        method = result['method']
        
        # Check if detection is correct
        is_correct = detected_lang == expected_lang
        status = "✅ PASS" if is_correct else f"❌ FAIL (Expected: {expected_lang})"
        
        print(f"\n{status}")
        print(f"  Text: '{text}'")
        print(f"  Description: {description}")
        print(f"  Detected: {detected_lang} ({result['language_info']['language_name']})")
        print(f"  Confidence: {confidence:.3f} ({confidence*100:.1f}%)")
        print(f"  Method: {method}")
        
        results.append({
            'text': text,
            'expected': expected_lang,
            'detected': detected_lang,
            'correct': is_correct,
            'description': description
        })
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    total = len(results)
    passed = sum(1 for r in results if r['correct'])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    if failed > 0:
        print("\nFailed Cases:")
        for r in results:
            if not r['correct']:
                print(f"  - '{r['text']}': Expected {r['expected']}, Got {r['detected']} ({r['description']})")
    else:
        print("\n🎉 All tests passed!")
    
    print("=" * 100)

if __name__ == '__main__':
    test_cases()
