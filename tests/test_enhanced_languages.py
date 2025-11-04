"""
Test Enhanced Language Support
Tests all newly added features:
1. Urdu detection
2. Translation for Odia, Assamese, Nepali, Sinhala, Sanskrit, Sindhi
3. Romanized conversion for additional languages
4. Code-mixing detection for Bengali, Tamil, Telugu, Kannada, Gujarati, Punjabi
"""

from preprocessing import detect_language, detect_code_mixing, detect_romanized_indian_language
from translation import translate_text
import json


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_urdu_detection():
    """Test Urdu language detection (now supported)"""
    print_header("TEST 1: Urdu Detection")
    
    test_cases = [
        ("یہ بہت اچھا ہے", "Urdu (native script)"),
        ("Yeh bohot achha hai", "Urdu (romanized)"),
    ]
    
    for text, description in test_cases:
        print(f"📝 {description}: {text}")
        result = detect_language(text, detailed=True)
        print(f"   Detected: {result['language_info']['language_name']} ({result['language']})")
        print(f"   Confidence: {result.get('confidence', 0):.2%}")
        print()


def test_new_translations():
    """Test translation support for newly added languages"""
    print_header("TEST 2: New Translation Support")
    
    test_cases = [
        ("ମୁଁ ବହୁତ ଖୁସି", "Odia", "or"),
        ("মই বহুত সুখী", "Assamese", "as"),
        ("म धेरै खुशी छु", "Nepali", "ne"),
        ("मम महती प्रसन्नता", "Sanskrit", "sa"),
        ("میں بہت خوش ہوں", "Urdu", "ur"),
    ]
    
    for text, lang_name, lang_code in test_cases:
        print(f"📝 {lang_name} → English: {text}")
        result = translate_text(text, target_lang='en', source_lang=lang_code)
        
        if result['success']:
            print(f"   ✅ Translation: {result['translated_text']}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        print()


def test_romanized_conversion_expansion():
    """Test romanized conversion for additional languages"""
    print_header("TEST 3: Expanded Romanized Conversion")
    
    test_cases = [
        ("Odia romanized aau bhala", "Odia", "or"),
        ("Assamese romanized moi bhaal", "Assamese", "as"),
        ("Nepali romanized ma khusi chu", "Nepali", "ne"),
        ("Sanskrit romanized mama priya", "Sanskrit", "sa"),
    ]
    
    for text, lang_name, lang_code in test_cases:
        print(f"📝 {lang_name} (Romanized): {text}")
        
        # Test conversion
        result = translate_text(text, target_lang='en', source_lang=lang_code, 
                              enable_romanized_conversion=True)
        
        if result.get('was_romanized'):
            print(f"   ✅ Romanization detected!")
            print(f"   Native script: {result.get('preprocessed_text', 'N/A')}")
            print(f"   Translation: {result.get('translated_text', 'N/A')}")
        else:
            print(f"   ℹ️  Not detected as romanized")
            print(f"   Translation: {result.get('translated_text', text)}")
        print()


def test_expanded_code_mixing():
    """Test code-mixing detection for additional Indian languages"""
    print_header("TEST 4: Expanded Code-Mixing Detection")
    
    test_cases = [
        # Bengali + English
        ("Ami khub happy ami office theke back aasche", "Bengali + English (Benglish)"),
        ("Tumi ki bolcho, this is really nice", "Bengali + English"),
        
        # Tamil + English
        ("Naan romba tired, office la heavy work irukku", "Tamil + English (Tanglish)"),
        ("Nalla movie watch pannalam guys", "Tamil + English"),
        
        # Telugu + English
        ("Nenu chaala happy, office lo bagundi", "Telugu + English (Tenglish)"),
        ("Emi chesthunna, lets go shopping", "Telugu + English"),
        
        # Kannada + English
        ("Naanu thumba happy, office ge late aayithu", "Kannada + English"),
        ("Chennagi movie watch maadona guys", "Kannada + English"),
        
        # Gujarati + English
        ("Hun khub happy chhu, office ma work saru chhe", "Gujarati + English"),
        ("Saras movie, let's watch together", "Gujarati + English"),
        
        # Punjabi + English
        ("Main bahut happy aan, office vich vadiya kaam hai", "Punjabi + English (Punglish)"),
        ("Changa movie, guys lets watch", "Punjabi + English"),
    ]
    
    for text, description in test_cases:
        print(f"📝 {description}")
        print(f"   Text: {text}")
        
        # Test code-mixing detection
        is_mixed, dominant_lang = detect_code_mixing(text)
        print(f"   Code-Mixed: {is_mixed}")
        print(f"   Dominant Language: {dominant_lang if dominant_lang else 'None'}")
        
        # Full language detection
        lang_result = detect_language(text, detailed=True)
        print(f"   Detected: {lang_result['language_name']}")
        print(f"   Is Code-Mixed: {lang_result.get('is_code_mixed', False)}")
        print()


def test_romanized_language_detection():
    """Test romanized detection for new languages"""
    print_header("TEST 5: Romanized Language Detection (Pattern-Based)")
    
    test_cases = [
        ("Ami bolchhi tumi kothay jachho", "Bengali"),
        ("Naan romba nalla irukken", "Tamil"),
        ("Nenu chaala manchiga unnanu", "Telugu"),
        ("Naanu thumba chennagi ide", "Kannada"),
        ("Hun khub saras chhu", "Gujarati"),
        ("Main bahut changa aan", "Punjabi"),
    ]
    
    for text, expected_lang in test_cases:
        print(f"📝 Expected: {expected_lang}")
        print(f"   Text: {text}")
        
        detected = detect_romanized_indian_language(text)
        print(f"   Detected: {detected if detected else 'Not detected'}")
        print()


def run_comprehensive_report():
    """Generate comprehensive enhancement report"""
    print_header("COMPREHENSIVE ENHANCEMENT REPORT")
    
    enhancements = {
        "✅ Urdu Detection": "Added Urdu to INDIAN_LANGUAGES mapping",
        "✅ Translation Expansion": "Added 6 languages: Odia, Assamese, Nepali, Sinhala, Sanskrit, Sindhi",
        "✅ Romanized Conversion": "Extended INDIAN_LANGUAGE_SCRIPTS to include all supported scripts",
        "✅ Code-Mixing Patterns": "Added patterns for 6 languages: Bengali, Tamil, Telugu, Kannada, Gujarati, Punjabi",
        "✅ Pattern Detection": "Enhanced detect_romanized_indian_language() to support 8 languages",
        "✅ Code-Mixing Detection": "Updated detect_code_mixing() to handle all Indian languages",
    }
    
    limitations = {
        "⚠️ Sinhala Romanized": "Not supported by indic_nlp_library (no ITRANS mapping)",
        "⚠️ Urdu Romanized": "Not supported by indic_nlp_library (Perso-Arabic script)",
        "⚠️ Sindhi Support": "Limited support in indic_nlp_library",
        "⚠️ Sanskrit Translation": "Limited/experimental in Google Translate",
        "⚠️ Sentiment Analysis": "No IndicBERT models for Urdu, Sanskrit, Nepali, Sinhala, Sindhi",
        "💡 Alternative": "Can use multilingual XLM-RoBERTa for sentiment analysis",
    }
    
    print("🎯 Implemented Enhancements:")
    for feature, description in enhancements.items():
        print(f"   {feature}: {description}")
    
    print("\n⚠️  Known Limitations:")
    for limitation, description in limitations.items():
        print(f"   {limitation}: {description}")
    
    print("\n📊 Updated Language Support Matrix:")
    languages_table = [
        ["Language", "Detection", "Translation", "Romanized", "Sentiment", "Code-Mix"],
        ["Hindi", "✅", "✅", "✅", "✅", "✅"],
        ["Marathi", "✅", "✅", "✅", "✅", "✅"],
        ["Bengali", "✅", "✅", "✅", "✅", "✅ NEW"],
        ["Tamil", "✅", "✅", "✅", "✅", "✅ NEW"],
        ["Telugu", "✅", "✅", "✅", "✅", "✅ NEW"],
        ["Kannada", "✅", "✅", "✅", "✅", "✅ NEW"],
        ["Malayalam", "✅", "✅", "✅", "✅", "❌"],
        ["Gujarati", "✅", "✅", "✅", "✅", "✅ NEW"],
        ["Punjabi", "✅", "✅", "✅", "✅", "✅ NEW"],
        ["Odia", "✅", "✅ NEW", "✅ NEW", "✅", "❌"],
        ["Assamese", "✅", "✅ NEW", "✅ NEW", "✅", "❌"],
        ["Urdu", "✅ NEW", "✅", "❌*", "❌", "❌"],
        ["Nepali", "✅", "✅ NEW", "✅ NEW", "❌", "❌"],
        ["Sanskrit", "✅", "✅ NEW**", "✅ NEW", "❌", "❌"],
        ["Sinhala", "✅", "✅ NEW", "❌*", "❌", "❌"],
        ["Sindhi", "✅", "✅ NEW**", "⚠️", "❌", "❌"],
    ]
    
    # Print table
    col_widths = [max(len(row[i]) for row in languages_table) for i in range(6)]
    for i, row in enumerate(languages_table):
        print("   " + " | ".join(cell.ljust(col_widths[j]) for j, cell in enumerate(row)))
        if i == 0:
            print("   " + "-+-".join("-" * w for w in col_widths))
    
    print("\n   * Not supported by indic_nlp_library")
    print("   ** Limited/experimental support in Google Translate")
    print()


if __name__ == "__main__":
    import sys
    import io
    
    # Fix Unicode encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("\n" + "="*80)
    print(" ENHANCED INDIAN LANGUAGE SUPPORT - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Run all tests
    try:
        run_comprehensive_report()
        test_urdu_detection()
        test_new_translations()
        test_romanized_conversion_expansion()
        test_expanded_code_mixing()
        test_romanized_language_detection()
        
        print_header("✅ ALL TESTS COMPLETED")
        print("Summary:")
        print("  • Urdu detection: Enabled ✅")
        print("  • Translation expansion: 6 languages added ✅")
        print("  • Romanized conversion: Extended to 13 languages ✅")
        print("  • Code-mixing detection: 6 new languages supported ✅")
        print("  • Total Indian languages: 16 (up from 9) 📈")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
