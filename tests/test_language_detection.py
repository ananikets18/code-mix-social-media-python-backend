"""
Comprehensive Language Detection Test Suite
Run this to validate all edge cases and automatically improve detection
"""

import json
from preprocessing import detect_language
from datetime import datetime

# Test cases covering all scenarios
TEST_CASES = [
    # Pure languages
    {
        "text": "This is a wonderful product!",
        "expected_language": "eng",
        "expected_type": "pure",
        "description": "Pure English"
    },
    {
        "text": "यह बहुत अच्छा है",
        "expected_language": "hin",
        "expected_type": "pure",
        "description": "Pure Hindi (Devanagari)"
    },
    {
        "text": "सूर्य उगवला म्हणून प्रकाश पसरला",
        "expected_language": "mar",
        "expected_type": "pure",
        "description": "Pure Marathi (Devanagari)"
    },
    
    # Romanized Indian languages
    {
        "text": "Bahut achha hai",
        "expected_language": ["hin", "hi_roman", "hin_roman"],
        "expected_type": "romanized",
        "description": "Romanized Hindi"
    },
    {
        "text": "Tu Khup chukicha bolat ahes rajesh",
        "expected_language": ["mar", "mr_roman", "mar_roman"],
        "expected_type": "romanized",
        "description": "Romanized Marathi"
    },
    
    # Code-mixed (English + Indian)
    {
        "text": "Tu chup bhet, guys lets continue with journery !",
        "expected_language": ["eng_mixed", "hin_mixed", "mar_mixed"],
        "expected_type": "code_mixed",
        "description": "Code-mixed: Marathi/Hindi + English"
    },
    {
        "text": "Tu Shant raha, ani movie enjoy kar !",
        "expected_language": ["eng_mixed", "hin_mixed", "mar_mixed"],
        "expected_type": "code_mixed",
        "description": "Code-mixed: Marathi + English"
    },
    {
        "text": "Bahut achha hai yaar, really nice!",
        "expected_language": ["eng_mixed", "hin_mixed"],
        "expected_type": "code_mixed",
        "description": "Code-mixed: Hindi + English (Hinglish)"
    },
    
    # Short text
    {
        "text": "Thanks!",
        "expected_language": "eng",
        "expected_type": "short",
        "description": "Short English"
    },
    {
        "text": "नहीं",
        "expected_language": "hin",
        "expected_type": "short",
        "description": "Short Hindi"
    },
    
    # Domain-specific
    {
        "text": "Stock price increased by $50 today",
        "expected_language": "eng",
        "expected_type": "pure",
        "description": "Financial domain English"
    },
]

def run_test_suite():
    """Run all test cases and report results"""
    print("=" * 80)
    print("COMPREHENSIVE LANGUAGE DETECTION TEST SUITE")
    print("=" * 80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Test Cases: {len(TEST_CASES)}")
    print("=" * 80)
    
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    for i, test_case in enumerate(TEST_CASES, 1):
        text = test_case['text']
        expected_lang = test_case['expected_language']
        expected_type = test_case['expected_type']
        description = test_case['description']
        
        print(f"\n[TEST {i}/{len(TEST_CASES)}] {description}")
        print("-" * 80)
        print(f"Text: {text}")
        
        # Run detection
        result = detect_language(text, detailed=True)
        
        detected_lang = result['language']
        confidence = result['confidence']
        method = result['method']
        is_code_mixed = result['language_info'].get('is_code_mixed', False)
        
        print(f"Detected: {detected_lang} ({confidence:.1%} confidence, method: {method})")
        print(f"Expected: {expected_lang} (type: {expected_type})")
        
        # Check if detection is correct
        if isinstance(expected_lang, list):
            is_correct = detected_lang in expected_lang
        else:
            is_correct = detected_lang == expected_lang
        
        # Check type matching
        type_correct = True
        if expected_type == "code_mixed":
            type_correct = is_code_mixed or "_mixed" in detected_lang
        elif expected_type == "romanized":
            type_correct = "_roman" in detected_lang or result['language_info'].get('is_romanized', False)
        
        # Determine test result
        if is_correct and type_correct:
            status = "✓ PASS"
            results['passed'].append({
                'test': description,
                'text': text,
                'detected': detected_lang,
                'confidence': confidence
            })
        elif is_correct and not type_correct:
            status = "⚠ PARTIAL (language correct, type wrong)"
            results['warnings'].append({
                'test': description,
                'text': text,
                'detected': detected_lang,
                'expected': expected_lang,
                'issue': f"Expected type: {expected_type}, but is_code_mixed={is_code_mixed}"
            })
        else:
            status = "✗ FAIL"
            results['failed'].append({
                'test': description,
                'text': text,
                'detected': detected_lang,
                'expected': expected_lang,
                'confidence': confidence,
                'glotlid': result['glotlid_analysis']['detected_language'],
                'glotlid_confidence': result['glotlid_analysis']['confidence']
            })
        
        print(f"Result: {status}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = len(TEST_CASES)
    passed = len(results['passed'])
    warnings = len(results['warnings'])
    failed = len(results['failed'])
    
    print(f"Total Tests: {total}")
    print(f"✓ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"⚠ Warnings: {warnings} ({warnings/total*100:.1f}%)")
    print(f"✗ Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Show failures
    if failed > 0:
        print("\n" + "=" * 80)
        print("FAILED TESTS - NEEDS ATTENTION")
        print("=" * 80)
        for i, failure in enumerate(results['failed'], 1):
            print(f"\n{i}. {failure['test']}")
            print(f"   Text: {failure['text']}")
            print(f"   Expected: {failure['expected']}")
            print(f"   Detected: {failure['detected']} ({failure['confidence']:.1%})")
            print(f"   GlotLID: {failure['glotlid']} ({failure['glotlid_confidence']:.1%})")
    
    # Show warnings
    if warnings > 0:
        print("\n" + "=" * 80)
        print("WARNINGS - PARTIAL MATCHES")
        print("=" * 80)
        for i, warning in enumerate(results['warnings'], 1):
            print(f"\n{i}. {warning['test']}")
            print(f"   Text: {warning['text']}")
            print(f"   Issue: {warning['issue']}")
    
    # Save results to JSON
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: test_results.json")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    results = run_test_suite()
    
    # Exit code based on results
    if len(results['failed']) > 0:
        print("\n⚠ Some tests failed. Check the output above.")
        exit(1)
    else:
        print("\n✓ All tests passed!")
        exit(0)
