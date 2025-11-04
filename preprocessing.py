"""Enhanced Multilingual Text Processing and Language Detection System"""

import sys
import os
import re
import emoji
import warnings
import numpy as np
from typing import Dict, List, Tuple, Optional, Union

from logger_config import get_logger, log_performance
from validators import TextValidator, validate_inputs, ValidationError

warnings.filterwarnings('ignore', category=FutureWarning)
logger = get_logger(__name__, level="INFO")

BASE_PATH = os.getcwd()
INDIC_NLP_RESOURCES_PATH = os.path.join(BASE_PATH, "indic_nlp_resources")
GLOTLID_MODEL_PATH = os.path.join(BASE_PATH, "cis-lmuglotlid", "model.bin")

sys.path.append(os.path.join(BASE_PATH, "indic_nlp_library"))

from indicnlp import common
from indicnlp import langinfo
from indicnlp.transliterate import unicode_transliterate as indic_transliterate
from indicnlp.tokenize import indic_tokenize
from glotlid_wrapper import GLotLID
from text_normalizer import normalize as normalize_text

common.set_resources_path(INDIC_NLP_RESOURCES_PATH)
# Initialize the transliteration library
indic_transliterate.init()
MENTION_PATTERN = re.compile(r'@\w+')
HASHTAG_PATTERN = re.compile(r'#(\w+)')
URL_PATTERN = re.compile(r'http\S+|www\.\S+')
HTML_ENTITY_PATTERN = re.compile(r'&\w+;')
WHITESPACE_PATTERN = re.compile(r'\s+')
NON_ESSENTIAL_PUNCT_PATTERN = re.compile(
    r'[^\w\s\u0900-\u097F\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF'
    r'\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u0D80-\u0DFF\u0E00-\u0E7F'
    r'\u0F00-\u0FFF\.\!\?]'
)

INDIAN_LANGUAGES = {
    'hi': 'Hindi', 'mr': 'Marathi', 'bn': 'Bengali', 'ta': 'Tamil',
    'te': 'Telugu', 'kn': 'Kannada', 'ml': 'Malayalam', 'gu': 'Gujarati',
    'pa': 'Punjabi', 'or': 'Odia', 'as': 'Assamese', 'sa': 'Sanskrit',
    'ne': 'Nepali', 'si': 'Sinhala', 'sd': 'Sindhi',
    'hin': 'Hindi', 'mar': 'Marathi', 'ben': 'Bengali', 'tam': 'Tamil',
    'tel': 'Telugu', 'kan': 'Kannada', 'mal': 'Malayalam', 'guj': 'Gujarati',
    'pan': 'Punjabi', 'ori': 'Odia', 'asm': 'Assamese', 'san': 'Sanskrit',
    'nep': 'Nepali', 'sin': 'Sinhala'
}

INTERNATIONAL_LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'tr': 'Turkish',
    'pl': 'Polish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish',
    'no': 'Norwegian', 'fi': 'Finnish', 'cs': 'Czech', 'hu': 'Hungarian',
    'el': 'Greek',
    'eng': 'English', 'spa': 'Spanish', 'fra': 'French', 'deu': 'German',
    'ita': 'Italian', 'por': 'Portuguese', 'rus': 'Russian', 'jpn': 'Japanese',
    'kor': 'Korean', 'zho': 'Chinese', 'ara': 'Arabic', 'tur': 'Turkish',
    'cmn': 'Chinese', 'arb': 'Arabic', 'ell': 'Greek'
}

# FIX #6: Robust Language Code Normalization Mapping
# GLotLID and other models may return unexpected/variant codes
# This mapping normalizes them to canonical forms for downstream compatibility
LANGUAGE_CODE_NORMALIZATION = {
    # Hindi variants
    'hif': 'hin',      # Fiji Hindi → Standard Hindi
    'bho': 'hin',      # Bhojpuri → Hindi (closely related)
    'awa': 'hin',      # Awadhi → Hindi (dialect)
    'mag': 'hin',      # Magahi → Hindi (dialect)
    'mai': 'hin',      # Maithili → Hindi (closely related)
    
    # Urdu (close to Hindi, often interchangeable for NLP)
    'urd': 'hin',      # Urdu → Hindi (very similar, especially in romanized form)
    'ur': 'hin',       # Urdu (2-letter) → Hindi
    
    # Marathi variants
    'mr': 'mar',       # 2-letter → 3-letter
    'tcz': 'mar',      # Tagin (GLotLID misdetection for romanized Marathi)
    
    # Bengali variants
    'bn': 'ben',       # 2-letter → 3-letter
    
    # Tamil variants
    'ta': 'tam',       # 2-letter → 3-letter
    
    # Telugu variants
    'te': 'tel',       # 2-letter → 3-letter
    
    # Kannada variants
    'kn': 'kan',       # 2-letter → 3-letter
    
    # Malayalam variants
    'ml': 'mal',       # 2-letter → 3-letter
    
    # Gujarati variants
    'gu': 'guj',       # 2-letter → 3-letter
    
    # Punjabi variants
    'pa': 'pan',       # 2-letter → 3-letter
    'pnb': 'pan',      # Western Punjabi → Punjabi
    
    # Odia/Oriya variants
    'or': 'ori',       # 2-letter → 3-letter
    
    # Sindhi variants
    'sd': 'sin',       # Sindhi 2-letter → 3-letter
    'snd': 'sin',      # Sindhi variant
    
    # English variants
    'en': 'eng',       # 2-letter → 3-letter
    'en-us': 'eng',    # English US → English
    'en-gb': 'eng',    # English GB → English
    
    # Obscure/constructed languages → map to 'unknown'
    'ido': 'unknown',  # Ido (constructed language)
    'io': 'unknown',   # Ido variant
    'jbo': 'unknown',  # Lojban (constructed language)
    'lfn': 'unknown',  # Lingua Franca Nova
    'vol': 'unknown',  # Volapük
    'ia': 'unknown',   # Interlingua
    'ie': 'unknown',   # Interlingue
    'nov': 'unknown',  # Novial
    
    # Undetermined/No linguistic content
    'und': 'unknown',  # Undetermined
    'zxx': 'unknown',  # No linguistic content
    'mis': 'unknown',  # Uncoded languages
    
    # Rare languages that GLotLID might detect incorrectly
    'lua': 'unknown',  # Luba-Lulua (rare African language)
    'luo': 'unknown',  # Luo (rare African language)
    'kde': 'unknown',  # Makonde (rare)
    'kpe': 'unknown',  # Kpelle (rare)
    'kri': 'unknown',  # Krio (rare)
    'ksh': 'unknown',  # Kölsch (rare German dialect)
    'kua': 'unknown',  # Kuanyama (rare)
    'ekk': 'unknown',  # Standard Estonian
    'uzn': 'unknown',  # Northern Uzbek
}

# Reverse mapping for display names
CANONICAL_LANGUAGE_NAMES = {
    **INDIAN_LANGUAGES,
    **INTERNATIONAL_LANGUAGES,
    'unknown': 'Unknown'
}

def normalize_language_code(lang_code: str, keep_suffixes: bool = False) -> str:
    """
    FIX #6: Normalize language codes to canonical forms
    
    Handles GLotLID variants, obscure languages, and ensures compatibility
    with sentiment/toxicity models that expect canonical codes.
    
    Args:
        lang_code (str): Raw language code from detection (e.g., 'hif', 'urd', 'ido')
        keep_suffixes (bool): If True, keeps suffixes like '_mixed', '_roman' (default: False)
    
    Returns:
        str: Normalized canonical language code (e.g., 'hin', 'eng', 'unknown')
    
    Examples:
        >>> normalize_language_code('hif')
        'hin'
        >>> normalize_language_code('urd')
        'hin'
        >>> normalize_language_code('hin_mixed', keep_suffixes=True)
        'hin_mixed'
        >>> normalize_language_code('ido')
        'unknown'
    """
    if not lang_code:
        return 'unknown'
    
    # Split into base code and suffix (e.g., 'hin_mixed' -> 'hin', '_mixed')
    base_code = lang_code
    suffix = ''
    
    if '_' in lang_code:
        parts = lang_code.split('_', 1)
        base_code = parts[0]
        suffix = '_' + parts[1] if keep_suffixes else ''
    
    # Convert to lowercase for case-insensitive matching
    base_code_lower = base_code.lower()
    
    # Check if normalization is needed
    if base_code_lower in LANGUAGE_CODE_NORMALIZATION:
        normalized = LANGUAGE_CODE_NORMALIZATION[base_code_lower]
        logger.info(f"[Language Code Normalization] {base_code} → {normalized}{suffix}")
        return normalized + suffix
    
    # Already canonical or not in mapping - return as is
    return base_code_lower + suffix

