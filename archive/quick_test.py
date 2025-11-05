#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test for "Analyze Text" fix"""

from preprocessing.language_detection import detect_language

result = detect_language("Analyze Text", detailed=True)
print(f"✓ Language: {result['language']} ({result['language_info']['language_name']})")
print(f"✓ Confidence: {result['confidence']:.3f}")
print(f"✓ Expected: eng (English)")
print(f"✓ Status: {'PASS ✅' if result['language'] == 'eng' else 'FAIL ❌'}")
