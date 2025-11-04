"""
SOLUTION: Stop manually testing edge cases!

This script creates an automated testing workflow:
1. Add your problematic text to test_cases.json
2. Run this script
3. It automatically identifies issues and suggests fixes

No more copy-pasting JSON outputs!
"""

import json
import os
from preprocessing import detect_language
from datetime import datetime

# File to store all test cases
TEST_CASES_FILE = "test_cases.json"

def initialize_test_cases():
    """Create initial test cases file if it doesn't exist"""
    default_cases = [
        {
            "text": "This is a wonderful product!",
            "expected_language": "eng",
            "expected_is_code_mixed": False,
            "description": "Pure English",
            "status": "baseline"
        },
        {
            "text": "सूर्य उगवला म्हणून प्रकाश पसरला",
            "expected_language": "mar",
            "expected_is_code_mixed": False,
            "description": "Pure Marathi (Devanagari)",
            "status": "baseline"
        },
        {
            "text": "Tu chup bhet, guys lets continue with journery !",
            "expected_language": ["eng_mixed", "hin_mixed", "mar_mixed"],
            "expected_is_code_mixed": True,
            "description": "Code-mixed: Marathi/Hindi + English",
            "status": "needs_fixing"
        },
        {
            "text": "Tu Shant raha, ani movie enjoy kar !",
            "expected_language": ["eng_mixed", "hin_mixed", "mar_mixed"],
            "expected_is_code_mixed": True,
            "description": "Code-mixed: Marathi + English",
            "status": "needs_fixing"
        }
    ]
    
    if not os.path.exists(TEST_CASES_FILE):
        with open(TEST_CASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_cases, f, indent=2, ensure_ascii=False)
        print(f"✓ Created {TEST_CASES_FILE} with {len(default_cases)} default test cases")
    
    return default_cases

def add_test_case(text, expected_language, expected_is_code_mixed=False, description=""):
    """Add a new test case to the file"""
    if os.path.exists(TEST_CASES_FILE):
        with open(TEST_CASES_FILE, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
    else:
        test_cases = []
    
    new_case = {
        "text": text,
        "expected_language": expected_language,
        "expected_is_code_mixed": expected_is_code_mixed,
        "description": description or f"Test case {len(test_cases) + 1}",
        "status": "new",
        "added_date": datetime.now().isoformat()
    }
    
    test_cases.append(new_case)
    
    with open(TEST_CASES_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_cases, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Added test case: {description}")
    return new_case

def run_automated_tests():
    """Run all test cases and identify issues"""
    print("=" * 80)
    print("AUTOMATED LANGUAGE DETECTION TESTING")
    print("=" * 80)
    
    if not os.path.exists(TEST_CASES_FILE):
        initialize_test_cases()
    
    with open(TEST_CASES_FILE, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
    
    print(f"\nTotal Test Cases: {len(test_cases)}")
    print("=" * 80)
    
    results = {
        'passed': [],
        'failed': [],
        'total': len(test_cases)
    }
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case['text']
        expected_lang = test_case['expected_language']
        expected_code_mixed = test_case.get('expected_is_code_mixed', False)
        description = test_case.get('description', 'No description')
        
        print(f"\n[{i}/{len(test_cases)}] {description}")
        print("-" * 80)
        print(f"Text: {text[:60]}...")
        
        # Run detection
        result = detect_language(text, detailed=True)
        detected_lang = result['language']
        is_code_mixed = result['language_info'].get('is_code_mixed', False)
        confidence = result['confidence']
        
        # Check if correct
        if isinstance(expected_lang, list):
            lang_correct = detected_lang in expected_lang
        else:
            lang_correct = detected_lang == expected_lang
        
        code_mixed_correct = is_code_mixed == expected_code_mixed
        
        # Print results
        print(f"Expected: {expected_lang} (code_mixed={expected_code_mixed})")
        print(f"Detected: {detected_lang} (code_mixed={is_code_mixed}, {confidence:.1%})")
        
        if lang_correct and code_mixed_correct:
            print("Result: ✓ PASS")
            results['passed'].append(test_case)
        else:
            print("Result: ✗ FAIL")
            issue = {
                'test_case': test_case,
                'detected': detected_lang,
                'is_code_mixed': is_code_mixed,
                'confidence': confidence,
                'glotlid': result['glotlid_analysis']['detected_language'],
                'glotlid_conf': result['glotlid_analysis']['confidence']
            }
            results['failed'].append(issue)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total: {results['total']}")
    print(f"✓ Passed: {len(results['passed'])} ({len(results['passed'])/results['total']*100:.1f}%)")
    print(f"✗ Failed: {len(results['failed'])} ({len(results['failed'])/results['total']*100:.1f}%)")
    
    # Show failures with suggestions
    if results['failed']:
        print("\n" + "=" * 80)
        print("FAILED TESTS - ACTION ITEMS")
        print("=" * 80)
        for i, failure in enumerate(results['failed'], 1):
            tc = failure['test_case']
            print(f"\n{i}. {tc['description']}")
            print(f"   Text: {tc['text']}")
            print(f"   Expected: {tc['expected_language']} (code_mixed={tc['expected_is_code_mixed']})")
            print(f"   Got: {failure['detected']} (code_mixed={failure['is_code_mixed']})")
            print(f"   GlotLID: {failure['glotlid']} ({failure['glotlid_conf']:.1%})")
            
            # Suggest fixes
            if failure['is_code_mixed'] != tc['expected_is_code_mixed']:
                if tc['expected_is_code_mixed']:
                    print(f"   → FIX: Add code-mixing patterns for this text")
                else:
                    print(f"   → FIX: Reduce false positive code-mixing detection")
    
    # Save results
    with open('test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("Results saved to: test_results.json")
    print("=" * 80)
    
    return results

def main():
    """Main entry point"""
    print("\n🤖 AUTOMATED LANGUAGE DETECTION TESTER")
    print("\nInstead of manually copy-pasting JSON outputs:")
    print("1. Add problematic texts to test_cases.json")
    print("2. Run this script")
    print("3. Get automatic analysis and fix suggestions\n")
    
    results = run_automated_tests()
    
    if results['failed']:
        print("\n⚠ ACTION REQUIRED:")
        print(f"  - {len(results['failed'])} tests are failing")
        print(f"  - Check test_results.json for details")
        print(f"  - Add missing patterns to preprocessing.py")
    else:
        print("\n✓ ALL TESTS PASSING!")
        print("  System is working correctly for all test cases")

if __name__ == "__main__":
    initialize_test_cases()
    main()