def get_language_display_name(lang_code: str) -> str:
    """
    Get human-readable display name for normalized language code
    
    Args:
        lang_code (str): Language code (normalized or raw)
    
    Returns:
        str: Display name (e.g., 'Hindi', 'Marathi', 'Unknown')
    """
    # Normalize first
    normalized = normalize_language_code(lang_code, keep_suffixes=False)
    
    # Get base code without suffixes
    base_code = normalized.split('_')[0]
    
    return CANONICAL_LANGUAGE_NAMES.get(base_code, 'Unknown')

ROMANIZED_INDIAN_PATTERNS = {
    'marathi': [
        r'\b(ahe|ahes|aahe|aahes|ahet|ahot)\b',
        r'\b(khup|khoop|khupach)\b',
        r'\b(mhanje|mhanun|mhanoon|mhantoy)\b',
        r'\b(bolat|bolta|bolto|bolte|boltes)\b',
        r'\b(chukicha|chukla|chuk|chukicha)\b',
        r'\b(bhet|bheta|bhetla|bheto)\b',
        r'\b(chup|choop|chupchap)\b',
        r'\b(tu|mi|me|mala|tula|tyala|tila)\b',
        r'\b(kashala|kasa|kase|kay|kuthay|kevha)\b',
        r'\b(sangu|sang|sanga|sangtoy)\b',
        r'\b(yenar|yeil|yete|yeto)\b',
        r'\b(ghari|ghara|gharun)\b',
        r'\b(kal|aaj|udya)\b',
        r'\b(thik|thiik|bara)\b',
        r'\b(nako|nakos)\b',
        r'\b(honar|hotay|hota|hoti|hoin)\b',  # Added 'hoin'
        r'\b(la|var|madhye)\b',  # Added postpositions
    ],
    'hindi': [
        r'\b(hai|hain|hoon|ho|hoga|hogi)\b',
        r'\b(bahut|bohot|bahoot|bahoth)\b',
        r'\b(kar|kara|karte|karti|karo|karenge)\b',
        r'\b(achha|accha|acha|achhe)\b',
        r'\b(chalo|chala|chale|chalte|chalenge)\b',
        r'\b(main|mein|mai|hum|tum|tumhe|tumhare)\b',
        r'\b(mujhe|mujhko|hamko|hamara)\b',
        r'\b(kya|kaise|kese|kyun|kyon|kab|kaha|kahan)\b',
        r'\b(yaar|yaara|yar|bhai|bhaiya)\b',
        r'\b(dekh|dekha|dekho|dekhte|dekhenge)\b',
        r'\b(bol|bola|bolo|bolte|bolenge)\b',
        r'\b(thik|theek|thiik)\b',
        r'\b(abhi|ab|phir|fir)\b',
        r'\b(jaana|jana|jao|jaate|jayenge|jaa|jaa raha|jaa rahe)\b',
        r'\b(aana|ana|aao|aate|aayenge)\b',
        r'\b(ye|yeh|vo|voh|woh|yahi|wohi)\b',  # Added demonstratives
        r'\b(mast|mazaa|maja|bindass|kamaal|zabardast)\b',  # Added slang
    ],
    'tamil': [
        # Pronouns
        r'\b(naan|naa|nee|neengal|avan|aval|avar|avanga)\b',
        # Common verbs with present/past/future markers
        r'\b(ren|ran|raan|raal|raar|rom|ranga|raanga)\b',  # Present tense markers
        r'\b(tten|ten|then|ttu|chu|dhu|ttom|tanga|ttanga)\b',  # Past tense markers
        r'\b(ven|veen|ppen|ppom|vom|venga|ppanga|vaanga)\b',  # Future tense markers
        # Common Tamil verbs
        r'\b(pathukaren|paathukkaren|poi|poren|varen|pannuren|pannuven)\b',
        r'\b(mudichiduven|mudichidaren|mudichitten|theduren|thedi)\b',
        r'\b(irukku|irukkum|irundhuchu|pannu|panna|po|poga|vaa|vara)\b',
        r'\b(sollu|solla|paaru|paakka|kelu|saapidu)\b',
        # Tamil-specific words
        r'\b(ippo|ippodhu|inniki|innaiku|naalai|nethu|appuram)\b',
        r'\b(romba|rombha|konjam|koncham|enna|yenna|epdi|eppadi)\b',
        r'\b(illa|illai|mudiyaathu|vendam|venda|aam|aama|seri)\b',
        # Tamil particles and connectors
        r'\b(dhan|dhaan|than|thaan|nu|nnu|oda|kuda|kooda)\b',
        r'\b(lendhu|lerndhu|kku|ku|la|le|layum)\b',
        # Tamil question words
        r'\b(enga|yeppodhu|yen|evlo|yaaru|yaar)\b',
    ],
    'generic_indic': [
        r'\b(nahi|nahin|na|nai|nay)\b',
        r'\b(tha|thi|the|thee)\b',
        r'\b(ka|ki|ke|ko|ka|ki)\b',
        r'\b(se|sai|say)\b',
        r'\b(par|pe|pe)\b',
    ]
}

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


# =============================================================================
# FIX #10: Hybrid Romanized to Native Script Conversion
# =============================================================================

# Common English words for token detection (top 500 most frequent words)
COMMON_ENGLISH_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
    'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
    'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
    'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us',
    'is', 'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did', 'having',
    'may', 'should', 'am', 'being', 'might', 'must', 'shall', 'could', 'would',
    'very', 'much', 'many', 'more', 'such', 'long', 'same', 'through', 'between',
    'find', 'man', 'here', 'thing', 'give', 'many', 'well', 'every', 'much', 'own',
    'say', 'part', 'place', 'case', 'week', 'company', 'where', 'system', 'think',
    'each', 'person', 'point', 'hand', 'high', 'follow', 'act', 'why', 'ask', 'try',
    'need', 'feel', 'become', 'leave', 'put', 'mean', 'keep', 'let', 'begin', 'seem',
    'help', 'talk', 'turn', 'start', 'show', 'hear', 'play', 'run', 'move', 'live',
    'believe', 'hold', 'bring', 'happen', 'write', 'provide', 'sit', 'stand', 'lose',
    'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand',
    'watch', 'far', 'call', 'ask', 'may', 'end', 'among', 'ever', 'across', 'although',
    'both', 'under', 'last', 'never', 'before', 'always', 'several', 'until', 'away',
    'something', 'fact', 'less', 'though', 'far', 'put', 'head', 'yet', 'government',
    'number', 'night', 'another', 'mr', 'mrs', 'miss', 'ms', 'dr', 'sir', 'madam',
    'yeah', 'yes', 'no', 'ok', 'okay', 'hi', 'hello', 'bye', 'thanks', 'please',
    'really', 'actually', 'basically', 'literally', 'totally', 'definitely', 'probably',
    'obviously', 'generally', 'usually', 'normally', 'typically', 'mostly', 'mainly',
    'right', 'wrong', 'true', 'false', 'big', 'small', 'great', 'little', 'old', 'young',
    'next', 'few', 'public', 'bad', 'able', 'late', 'hard', 'real', 'best', 'better',
    'traffic', 'heavy', 'today', 'tomorrow', 'yesterday', 'morning', 'evening', 'night',
    'meeting', 'office', 'start', 'wait', 'finish', 'complete', 'done', 'ready', 'busy',
    'free', 'available', 'schedule', 'appointment', 'conference', 'call', 'email', 'message',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'january', 'february', 'march', 'april', 'june', 'july', 'august', 'september',
    'october', 'november', 'december', 'am', 'pm', 'going', 'coming', 'doing', 'making',
    'taking', 'seeing', 'looking', 'feeling', 'thinking', 'trying', 'working', 'playing'
}

