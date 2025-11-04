"""Test script to verify all romanized dictionaries are loaded and working"""

from translation import ROMANIZED_DICTIONARY, romanized_to_devanagari
from preprocessing import detect_language
from translation import translate_text

print("=" * 80)
print("ROMANIZED DICTIONARIES - COMPREHENSIVE TEST")
print("=" * 80)

# Test 1: Check if dictionaries are loaded
print("\n📚 Test 1: Dictionary Loading Status")
print("-" * 80)
expected_languages = ['hindi', 'marathi', 'bengali', 'tamil', 'telugu', 'punjabi']

for lang in expected_languages:
    if lang in ROMANIZED_DICTIONARY:
        word_count = len(ROMANIZED_DICTIONARY[lang])
        print(f"✅ {lang.title():15} - {word_count:3} words loaded")
    else:
        print(f"❌ {lang.title():15} - NOT LOADED")

total_words = sum(len(words) for words in ROMANIZED_DICTIONARY.values())
print(f"\n📊 Total: {len(ROMANIZED_DICTIONARY)} languages, {total_words} words")

# Test 2: Sample conversions for each language
print("\n" + "=" * 80)
print("🔄 Test 2: Sample Conversions")
print("=" * 80)

test_cases = {
    'Hindi': {
        'code': 'hin',
        'romanized': 'mai aaj bahut khush hoon',
        'sample_words': ['mai', 'aaj', 'bahut', 'khush']
    },
    'Marathi': {
        'code': 'mar',
        'romanized': 'mi aaj khup khush ahe',
        'sample_words': ['mi', 'aaj', 'khup', 'khush']
    },
    'Bengali': {
        'code': 'ben',
        'romanized': 'ami aaj khub khushi',
        'sample_words': ['ami', 'aaj', 'khub', 'khushi']
    },
    'Tamil': {
        'code': 'tam',
        'romanized': 'naan inniki romba sandhosham',
        'sample_words': ['naan', 'inniki', 'romba', 'sandhosham']
    },
    'Telugu': {
        'code': 'tel',
        'romanized': 'nenu indu chala santosham',
        'sample_words': ['nenu', 'indu', 'chala', 'santosham']
    },
    'Punjabi': {
        'code': 'pan',
        'romanized': 'main aaj bahut khush hai',
        'sample_words': ['main', 'aaj', 'bahut', 'khush']
    }
}

for lang_name, test_data in test_cases.items():
    print(f"\n{lang_name}:")
    print(f"  Input:  {test_data['romanized']}")
    
    # Convert
    converted = romanized_to_devanagari(test_data['romanized'], test_data['code'])
    print(f"  Output: {converted}")
    
    # Check sample words
    lang_key = {
        'hin': 'hindi', 'mar': 'marathi', 'ben': 'bengali',
        'tam': 'tamil', 'tel': 'telugu', 'pan': 'punjabi'
    }.get(test_data['code'])
    
    if lang_key in ROMANIZED_DICTIONARY:
        found_words = [w for w in test_data['sample_words'] 
                      if w in ROMANIZED_DICTIONARY[lang_key]]
        print(f"  Coverage: {len(found_words)}/{len(test_data['sample_words'])} words in dictionary")

# Test 3: End-to-end translation test
print("\n" + "=" * 80)
print("🌍 Test 3: End-to-End Translation Test")
print("=" * 80)

translation_tests = [
    {
        'text': 'mai aaj bahut khush hoon yaar',
        'lang': 'Hindi',
        'expected_detection': 'hin'
    },
    {
        'text': 'mi aaj khup khush ahe',
        'lang': 'Marathi',
        'expected_detection': 'mar'
    },
    {
        'text': 'ami aaj khub bhalo achi',
        'lang': 'Bengali',
        'expected_detection': 'ben'
    }
]

for i, test in enumerate(translation_tests, 1):
    print(f"\nTest {i} - {test['lang']}:")
    print(f"  Input: {test['text']}")
    
    # Detect language
    try:
        lang_result = detect_language(test['text'])
        
        # Handle both string and dict returns
        if isinstance(lang_result, str):
            detected_lang = lang_result
            is_romanized = False
        else:
            detected_lang = lang_result.get('language')
            is_romanized = lang_result.get('is_romanized', False)
        
        print(f"  Detected: {detected_lang} (romanized: {is_romanized})")
        
        if is_romanized or detected_lang in ['hin', 'mar', 'ben', 'tam', 'tel', 'pan']:
            # Translate
            try:
                translation = translate_text(
                    text=test['text'],
                    target_lang='en',
                    is_romanized=is_romanized
                )
                
                if translation['success']:
                    if 'converted_to_devanagari' in translation:
                        print(f"  Converted: {translation['converted_to_devanagari']}")
                    print(f"  Translation: {translation['translated_text']}")
                    print(f"  ✅ Success!")
                else:
                    print(f"  ❌ Translation failed: {translation.get('error')}")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
        else:
            print(f"  ⚠️ Not detected as romanized")
    except Exception as e:
        print(f"  ❌ Detection error: {str(e)}")

# Test 4: Dictionary statistics
print("\n" + "=" * 80)
print("📊 Test 4: Dictionary Statistics")
print("=" * 80)

for lang, words in ROMANIZED_DICTIONARY.items():
    print(f"\n{lang.title()}:")
    print(f"  Total words: {len(words)}")
    
    # Sample 5 random words
    sample_words = list(words.items())[:5]
    print(f"  Samples:")
    for rom, native in sample_words:
        print(f"    {rom:15} → {native}")

print("\n" + "=" * 80)
print("✅ All tests completed!")
print("=" * 80)
