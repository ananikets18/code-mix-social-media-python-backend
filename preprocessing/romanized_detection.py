"""Romanized Language Detection

This module contains functions for detecting and converting romanized Indian languages.
Includes pattern-based detection, ITRANS transliteration, and hybrid conversion.

Extracted from preprocessing.py for better modularity.
"""

import sys
import os
import re
from typing import Dict, List, Tuple, Optional, Union

from logger_config import get_logger
from .language_constants import (
    ROMANIZED_INDIAN_PATTERNS,
    COMMON_ENGLISH_WORDS,
    ENGLISH_PATTERNS,
    INDIAN_LANGUAGES
)
from .detection_config import DETECTION_CONFIG

logger = get_logger(__name__, level="INFO")

# Add indic_nlp_library to path
BASE_PATH = os.getcwd()
sys.path.append(os.path.join(BASE_PATH, "indic_nlp_library"))

from indicnlp.transliterate import unicode_transliterate as indic_transliterate
from indicnlp import common as indic_common

# Flag to track if transliteration library is initialized
_transliterate_initialized = False

def _ensure_transliterate_initialized():
    """Lazy initialization of the transliteration library"""
    global _transliterate_initialized
    if not _transliterate_initialized:
        # Set resources path
        indic_resources_path = os.path.join(BASE_PATH, "indic_nlp_resources")
        indic_common.set_resources_path(indic_resources_path)
        
        # Initialize the transliteration library
        indic_transliterate.init()
        _transliterate_initialized = True
        logger.info(f"Initialized indic_nlp transliteration with resources at: {indic_resources_path}")


def detect_romanized_indian_language(text: str) -> Tuple[Optional[str], float]:
    """
    Detect if Latin-script text is romanized Indian language
    
    Returns:
        Tuple[Optional[str], float]: (detected_language, confidence_score)
            - detected_language: Language code ('hin', 'mar', 'tam', etc.) or None
            - confidence_score: Float between 0.0 and 1.0 based on pattern matches
    """
    if not text or len(text.strip()) < 3:
        return None, 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    total_words = len(words)
    
    if total_words == 0:
        return None, 0.0
    
    language_scores = {'marathi': 0, 'hindi': 0, 'tamil': 0, 'generic_indic': 0}
    matched_words = {'marathi': [], 'hindi': [], 'tamil': [], 'generic_indic': []}
    
    for lang, patterns in ROMANIZED_INDIAN_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                language_scores[lang] += len(matches)
                matched_words[lang].extend(matches)
    
    # Calculate confidence scores for each language
    total_marathi_matches = language_scores['marathi'] + (language_scores['generic_indic'] * 0.5)
    total_hindi_matches = language_scores['hindi'] + (language_scores['generic_indic'] * 0.5)
    total_tamil_matches = language_scores['tamil']  # Tamil doesn't use generic Indic patterns
    
    marathi_confidence = total_marathi_matches / total_words
    hindi_confidence = total_hindi_matches / total_words
    tamil_confidence = total_tamil_matches / total_words
    
    # FIXED: Dynamic confidence calculation with Tamil support
    detected_lang = None
    raw_confidence = 0.0
    
    # Check Tamil first (most distinctive patterns)
    if language_scores['tamil'] >= 1:
        strong_tamil = any(word in text_lower for word in 
            ['naan', 'naa', 'ren', 'ven', 'tten', 'poi', 'pathukaren', 'mudichiduven', 
             'irukku', 'ippo', 'ippodhu', 'romba', 'illa', 'illai'])
        
        if strong_tamil or language_scores['tamil'] >= 2:
            detected_lang = 'tam'
            # Higher confidence for strong markers
            raw_confidence = min(0.95, tamil_confidence + 0.4)
        elif tamil_confidence >= 0.15:
            detected_lang = 'tam'
            raw_confidence = tamil_confidence + 0.3
    
    # Check Marathi (if not Tamil)
    if not detected_lang and language_scores['marathi'] >= 1:
        strong_marathi = any(word in text_lower for word in 
            ['kashala', 'sangu', 'ahe', 'ahes', 'aahe', 'mhanje', 'bhet', 'nako'])
        
        if strong_marathi or language_scores['marathi'] >= 2:
            detected_lang = 'mar'
            # Higher confidence for strong markers
            raw_confidence = min(0.90, marathi_confidence + 0.3)
        elif marathi_confidence > hindi_confidence and marathi_confidence >= 0.2:
            detected_lang = 'mar'
            raw_confidence = marathi_confidence + 0.2
    
    # Check Hindi (if not Tamil or Marathi)
    if not detected_lang and language_scores['hindi'] >= 1:
        strong_hindi = any(word in text_lower for word in 
            ['hai', 'hoon', 'kya', 'kaise', 'yaar', 'bahut', 'mein'])
        
        if strong_hindi or language_scores['hindi'] >= 2:
            detected_lang = 'hin'
            # Higher confidence for strong markers
            raw_confidence = min(0.90, hindi_confidence + 0.3)
        elif hindi_confidence > marathi_confidence and hindi_confidence >= 0.2:
            detected_lang = 'hin'
            raw_confidence = hindi_confidence + 0.2
    
    # Fallback to generic Indic (if no specific language detected)
    if not detected_lang and language_scores['generic_indic'] >= 2:
        if language_scores['generic_indic'] / total_words >= 0.25:
            detected_lang = 'hin'
            # Lower confidence for generic markers
            raw_confidence = (language_scores['generic_indic'] / total_words) + 0.1
    
    # Normalize confidence to [0.0, 1.0] range
    final_confidence = min(1.0, max(0.0, raw_confidence))
    
    # FIX #5: Diagnostic logging for pattern-based romanized detection
    if detected_lang:
        logger.debug(f"[Romanized Pattern] Detected: {detected_lang}, Confidence: {final_confidence:.3f}, "
                    f"Marathi matches: {language_scores['marathi']}, Hindi matches: {language_scores['hindi']}, "
                    f"Tamil matches: {language_scores['tamil']}, "
                    f"Generic matches: {language_scores['generic_indic']}, Total words: {total_words}")
    else:
        logger.debug(f"[Romanized Pattern] No romanized language detected (Total words: {total_words})")
    
    return detected_lang, final_confidence


