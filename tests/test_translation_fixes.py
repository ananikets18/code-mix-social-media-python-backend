"""
Test cases for translation and language detection fixes
Based on user-reported issues
"""

import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from preprocessing import detect_language
from translation import translate_text
from main import analyze_text_comprehensive

def print_result(test_name, text, result):
    """Print test result in a readable format"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"Input: {text}")
    print(f"Language: {result['language']['language']} ({result['language']['language_info']['language_name']})")
    print(f"Confidence: {result['language']['confidence']:.2%}")
    print(f"Is Code-Mixed: {result['language']['language_info']['is_code_mixed']}")
    
    if result.get('translations'):
        for lang, trans in result['translations'].items():
            print(f"Translation ({lang}): {trans}")
    else:
        print("Translation: None")


def test_all_languages():
    """Test all reported language issues"""
    
    test_cases = [
        # Working cases (verify they still work)
        ("Hindi to English", "यह बहुत अच्छा है"),
        ("English to Hindi", "This is very good"),
        ("Marathi (Devanagari) to English", "हे खूप चांगले आहे"),
        ("French to English", "Bonjour, comment allez-vous?"),
        ("Spanish to English", "Hola, ¿cómo estás?"),
        ("German to English", "Guten Tag, wie geht es Ihnen?"),
        ("Portuguese to English", "Olá, como você está?"),
        ("Russian to English", "Привет, как дела?"),
        
        # Previously failing cases
        ("Italian (small)", "Ciao"),
        ("Italian (full sentence)", "Ciao, come stai? Spero che tu stia bene."),
        ("Chinese", "你好，你好吗？"),
        ("Japanese", "こんにちは、元気ですか？"),
        ("Korean", "안녕하세요, 어떻게 지내세요?"),
        ("Arabic", "مرحبا، كيف حالك؟"),
        ("Greek", "Γεια σου, πώς είσαι;"),
        
        # Romanized Indian languages
        ("Romanized Hindi", "Mai bahut khush hoon aaj"),
        ("Romanized Marathi", "Mi khup khush aahe aaj"),
        ("Romanized Marathi 2", "Tu kashala sangu me?"),
        
        # Code-mixed (previously failing)
        ("Hindi + English (Code-mixed)", "Yaar ye movie bahut mast hai! Must watch bro"),
        ("Marathi + English (Code-mixed)", "Tu chup bhet, guys lets continue with journey"),
        ("Hinglish", "Mai kal market jaa raha hoon, shopping karne"),
    ]
    
    print("\n" + "="*70)
    print("COMPREHENSIVE TRANSLATION & LANGUAGE DETECTION TEST SUITE")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for test_name, text in test_cases:
        try:
            result = analyze_text_comprehensive(text)
            print_result(test_name, text, result)
            
            # Check if translation exists
            lang_code = result['language']['language']
            base_lang = lang_code.split('_')[0]
            
            if base_lang not in ['eng', 'en']:
                if result.get('translations') and result['translations'].get('english'):
                    print("✅ PASS - Translation successful")
                    passed += 1
                else:
                    print("❌ FAIL - Translation missing")
                    failed += 1
            else:
                print("✅ PASS - English text detected")
                passed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"{'='*70}\n")


def test_language_name_mapping():
    """Test that all language codes have proper names"""
    print("\n" + "="*70)
    print("LANGUAGE NAME MAPPING TEST")
    print("="*70)
    
    test_texts = {
        'Chinese (cmn)': "你好",
        'Arabic (arb)': "مرحبا",
        'Greek (ell)': "Γεια σου",
    }
    
    for desc, text in test_texts.items():
        result = detect_language(text, detailed=True)
        lang_name = result['language_info']['language_name']
        
        print(f"\n{desc}")
        print(f"  Code: {result['language']}")
        print(f"  Name: {lang_name}")
        
        if lang_name != 'Unknown':
            print("  ✅ PASS")
        else:
            print("  ❌ FAIL - Language name is 'Unknown'")


if __name__ == "__main__":
    print("\n🧪 Running Translation & Language Detection Tests\n")
    
    # Test language name mappings first
    test_language_name_mapping()
    
    # Test all language translations
    test_all_languages()
    
    print("\n✅ All tests complete!\n")