# English-specific patterns
ENGLISH_PATTERNS = {
    'contractions': re.compile(r"\b(don't|won't|can't|isn't|aren't|wasn't|weren't|hasn't|haven't|hadn't|doesn't|didn't|i'm|you're|he's|she's|it's|we're|they're|i'll|you'll|he'll|she'll|we'll|they'll|i've|you've|we've|they've|i'd|you'd|he'd|she'd|we'd|they'd)\b", re.IGNORECASE),
    'suffixes': re.compile(r'\b\w+(ing|ed|ly|er|est|tion|sion|ness|ment|ful|less|able|ible|ous|ious|ive|al|ial)\b', re.IGNORECASE),
    'all_caps': re.compile(r'\b[A-Z]{2,}\b'),  # Acronyms like USA, OK, ASAP
}


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
    
    # Method 2: Script Diversity Checking (NEW)
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


def _get_language_display_name(lang_code: str) -> str:
    """
    Get human-readable display name for language code
    
    Handles complex codes like:
    - 'mr_roman' -> 'Marathi (Romanized)'
    - 'hi_eng_mixed' -> 'Hindi-English (Code-Mixed)'
    - 'eng_indic_mixed' -> 'English-Indic (Code-Mixed)'
    """
    # Handle code-mixed languages
    if '_eng_mixed' in lang_code:
        base_lang = lang_code.split('_')[0]
        base_name = INDIAN_LANGUAGES.get(base_lang, 'Unknown')
        return f"{base_name}-English (Code-Mixed)"
    elif '_indic_mixed' in lang_code:
        base_lang = lang_code.split('_')[0]
        base_name = INTERNATIONAL_LANGUAGES.get(base_lang, 'Unknown')
        return f"{base_name}-Indic (Code-Mixed)"
    elif '_mixed' in lang_code:
        base_lang = lang_code.split('_')[0]
        base_name = (INDIAN_LANGUAGES.get(base_lang) or 
                    INTERNATIONAL_LANGUAGES.get(base_lang) or 'Unknown')
        return f"{base_name} (Code-Mixed)"
    elif '_roman' in lang_code:
        base_lang = lang_code.split('_')[0]
        base_name = INDIAN_LANGUAGES.get(base_lang, 'Unknown')
        return f"{base_name} (Romanized)"
    else:
        # Simple language code
        return (INDIAN_LANGUAGES.get(lang_code) or 
               INTERNATIONAL_LANGUAGES.get(lang_code) or 
               'Unknown')


# Lazy loading configuration - Models loaded only when needed
_glotlid_model = None  # Cached model instance
_glotlid_load_attempted = False  # Track if we tried to load
_model_load_enabled = True  # Can be disabled for memory optimization

def enable_glotlid_loading(enable: bool = True):
    """
    Enable or disable GLotLID model loading
    Useful for memory-constrained environments
    
    Args:
        enable (bool): True to enable loading, False to disable
    """
    global _model_load_enabled
    _model_load_enabled = enable
    if not enable and _glotlid_model is not None:
        print("[WARN] GLotLID loading disabled. Note: Already loaded model will remain in memory.")
        print("   Restart application to free memory.")

def unload_glotlid_model():
    """
    Unload GLotLID model from memory to free resources
    Useful for long-running applications
    """
    global _glotlid_model, _glotlid_load_attempted
    if _glotlid_model is not None:
        _glotlid_model = None
        _glotlid_load_attempted = False
        print("[OK] GLotLID model unloaded from memory (~1.6GB freed)")
    else:
        print("[INFO] GLotLID model was not loaded")

def get_glotlid_model():
    """
    Lazy load GLotLID model - only loads when first accessed
    Implements caching to avoid reloading
    
    Returns:
        GLotLID model instance or None if loading disabled/failed
    """
    global _glotlid_model, _glotlid_load_attempted
    
    # Return cached model if already loaded
    if _glotlid_model is not None:
        return _glotlid_model
    
    # Don't retry if loading is disabled or already failed
    if not _model_load_enabled or _glotlid_load_attempted:
        return None
    
    # Mark that we attempted loading
    _glotlid_load_attempted = True
    
    # Attempt to load model
    try:
        print("[INFO] Loading GLotLID model (first use, ~1.6GB)...")
        _glotlid_model = GLotLID(GLOTLID_MODEL_PATH)
        print(f"[OK] GLotLID model loaded successfully ({GLOTLID_MODEL_PATH})")
        return _glotlid_model
    except FileNotFoundError:
        print(f"[ERROR] GLotLID model file not found: {GLOTLID_MODEL_PATH}")
        print("   Language detection will use script-based detection only")
        return None
    except Exception as e:
        print(f"[WARN] Warning: Could not load GLotLID model - {str(e)}")
        print("   Language detection will fall back to script-based detection")
        return None

def is_glotlid_loaded() -> bool:
    """Check if GLotLID model is currently loaded in memory"""
    return _glotlid_model is not None

def get_memory_usage_info() -> Dict:
    """
    Get information about current memory usage
    
    Returns:
        Dict with memory usage information
    """
    return {
        'glotlid_loaded': is_glotlid_loaded(),
        'glotlid_size_estimate': '~1.6GB' if is_glotlid_loaded() else '0GB',
        'load_enabled': _model_load_enabled,
        'load_attempted': _glotlid_load_attempted
    }

def detect_script_based_language(text: str) -> Tuple[Optional[str], Dict[str, int]]:
    """
    Optimized: Detect Indian language based on Unicode script analysis
    Uses vectorized numpy operations for 10x speed improvement
    
    Args:
        text (str): Input text to analyze
        
    Returns:
        Tuple[Optional[str], Dict[str, int]]: (detected_language, script_counts)
    """
    if not text:
        return None, {}
    
    # Convert text to numpy array of code points (vectorized)
    char_codes = np.array([ord(c) for c in text], dtype=np.int32)
    
    script_counts = {}
    total_indic_chars = 0
    
    # Vectorized script detection - check all characters at once
    for lang_code, script_range in langinfo.SCRIPT_RANGES.items():
        # Vectorized comparison (much faster than loop)
        in_range = (char_codes >= script_range[0]) & (char_codes <= script_range[1])
        count = np.sum(in_range)
        
        if count > 0:
            script_counts[lang_code] = int(count)
            total_indic_chars += count
    
    if script_counts and total_indic_chars > 0:
        # Return the script with highest count
        detected_lang = max(script_counts, key=script_counts.get)
        return detected_lang, script_counts
    
    return None, {}