def detect_romanized_with_indic_nlp(text: str) -> Tuple[Optional[str], float]:
    """
    Enhanced romanized detection using indic_nlp_library's transliteration
    This is more robust than pattern matching as it uses the library's ITRANS mappings
    
    Returns:
        Tuple[Optional[str], float]: (detected_language, confidence_score)
            - detected_language: Language code ('hin', 'mar', etc.) or None
            - confidence_score: Float between 0.0 and 1.0 based on transliteration quality
    """
    if not text or len(text.strip()) < 3:
        return None, 0.0
    
    try:
        # Ensure transliteration library is initialized
        _ensure_transliterate_initialized()
        
        # Try converting romanized text to Devanagari for both Hindi and Marathi
        # Then check which conversion results in more valid Indic characters
        
        hindi_converted = indic_transliterate.ItransTransliterator.from_itrans(text, 'hi')
        marathi_converted = indic_transliterate.ItransTransliterator.from_itrans(text, 'mr')
        
        # Count how many Devanagari characters were generated
        hindi_indic_chars = sum(1 for c in hindi_converted if '\u0900' <= c <= '\u097F')
        marathi_indic_chars = sum(1 for c in marathi_converted if '\u0900' <= c <= '\u097F')
        
        total_chars = len(text)
        
        # If significant portion converted to Indic script, it's likely romanized Indic
        hindi_ratio = hindi_indic_chars / total_chars if total_chars > 0 else 0
        marathi_ratio = marathi_indic_chars / total_chars if total_chars > 0 else 0
        
        # Threshold: at least 30% of characters should convert to Indic script
        threshold = 0.30
        
        # FIXED: Calculate dynamic confidence based on transliteration quality
        max_ratio = max(hindi_ratio, marathi_ratio)
        
        if hindi_ratio >= threshold or marathi_ratio >= threshold:
            # Use pattern matching as tiebreaker (now returns confidence)
            pattern_lang, pattern_confidence = detect_romanized_indian_language(text)
            
            # FIX #5: Diagnostic logging for ITRANS detection
            logger.debug(f"[ITRANS Transliteration] Hindi ratio: {hindi_ratio:.3f}, Marathi ratio: {marathi_ratio:.3f}, "
                        f"Threshold: {threshold:.2f}, Pattern lang: {pattern_lang}, Pattern confidence: {pattern_confidence:.3f}")
            
            if pattern_lang:
                # Combine transliteration and pattern confidence
                combined_confidence = (max_ratio * 0.6) + (pattern_confidence * 0.4)
                logger.debug(f"[ITRANS Combined] Lang: {pattern_lang}, Combined confidence: {combined_confidence:.3f} "
                           f"(transliteration: {max_ratio:.3f} * 0.6 + pattern: {pattern_confidence:.3f} * 0.4)")
                return pattern_lang, min(0.95, combined_confidence)
            elif marathi_ratio > hindi_ratio:
                # Pure transliteration-based confidence
                confidence = min(0.85, marathi_ratio + 0.2)
                return 'mar', confidence
            else:
                # Pure transliteration-based confidence
                confidence = min(0.85, hindi_ratio + 0.2)
                return 'hin', confidence
        
        # Fallback to pattern-based detection
        return detect_romanized_indian_language(text)
        
    except Exception as e:
        logger.debug(f"Error in indic_nlp transliteration: {e}, falling back to pattern matching")
        return detect_romanized_indian_language(text)


