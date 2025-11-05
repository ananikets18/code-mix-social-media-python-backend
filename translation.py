# nlp-project/translation.py
# Lightweight translation module using Google Translate API

from googletrans import Translator
import time
import sys
import os
import json

# Add indic_nlp_library to path
BASE_PATH = os.getcwd()
sys.path.append(os.path.join(BASE_PATH, "indic_nlp_library"))

from indicnlp.transliterate import unicode_transliterate as indic_transliterate
from logger_config import get_logger

# Initialize
translator = Translator()
logger = get_logger(__name__, level="INFO")

# Common language codes (can expand as needed)
LANGUAGE_CODES = {
    # Indian Languages
    'hindi': 'hi',
    'bengali': 'bn',
    'tamil': 'ta',
    'telugu': 'te',
    'marathi': 'mr',
    'gujarati': 'gu',
    'kannada': 'kn',
    'malayalam': 'ml',
    'punjabi': 'pa',
    'urdu': 'ur',
    
    # International Languages
    'english': 'en',
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'chinese': 'zh-cn',
    'japanese': 'ja',
    'korean': 'ko',
    'arabic': 'ar',
    'russian': 'ru',
    'portuguese': 'pt',
    'italian': 'it',
    'dutch': 'nl',
    'turkish': 'tr',
}

