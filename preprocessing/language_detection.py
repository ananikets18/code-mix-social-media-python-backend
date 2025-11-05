
from typing import Dict, Union, Optional, Tuple, List
import re
import numpy as np

from logger_config import get_logger, log_performance
from validators import TextValidator, validate_inputs

from .language_constants import INDIAN_LANGUAGES, INTERNATIONAL_LANGUAGES, OBSCURE_LANGUAGES
from .detection_config import DETECTION_CONFIG
from .script_detection import detect_script_based_language, analyze_text_composition
from .romanized_detection import detect_romanized_language, detect_romanized_indian_language
from .code_mixing_detection import detect_code_mixing
from .glotlid_detection import detect_glotlid_language, get_glotlid_model
from .language_utils import normalize_language_code, get_language_display_name

logger = get_logger(__name__, level="WARNING")


@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=0, max_length=50000)
)
def detect_language(text: str, detailed: bool = False) -> Union[str, Dict]:
    """
    Advanced multilingual language detection with high accuracy.
    
    Supports international, Indian, and code-mixed languages.
    Uses ensemble fusion (GLotLID + romanized detection) for improved accuracy.
    Handles short text and romanized Indic script specially.
    
    Args:
        text (str): Input text to analyze
        detailed (bool): If True, returns detailed analysis
        
    Returns:
        str or Dict: Language code or detailed analysis results
    
    Raises:
        ValidationError: If input validation fails
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for language detection")
        return 'unknown' if not detailed else {'language': 'unknown', 'confidence': 0.0, 'method': 'empty_text'}
    
    config = DETECTION_CONFIG
    text_length = len(text.strip())
    is_short_text = text_length <= config['short_text_threshold']
    is_very_short_text = text_length <= config['very_short_text_threshold']
    
    # Analyze text composition
    composition_analysis = analyze_text_composition(text)
    comp = composition_analysis['composition']
    
    # Check for code-mixing early
    is_code_mixed_detected, code_mixed_primary_lang = detect_code_mixing(text)
    
    # Check for romanized Indic before GLotLID
    latin_percentage = comp['latin_percentage']
    indic_percentage = comp['indic_percentage']
    romanized_lang = None
    romanized_confidence = 0.0
    
    if latin_percentage > 60 and indic_percentage < 10:
        if is_code_mixed_detected:
            logger.warning(f"Code-mixed detected: {code_mixed_primary_lang} + English")
        else:
            romanized_lang, romanized_confidence = detect_romanized_language(text)
    
    # Method 1: Script-based detection
    script_lang, script_counts = detect_script_based_language(text)
    
    # Method 2: GLotLID detection
    glotlid_lang, glotlid_confidence, glotlid_code_mixed = detect_glotlid_language(text)
    
    # Ensemble fusion
    ensemble_result = None
    if config.get('ensemble_enabled', True) and glotlid_lang:
        glotlid_model = get_glotlid_model()
        if glotlid_model is not None:
            try:
                ensemble_result = glotlid_model.ensemble_predict(
                    text=text,
                    romanized_lang=romanized_lang,
                    romanized_confidence=romanized_confidence,
                    glotlid_high_conf_threshold=config.get('glotlid_high_confidence_threshold', 0.90),
                    k=3
                )
                logger.warning(f"Ensemble result: {ensemble_result['final_language']} ({ensemble_result['final_confidence']:.3f})")
                
                if (ensemble_result['final_confidence'] >= config.get('ensemble_min_combined_confidence', 0.65) and
                    ensemble_result['final_confidence'] > 0.85 and 
                    not is_code_mixed_detected and 
                    text_length > config['disable_early_detection_threshold']):
                    
                    ensemble_lang = ensemble_result['final_language']
                    if detailed:
                        return _build_detailed_result(
                            ensemble_lang, ensemble_result['final_confidence'],
                            f"ensemble_{ensemble_result['detection_method']}",
                            text_length, is_short_text, is_very_short_text,
                            composition_analysis, script_lang, script_counts,
                            glotlid_lang, glotlid_confidence, glotlid_code_mixed,
                            romanized_lang, romanized_confidence,
                            config, ensemble_result=ensemble_result
                        )
                    return ensemble_lang
            except Exception as e:
                logger.warning(f"Ensemble prediction failed: {e}")
                ensemble_result = None
    
    # Handle romanized detection
    if ensemble_result is None and romanized_lang and romanized_confidence > config['romanized_early_detection_threshold']:
        if text_length <= config['disable_early_detection_threshold']:
            logger.warning(f"Short text ({text_length} chars): Skipping early detection")
        elif glotlid_lang and glotlid_confidence > config['glotlid_override_threshold']:
            logger.warning(f"GLotLID override: {glotlid_lang} ({glotlid_confidence:.2f})")
            romanized_lang = None
            romanized_confidence = 0.0
        else:
            required_confidence = config['short_text_romanized_threshold'] if is_short_text else config['romanized_early_detection_threshold']
            if romanized_confidence >= required_confidence:
                logger.warning(f"Romanized Indic: {romanized_lang} ({romanized_confidence:.2f})")
                if detailed:
                    return _build_detailed_result(
                        romanized_lang, romanized_confidence, 'romanized_indic_early_detection',
                        text_length, is_short_text, is_very_short_text,
                        composition_analysis, script_lang, script_counts,
                        glotlid_lang, glotlid_confidence, glotlid_code_mixed,
                        romanized_lang, romanized_confidence, config
                    )
                return romanized_lang
    
    # Filter obscure languages
    if glotlid_lang in OBSCURE_LANGUAGES and glotlid_confidence < 0.8:
        logger.warning(f"Obscure language detected: {glotlid_lang}")
        if latin_percentage > 50:
            rom_lang, rom_conf = detect_romanized_indian_language(text)
            if rom_lang:
                logger.warning(f"Corrected '{glotlid_lang}' to '{rom_lang}'")
                if detailed:
                    return _build_detailed_result(
                        rom_lang, rom_conf, 'obscure_filtered_romanized_detected',
                        text_length, is_short_text, is_very_short_text,
                        composition_analysis, script_lang, script_counts,
                        glotlid_lang, glotlid_confidence, glotlid_code_mixed,
                        rom_lang, rom_conf, config
                    )
                return rom_lang
        glotlid_lang = 'unknown'
        glotlid_confidence = 0.3
    
    # Core detection logic
    detected_language, detection_method, final_confidence = _detect_language_core(
        text, text_length, is_short_text, is_very_short_text,
        composition_analysis, script_lang, script_counts,
        glotlid_lang, glotlid_confidence, glotlid_code_mixed,
        romanized_lang, romanized_confidence,
        is_code_mixed_detected, code_mixed_primary_lang,
        ensemble_result, config
    )
    
    logger.warning(f"Final language: {detected_language}, Confidence: {final_confidence:.3f}")
    
    # Normalize language code
    original_detected_language = detected_language
    normalized_detected_language = normalize_language_code(detected_language, keep_suffixes=True)
    
    if original_detected_language != normalized_detected_language:
        logger.warning(f"Language code normalized: {original_detected_language} → {normalized_detected_language}")
    
    if not detailed:
        base_code = normalized_detected_language.split('_')[0] if '_' in normalized_detected_language else normalized_detected_language
        return base_code
    
    return _build_detailed_result(
        normalized_detected_language, final_confidence, detection_method,
        text_length, is_short_text, is_very_short_text,
        composition_analysis, script_lang, script_counts,
        glotlid_lang, glotlid_confidence, glotlid_code_mixed,
        romanized_lang, romanized_confidence, config,
        original_language=original_detected_language,
        ensemble_result=ensemble_result
    )


def _detect_language_core(text, text_length, is_short_text, is_very_short_text,
                          composition_analysis, script_lang, script_counts,
                          glotlid_lang, glotlid_confidence, glotlid_code_mixed,
                          romanized_lang, romanized_confidence,
                          is_code_mixed_detected, code_mixed_primary_lang,
                          ensemble_result, config):
    """Core detection logic - returns (language, method, confidence)"""
    
    indic_percentage = composition_analysis['composition']['indic_percentage']
    latin_percentage = composition_analysis['composition']['latin_percentage']
    
    # Short text handling
    if is_short_text:
        return _detect_short_text(
            text, text_length, is_very_short_text, script_lang, indic_percentage, latin_percentage,
            glotlid_lang, glotlid_confidence, romanized_lang, romanized_confidence, config
        )
    
    # Standard detection logic
    if ensemble_result and ensemble_result['final_confidence'] >= config.get('ensemble_min_combined_confidence', 0.65):
        return ensemble_result['final_language'], f"ensemble_{ensemble_result['detection_method']}", ensemble_result['final_confidence']
    
    if glotlid_lang and glotlid_confidence > 0.95:
        return glotlid_lang, 'glotlid_high_confidence', glotlid_confidence
    
    if glotlid_code_mixed and glotlid_lang and glotlid_confidence > config['glotlid_threshold']:
        return f"{glotlid_lang}_mixed", 'glotlid_code_mixed', glotlid_confidence
    
    if script_lang and indic_percentage > config['strong_script_threshold']:
        return script_lang, 'script_analysis', min(0.95, indic_percentage / 100 + 0.1)
    
    if glotlid_lang and glotlid_confidence > config['high_confidence_threshold']:
        if latin_percentage > 70:
            is_mixed, primary_lang = detect_code_mixing(text)
            if is_mixed:
                if primary_lang == 'eng':
                    return f"{glotlid_lang}_indic_mixed", 'code_mixed_high_confidence', 0.82
                else:
                    return f"{primary_lang}_eng_mixed", 'code_mixed_high_confidence', 0.82
        return glotlid_lang, 'glotlid', glotlid_confidence
    
    if script_lang and config['code_mixed_min_threshold'] <= indic_percentage <= config['code_mixed_max_threshold'] and composition_analysis['composition']['is_code_mixed']:
        return f"{script_lang}_mixed", 'code_mixed_analysis', min(0.85, indic_percentage / 100 + 0.2)
    
    if glotlid_lang and glotlid_confidence > config['medium_confidence_threshold']:
        is_mixed, primary_lang = detect_code_mixing(text)
        if is_mixed and latin_percentage > 70:
            if primary_lang == 'eng':
                return f"{glotlid_lang}_mixed", 'code_mixed_romanized', 0.80
            else:
                return f"{primary_lang}_eng_mixed", 'code_mixed_romanized', 0.80
        
        rom_lang, rom_conf = detect_romanized_indian_language(text)
        if rom_lang and latin_percentage > 70:
            if rom_conf > glotlid_confidence:
                return rom_lang, 'romanized_indic', rom_conf
            else:
                return glotlid_lang, 'glotlid_medium_override_romanized', glotlid_confidence
        return glotlid_lang, 'glotlid_medium', glotlid_confidence
    
    if latin_percentage > config['latin_dominance_threshold']:
        rom_lang, rom_conf = detect_romanized_indian_language(text)
        if rom_lang and rom_conf >= 0.5:
            if glotlid_lang and glotlid_lang != 'unknown' and glotlid_confidence > rom_conf:
                return glotlid_lang, 'glotlid_latin_override_romanized', glotlid_confidence
            return rom_lang, 'romanized_indic_latin', rom_conf
        
        is_mixed, primary_lang = detect_code_mixing(text)
        if is_mixed:
            if primary_lang == 'eng':
                return 'eng_indic_mixed', 'code_mixed_latin_dominant', 0.75
            else:
                return f"{primary_lang}_eng_mixed", 'code_mixed_latin_dominant', 0.75
        
        if rom_lang:
            return rom_lang, 'romanized_indic_latin_low_conf', rom_conf
        if glotlid_lang and glotlid_lang != 'unknown':
            return glotlid_lang, 'glotlid_latin', glotlid_confidence
        return 'eng', 'latin_fallback', 0.5
    
    if glotlid_lang and glotlid_lang != 'unknown':
        return glotlid_lang, 'glotlid_low', glotlid_confidence
    
    if script_lang and config['minor_script_min_threshold'] <= indic_percentage < config['minor_script_max_threshold']:
        return f"{script_lang}_transliterated", 'transliterated', 0.5
    
    return 'unknown', 'no_detection', 0.3


def _detect_short_text(text, text_length, is_very_short_text, script_lang, indic_percentage, latin_percentage,
                       glotlid_lang, glotlid_confidence, romanized_lang, romanized_confidence, config):
    """Short text detection logic"""
    
    if is_very_short_text:
        if glotlid_lang and glotlid_confidence > 0.3:
            return glotlid_lang, 'glotlid_very_short_text', min(0.70, glotlid_confidence)
        elif script_lang and indic_percentage > 50:
            return script_lang, 'script_very_short_text', min(0.75, indic_percentage / 100 + 0.1)
        else:
            return 'unknown', 'very_short_text_insufficient_data', 0.3
    
    # Short text (6-10 chars)
    if glotlid_lang and glotlid_confidence > config['short_text_glotlid_threshold']:
        return glotlid_lang, 'glotlid_short_text', min(0.80, glotlid_confidence)
    elif script_lang and indic_percentage > config['short_text_script_threshold']:
        return script_lang, 'script_analysis_short_text', min(0.85, indic_percentage / 100 + 0.1)
    elif romanized_lang and romanized_confidence > config['short_text_romanized_threshold']:
        return romanized_lang, 'romanized_short_text', romanized_confidence * 0.9
    else:
        if indic_percentage > 0:
            return script_lang if script_lang else 'unknown', 'script_fallback_short_text', 0.4
        elif latin_percentage > 50:
            return 'eng', 'latin_fallback_short_text', 0.4
        else:
            return 'unknown', 'short_text_ambiguous', 0.3


def _build_detailed_result(language, confidence, method, text_length, is_short_text, is_very_short_text,
                           composition_analysis, script_lang, script_counts,
                           glotlid_lang, glotlid_confidence, glotlid_code_mixed,
                           romanized_lang, romanized_confidence, config,
                           original_language=None, ensemble_result=None):
    """Build detailed analysis result dictionary"""
    
    result = {
        'language': language,
        'confidence': confidence,
        'method': method,
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
        'language_info': {
            'is_indian_language': language.split('_')[0] in INDIAN_LANGUAGES,
            'is_international_language': language.split('_')[0] in INTERNATIONAL_LANGUAGES,
            'is_code_mixed': '_mixed' in language or '_eng_mixed' in language or composition_analysis['composition']['is_code_mixed'],
            'is_romanized': '_roman' in language or (language.split('_')[0] in INDIAN_LANGUAGES and composition_analysis['composition']['latin_percentage'] > 70),
            'language_name': get_language_display_name(language)
        },
        'detection_config': config
    }
    
    if original_language:
        result['original_language'] = original_language
    
    if ensemble_result:
        result['ensemble_analysis'] = ensemble_result
    
    return result


def get_language_statistics(text: str) -> Dict:
    """Get comprehensive language statistics for input text"""
    if not text:
        return {'error': 'Empty text provided'}
    
    detailed_analysis = detect_language(text, detailed=True)
    
    stats = {
        'text_length': len(text),
        'word_count': len(text.split()),
        'language_detection': detailed_analysis
    }
    
    return stats


def detect_language_simple(text: str) -> str:
    """Simple language detection for backward compatibility"""
    return detect_language(text, detailed=False)