def detect_romanized_language(text: str, use_enhanced: bool = None) -> Tuple[Optional[str], float]:
    """
    Unified romanized language detection function
    
    Args:
        text: Input text to analyze
        use_enhanced: If True, use indic_nlp_library; if False, use patterns only;
                     if None, use DETECTION_CONFIG setting
    
    Returns:
        Tuple[Optional[str], float]: (detected_language, confidence_score)
            - detected_language: Language code or None
            - confidence_score: Float between 0.0 and 1.0
    """
    if use_enhanced is None:
        use_enhanced = DETECTION_CONFIG.get('use_indic_nlp_enhanced', True)
    
    if use_enhanced:
        # Try enhanced detection first (uses indic_nlp_library + patterns)
        return detect_romanized_with_indic_nlp(text)
    else:
        # Use pattern-based detection only
        return detect_romanized_indian_language(text)


def is_english_token(token: str, romanized_dict: Optional[set] = None) -> bool:
    """
    FIX #10: Determine if a token is likely an English word
    
    Uses multiple heuristics:
    1. Common English word dictionary lookup
    2. English-specific patterns (contractions, suffixes)
    3. Capitalization patterns (proper nouns, acronyms)
    4. Cross-check with romanized dictionary to avoid false positives
    5. Numbers and alphanumeric tokens
    
    Args:
        token (str): Word token to check
        romanized_dict (Optional[set]): Set of romanized Indic words to cross-check
        
    Returns:
        bool: True if token is likely English, False otherwise
    """
    if not token or len(token) < 1:
        return False
    
    # Clean token (remove punctuation)
    clean_token = token.strip('.,!?;:\'"()[]{}').lower()
    
    if not clean_token:
        return False
    
    # Special case: Numbers and alphanumeric - always preserve
    if clean_token.isdigit() or any(c.isdigit() for c in clean_token):
        return True
    
    # Special case: Single uppercase letters (I, A) are almost always English
    if len(token) == 1 and token.isupper():
        return True
    
    # 1. Check common English words
    if clean_token in COMMON_ENGLISH_WORDS:
        # Double-check: If it's also in romanized dictionary, it's ambiguous
        # But common English words have priority
        if romanized_dict and clean_token in romanized_dict:
            # Very common English words override romanized dict
            very_common = {'the', 'to', 'of', 'and', 'a', 'in', 'is', 'it', 'you', 'that', 
                          'he', 'was', 'for', 'on', 'are', 'with', 'as', 'I', 'his', 'they',
                          'be', 'at', 'one', 'have', 'this', 'from', 'or', 'had', 'by', 'not',
                          'but', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said',
                          'if', 'do', 'will', 'each', 'about', 'how', 'up', 'out', 'them',
                          'my', 'so', 'am', 'going', 'today', 'tomorrow', 'yesterday',
                          'morning', 'evening', 'night', 'time', 'day', 'week', 'month', 'year'}
            if clean_token in very_common:
                return True
            return False  # Ambiguous - prefer Indic
        return True
    
    # 2. Check for English contractions
    if ENGLISH_PATTERNS['contractions'].match(clean_token):
        return True
    
    # 3. Check for ALL CAPS (likely acronym or emphasis)
    if ENGLISH_PATTERNS['all_caps'].match(token):
        return True
    
    # 4. Check for English suffixes
    if ENGLISH_PATTERNS['suffixes'].match(clean_token) and len(clean_token) > 5:
        # Longer words with English suffixes are likely English
        # But cross-check with romanized dict
        if romanized_dict and clean_token in romanized_dict:
            return False
        return True
    
    # 5. Check capitalization (proper nouns)
    # If token starts with capital and is not at sentence start, likely proper noun
    if token[0].isupper() and len(token) > 2:
        # Proper nouns in English context are likely English
        # But not if it's in romanized dictionary
        if romanized_dict and clean_token in romanized_dict:
            return False
        return True
    
    return False


