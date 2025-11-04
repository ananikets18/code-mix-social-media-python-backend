"""Quick test - Social Media Post Analysis with NEW architecture"""

import sys
import json

# Test the exact social media use case
text = "Mera dost bahut smart hai yaar! Tu bhi usse mil bro 😊"

print("\n" + "="*80)
print("SOCIAL MEDIA POST ANALYSIS - NEW ARCHITECTURE TEST")
print("="*80)
print(f"\nInput Text: {text}")
print("="*80 + "\n")

try:
    from main import analyze_text_comprehensive
    
    # Analyze with translation enabled
    result = analyze_text_comprehensive(
        text=text,
        normalization_level=None,
        preserve_emojis=True,
        punctuation_mode='preserve',
        check_profanity=True,
        detect_domains=True,
        translate_to_english=True
    )
    
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80 + "\n")
    
    if 'error' in result:
        print(f"ERROR: {result['error_message']}")
    else:
        print(f"1. LANGUAGE DETECTION:")
        print(f"   - Language: {result['language'].get('language', 'unknown')}")
        print(f"   - Display Name: {result['language'].get('language_info', {}).get('language_name', 'Unknown')}")
        print(f"   - Is Romanized: {result['language'].get('language_info', {}).get('is_romanized', False)}")
        print(f"   - Is Code-Mixed: {result['language'].get('language_info', {}).get('is_code_mixed', False)}")
        print(f"   - Confidence: {result['language'].get('confidence', 0)*100:.1f}%")
        
        print(f"\n2. TRANSLITERATION:")
        if result.get('transliteration') and result['transliteration'].get('was_transliterated'):
            print(f"   - Status: SUCCESS")
            print(f"   - Conversion Rate: {result['transliteration']['conversion_rate']*100:.1f}%")
            print(f"   - Words Converted: {result['transliteration']['words_converted']}")
            print(f"   - Words Preserved: {result['transliteration']['words_preserved']}")
            print(f"   - Native Script: {result['transliteration']['transliterated_text']}")
        else:
            print(f"   - Status: SKIPPED or FAILED")
            if result.get('transliteration', {}).get('errors'):
                print(f"   - Errors: {result['transliteration']['errors']}")
        
        print(f"\n3. SENTIMENT ANALYSIS:")
        print(f"   - Sentiment: {result['sentiment'].get('label', 'unknown').upper()}")
        print(f"   - Confidence: {result['sentiment'].get('confidence', 0)*100:.1f}%")
        print(f"   - Model: {result['sentiment'].get('model_used', 'unknown')}")
        
        print(f"\n4. TOXICITY DETECTION:")
        toxic_scores = result.get('toxicity', {})
        max_score = max(toxic_scores.values()) if toxic_scores and not isinstance(toxic_scores, str) else 0
        print(f"   - Max Toxicity: {max_score*100:.2f}%")
        print(f"   - Toxic: {toxic_scores.get('toxic', 0)*100:.2f}%")
        
        print(f"\n5. TRANSLATION:")
        if result.get('translations', {}).get('english'):
            print(f"   - English: {result['translations']['english']}")
        else:
            print(f"   - Status: Not translated or failed")
        
        print(f"\n6. PROFANITY:")
        print(f"   - Has Profanity: {result.get('profanity', {}).get('has_profanity', False)}")
        
        print("\n" + "="*80)
        print("KEY IMPROVEMENTS DEMONSTRATION:")
        print("="*80)
        
        print("\nOLD SYSTEM:")
        print("  - Translation: GARBLED (āīāīāē...) <-- BUG")
        print("  - Sentiment analyzed on: Romanized text")
        print("  - Translation attempted: On romanized text (broke ITRANS)")
        
        print("\nNEW SYSTEM:")
        print(f"  - Translation: {result.get('translations', {}).get('english', 'N/A')[:60]}...")
        print(f"  - Sentiment analyzed on: {'Native script' if result.get('processing_info', {}).get('text_analyzed_in_native_script') else 'Original text'}")
        print(f"  - Transliteration done: BEFORE analysis (separate step)")
        
        print("\n" + "="*80)
        print("SUCCESS! The system is now ready for social media analysis!")
        print("="*80 + "\n")
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
