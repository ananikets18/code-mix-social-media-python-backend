import re
import numpy as np
from typing import Dict, Optional, Union

from .language_constants import ROMANIZED_INDIAN_PATTERNS
from .detection_config import DETECTION_CONFIG
from .script_detection import analyze_text_composition


def detect_code_mixing(text: str, detailed: bool = False) -> Union[tuple[bool, Optional[str]], Dict]:
    if not text or len(text.strip()) < 3:
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

    config = DETECTION_CONFIG
    text_char_length = len(text.strip())

    if text_char_length <= 15:
        adaptive_threshold = config.get('adaptive_threshold_short_text', 0.12)
        text_category = 'short'
    elif text_char_length <= 30:
        adaptive_threshold = config.get('adaptive_threshold_medium_text', 0.10)
        text_category = 'medium'
    else:
        adaptive_threshold = config.get('adaptive_threshold_long_text', 0.08)
        text_category = 'long'

    indian_word_count = 0
    detected_indian_lang = None
    indian_matched_words = []

    for lang, patterns in ROMANIZED_INDIAN_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                indian_word_count += len(matches)
                indian_matched_words.extend(matches)
                if lang == 'marathi':
                    detected_indian_lang = 'mar'
                elif lang == 'hindi':
                    detected_indian_lang = 'hin'
                elif lang == 'tamil':
                    detected_indian_lang = 'tam'
                elif not detected_indian_lang:
                    detected_indian_lang = 'hin'  # Default Hindi

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

    composition_analysis = analyze_text_composition(text)
    char_codes = np.array([ord(c) for c in text], dtype=np.int32)

    devanagari_mask = (char_codes >= 0x0900) & (char_codes <= 0x097F)
    devanagari_chars = int(np.sum(devanagari_mask))

    latin_mask = ((char_codes >= 65) & (char_codes <= 90)) | ((char_codes >= 97) & (char_codes <= 122))
    latin_chars = int(np.sum(latin_mask))

    total_chars = len(text)
    devanagari_percentage = (devanagari_chars / total_chars * 100) if total_chars > 0 else 0
    latin_percentage = (latin_chars / total_chars * 100) if total_chars > 0 else 0

    min_devanagari = max(2, int(text_char_length * 0.05))
    min_latin = max(3, int(text_char_length * 0.10))

    has_script_diversity = (devanagari_chars >= min_devanagari and latin_chars >= min_latin)

    english_tokens = 0
    indic_tokens = 0
    neutral_tokens = 0

    for word in words:
        word_clean = word.strip()
        if len(word_clean) < 2:
            neutral_tokens += 1
            continue
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in word_clean)
        is_english_marker = any(re.match(pattern, word_clean) for pattern in english_markers)
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

    total_classified = indic_tokens + english_tokens
    if total_classified > 0:
        indic_ratio_strict = indic_tokens / total_classified
        english_ratio_strict = english_tokens / total_classified
        if total_words > 0:
            indic_ratio = indic_tokens / total_words
            english_ratio = english_tokens / total_words
            neutral_ratio = neutral_tokens / total_words
        else:
            indic_ratio = english_ratio = neutral_ratio = 0
    else:
        indic_ratio_strict = english_ratio_strict = 0
        indic_ratio = english_ratio = 0
        neutral_ratio = 1.0

    is_code_mixed = False
    primary_language = None
    confidence = 0.0
    detection_method = 'none'

    if has_script_diversity and devanagari_percentage >= 10 and latin_percentage >= 20:
        is_code_mixed = True
        if devanagari_percentage > latin_percentage:
            from .script_detection import detect_script_based_language
            script_lang, _ = detect_script_based_language(text)
            primary_language = script_lang if script_lang else 'hin'
        else:
            if indic_tokens > english_tokens:
                primary_language = detected_indian_lang if detected_indian_lang else 'hin'
            else:
                primary_language = 'eng'
        confidence = min(0.92, (devanagari_percentage + latin_percentage) / 100)
        detection_method = 'script_diversity'

    elif indic_tokens >= 1 and english_tokens >= 1:
        if indic_ratio >= adaptive_threshold and english_ratio >= adaptive_threshold:
            is_code_mixed = True
            if indic_ratio > english_ratio:
                primary_language = detected_indian_lang if detected_indian_lang else 'hin'
            elif english_ratio > indic_ratio:
                primary_language = 'eng'
            else:
                if indian_word_count >= english_word_count:
                    primary_language = detected_indian_lang if detected_indian_lang else 'hin'
                else:
                    primary_language = 'eng'

            mixing_strength = min(indic_ratio, english_ratio)
            if mixing_strength >= config.get('aggressive_code_mixing_threshold', 0.25):
                confidence = min(0.90, (indic_ratio + english_ratio) * 1.5)
            else:
                confidence = min(0.85, (indic_ratio + english_ratio) * 1.3)
            detection_method = 'token_analysis_adaptive'

    elif indian_word_count >= 1 and english_word_count >= 1:
        total_identified = indian_word_count + english_word_count
        min_markers = config.get('code_mixed_min_markers', 2)
        if total_identified >= min_markers:
            is_code_mixed = True
            if indian_word_count > english_word_count:
                primary_language = detected_indian_lang if detected_indian_lang else 'hin'
            else:
                primary_language = 'eng'
            confidence = min(0.80, (total_identified / total_words) * 2.0)
            detection_method = 'pattern_based'

    if detailed:
        return {
            'is_code_mixed': is_code_mixed,
            'primary_language': primary_language,
            'confidence': confidence,
            'method': detection_method,
            'text_category': text_category,
            'adaptive_threshold_used': adaptive_threshold,
            'analysis': {
                'pattern_based': {
                    'indian_word_count': indian_word_count,
                    'english_word_count': english_word_count,
                    'indian_matched_words': indian_matched_words[:10],
                    'english_matched_words': english_matched_words[:10]
                },
                'script_diversity': {
                    'has_diversity': has_script_diversity,
                    'devanagari_chars': devanagari_chars,
                    'latin_chars': latin_chars,
                    'devanagari_percentage': round(devanagari_percentage, 2),
                    'latin_percentage': round(latin_percentage, 2),
                    'min_devanagari_required': min_devanagari,
                    'min_latin_required': min_latin
                },
                'token_analysis': {
                    'total_words': total_words,
                    'indic_tokens': indic_tokens,
                    'english_tokens': english_tokens,
                    'neutral_tokens': neutral_tokens,
                    'indic_ratio': round(indic_ratio, 3),
                    'english_ratio': round(english_ratio, 3),
                    'neutral_ratio': round(neutral_ratio, 3),
                    'indic_ratio_strict': round(indic_ratio_strict, 3),
                    'english_ratio_strict': round(english_ratio_strict, 3)
                }
            }
        }
    else:
        return (is_code_mixed, primary_language)