def convert_romanized_to_native(text: str, lang_code: str, preserve_english: bool = True) -> Dict:
    """
    FIX #10: Hybrid romanized-to-native script conversion for mixed language text
    
    Intelligently converts romanized Indic text to native script while preserving
    English words, proper nouns, and other Latin script content.
    
    Features:
    - Token-level language detection (English vs Indic)
    - Selective transliteration (only Indic tokens)
    - Preserves English words, proper nouns, punctuation
    - Uses both ITRANS and romanized dictionary methods
    - Provides detailed conversion statistics
    
    Args:
        text (str): Input text (may be mixed language)
        lang_code (str): Target language code ('hin', 'mar', 'ben', etc.)
        preserve_english (bool): If True, skip English tokens from conversion
        
    Returns:
        Dict: {
            'converted_text': str,  # Final converted text
            'original_text': str,   # Original input
            'conversion_method': str,  # 'hybrid', 'dictionary', 'itrans', or 'none'
            'statistics': {
                'total_tokens': int,
                'converted_tokens': int,
                'preserved_tokens': int,  # English words preserved
                'failed_tokens': int,     # Couldn't convert
                'conversion_rate': float  # Percentage converted
            },
            'token_details': List[Dict]  # Per-token conversion info
        }
    """
    if not text or len(text.strip()) < 2:
        return {
            'converted_text': text,
            'original_text': text,
            'conversion_method': 'none',
            'statistics': {'total_tokens': 0, 'converted_tokens': 0, 'preserved_tokens': 0, 
                          'failed_tokens': 0, 'conversion_rate': 0.0},
            'token_details': []
        }
    
    # Import romanized dictionary if available
    try:
        from translation import ROMANIZED_DICTIONARY
        lang_map = {
            'hin': 'hindi', 'hi': 'hindi', 'mar': 'marathi', 'mr': 'marathi',
            'ben': 'bengali', 'bn': 'bengali', 'tam': 'tamil', 'ta': 'tamil',
            'tel': 'telugu', 'te': 'telugu', 'pan': 'punjabi', 'pa': 'punjabi',
        }
        lang_key = lang_map.get(lang_code)
        romanized_dict = set(ROMANIZED_DICTIONARY.get(lang_key, {}).keys()) if lang_key else set()
    except ImportError:
        logger.warning("[FIX #10] Could not import ROMANIZED_DICTIONARY from translation.py")
        romanized_dict = set()
    
    # Tokenize text (preserve punctuation and spacing)
    tokens = text.split()
    converted_tokens = []
    token_details = []
    
    total_tokens = len(tokens)
    converted_count = 0
    preserved_count = 0
    failed_count = 0
    
    for i, token in enumerate(tokens):
        # Remove punctuation for analysis
        clean_token = token.strip('.,!?;:\'"()[]{}').lower()
        
        # Skip empty tokens
        if not clean_token:
            converted_tokens.append(token)
            continue
        
        # Extract punctuation to preserve
        prefix_punct = ''
        suffix_punct = ''
        for c in token:
            if not c.isalnum():
                prefix_punct += c
            else:
                break
        for c in reversed(token):
            if not c.isalnum():
                suffix_punct = c + suffix_punct
            else:
                break
        
        # Check if token is English
        is_english = is_english_token(token, romanized_dict) if preserve_english else False
        
        if is_english:
            # Preserve English token as-is
            converted_tokens.append(token)
            preserved_count += 1
            token_details.append({
                'original': token,
                'converted': token,
                'status': 'preserved_english',
                'method': 'none'
            })
            logger.debug(f"[FIX #10 Hybrid] Token '{token}' identified as English - preserved")
        else:
            # Try to convert to native script
            conversion_success = False
            converted_word = clean_token
            conversion_method = 'none'
            
            # Method 1: Dictionary lookup (fastest and most accurate for common words)
            if romanized_dict and clean_token in romanized_dict:
                try:
                    from translation import ROMANIZED_DICTIONARY
                    converted_word = ROMANIZED_DICTIONARY[lang_key][clean_token]
                    conversion_success = True
                    conversion_method = 'dictionary'
                    logger.debug(f"[FIX #10 Hybrid] Token '{clean_token}' converted via dictionary: '{converted_word}'")
                except:
                    pass
            
            # Method 2: ITRANS transliteration (for words not in dictionary)
            if not conversion_success:
                try:
                    # Ensure transliteration library is initialized
                    _ensure_transliterate_initialized()
                    
                    # Use ITRANS for Hindi/Marathi
                    if lang_code in ['hin', 'hi', 'mar', 'mr']:
                        target_lang = 'hi' if lang_code in ['hin', 'hi'] else 'mr'
                        itrans_result = indic_transliterate.ItransTransliterator.from_itrans(clean_token, target_lang)
                        
                        # Check if conversion produced native script characters
                        native_chars = sum(1 for c in itrans_result if '\u0900' <= c <= '\u097F')
                        if native_chars > 0:
                            converted_word = itrans_result
                            conversion_success = True
                            conversion_method = 'itrans'
                            logger.debug(f"[FIX #10 Hybrid] Token '{clean_token}' converted via ITRANS: '{converted_word}'")
                except Exception as e:
                    logger.debug(f"[FIX #10 Hybrid] ITRANS conversion failed for '{clean_token}': {e}")
            
            # Add back punctuation
            final_token = prefix_punct + converted_word + suffix_punct
            converted_tokens.append(final_token)
            
            if conversion_success:
                converted_count += 1
                token_details.append({
                    'original': token,
                    'converted': final_token,
                    'status': 'converted',
                    'method': conversion_method
                })
            else:
                failed_count += 1
                token_details.append({
                    'original': token,
                    'converted': token,
                    'status': 'failed',
                    'method': 'none'
                })
                logger.debug(f"[FIX #10 Hybrid] Token '{token}' could not be converted - kept as-is")
    
    # Join converted tokens
    converted_text = ' '.join(converted_tokens)
    
    # Calculate statistics
    conversion_rate = (converted_count / total_tokens * 100) if total_tokens > 0 else 0.0
    
    # Determine overall conversion method
    if converted_count > 0 and preserved_count > 0:
        overall_method = 'hybrid'
    elif converted_count > 0:
        overall_method = 'dictionary' if 'dictionary' in [t['method'] for t in token_details] else 'itrans'
    else:
        overall_method = 'none'
    
    result = {
        'converted_text': converted_text,
        'original_text': text,
        'conversion_method': overall_method,
        'statistics': {
            'total_tokens': total_tokens,
            'converted_tokens': converted_count,
            'preserved_tokens': preserved_count,
            'failed_tokens': failed_count,
            'conversion_rate': round(conversion_rate, 2)
        },
        'token_details': token_details
    }
    
    logger.info(f"[FIX #10] Hybrid conversion: {converted_count}/{total_tokens} tokens converted, "
               f"{preserved_count} preserved (English), {failed_count} failed, "
               f"method={overall_method}, rate={conversion_rate:.1f}%")
    
    return result