# Detection thresholds configuration (now configurable instead of hard-coded)
DETECTION_CONFIG = {
    'min_text_length': 3,           # Reduced from 5 to handle short text
    'glotlid_threshold': 0.5,       # Minimum GLotLID confidence (was hard-coded 0.7)
    'high_confidence_threshold': 0.8,
    'medium_confidence_threshold': 0.6,
    'low_confidence_threshold': 0.4,
    'glotlid_override_threshold': 0.9,  # FIX #2: GLotLID confidence needed to override romanized detection
    'romanized_early_detection_threshold': 0.75,  # FIX #1: Min romanized confidence for early detection
    'strong_script_threshold': 50,   # % of Indic chars for strong detection
    'code_mixed_min_threshold': 20,  # Min % for code-mixed detection
    'code_mixed_max_threshold': 50,  # Max % for code-mixed detection
    'minor_script_min_threshold': 5, # Min % for transliterated detection
    'minor_script_max_threshold': 20, # Max % for transliterated detection
    'latin_dominance_threshold': 70,  # % for latin script dominance
    'short_text_threshold': 10,      # Length for special short text handling
    'use_indic_nlp_enhanced': True,  # Use indic_nlp_library for romanized detection
    
    # FIX #3: Enhanced code-mixing detection parameters (social media tuned)
    'code_mixed_min_devanagari_chars': 3,  # Min Devanagari chars for script diversity
    'code_mixed_min_latin_chars': 5,       # Min Latin chars for script diversity
    'code_mixed_token_threshold': 0.15,    # Min ratio of tokens (15%) for each language
    'code_mixed_min_markers': 2,           # Min total markers for pattern-based detection (was 3)
    
    # FIX #7: Refined code-mixing thresholds for soft mixing (Marathi-English)
    # UPDATED: Further lowered thresholds for more sensitive detection
    'soft_code_mixing_threshold': 0.05,    # Min 5% for soft mixing detection (was 10%, then 15%)
    'aggressive_code_mixing_threshold': 0.15,  # 15%+ indicates strong code-mixing (was 25%)
    'adaptive_threshold_short_text': 0.12,  # Slightly higher for short text (8-15 chars)
    'adaptive_threshold_medium_text': 0.10, # Standard for medium text (16-30 chars)
    'adaptive_threshold_long_text': 0.08,   # Lower for long text (30+ chars) - more context
    
    # FIX #4: Short text specific thresholds to avoid early false positives
    'very_short_text_threshold': 5,        # Very short text (≤5 chars) - extremely noisy
    'short_text_romanized_threshold': 0.85,  # Higher threshold for short text romanized detection
    'short_text_glotlid_threshold': 0.4,   # Lower GLotLID threshold for short text (was 0.5)
    'short_text_script_threshold': 25,     # Lower script percentage for short text (was 30%)
    'disable_early_detection_threshold': 8,  # Disable romanized early detection for text ≤8 chars
    
    # FIX #8: Ensemble fusion parameters for GLotLID + Romanized detection
    'ensemble_enabled': True,              # Enable ensemble decision fusion
    'glotlid_high_confidence_threshold': 0.90,  # Prefer GLotLID when confidence > 0.90
    'ensemble_weight_glotlid_default': 0.60,    # Default GLotLID weight in ensemble
    'ensemble_weight_romanized_default': 0.40,  # Default romanized weight in ensemble
    'ensemble_min_combined_confidence': 0.65,   # Minimum combined confidence for ensemble
    'ensemble_conf_gap_threshold': 0.30,   # Confidence gap for method preference
    'ensemble_latin_threshold_high': 80,   # High Latin % (equal weights)
    'ensemble_latin_threshold_medium': 70, # Medium Latin % (slight GLotLID preference)
    
    # FIX #10: Hybrid romanized-to-native conversion parameters
    'hybrid_conversion_enabled': True,     # Enable hybrid conversion (vs dictionary-only)
    'preserve_english_tokens': True,       # Preserve English words in mixed text
    'preserve_capitalized_words': True,    # Preserve proper nouns (capitalized words)
    'preserve_all_caps': True,            # Preserve acronyms (e.g., USA, OK)
    'english_word_min_length': 2,         # Minimum length for English word detection
    'min_conversion_confidence': 0.3,     # Minimum confidence to attempt conversion
    'prefer_dictionary_over_itrans': True, # Prefer dictionary lookups over ITRANS
}

# Obscure/constructed languages that are rarely seen in real usage
# If detected with low confidence, likely a misdetection
OBSCURE_LANGUAGES = [
    'ido', 'jbo', 'lfn', 'vol', 'io', 'ia', 'ie', 'nov',  # Constructed languages
    'lua', 'luo', 'kde', 'kpe', 'kri', 'ksh', 'kua',      # Very rare languages
]

def update_detection_config(**kwargs):
    """
    Update detection configuration thresholds
    
    Args:
        **kwargs: Configuration parameters to update
        
    Example:
        update_detection_config(min_text_length=2, high_confidence_threshold=0.85)
    """
    for key, value in kwargs.items():
        if key in DETECTION_CONFIG:
            DETECTION_CONFIG[key] = value
        else:
            print(f"⚠️ Warning: Unknown config parameter '{key}' ignored")

def get_detection_config():
    """Get current detection configuration"""
    return DETECTION_CONFIG.copy()


def detect_glotlid_language(text: str, min_length: int = None, threshold: float = None) -> Tuple[Optional[str], float, bool]:
    """
    Detect language using GLotLID model with code-mixed detection
    Now supports configurable thresholds and better short text handling
    Uses lazy loading - model only loaded on first use
    
    Args:
        text (str): Input text to analyze
        min_length (int): Minimum text length (uses config default if None)
        threshold (float): Confidence threshold (uses config default if None)
        
    Returns:
        Tuple[Optional[str], float, bool]: (detected_language, confidence, is_code_mixed)
    """
    # Lazy load model on first use
    glotlid_model = get_glotlid_model()
    
    if glotlid_model is None:
        return None, 0.0, False
    
    try:
        # Clean text for better prediction
        clean_text = text.strip().replace('\n', ' ')
        
        # Use configurable minimum length (default from config)
        min_len = min_length if min_length is not None else DETECTION_CONFIG['min_text_length']
        if len(clean_text) < min_len:
            return None, 0.0, False
        
        # Use configurable threshold (default from config)
        conf_threshold = threshold if threshold is not None else DETECTION_CONFIG['glotlid_threshold']
        
        # FIX #4: Short text specific threshold - lower for better detection
        text_len = len(clean_text)
        if text_len <= DETECTION_CONFIG['very_short_text_threshold']:
            # Very short text (≤5 chars) - use very lenient threshold
            conf_threshold = DETECTION_CONFIG['short_text_glotlid_threshold'] * 0.7  # ~0.28
        elif text_len <= DETECTION_CONFIG['short_text_threshold']:
            # Short text (6-10 chars) - use lenient threshold
            conf_threshold = DETECTION_CONFIG['short_text_glotlid_threshold']  # 0.4
        
        # Predict language with GLotLID
        result = glotlid_model.predict_language(clean_text, k=3, threshold=conf_threshold)
        
        # Extract primary prediction
        primary_lang = result['primary_language']
        primary_confidence = result['confidence']
        is_code_mixed = result['is_code_mixed']
        
        return primary_lang, primary_confidence, is_code_mixed
    
    except Exception as e:
        print(f"⚠️ GLotLID prediction error: {e}")
        return None, 0.0, False

def analyze_text_composition(text: str) -> Dict[str, any]:
    """
    Optimized: Analyze the composition of text to understand script mixing
    Uses vectorized operations and regex for 5-10x speed improvement
    
    Args:
        text (str): Input text to analyze
        
    Returns:
        Dict: Analysis results including script percentages and character types
    """
    total_chars = len(text)
    if total_chars == 0:
        return {'total_chars': 0, 'composition': {}}
    
    # Convert text to numpy array of code points (vectorized - single pass)
    char_codes = np.array([ord(c) for c in text], dtype=np.int32)
    
    # Vectorized character type detection
    # ASCII letters (a-z, A-Z)
    latin_mask = (char_codes >= 65) & (char_codes <= 90) | (char_codes >= 97) & (char_codes <= 122)
    latin_chars = int(np.sum(latin_mask))
    
    # Digits (0-9)
    numeric_mask = (char_codes >= 48) & (char_codes <= 57)
    numeric_chars = int(np.sum(numeric_mask))
    
    # Common punctuation
    punctuation_codes = np.array([ord(c) for c in '.,!?;:'], dtype=np.int32)
    punctuation_chars = int(np.sum(np.isin(char_codes, punctuation_codes)))
    
    # Script-specific counters (vectorized)
    script_counts = {}
    indic_chars = 0
    
    for lang_code, script_range in langinfo.SCRIPT_RANGES.items():
        in_range = (char_codes >= script_range[0]) & (char_codes <= script_range[1])
        count = int(np.sum(in_range))
        
        if count > 0:
            script_counts[lang_code] = count
            indic_chars += count
    
    # Other chars (total - sum of categorized)
    other_chars = total_chars - (indic_chars + latin_chars + numeric_chars + punctuation_chars)
    
    # Calculate percentages (avoid division by zero)
    composition = {
        'indic_percentage': (indic_chars / total_chars) * 100 if total_chars > 0 else 0,
        'latin_percentage': (latin_chars / total_chars) * 100 if total_chars > 0 else 0,
        'numeric_percentage': (numeric_chars / total_chars) * 100 if total_chars > 0 else 0,
        'punctuation_percentage': (punctuation_chars / total_chars) * 100 if total_chars > 0 else 0,
        'other_percentage': (other_chars / total_chars) * 100 if total_chars > 0 else 0,
        'script_counts': script_counts,
        'is_code_mixed': indic_chars > 0 and latin_chars > 0,
        'dominant_script': 'indic' if indic_chars > latin_chars else 'latin' if latin_chars > 0 else 'other'
    }
    
    return {
        'total_chars': total_chars,
        'composition': composition
    }