# Load romanized dictionaries from JSON files
def load_romanized_dictionaries():
    """
    Load romanized dictionaries from JSON files
    
    Returns:
        dict: Dictionary mapping language names to word mappings
    """
    dictionaries = {}
    dict_dir = os.path.join(BASE_PATH, "romanized_dictionaries")
    
    # Language file mappings (filename -> language key)
    language_files = {
        'hindi.json': 'hindi',
        'marathi.json': 'marathi',
        'bengali.json': 'bengali',
        'tamil.json': 'tamil',
        'telugu.json': 'telugu',
        'punjabi.json': 'punjabi',
    }
    
    for filename, lang_key in language_files.items():
        filepath = os.path.join(dict_dir, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Flatten categories into single dictionary
                word_map = {}
                for category, words in data.get('categories', {}).items():
                    word_map.update(words)
                
                dictionaries[lang_key] = word_map
                logger.debug(f"✅ Loaded {len(word_map)} words for {lang_key}")
                
            except Exception as e:
                logger.error(f"❌ Failed to load {filename}: {str(e)}")
        else:
            logger.warning(f"⚠️ Dictionary file not found: {filepath}")
    
    return dictionaries

# Load dictionaries at module initialization
ROMANIZED_DICTIONARY = load_romanized_dictionaries()
logger.info(f"📚 Loaded {len(ROMANIZED_DICTIONARY)} romanized dictionaries")


def romanized_to_devanagari(text, lang_code):
    """
    FIX #10 (Enhanced): Convert romanized Indian language text to native script
    
    Now uses hybrid conversion that intelligently handles mixed language text:
    - Preserves English words and proper nouns
    - Only converts romanized Indic tokens
    - Supports both dictionary and ITRANS methods
    - Provides detailed conversion statistics
    
    Uses word-level dictionary mapping for common casual romanization
    Falls back to ITRANS transliteration for words not in dictionary
    
    Supports: Hindi, Marathi, Bengali, Tamil, Telugu, Punjabi
    
    Args:
        text (str): Romanized text (e.g., "aaj traffic bahut hai")
        lang_code (str): Language code ('hin', 'mar', 'ben', 'tam', 'tel', 'pan', etc.)
        
    Returns:
        str: Text in native script or original if conversion fails
    """
    # Import hybrid conversion function from preprocessing
    try:
        from preprocessing import convert_romanized_to_native
        
        # Use the new hybrid conversion
        result = convert_romanized_to_native(text, lang_code, preserve_english=True)
        
        # Log statistics
        stats = result['statistics']
        logger.debug(f"[Romanized] {stats['converted_tokens']}/{stats['total_tokens']} converted, "
                    f"method={result['conversion_method']}")
        
        # Return converted text if any tokens were converted
        if stats['converted_tokens'] > 0:
            return result['converted_text']
        else:
            logger.debug(f"No romanized words converted for '{text[:30]}...'")
            return text
            
    except ImportError as e:
        logger.warning(f"[FIX #10] Could not import hybrid conversion, using legacy method: {e}")
        # Fall back to legacy dictionary-only method
        pass
    except Exception as e:
        logger.warning(f"[FIX #10] Hybrid conversion failed: {e}, using legacy method")
        pass
    
    # LEGACY METHOD (dictionary-only, for backward compatibility)
    # Map ISO codes to language keys
    lang_map = {
        # Hindi
        'hin': 'hindi', 'hi': 'hindi',
        # Marathi
        'mar': 'marathi', 'mr': 'marathi',
        # Bengali
        'ben': 'bengali', 'bn': 'bengali',
        # Tamil
        'tam': 'tamil', 'ta': 'tamil',
        # Telugu
        'tel': 'telugu', 'te': 'telugu',
        # Punjabi
        'pan': 'punjabi', 'pa': 'punjabi',
    }
    
    # Get language key for dictionary
    lang_key = lang_map.get(lang_code)
    
    # Only process languages that have dictionaries
    if lang_key not in ROMANIZED_DICTIONARY:
        logger.debug(f"Language {lang_code} doesn't have romanization dictionary")
        return text
    
    try:
        # Split text into words (preserve punctuation and spaces)
        words = text.split()
        converted_words = []
        dictionary = ROMANIZED_DICTIONARY[lang_key]
        conversion_count = 0
        
        for word in words:
            # Remove punctuation for lookup
            clean_word = word.strip('.,!?;:').lower()
            
            # Check dictionary
            if clean_word in dictionary:
                # Replace with Devanagari
                devanagari_word = dictionary[clean_word]
                # Preserve original punctuation
                if word != clean_word:
                    # Add back punctuation
                    punctuation = ''.join(c for c in word if not c.isalnum())
                    converted_words.append(devanagari_word + punctuation)
                else:
                    converted_words.append(devanagari_word)
                conversion_count += 1
            else:
                # Keep original word (might be English or proper noun)
                converted_words.append(word)
        
        # Join words back
        converted_text = ' '.join(converted_words)
        
        if conversion_count > 0:
            logger.info(f"✅ Converted {conversion_count} words to Devanagari: '{text[:30]}...' → '{converted_text[:30]}...'")
            return converted_text
        else:
            logger.debug(f"No romanized words found in dictionary for '{text[:30]}...'")
            return text
        
    except Exception as e:
        logger.warning(f"⚠️  Romanization conversion failed: {e}, using original text")
        return text


def translate_text(text, target_lang='en', source_lang='auto', is_romanized=False):
    """
    Translate text to target language using Google Translate API
    Enhanced with romanized → Devanagari conversion for better accuracy
    
    Args:
        text (str): Text to translate
        target_lang (str): Target language code (e.g., 'hi', 'en', 'es')
        source_lang (str): Source language code ('auto' for auto-detection)
        is_romanized (bool): Whether the text is romanized Indian language
        
    Returns:
        dict: Translation result with text, source language, and confidence
    """
    
    ISO_CODE_MAP = {
        'hin': 'hi', 'mar': 'mr', 'ben': 'bn', 'tam': 'ta', 'tel': 'te',
        'kan': 'kn', 'mal': 'ml', 'guj': 'gu', 'pan': 'pa', 'urd': 'ur',
        'eng': 'en', 'spa': 'es', 'fra': 'fr', 'deu': 'de', 'ita': 'it',
        'por': 'pt', 'rus': 'ru', 'jpn': 'ja', 'kor': 'ko', 'ara': 'ar',
        'zho': 'zh-cn', 'cmn': 'zh-cn', 'arb': 'ar', 'ell': 'el'
    }
    
    # Store original text for result
    original_text = text
    converted_text = None
    
    # ENHANCEMENT: Convert romanized to Devanagari before translation
    if is_romanized and source_lang != 'auto' and source_lang in ['hin', 'mar', 'hi', 'mr']:
        converted_text = romanized_to_devanagari(text, source_lang)
        if converted_text != text:  # Conversion was successful
            text = converted_text
            logger.info(f"🔄 Using Devanagari text for translation: '{text[:50]}...'")
    
    if target_lang in ISO_CODE_MAP:
        target_lang = ISO_CODE_MAP[target_lang]
    if source_lang in ISO_CODE_MAP:
        source_lang = ISO_CODE_MAP[source_lang]
    
    try:
        result = translator.translate(text, dest=target_lang, src=source_lang)
        
        return {
            'success': True,
            'original_text': original_text,
            'converted_text': converted_text,  # NEW: Devanagari conversion if applied
            'translated_text': result.text,
            'source_language': result.src,
            'target_language': target_lang,
            'confidence': getattr(result, 'confidence', None),
            'pronunciation': getattr(result, 'pronunciation', None),
            'used_romanized_conversion': converted_text is not None  # NEW: Flag
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'original_text': original_text,
            'translated_text': None
        }

def translate_to_multiple_languages(text, target_languages=['hi', 'es', 'fr']):
    """
    Translate text to multiple languages
    
    Args:
        text (str): Text to translate
        target_languages (list): List of target language codes
        
    Returns:
        dict: Translations for each language
    """
    results = {}
    
    for lang in target_languages:
        # Add small delay to avoid rate limiting
        time.sleep(0.1)
        
        result = translate_text(text, target_lang=lang)
        if result['success']:
            results[lang] = result['translated_text']
        else:
            results[lang] = f"Error: {result['error']}"
    
    return {
        'original_text': text,
        'translations': results
    }

def detect_and_translate_to_english(text):
    """
    Auto-detect language and translate to English
    
    Args:
        text (str): Text in any language
        
    Returns:
        dict: Detection and translation results
    """
    return translate_text(text, target_lang='en', source_lang='auto')

def get_supported_languages():
    """
    Get list of commonly used languages
    
    Returns:
        dict: Language name to code mapping
    """
    return LANGUAGE_CODES.copy()

# Test function
def test_translation():
    """Test translation functionality"""
    print("🧪 Testing Translation Module")
    print("=" * 60)
    
    # Test 1: English to Hindi
    print("\n📝 Test 1: English → Hindi")
    result = translate_text("Hello, how are you?", target_lang='hi')
    if result['success']:
        print(f"   Original: {result['original_text']}")
        print(f"   Translated: {result['translated_text']}")
        print(f"   Source: {result['source_language']}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 2: Hindi to English
    print("\n📝 Test 2: Hindi → English")
    result = translate_text("नमस्ते, आप कैसे हैं?", target_lang='en')
    if result['success']:
        print(f"   Original: {result['original_text']}")
        print(f"   Translated: {result['translated_text']}")
        print(f"   Source: {result['source_language']}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 3: Auto-detect and translate
    print("\n📝 Test 3: Auto-detect → English")
    result = detect_and_translate_to_english("Bonjour, comment allez-vous?")
    if result['success']:
        print(f"   Original: {result['original_text']}")
        print(f"   Detected Language: {result['source_language']}")
        print(f"   English: {result['translated_text']}")
    else:
        print(f"   ❌ Error: {result['error']}")
    
    # Test 4: Multiple languages
    print("\n📝 Test 4: Translate to Multiple Languages")
    result = translate_to_multiple_languages(
        "This is a great project!",
        target_languages=['hi', 'es', 'fr', 'de']
    )
    print(f"   Original: {result['original_text']}")
    for lang, translation in result['translations'].items():
        print(f"   {lang.upper()}: {translation}")
    
    print("\n✅ Translation tests complete!")
    print("=" * 60)


# ==================== MODEL STATUS FUNCTION ====================

def get_translation_model_status():
    """Get the status of translation system"""
    global ROMANIZED_DICTIONARY
    
    dictionaries_loaded = len(ROMANIZED_DICTIONARY) if ROMANIZED_DICTIONARY else 0
    
    # Translation uses Google Translate API - always available
    # We check if dictionaries are loaded for romanized conversion
    status = "loaded" if dictionaries_loaded > 0 else "not_loaded"
    
    return {
        "status": status,
        "dictionaries_loaded": dictionaries_loaded,
        "translator": "Google Translate API",
        "romanized_support": list(ROMANIZED_DICTIONARY.keys()) if ROMANIZED_DICTIONARY else []
    }


if __name__ == "__main__":
    test_translation()
