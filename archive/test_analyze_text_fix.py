#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the "Analyze Text" language detection fix
"""

from preprocessing.language_detection import detect_language
import json

def test_analyze_text():
    """Test that 'Analyze Text' is correctly detected as English"""
    
    test_text = "Analyze Text"
    
    print("=" * 80)
    print("Testing Language Detection Fix for 'Analyze Text'")
    print("=" * 80)
    
    result = detect_language(test_text, detailed=True)
    
    print(f"\nInput Text: '{test_text}'")
    print(f"\nDetection Results:")
    print(f"  Language Code: {result['language']}")
    print(f"  Language Name: {result['language_info']['language_name']}")
    print(f"  Confidence: {result['confidence']:.3f} ({result['confidence']*100:.1f}%)")
    print(f"  Detection Method: {result['method']}")
    print(f"  Text Length: {result['text_length']} chars")
    
    print(f"\nGLotLID Analysis:")
    print(f"  Detected: {result['glotlid_analysis']['detected_language']}")
    print(f"  Confidence: {result['glotlid_analysis']['confidence']:.3f}")
    
    if 'ensemble_analysis' in result:
        print(f"\nEnsemble Analysis:")
        print(f"  Final Language: {result['ensemble_analysis']['final_language']}")
        print(f"  Final Confidence: {result['ensemble_analysis']['final_confidence']:.3f}")
        print(f"  Detection Method: {result['ensemble_analysis']['detection_method']}")
        print(f"  Explanation: {result['ensemble_analysis']['decision_explanation']}")
    
    # Verify the fix
    print("\n" + "=" * 80)
    if result['language'] == 'eng':
        print("✅ SUCCESS: Text correctly detected as English!")
    else:
        print(f"❌ FAILURE: Text detected as '{result['language']}' instead of English")
    print("=" * 80)
    
    # Return full result as JSON
    print("\nFull Result (JSON):")
    print(json.dumps({
        'language': result['language'],
        'confidence': result['confidence'],
        'method': result['method'],
        'language_name': result['language_info']['language_name'],
        'is_english': result['language'] == 'eng'
    }, indent=2))

if __name__ == '__main__':
    test_analyze_text()