@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=0, max_length=50000)
)
def detect_language(text: str, detailed: bool = False) -> Union[str, Dict]:
    """
    Advanced multilingual language detection with high accuracy
    Supports international, Indian, and code-mixed languages
    Now with configurable thresholds and better short text handling
    
    Args:
        text (str): Input text to analyze
        detailed (bool): If True, returns detailed analysis
        
    Returns:
        str or Dict: Language code or detailed analysis results
    
    Raises:
        ValidationError: If input validation fails
    """
    logger.debug(f"Detecting language for text (length={len(text)})")
    
    # FIX #5: Enhanced diagnostic logging at entry
    logger.debug(f"[Detection Start] Text preview: '{text[:100]}{'...' if len(text) > 100 else ''}', Length: {len(text)} chars")
    
    if not text or not text.strip():
        logger.warning("Empty text provided for language detection")
        return 'unknown' if not detailed else {'language': 'unknown', 'confidence': 0.0, 'method': 'empty_text'}
    
    # Get current config
    config = DETECTION_CONFIG
    text_length = len(text.strip())
    is_short_text = text_length <= config['short_text_threshold']
    is_very_short_text = text_length <= config['very_short_text_threshold']  # FIX #4: New category
    
    # FIX #5: Log text categorization
    logger.debug(f"[Text Category] Length: {text_length}, Short: {is_short_text}, Very short: {is_very_short_text}")
    
    # Analyze text composition
    composition_analysis = analyze_text_composition(text)
    
    # FIX #5: Log composition analysis
    comp = composition_analysis['composition']
    logger.debug(f"[Composition] Indic: {comp['indic_percentage']:.1f}%, Latin: {comp['latin_percentage']:.1f}%, "
                f"Numeric: {comp['numeric_percentage']:.1f}%, Code-mixed: {comp['is_code_mixed']}, "
                f"Dominant: {comp['dominant_script']}")
    
    # CRITICAL FIX: Check for code-mixing EARLY for romanized text
    # This properly detects "Yaar ye movie bahut mast hai!" as code-mixed
    is_code_mixed_detected, code_mixed_primary_lang = detect_code_mixing(text)
    
    # FIX #9: Enhanced code-mixing event logging with diagnostic details
    if is_code_mixed_detected:
        logger.info(f"[Code-Mixing FIX #9] ⚡ Early detection POSITIVE: Primary={code_mixed_primary_lang}, "
                   f"Text='{text[:60]}{'...' if len(text) > 60 else ''}', "
                   f"Latin%={composition_analysis['composition']['latin_percentage']:.1f}, "
                   f"Indic%={composition_analysis['composition']['indic_percentage']:.1f}")
        logger.info(f"[Code-Mixing] Early detection POSITIVE: Primary={code_mixed_primary_lang}")
    else:
        logger.debug(f"[Code-Mixing FIX #9] No code-mixing in early detection phase")
        logger.debug(f"[Code-Mixing] Early detection: No code-mixing detected")
    
    # CRITICAL FIX: Check for romanized Indic BEFORE GlotLID for Latin-dominant text
    # This prevents "ido", "lua", etc. false positives
    latin_percentage = composition_analysis['composition']['latin_percentage']
    indic_percentage = composition_analysis['composition']['indic_percentage']
    
    # If text is mostly Latin script and has low/no Indic script, check for romanized
    romanized_lang = None
    romanized_confidence = 0.0
    
    if latin_percentage > 60 and indic_percentage < 10:
        # First check if it's code-mixed (romanized Indian + English)
        if is_code_mixed_detected:
            # Code-mixed detected - don't return early, let full detection handle it
            logger.info(f"[Code-Mixing FIX #9] 🔀 Code-mixed context: {code_mixed_primary_lang} + English, "
                       f"Latin={latin_percentage:.1f}%, Indic={indic_percentage:.1f}%, continuing full detection pipeline")
            logger.info(f"🔀 Code-mixed detected: {code_mixed_primary_lang} + English for text: '{text[:50]}...'")
        else:
            # FIXED: Pure romanized (not code-mixed) - use enhanced detection with dynamic confidence
            romanized_lang, romanized_confidence = detect_romanized_language(text)
            
            if romanized_lang:
                logger.debug(f"Romanized detection: {romanized_lang} (confidence={romanized_confidence:.2f})")
                # Don't return early yet - check GLotLID first for potential override
    
    # Method 1: Script-based detection for Indic languages
    script_lang, script_counts = detect_script_based_language(text)
    
    # FIX #5: Log script detection
    if script_lang:
        logger.debug(f"[Script Detection] Detected: {script_lang}, Counts: {script_counts}")
    else:
        logger.debug(f"[Script Detection] No Indic script detected")
    
    # Method 2: GLotLID detection for all languages (especially code-mixed)
    glotlid_lang, glotlid_confidence, glotlid_code_mixed = detect_glotlid_language(text)
    
    # FIX #5: Log GLotLID detection
    if glotlid_lang:
        logger.info(f"[GLotLID] Detected: {glotlid_lang}, Confidence: {glotlid_confidence:.3f}, Code-mixed: {glotlid_code_mixed}")
    else:
        logger.debug(f"[GLotLID] No language detected (model not loaded or confidence too low)")
    
    # FIX #8: Ensemble Fusion Decision-Making
    # Use weighted confidence scoring from both GLotLID and romanized detection
    # instead of picking one method outright
    ensemble_result = None
    if config.get('ensemble_enabled', True) and glotlid_lang:
        # Get GLotLID model for ensemble prediction
        glotlid_model = get_glotlid_model()
        if glotlid_model is not None:
            try:
                # Call ensemble method with romanized detection results
                ensemble_result = glotlid_model.ensemble_predict(
                    text=text,
                    romanized_lang=romanized_lang,
                    romanized_confidence=romanized_confidence,
                    glotlid_high_conf_threshold=config.get('glotlid_high_confidence_threshold', 0.90),
                    k=3
                )
                
                logger.info(f"[Ensemble FIX #8] Method: {ensemble_result['detection_method']}, "
                          f"Final: {ensemble_result['final_language']} ({ensemble_result['final_confidence']:.3f})")
                logger.debug(f"[Ensemble] Decision: {ensemble_result['decision_explanation']}")
                
                # Check if ensemble made a strong decision
                if ensemble_result['final_confidence'] >= config.get('ensemble_min_combined_confidence', 0.65):
                    # Ensemble has high confidence - use it for early detection if appropriate
                    ensemble_lang = ensemble_result['final_language']
                    ensemble_conf = ensemble_result['final_confidence']
                    ensemble_method = ensemble_result['detection_method']
                    
                    # Early return for high-confidence ensemble decisions (non-code-mixed)
                    if (ensemble_conf > 0.85 and 
                        not is_code_mixed_detected and 
                        text_length > config['disable_early_detection_threshold']):
                        
                        logger.info(f"✨ Ensemble EARLY DECISION: {ensemble_lang} ({ensemble_conf:.3f}) via {ensemble_method}")
                        
                        if detailed:
                            return {
                                'language': ensemble_lang,
                                'confidence': ensemble_conf,
                                'method': f'ensemble_{ensemble_method}',
                                'text_length': text_length,
                                'is_short_text': is_short_text,
                                'is_very_short_text': is_very_short_text,
                                'composition': composition_analysis['composition'],
                                'script_analysis': {
                                    'detected_script': script_lang,
                                    'script_counts': script_counts
                                },
                                'glotlid_analysis': {
                                    'detected_language': glotlid_lang,
                                    'confidence': glotlid_confidence,
                                    'is_code_mixed': glotlid_code_mixed
                                },
                                'romanized_analysis': {
                                    'detected_language': romanized_lang,
                                    'confidence': romanized_confidence
                                },
                                'ensemble_analysis': ensemble_result,
                                'language_info': {
                                    'is_indian_language': ensemble_lang in INDIAN_LANGUAGES,
                                    'is_international_language': ensemble_lang in INTERNATIONAL_LANGUAGES,
                                    'is_code_mixed': False,
                                    'is_romanized': romanized_lang is not None,
                                    'language_name': INDIAN_LANGUAGES.get(ensemble_lang) or INTERNATIONAL_LANGUAGES.get(ensemble_lang, 'Unknown')
                                },
                                'detection_config': config
                            }
                        else:
                            return ensemble_lang
                    
            except Exception as e:
                logger.warning(f"Ensemble prediction failed: {e}, falling back to original logic")
                ensemble_result = None
    
    # FIX #2: GLotLID Override Logic (Fallback if ensemble not used)
    # FIX #4: Prevent early detection for short text to avoid false positives
    # If GLotLID has VERY high confidence (>threshold), it overrides romanized detection
    if ensemble_result is None and romanized_lang and romanized_confidence > config['romanized_early_detection_threshold']:
        # FIX #4: Disable early detection for very short text (≤8 chars) - too noisy
        if text_length <= config['disable_early_detection_threshold']:
            logger.info(f"⏸️  Short text ({text_length} chars): Skipping romanized early detection to avoid false positives")
            # Don't clear romanized_lang, but don't return early - let full pipeline decide
        elif glotlid_lang and glotlid_confidence > config['glotlid_override_threshold']:
            # GLotLID has higher confidence - override romanized detection
            logger.info(f"⚡ GLotLID OVERRIDE: {glotlid_lang} (confidence={glotlid_confidence:.2f}) overrides romanized {romanized_lang} ({romanized_confidence:.2f})")
            # Clear romanized detection - let GLotLID handle it
            romanized_lang = None
            romanized_confidence = 0.0
        else:
            # FIX #4: For short text, require HIGHER romanized confidence
            required_confidence = config['short_text_romanized_threshold'] if is_short_text else config['romanized_early_detection_threshold']
            
            if romanized_confidence >= required_confidence:
                # Romanized confidence is high enough and GLotLID doesn't override
                logger.info(f"🎯 Romanized Indic detected: {romanized_lang} (confidence={romanized_confidence:.2f}) - GLotLID not strong enough to override")
                if detailed:
                    return {
                        'language': romanized_lang,
                        'confidence': romanized_confidence,
                        'method': 'romanized_indic_early_detection',
                        'text_length': text_length,
                        'is_short_text': is_short_text,
                        'is_very_short_text': is_very_short_text,
                        'composition': composition_analysis['composition'],
                        'script_analysis': {
                            'detected_script': None,
                            'script_counts': {}
                        },
                        'glotlid_analysis': {
                            'detected_language': glotlid_lang,
                            'confidence': glotlid_confidence,
                            'is_code_mixed': glotlid_code_mixed,
                            'note': f'GLotLID prediction ({glotlid_confidence:.2f}) not strong enough to override romanized detection'
                        },
                        'language_info': {
                            'is_indian_language': True,
                            'is_international_language': False,
                            'is_code_mixed': False,
                            'is_romanized': True,
                            'language_name': INDIAN_LANGUAGES.get(romanized_lang, 'Unknown')
                        },
                        'detection_config': config,
                        'override_info': {
                            'romanized_confidence': romanized_confidence,
                            'glotlid_confidence': glotlid_confidence,
                            'override_threshold': config['glotlid_override_threshold'],
                            'override_applied': False,
                            'short_text_adjusted': is_short_text
                        }
                    }
                else:
                    return romanized_lang
            else:
                logger.info(f"⏸️  Short text: Romanized confidence {romanized_confidence:.2f} below required {required_confidence:.2f}, continuing detection")
    
    # CRITICAL FIX: Filter obscure/constructed languages with low confidence
    # These are almost never seen in real usage and are likely misdetections
    if glotlid_lang in OBSCURE_LANGUAGES:
        logger.warning(f"⚠️  Obscure language detected: {glotlid_lang} with confidence {glotlid_confidence:.2%}")
        
        # If confidence is not very high, treat as likely misdetection
        if glotlid_confidence < 0.8:
            logger.info(f"🔧 Filtering obscure language '{glotlid_lang}', checking for romanized Indic...")
            
            # Check if this might be romanized Indic
            if latin_percentage > 50:
                romanized_lang, romanized_confidence = detect_romanized_indian_language(text)
                if romanized_lang:
                    logger.info(f"✅ Corrected '{glotlid_lang}' → '{romanized_lang}' (romanized Indic, confidence={romanized_confidence:.2f})")
                    # Override GlotLID with romanized detection
                    if detailed:
                        return {
                            'language': romanized_lang,
                            'confidence': romanized_confidence,  # FIXED: Use dynamic confidence
                            'method': 'obscure_filtered_romanized_detected',
                            'text_length': text_length,
                            'is_short_text': is_short_text,
                            'is_very_short_text': is_very_short_text,  # FIX #4
                            'composition': composition_analysis['composition'],
                            'script_analysis': {
                                'detected_script': script_lang,
                                'script_counts': script_counts
                            },
                            'glotlid_analysis': {
                                'detected_language': glotlid_lang,
                                'confidence': glotlid_confidence,
                                'is_code_mixed': glotlid_code_mixed,
                                'note': f'Filtered obscure language ({glotlid_lang}), corrected to romanized Indic'
                            },
                            'language_info': {
                                'is_indian_language': True,
                                'is_international_language': False,
                                'is_code_mixed': False,
                                'is_romanized': True,
                                'language_name': INDIAN_LANGUAGES.get(romanized_lang, 'Unknown')
                            },
                            'detection_config': config
                        }
                    else:
                        return romanized_lang
            
            # If no romanized match, mark as unknown with low confidence
            logger.info(f"Marking obscure language '{glotlid_lang}' as unknown")
            glotlid_lang = 'unknown'
            glotlid_confidence = 0.3
    
    # Decision logic for high accuracy (using configurable thresholds)
    detected_language = 'unknown'
    detection_method = 'unknown'
    final_confidence = 0.0
    
    indic_percentage = composition_analysis['composition']['indic_percentage']
    latin_percentage = composition_analysis['composition']['latin_percentage']
    is_code_mixed = composition_analysis['composition']['is_code_mixed']
    
    # FIX #4: Enhanced short text handling to avoid early false positives
    # Special handling for short text
    if is_short_text:
        logger.debug(f"Short text detected ({text_length} chars), using adjusted thresholds")
        logger.info(f"[Short Text Mode] Very short: {is_very_short_text}, GLotLID threshold: {config['short_text_glotlid_threshold']}, "
                   f"Script threshold: {config['short_text_script_threshold']}%")
        
        # For very short text (≤5 chars), be very conservative
        if is_very_short_text:
            logger.debug(f"Very short text ({text_length} chars), extremely conservative detection")
            # Priority 1: GLotLID with very low threshold (always try it first)
            if glotlid_lang and glotlid_confidence > 0.3:  # Very lenient for very short
                detected_language = glotlid_lang
                detection_method = 'glotlid_very_short_text'
                final_confidence = min(0.70, glotlid_confidence)  # Cap confidence for very short
                logger.info(f"[Short Text Decision] Very short GLotLID: {detected_language} (confidence capped at {final_confidence:.2f})")
            # Priority 2: Strong script presence
            elif script_lang and indic_percentage > 50:  # Need strong signal
                detected_language = script_lang
                detection_method = 'script_very_short_text'
                final_confidence = min(0.75, indic_percentage / 100 + 0.1)
                logger.info(f"[Short Text Decision] Very short script: {detected_language} (Indic: {indic_percentage:.1f}%)")
            # Priority 3: Fallback to 'unknown' for very short ambiguous text
            else:
                detected_language = 'unknown'
                detection_method = 'very_short_text_insufficient_data'
                final_confidence = 0.3
                logger.warning(f"Very short text '{text}' - insufficient data for reliable detection")
                logger.info(f"[Short Text Decision] Very short insufficient data: Returning 'unknown'")
        else:
            # Short text (6-10 chars) - use adjusted thresholds
            # Priority 1: Always try GLotLID first with lowered threshold
            if glotlid_lang and glotlid_confidence > config['short_text_glotlid_threshold']:
                detected_language = glotlid_lang
                detection_method = 'glotlid_short_text'
                final_confidence = min(0.80, glotlid_confidence)  # Cap confidence for short text
                logger.info(f"[Short Text Decision] GLotLID: {detected_language} (confidence: {glotlid_confidence:.2f}, capped at {final_confidence:.2f})")
            # Priority 2: Script analysis with lowered threshold
            elif script_lang and indic_percentage > config['short_text_script_threshold']:
                detected_language = script_lang
                detection_method = 'script_analysis_short_text'
                final_confidence = min(0.85, indic_percentage / 100 + 0.1)
                logger.info(f"[Short Text Decision] Script: {detected_language} (Indic: {indic_percentage:.1f}%)")
            # Priority 3: Romanized detection (if present and confident enough)
            elif romanized_lang and romanized_confidence > config['short_text_romanized_threshold']:
                detected_language = romanized_lang
                detection_method = 'romanized_short_text'
                final_confidence = romanized_confidence * 0.9  # Reduce confidence for short text
                logger.info(f"[Short Text Decision] Romanized: {detected_language} (confidence reduced to {final_confidence:.2f})")
            # Priority 4: Fallback to basic script or Latin default
            else:
                if indic_percentage > 0:
                    detected_language = script_lang if script_lang else 'unknown'
                    detection_method = 'script_fallback_short_text'
                    final_confidence = 0.4
                    logger.info(f"[Short Text Decision] Script fallback: {detected_language}")
                elif latin_percentage > 50:
                    detected_language = 'eng'  # Default to English for short Latin text
                    detection_method = 'latin_fallback_short_text'
                    final_confidence = 0.4
                    logger.info(f"[Short Text Decision] Latin fallback: English")
                else:
                    detected_language = 'unknown'
                    detection_method = 'short_text_ambiguous'
                    final_confidence = 0.3
                    logger.info(f"[Short Text Decision] Ambiguous: Returning 'unknown'")
    else:
        # Standard detection logic for normal-length text (using configurable thresholds)
        logger.debug(f"[Standard Detection] Using normal-length text detection logic")
        
        # FIX #8: Priority 0.5 - Use ensemble result if available and confident
        if ensemble_result and ensemble_result['final_confidence'] >= config.get('ensemble_min_combined_confidence', 0.65):
            detected_language = ensemble_result['final_language']
            detection_method = f"ensemble_{ensemble_result['detection_method']}"
            final_confidence = ensemble_result['final_confidence']
            logger.info(f"[Detection Decision] Priority 0.5 (FIX #8) - Ensemble: {detected_language} ({final_confidence:.3f}) via {ensemble_result['detection_method']}")
        
        # Priority 1: Very high confidence GLotLID (>95%) - Trust it completely
        # This helps distinguish between Devanagari-based languages (Hindi, Marathi, etc.)
        elif glotlid_lang and glotlid_confidence > 0.95:
            detected_language = glotlid_lang
            detection_method = 'glotlid_high_confidence'
            final_confidence = glotlid_confidence
            logger.info(f"[Detection Decision] Priority 1 - Very high confidence GLotLID: {detected_language} ({final_confidence:.3f})")
        
        # Priority 2: GLotLID code-mixed detection (handles Hinglish, etc.)
        elif glotlid_code_mixed and glotlid_lang and glotlid_confidence > config['glotlid_threshold']:
            detected_language = f"{glotlid_lang}_mixed"
            detection_method = 'glotlid_code_mixed'
            final_confidence = glotlid_confidence
            logger.info(f"[Detection Decision] Priority 2 - GLotLID code-mixed: {detected_language} ({final_confidence:.3f})")
        
        # Priority 3: Strong Indic script presence (but lower priority than very high confidence GlotLID)
        elif script_lang and indic_percentage > config['strong_script_threshold']:
            detected_language = script_lang
            detection_method = 'script_analysis'
            final_confidence = min(0.95, indic_percentage / 100 + 0.1)
            logger.info(f"[Detection Decision] Priority 3 - Strong script: {detected_language} (Indic: {indic_percentage:.1f}%)")
        
        # Priority 4: High confidence GLotLID detection
        elif glotlid_lang and glotlid_confidence > config['high_confidence_threshold']:
            # Even with high confidence, check for code-mixing in Latin-script text
            if latin_percentage > 70:
                is_mixed, primary_lang = detect_code_mixing(text)
                if is_mixed:
                    if primary_lang == 'eng':
                        detected_language = f"{glotlid_lang}_indic_mixed"
                        logger.info(f"[Detection Decision] Priority 4 - GLotLID + code-mixed (English primary): {detected_language}")
                    else:
                        detected_language = f"{primary_lang}_eng_mixed"
                        logger.info(f"[Detection Decision] Priority 4 - GLotLID + code-mixed (Indic primary): {detected_language}")
                    detection_method = 'code_mixed_high_confidence'
                    final_confidence = 0.82
                else:
                    detected_language = glotlid_lang
                    detection_method = 'glotlid'
                    final_confidence = glotlid_confidence
                    logger.info(f"[Detection Decision] Priority 4 - GLotLID (no code-mixing): {detected_language} ({final_confidence:.3f})")
            else:
                detected_language = glotlid_lang
                detection_method = 'glotlid'
                final_confidence = glotlid_confidence
                logger.info(f"[Detection Decision] Priority 4 - GLotLID: {detected_language} ({final_confidence:.3f})")
        
        # Priority 4: Code-mixed with significant Indic presence
        elif (script_lang and 
              config['code_mixed_min_threshold'] <= indic_percentage <= config['code_mixed_max_threshold'] 
              and is_code_mixed):
            detected_language = f"{script_lang}_mixed"
            detection_method = 'code_mixed_analysis'
            final_confidence = min(0.85, indic_percentage / 100 + 0.2)
        
        # Priority 5: Medium confidence GLotLID for international languages
        elif glotlid_lang and glotlid_confidence > config['medium_confidence_threshold']:
            # First check for code-mixing (e.g., "Tu chup bhet, guys lets continue")
            is_mixed, primary_lang = detect_code_mixing(text)
            if is_mixed and latin_percentage > 70:
                # Code-mixing detected with romanized text
                if primary_lang == 'eng':
                    detected_language = f"{glotlid_lang}_mixed"  # Use GlotLID's suggestion
                else:
                    detected_language = f"{primary_lang}_eng_mixed"
                detection_method = 'code_mixed_romanized'
                final_confidence = 0.80
            else:
                # FIXED: Check if this might be romanized Indian language (not code-mixed)
                romanized_lang, romanized_confidence = detect_romanized_indian_language(text)
                if romanized_lang and latin_percentage > 70:
                    # FIXED: Compare romanized confidence with GLotLID confidence
                    if romanized_confidence > glotlid_confidence:
                        detected_language = romanized_lang
                        detection_method = 'romanized_indic'
                        final_confidence = romanized_confidence  # FIXED: Use dynamic confidence
                    else:
                        # GLotLID has higher confidence
                        detected_language = glotlid_lang
                        detection_method = 'glotlid_medium_override_romanized'
                        final_confidence = glotlid_confidence
                        logger.debug(f"GLotLID ({glotlid_confidence:.2f}) overrides romanized ({romanized_confidence:.2f})")
                else:
                    detected_language = glotlid_lang
                    detection_method = 'glotlid_medium'
                    final_confidence = glotlid_confidence
        
        # Priority 6: Romanized Indian language with Latin dominance
        # Check for romanized/transliterated Indian languages (like "Tu khup chukicha bolat ahes")
        elif latin_percentage > config['latin_dominance_threshold']:
            # FIXED: Check for pure romanized Indian language FIRST (before code-mixing)
            romanized_lang, romanized_confidence = detect_romanized_indian_language(text)
            
            if romanized_lang and romanized_confidence >= 0.5:
                # Strong romanized language detection - likely pure romanized text with English words
                # FIXED: Compare with GLotLID if available
                if glotlid_lang and glotlid_lang != 'unknown' and glotlid_confidence > romanized_confidence:
                    detected_language = glotlid_lang
                    detection_method = 'glotlid_latin_override_romanized'
                    final_confidence = glotlid_confidence
                    logger.info(f"[Detection Decision] Priority 6 - GLotLID ({glotlid_confidence:.2f}) overrides romanized ({romanized_confidence:.2f})")
                else:
                    detected_language = romanized_lang
                    detection_method = 'romanized_indic_latin'
                    final_confidence = romanized_confidence
                    logger.info(f"[Detection Decision] Priority 6 - Romanized Indic: {romanized_lang} ({romanized_confidence:.2f})")
            else:
                # Weak or no romanized detection - check for code-mixing
                is_mixed, primary_lang = detect_code_mixing(text)
                if is_mixed:
                    if primary_lang == 'eng':
                        detected_language = 'eng_indic_mixed'
                    else:
                        detected_language = f"{primary_lang}_eng_mixed"
                    detection_method = 'code_mixed_latin_dominant'
                    final_confidence = 0.75
                    logger.info(f"[Detection Decision] Priority 6 - Code-mixed (romanized conf too low: {romanized_confidence:.2f}): {detected_language}")
                elif romanized_lang:
                    # Romanized detection exists but low confidence, and no code-mixing detected
                    detected_language = romanized_lang
                    detection_method = 'romanized_indic_latin_low_conf'
                    final_confidence = romanized_confidence
                    logger.info(f"[Detection Decision] Priority 6 - Romanized (low conf, no mixing): {romanized_lang} ({romanized_confidence:.2f})")
                elif glotlid_lang and glotlid_lang != 'unknown':
                    detected_language = glotlid_lang
                    detection_method = 'glotlid_latin'
                    final_confidence = glotlid_confidence
                    logger.warning(f"⚠️  Low confidence Latin detection: {glotlid_lang} ({glotlid_confidence:.2%})")
                else:
                    detected_language = 'eng'  # Default to English
                    detection_method = 'latin_fallback'
                    final_confidence = 0.5
        
        # Priority 7: Low confidence GLotLID fallback
        elif glotlid_lang and glotlid_lang != 'unknown':
            detected_language = glotlid_lang
            detection_method = 'glotlid_low'
            # CRITICAL FIX: Don't inflate confidence!
            # If GlotLID confidence is <50%, report it as-is with warning
            final_confidence = glotlid_confidence  # Use actual, not max(0.5, ...)
            if glotlid_confidence < 0.5:
                logger.warning(f"⚠️  Very low confidence detection: {glotlid_lang} ({glotlid_confidence:.2%})")
                logger.warning(f"   Text: '{text[:50]}...'")
                logger.warning(f"   Consider this detection unreliable!")
        
        # Priority 7: Minor Indic presence - likely transliterated
        elif (script_lang and 
              config['minor_script_min_threshold'] <= indic_percentage < config['minor_script_max_threshold']):
            detected_language = f"{script_lang}_transliterated"
            detection_method = 'transliterated'
            final_confidence = 0.5
    
    # Log the detection result
    logger.info(f"Language detected: {detected_language} (confidence={final_confidence:.2f}, method={detection_method})")
    
    # FIX #5: Comprehensive final summary logging
    logger.info(f"[FINAL RESULT] Language: {detected_language}, Confidence: {final_confidence:.3f}, Method: {detection_method}")
    logger.debug(f"[Detection Summary] Text: '{text[:50]}...', Length: {text_length}, "
                f"Script: {script_lang or 'None'}, GLotLID: {glotlid_lang or 'None'}({glotlid_confidence:.2f}), "
                f"Romanized: {romanized_lang or 'None'}({romanized_confidence:.2f}), "
                f"Code-mixed: {is_code_mixed_detected}")
    
    # FIX #6: Normalize language code before return
    # Handle suffixes (_mixed, _roman, etc.) separately for normalization
    original_detected_language = detected_language
    normalized_detected_language = normalize_language_code(detected_language, keep_suffixes=True)
    
    if original_detected_language != normalized_detected_language:
        logger.info(f"[FIX #6] Language code normalized: {original_detected_language} → {normalized_detected_language}")
    
    # Clean up language codes for return
    if not detailed:
        # Return clean language code (remove suffixes for basic mode)
        base_code = normalized_detected_language.split('_')[0] if '_' in normalized_detected_language else normalized_detected_language
        return base_code
    
    # Detailed analysis results
    result = {
        'language': normalized_detected_language,  # FIX #6: Use normalized code
        'original_language': original_detected_language,  # FIX #6: Preserve original for debugging
        'confidence': final_confidence,
        'method': detection_method,
        'text_length': text_length,
        'is_short_text': is_short_text,
        'is_very_short_text': is_very_short_text,  # FIX #4: Added very short text indicator
        'composition': composition_analysis['composition'],
        'script_analysis': {
            'detected_script': script_lang,
            'script_counts': script_counts
        },
        'glotlid_analysis': {
            'detected_language': glotlid_lang,
            'confidence': glotlid_confidence,
            'is_code_mixed': glotlid_code_mixed
        },
        'language_info': {
            'is_indian_language': normalized_detected_language.split('_')[0] in INDIAN_LANGUAGES,
            'is_international_language': normalized_detected_language.split('_')[0] in INTERNATIONAL_LANGUAGES,
            'is_code_mixed': is_code_mixed_detected or '_mixed' in normalized_detected_language or '_eng_mixed' in normalized_detected_language,
            'is_romanized': '_roman' in normalized_detected_language or (normalized_detected_language.split('_')[0] in INDIAN_LANGUAGES and latin_percentage > 70),
            'language_name': get_language_display_name(normalized_detected_language)  # FIX #6: Use new function
        },
        'detection_config': config  # Include config used for transparency
    }
    
    logger.debug(f"Detailed language analysis: {result}")
    return result

