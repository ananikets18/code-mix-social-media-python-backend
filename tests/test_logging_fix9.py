"""
FIX #9: Test Code-Mixing Logging Output
=========================================

Purpose: Verify that FIX #9 logging provides useful diagnostic information
for debugging and threshold tuning in production.

Tests:
1. Code-mixed text (should see all logging phases)
2. Pure language text (should see minimal logging)
3. Romanized text (should see romanized detection logging)
4. Short vs. long text (should see different adaptive thresholds)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from preprocessing import detect_language, detect_code_mixing
import logging

# Set logging to DEBUG to see all FIX #9 logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_code_mixed_logging():
    """Test logging for code-mixed text"""
    print("\n" + "="*80)
    print("TEST 1: Code-Mixed Text Logging")
    print("="*80)
    
    text = "Aaj traffic khup heavy aahe, main road par bahut vehicles hain"
    print(f"Input: {text}")
    print("\nExpected logs:")
    print("  - Entry log with text preview and length")
    print("  - Configuration log with thresholds (adaptive based on length)")
    print("  - Detection method logs (script diversity, token analysis)")
    print("  - Final decision summary")
    print("\nActual logs:\n")
    
    result = detect_language(text, detailed=True)
    
    print(f"\nResult: {result}")
    print("✅ Test 1 Complete\n")

def test_pure_language_logging():
    """Test logging for pure language text"""
    print("\n" + "="*80)
    print("TEST 2: Pure Language Text Logging")
    print("="*80)
    
    text = "This is a simple English sentence with no code-mixing at all"
    print(f"Input: {text}")
    print("\nExpected logs:")
    print("  - Entry log")
    print("  - Should NOT see code-mixing detection logs")
    print("  - Final decision should be is_code_mixed=False")
    print("\nActual logs:\n")
    
    result = detect_language(text, detailed=True)
    
    print(f"\nResult: {result}")
    print("✅ Test 2 Complete\n")

def test_romanized_logging():
    """Test logging for romanized Indic text"""
    print("\n" + "="*80)
    print("TEST 3: Romanized Indic Text Logging")
    print("="*80)
    
    text = "Namaste, aap kaise hain? Main theek hoon"
    print(f"Input: {text}")
    print("\nExpected logs:")
    print("  - Entry log")
    print("  - Romanized detection log (is_romanized=True)")
    print("  - May see code-mixing detection if English words detected")
    print("\nActual logs:\n")
    
    result = detect_language(text, detailed=True)
    
    print(f"\nResult: {result}")
    print("✅ Test 3 Complete\n")

def test_adaptive_threshold_logging():
    """Test logging shows different thresholds for different text lengths"""
    print("\n" + "="*80)
    print("TEST 4: Adaptive Threshold Logging")
    print("="*80)
    
    # Short text (≤15 chars) - should use threshold=0.12
    short_text = "OK bye"
    print(f"\nShort text: '{short_text}' (len={len(short_text)})")
    print("Expected: threshold=0.12, category=short")
    print("Actual logs:\n")
    
    detect_code_mixing(short_text, "en")
    
    # Medium text (16-30 chars) - should use threshold=0.10
    medium_text = "Hello how are you today?"
    print(f"\nMedium text: '{medium_text}' (len={len(medium_text)})")
    print("Expected: threshold=0.10, category=medium")
    print("Actual logs:\n")
    
    detect_code_mixing(medium_text, "en")
    
    # Long text (>30 chars) - should use threshold=0.08
    long_text = "This is a longer sentence that should be categorized as long text for threshold testing"
    print(f"\nLong text: '{long_text}' (len={len(long_text)})")
    print("Expected: threshold=0.08, category=long")
    print("Actual logs:\n")
    
    detect_code_mixing(long_text, "en")
    
    print("✅ Test 4 Complete\n")

def test_confidence_and_method_logging():
    """Test that confidence scores and detection methods are logged"""
    print("\n" + "="*80)
    print("TEST 5: Confidence and Method Logging")
    print("="*80)
    
    text = "Marathi madhe काही words English madhe aahet"
    print(f"Input: {text}")
    print("\nExpected logs:")
    print("  - Detection method (script_diversity, token_analysis, or pattern_based)")
    print("  - Confidence scores")
    print("  - Latin% and Indic% percentages")
    print("\nActual logs:\n")
    
    result = detect_code_mixing(text, "mar")
    
    print(f"\nResult: {result}")
    print("✅ Test 5 Complete\n")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("FIX #9: Code-Mixing Logging Tests")
    print("="*80)
    print("\nThese tests verify that FIX #9 logging provides useful diagnostic")
    print("information for debugging and threshold tuning.")
    print("\nLook for logs with [FIX #9] or [API FIX #9] tags.\n")
    
    test_code_mixed_logging()
    test_pure_language_logging()
    test_romanized_logging()
    test_adaptive_threshold_logging()
    test_confidence_and_method_logging()
    
    print("\n" + "="*80)
    print("All FIX #9 Logging Tests Complete!")
    print("="*80)
    print("\nReview the logs above to verify:")
    print("  ✓ Entry/exit logs show text previews and lengths")
    print("  ✓ Configuration logs show adaptive thresholds")
    print("  ✓ Detection method logs show which detection triggered")
    print("  ✓ Final decision logs show all key parameters")
    print("  ✓ Confidence scores and script percentages are logged")
    print("\nThis logging enables threshold tuning without code changes!")
