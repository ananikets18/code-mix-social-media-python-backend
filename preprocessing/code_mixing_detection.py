"""Code-Mixing Detection

This module contains functions for detecting code-mixed text (e.g., Hinglish, Marathi+English).
Implements advanced detection with adaptive thresholds and comprehensive diagnostics.

Extracted from preprocessing.py for better modularity.
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Optional, Union

from logger_config import get_logger
from .language_constants import ROMANIZED_INDIAN_PATTERNS
from .detection_config import DETECTION_CONFIG
from .script_detection import analyze_text_composition

logger = get_logger(__name__, level="INFO")


def detect_code_mixing(text: str, detailed: bool = False) -> Union[tuple[bool, Optional[str]], Dict]:
    """
    FIX #7 (Enhanced): Advanced code-mixing detection with adaptive thresholds
    FIX #9 (Enhanced Logging): Comprehensive diagnostic logging for threshold tuning
    
    Detects code-mixing (e.g., Hinglish, Marathi+English) using multiple methods:
    1. Pattern-based detection (romanized Indian + English markers)
    2. Script diversity checking (Devanagari + Latin scripts)
    3. Token-level composition analysis with adaptive thresholds
    4. Soft mixing detection (handles subtle Marathi-English mixing)
    
    Args:
        text (str): Input text to analyze
        detailed (bool): If True, returns detailed analysis dictionary
    
    Returns:
        tuple[bool, Optional[str]] or Dict: 
            - Simple mode: (is_code_mixed, primary_language_code)
            - Detailed mode: Dictionary with analysis details
    """
    # FIX #9: Log entry point with text preview
    logger.debug(f"[Code-Mixing FIX #9] Starting analysis for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
    
    if not text or len(text.strip()) < 3:
        logger.debug(f"[Code-Mixing FIX #9] Text too short or empty (length={len(text.strip())}), skipping analysis")
        if detailed:
            return {'is_code_mixed': False, 'primary_language': None, 'confidence': 0.0, 'method': 'empty_text'}
        return (False, None)
    
    text_lower = text.lower()
    words = text_lower.split()
    total_words = len(words)
    
    if total_words == 0:
        if detailed:
            return {'is_code_mixed': False, 'primary_language': None, 'confidence': 0.0, 'method': 'no_words'}
        return (False, None)
    
    # Get config thresholds
    config = DETECTION_CONFIG
    
    # FIX #7: Adaptive threshold selection based on text length
    text_char_length = len(text.strip())
    
    if text_char_length <= 15:
        # Short text: slightly higher threshold to avoid false positives
        adaptive_threshold = config.get('adaptive_threshold_short_text', 0.12)
        text_category = 'short'
    elif text_char_length <= 30:
        # Medium text: standard threshold
        adaptive_threshold = config.get('adaptive_threshold_medium_text', 0.10)
        text_category = 'medium'
    else:
        # Long text: lower threshold (more context = more reliable)
        adaptive_threshold = config.get('adaptive_threshold_long_text', 0.08)
        text_category = 'long'
    
    # FIX #9: Enhanced logging with configuration details
    logger.info(f"[Code-Mixing FIX #9] Configuration - Text: {text_category} ({text_char_length} chars, {total_words} words), "
                f"Adaptive threshold: {adaptive_threshold:.3f}, "
                f"Min markers: {config.get('code_mixed_min_markers', 2)}, "
                f"Aggressive threshold: {config.get('aggressive_code_mixing_threshold', 0.25):.3f}")
    logger.debug(f"[Code-Mixing] Text category: {text_category} ({text_char_length} chars, {total_words} words), "
                f"Adaptive threshold: {adaptive_threshold:.2f}")
    
    # Method 1: Pattern-based detection (existing logic - enhanced)
    indian_word_count = 0
    detected_indian_lang = None
    indian_matched_words = []
    
    for lang, patterns in ROMANIZED_INDIAN_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                indian_word_count += len(matches)
                indian_matched_words.extend(matches)
                # Return 3-letter ISO codes
                if lang == 'marathi':
                    detected_indian_lang = 'mar'
                elif lang == 'hindi':
                    detected_indian_lang = 'hin'
                elif lang == 'tamil':
                    detected_indian_lang = 'tam'
                elif not detected_indian_lang:
                    detected_indian_lang = 'hin'  # Default to Hindi
    
    # Enhanced English markers (social media focused)
    english_markers = [
        r'\b(guys|let|lets|with|continue|journey|really|actually|anyway|literally)\b',
        r'\b(okay|ok|yeah|yup|nope|sure|maybe|perhaps|btw|omg|lol|lmao)\b',
        r'\b(what|when|where|which|who|how|why|whose|whom)\b',
        r'\b(good|bad|nice|great|awesome|cool|must|watch|bro|dude|man)\b',
        r'\b(movie|shopping|market|office|traffic|late|tired|break|party|fun)\b',
        r'\b(love|like|want|need|got|get|going|doing|know|think|feel)\b',
        r'\b(just|very|too|so|really|totally|completely|absolutely)\b',
        r'\b(this|that|these|those|here|there|now|then|today|tomorrow)\b'
    ]
    
    english_word_count = 0
    english_matched_words = []
    for pattern in english_markers:
        matches = re.findall(pattern, text_lower)
        if matches:
            english_word_count += len(matches)
            english_matched_words.extend(matches)
    
    # Method 2: Script Diversity Checking
    # Get composition analysis
    composition_analysis = analyze_text_composition(text)
    
    # Convert text to numpy array for vectorized analysis
    char_codes = np.array([ord(c) for c in text], dtype=np.int32)
    
    # Check for Devanagari script (Hindi/Marathi/etc.)
    devanagari_mask = (char_codes >= 0x0900) & (char_codes <= 0x097F)
    devanagari_chars = int(np.sum(devanagari_mask))
    
    # Check for Latin script (a-z, A-Z)
    latin_mask = ((char_codes >= 65) & (char_codes <= 90)) | ((char_codes >= 97) & (char_codes <= 122))
    latin_chars = int(np.sum(latin_mask))
    
    total_chars = len(text)
    
    # Script percentages
    devanagari_percentage = (devanagari_chars / total_chars * 100) if total_chars > 0 else 0
    latin_percentage = (latin_chars / total_chars * 100) if total_chars > 0 else 0
    
    # FIX #7: Adaptive script diversity thresholds
    min_devanagari = max(2, int(text_char_length * 0.05))  # At least 5% or 2 chars
    min_latin = max(3, int(text_char_length * 0.10))  # At least 10% or 3 chars
    
    # Script diversity detection with adaptive thresholds
    has_script_diversity = (
        devanagari_chars >= min_devanagari and 
        latin_chars >= min_latin
    )
    
    # Method 3: Token-level composition analysis (ENHANCED)
    # Classify each word as likely English, Indic, or neutral
    english_tokens = 0
    indic_tokens = 0
    neutral_tokens = 0
    
    for word in words:
        word_clean = word.strip()
        if len(word_clean) < 2:
            neutral_tokens += 1
            continue
        
        # Check if word contains Devanagari characters
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in word_clean)
        
        # Check if word matches English patterns
        is_english_marker = any(re.match(pattern, word_clean) for pattern in english_markers)
        
        # Check if word matches Indian patterns
        is_indic_marker = any(
            any(re.match(pattern, word_clean) for pattern in patterns)
            for patterns in ROMANIZED_INDIAN_PATTERNS.values()
        )
        
        if has_devanagari or is_indic_marker:
            indic_tokens += 1
        elif is_english_marker:
            english_tokens += 1
        else:
            neutral_tokens += 1
    
    # FIX #7: Enhanced ratio calculation with neutral token handling
    # Treat neutral tokens as potentially belonging to either language based on context
    total_classified = indic_tokens + english_tokens
    
    if total_classified > 0:
        # Primary ratios (excluding neutral)
        indic_ratio_strict = (indic_tokens / total_classified) if total_classified > 0 else 0
        english_ratio_strict = (english_tokens / total_classified) if total_classified > 0 else 0
        
        # Secondary ratios (including neutral - distributed proportionally)
        if total_words > 0:
            indic_ratio = (indic_tokens / total_words)
            english_ratio = (english_tokens / total_words)
            neutral_ratio = (neutral_tokens / total_words)
        else:
            indic_ratio = 0
            english_ratio = 0
            neutral_ratio = 0
    else:
        # No classified tokens
        indic_ratio_strict = 0
        english_ratio_strict = 0
        indic_ratio = 0
        english_ratio = 0
        neutral_ratio = 1.0
    
    # Decision Logic (tuned for social media and soft mixing)
    is_code_mixed = False
    primary_language = None
    confidence = 0.0
    detection_method = 'none'
    
    # FIX #5: Diagnostic logging for code-mixing analysis
    logger.debug(f"[Code-Mixing Analysis] Text length: {total_words} words, "
                f"Indian words: {indian_word_count}, English words: {english_word_count}, "
                f"Indic tokens: {indic_tokens}, English tokens: {english_tokens}, Neutral: {neutral_tokens}")
    logger.debug(f"[Code-Mixing Scripts] Devanagari: {devanagari_percentage:.1f}%, Latin: {latin_percentage:.1f}%, "
                f"Has diversity: {has_script_diversity} (min_dev={min_devanagari}, min_lat={min_latin})")
    logger.debug(f"[Code-Mixing Ratios] Indic: {indic_ratio:.3f}, English: {english_ratio:.3f}, "
                f"Neutral: {neutral_ratio:.3f}, Adaptive threshold: {adaptive_threshold:.3f}")
    
    # Priority 1: Script diversity (strong indicator)
    if has_script_diversity and devanagari_percentage >= 10 and latin_percentage >= 20:
        is_code_mixed = True
        # Determine primary language by BOTH script dominance AND token count
        if devanagari_percentage > latin_percentage:
            # Script says Indic dominant
            from .script_detection import detect_script_based_language
            script_lang, _ = detect_script_based_language(text)
            primary_language = script_lang if script_lang else 'hin'
            logger.debug(f"[Code-Mixing Decision] Script diversity: Devanagari dominant ({devanagari_percentage:.1f}% > {latin_percentage:.1f}%), "
                        f"Primary: {primary_language}")
        else:
            # Latin script dominant - check token ratio to decide
            if indic_tokens > english_tokens:
                # More Indic tokens even though Latin script dominant (romanized Indic)
                primary_language = detected_indian_lang if detected_indian_lang else 'hin'
                logger.debug(f"[Code-Mixing Decision] Script diversity: Latin dominant but more Indic tokens ({indic_tokens} > {english_tokens}), "
                           f"Primary: {primary_language}")
            else:
                primary_language = 'eng'
                logger.debug(f"[Code-Mixing Decision] Script diversity: Latin dominant with more English tokens ({english_tokens} >= {indic_tokens}), "
                           f"Primary: {primary_language}")
        confidence = min(0.92, (devanagari_percentage + latin_percentage) / 100)
        detection_method = 'script_diversity'
        logger.info(f"[Code-Mixing] DETECTED via script_diversity: Primary={primary_language}, Confidence={confidence:.2f}")
    
    # Priority 2: Token-level analysis with ADAPTIVE thresholds (enhanced for soft mixing)
    elif indic_tokens >= 1 and english_tokens >= 1:
        # Both types of tokens present
        
        # FIX #7: Use adaptive threshold instead of fixed 15%
        if indic_ratio >= adaptive_threshold and english_ratio >= adaptive_threshold:
            is_code_mixed = True
            # Use token ratio (more accurate than word count)
            if indic_ratio > english_ratio:
                primary_language = detected_indian_lang if detected_indian_lang else 'hin'
                logger.debug(f"[Code-Mixing Decision] Token analysis (adaptive): Indic dominant ({indic_ratio:.3f} > {english_ratio:.3f}), "
                           f"Primary: {primary_language}")
            elif english_ratio > indic_ratio:
                primary_language = 'eng'
                logger.debug(f"[Code-Mixing Decision] Token analysis (adaptive): English dominant ({english_ratio:.3f} > {indic_ratio:.3f}), "
                           f"Primary: {primary_language}")
            else:
                # Equal ratios - use word count as tiebreaker
                if indian_word_count >= english_word_count:
                    primary_language = detected_indian_lang if detected_indian_lang else 'hin'
                    logger.debug(f"[Code-Mixing Decision] Token analysis (adaptive): Equal ratios, word count tiebreaker: Indic ({indian_word_count} >= {english_word_count})")
                else:
                    primary_language = 'eng'
                    logger.debug(f"[Code-Mixing Decision] Token analysis (adaptive): Equal ratios, word count tiebreaker: English ({english_word_count} > {indian_word_count})")
            
            # Confidence based on mixing intensity
            mixing_strength = min(indic_ratio, english_ratio)
            if mixing_strength >= config.get('aggressive_code_mixing_threshold', 0.25):
                confidence = min(0.90, (indic_ratio + english_ratio) * 1.5)  # Strong mixing
            else:
                confidence = min(0.85, (indic_ratio + english_ratio) * 1.3)  # Soft mixing
            
            detection_method = 'token_analysis_adaptive'
            logger.info(f"[Code-Mixing] DETECTED via token_analysis (adaptive): Primary={primary_language}, Confidence={confidence:.2f}, "
                       f"Indic ratio={indic_ratio:.3f}, English ratio={english_ratio:.3f}, Threshold={adaptive_threshold:.3f}")
        else:
            logger.debug(f"[Code-Mixing] Below adaptive threshold: Indic={indic_ratio:.3f}, English={english_ratio:.3f}, Required={adaptive_threshold:.3f}")
    
    # Priority 3: Pattern-based detection (existing logic - enhanced thresholds)
    elif indian_word_count >= 1 and english_word_count >= 1:
        total_identified = indian_word_count + english_word_count
        
        # Social media tuned threshold: minimum 2 markers (was 3)
        min_markers = config.get('code_mixed_min_markers', 2)
        
        if total_identified >= min_markers:
            is_code_mixed = True
            if indian_word_count > english_word_count:
                primary_language = detected_indian_lang if detected_indian_lang else 'hin'
                logger.debug(f"[Code-Mixing Decision] Pattern-based: Indic dominant ({indian_word_count} > {english_word_count})")
            else:
                primary_language = 'eng'
                logger.debug(f"[Code-Mixing Decision] Pattern-based: English dominant ({english_word_count} >= {indian_word_count})")
            confidence = min(0.80, (total_identified / total_words) * 2.0)
            detection_method = 'pattern_based'
            logger.info(f"[Code-Mixing] DETECTED via pattern_based: Primary={primary_language}, Confidence={confidence:.2f}, "
                       f"Total markers={total_identified}/{min_markers}")
        else:
            logger.debug(f"[Code-Mixing] NOT detected: Pattern markers below threshold ({total_identified} < {min_markers})")
    else:
        logger.debug(f"[Code-Mixing] NOT detected: Insufficient markers (Indian={indian_word_count}, English={english_word_count})")
    
    # FIX #9: Final decision summary logging
    if is_code_mixed:
        logger.info(f"[Code-Mixing FIX #9] ✅ FINAL DECISION: Code-mixed={is_code_mixed}, Primary={primary_language}, "
                   f"Confidence={confidence:.3f}, Method={detection_method}, Text='{text[:40]}{'...' if len(text) > 40 else ''}'")
    else:
        logger.info(f"[Code-Mixing FIX #9] ❌ FINAL DECISION: Not code-mixed, Text='{text[:40]}{'...' if len(text) > 40 else ''}'")
    
    # Return results
    if detailed:
        return {
            'is_code_mixed': is_code_mixed,
            'primary_language': primary_language,
            'confidence': confidence,
            'method': detection_method,
            'text_category': text_category,  # FIX #7: Added text category
            'adaptive_threshold_used': adaptive_threshold,  # FIX #7: Show threshold used
            'analysis': {
                'pattern_based': {
                    'indian_word_count': indian_word_count,
                    'english_word_count': english_word_count,
                    'indian_matched_words': indian_matched_words[:10],  # Limit for readability
                    'english_matched_words': english_matched_words[:10]
                },
                'script_diversity': {
                    'has_diversity': has_script_diversity,
                    'devanagari_chars': devanagari_chars,
                    'latin_chars': latin_chars,
                    'devanagari_percentage': round(devanagari_percentage, 2),
                    'latin_percentage': round(latin_percentage, 2),
                    'min_devanagari_required': min_devanagari,  # FIX #7
                    'min_latin_required': min_latin  # FIX #7
                },
                'token_analysis': {
                    'total_words': total_words,
                    'indic_tokens': indic_tokens,
                    'english_tokens': english_tokens,
                    'neutral_tokens': neutral_tokens,
                    'indic_ratio': round(indic_ratio, 3),
                    'english_ratio': round(english_ratio, 3),
                    'neutral_ratio': round(neutral_ratio, 3),
                    'indic_ratio_strict': round(indic_ratio_strict, 3),  # FIX #7
                    'english_ratio_strict': round(english_ratio_strict, 3)  # FIX #7
                }
            }
        }
    else:
        return (is_code_mixed, primary_language)