@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=0, max_length=50000)
)
def preprocess_text(text: str, preserve_emojis: bool = True, normalization_level: str = None, 
                    punctuation_mode: str = 'preserve') -> str:
    """
    Optimized: Advanced text preprocessing with multilingual support
    Uses compiled regex patterns for 5-10x speed improvement
    
    Args:
        text (str): Input text to preprocess
        preserve_emojis (bool): Whether to preserve emoji descriptions (default: True)
        normalization_level (str): Text normalization level ('light', 'moderate', 'aggressive', or None)
        punctuation_mode (str): How to handle punctuation (default: 'preserve')
        
    Returns:
        str: Cleaned and preprocessed text
    
    Raises:
        ValidationError: If input validation fails
    """
    logger.debug(f"Preprocessing text (length={len(text)}, emoji={preserve_emojis}, normalize={normalization_level})")
    if not text:
        return ""
    
    # Step 1: Apply text normalization first (if enabled)
    if normalization_level and normalization_level in ['light', 'moderate', 'aggressive']:
        text = normalize_text(text, level=normalization_level)
    
    # Step 2: Handle emojis (now preserves by default)
    if preserve_emojis:
        text = emoji.demojize(text, delimiters=(" ", " "))
    else:
        text = emoji.replace_emoji(text, replace='')
    
    # Step 3: Convert to lowercase (preserving Unicode)
    text = text.lower()
    
    # Step 4: Remove social media artifacts (using compiled patterns - much faster)
    text = MENTION_PATTERN.sub('', text)  # Remove mentions
    text = HASHTAG_PATTERN.sub(r'\1', text)  # Remove hashtag symbol but keep text
    text = URL_PATTERN.sub('', text)  # Remove URLs
    
    # Step 5: Remove HTML entities
    text = HTML_ENTITY_PATTERN.sub('', text)
    
    # Step 6: Clean excessive whitespace
    text = WHITESPACE_PATTERN.sub(' ', text).strip()
    
    # Step 7: Handle punctuation based on mode
    if punctuation_mode == 'aggressive':
        # Remove most punctuation except sentence boundaries
        text = NON_ESSENTIAL_PUNCT_PATTERN.sub('', text)
    elif punctuation_mode == 'minimal':
        # Remove only redundant/decorative punctuation
        import re
        text = re.sub(r'[`"\'\[\]{}\\]', '', text)  # Remove quotes, brackets, backslashes
    # else: 'preserve' mode - keep all punctuation
    
    return text.strip()

def get_language_statistics(text: str) -> Dict:
    """
    Get comprehensive language statistics for the input text
    
    Args:
        text (str): Input text to analyze
        
    Returns:
        Dict: Comprehensive statistics about the text
    """
    if not text:
        return {'error': 'Empty text provided'}
    
    # Get detailed language detection
    detailed_analysis = detect_language(text, detailed=True)
    
    # Additional statistics
    stats = {
        'text_length': len(text),
        'word_count': len(text.split()),
        'language_detection': detailed_analysis,
        'preprocessing_preview': {
            'original': text[:100] + '...' if len(text) > 100 else text,
            'cleaned': preprocess_text(text)[:100] + '...' if len(preprocess_text(text)) > 100 else preprocess_text(text)
        }
    }
    
    return stats

# For backward compatibility
def detect_language_simple(text: str) -> str:
    """Simple language detection for backward compatibility"""
    return detect_language(text, detailed=False)
