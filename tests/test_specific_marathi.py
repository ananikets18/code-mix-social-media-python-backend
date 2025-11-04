"""
Test specific Marathi sentence from user feedback

Text: "Aaj meeting thodi late start honar ahe, so thoda wait kara"
Expected: Marathi-English code-mixed, proper English word preservation

Author: NLP Project Team
Created: 2025-11-03
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing import detect_romanized_indian_language, is_english_token, convert_romanized_to_native
from translation import ROMANIZED_DICTIONARY


def test_sentence_analysis():
    """Analyze the specific Marathi-English mixed sentence"""
    text = "Aaj meeting thodi late start honar ahe, so thoda wait kara"
    
    print("\n" + "="*80)
    print("DETAILED ANALYSIS: Marathi-English Code-Mixed Sentence")
    print("="*80 + "\n")
    
    print(f"Input Text: '{text}'")
    print()
    
    # Step 1: Language Detection
    print("STEP 1: Language Detection")
    print("-" * 80)
    lang, confidence = detect_romanized_indian_language(text)
    print(f"Detected Language: {lang}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Status: {'✅ CORRECT (Marathi)' if lang == 'mar' else '❌ WRONG'}")
    print()
    
    # Step 2: Token-by-Token Analysis
    print("STEP 2: Token-by-Token Analysis")
    print("-" * 80)
    
    tokens = text.split()
    marathi_dict = set(ROMANIZED_DICTIONARY.get('marathi', {}).keys())
    
    expected_english = {'meeting', 'late', 'start', 'so', 'wait'}
    expected_marathi = {'aaj', 'thodi', 'honar', 'ahe', 'thoda', 'kara'}
    
    print(f"{'Token':<15} {'In Dict?':<12} {'Is English?':<15} {'Expected':<15} {'Status'}")
    print("-" * 80)
    
    english_correct = 0
    marathi_correct = 0
    
    for token in tokens:
        clean_token = token.strip('.,!?;:').lower()
        in_dict = clean_token in marathi_dict
        is_eng = is_english_token(token, marathi_dict)
        
        if clean_token in expected_english:
            expected = "English"
            is_correct = is_eng
            if is_correct:
                english_correct += 1
        elif clean_token in expected_marathi:
            expected = "Marathi"
            is_correct = not is_eng
            if is_correct:
                marathi_correct += 1
        else:
            expected = "Unknown"
            is_correct = True
        
        status = "✅" if is_correct else "❌"
        
        print(f"{token:<15} {str(in_dict):<12} {str(is_eng):<15} {expected:<15} {status}")
    
    print()
    print(f"English Words Correctly Identified: {english_correct}/{len(expected_english)} "
          f"({english_correct/len(expected_english)*100:.0f}%)")
    print(f"Marathi Words Correctly Identified: {marathi_correct}/{len(expected_marathi)} "
          f"({marathi_correct/len(expected_marathi)*100:.0f}%)")
    print()
    
    # Step 3: Conversion Test
    print("STEP 3: Romanized to Native Script Conversion")
    print("-" * 80)
    
    result = convert_romanized_to_native(text, 'mar', preserve_english=True)
    
    print(f"Original Text:")
    print(f"  {text}")
    print()
    print(f"Converted Text:")
    print(f"  {result['converted_text']}")
    print()
    print(f"Conversion Method: {result['conversion_method']}")
    print(f"Statistics:")
    print(f"  - Total Tokens: {result['statistics']['total_tokens']}")
    print(f"  - Converted: {result['statistics']['converted_tokens']}")
    print(f"  - Preserved (English): {result['statistics']['preserved_tokens']}")
    print(f"  - Conversion Rate: {result['statistics']['conversion_rate']:.1f}%")
    print()
    
    # Step 4: Detailed Token Conversion
    print("STEP 4: Token-by-Token Conversion Details")
    print("-" * 80)
    print(f"{'Original':<15} {'Converted':<20} {'Status':<15} {'Method'}")
    print("-" * 80)
    
    for detail in result['token_details']:
        orig = detail['original']
        conv = detail['converted']
        status = detail['status']
        method = detail['method']
        
        if status == 'preserved_english':
            status_icon = "🔵 Preserved"
        elif status == 'converted':
            status_icon = "🟢 Converted"
        else:
            status_icon = "⚪ Unchanged"
        
        print(f"{orig:<15} {conv:<20} {status_icon:<15} {method}")
    
    print()
    
    # Step 5: Verification
    print("STEP 5: Final Verification")
    print("-" * 80)
    
    converted = result['converted_text']
    
    # Check if English words are preserved
    english_preserved = all(word in converted for word in ['meeting', 'late', 'start', 'wait'])
    
    # Check if Marathi words are converted to Devanagari
    # Look for Devanagari characters (range: U+0900 to U+097F)
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in converted)
    
    print(f"✓ Language Detection: {'✅' if lang == 'mar' else '❌'} (Expected: mar, Got: {lang})")
    print(f"✓ English Preservation: {'✅' if english_preserved else '❌'} "
          f"(meeting, late, start, wait should remain)")
    print(f"✓ Devanagari Conversion: {'✅' if has_devanagari else '❌'} "
          f"(Marathi words should convert)")
    print(f"✓ Conversion Rate: {'✅' if result['statistics']['conversion_rate'] >= 40 else '❌'} "
          f"({result['statistics']['conversion_rate']:.1f}%)")
    
    print()
    
    # Overall result
    all_checks = (
        lang == 'mar' and
        english_preserved and
        has_devanagari and
        result['statistics']['conversion_rate'] >= 40
    )
    
    if all_checks:
        print("🎉 ALL CHECKS PASSED! 🎉")
        print("\nThe system correctly:")
        print("  ✓ Detected Marathi language")
        print("  ✓ Preserved English words (meeting, late, start, wait)")
        print("  ✓ Converted Marathi words to Devanagari")
        print("  ✓ Achieved good conversion rate")
        return True
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("\nIssues to address:")
        if lang != 'mar':
            print(f"  ✗ Language detection: Expected 'mar', got '{lang}'")
        if not english_preserved:
            print("  ✗ Some English words were converted instead of preserved")
        if not has_devanagari:
            print("  ✗ Marathi words were not converted to Devanagari")
        if result['statistics']['conversion_rate'] < 40:
            print(f"  ✗ Low conversion rate: {result['statistics']['conversion_rate']:.1f}%")
        return False
    
    print()
    print("="*80)


if __name__ == "__main__":
    test_sentence_analysis()
