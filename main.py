# Enhanced NLP Project with Comprehensive Language Support

from preprocessing import detect_language, preprocess_text, get_language_statistics
from inference import predict_sentiment, predict_toxicity
from translation import translate_text, detect_and_translate_to_english
from domain_processors import DomainProcessor
from profanity_filter import ProfanityFilter
from logger_config import get_logger
from adaptive_learning import (
    check_cache_before_detection,
    store_successful_detection,
    get_learning_statistics,
    store_detection_failure_with_context
)

logger = get_logger(__name__, level="INFO")


def print_startup_info():
    """Display startup information about the NLP system"""
    print("\n" + "="*80)
    print("🚀 Multilingual NLP Analysis System - Enhanced Edition")
    print("="*80)
    print("\n📋 Recent Fixes & Enhancements:")
    print("  ✅ FIX #10: Hybrid Romanized-to-Native Conversion")
    print("     • Intelligently preserves English words in mixed text")
    print("     • Converts only romanized Indic tokens to native script")
    print("     • Supports 6 languages: Hindi, Marathi, Bengali, Tamil, Telugu, Punjabi")
    print("  ✅ FIX #9: Enhanced Logging for Code-Mixing Events")
    print("     • Comprehensive diagnostic logging for threshold tuning")
    print("  ✅ FIX #8: Ensemble Fusion (GLotLID + Romanized Detection)")
    print("     • Weighted confidence scoring for better language detection")
    print("  ✅ FIX #7: Adaptive Code-Mixing Thresholds")
    print("     • Dynamic thresholds based on text length")
    print("  ✅ FIX #6: Robust Language Code Normalization")
    print("     • Handles 60+ language code variants")
    print("\n🌐 Supported Features:")
    print("  • Language Detection (International + Indian + Code-Mixed)")
    print("  • Sentiment Analysis (Multilingual)")
    print("  • Toxicity Detection (6 categories)")
    print("  • Translation (Auto-detect + Romanized conversion)")
    print("  • Profanity Filtering (10 languages)")
    print("  • Domain Detection (Technical, Medical, Legal, etc.)")
    print("  • Hybrid Romanized-to-Native Conversion [NEW!]")
    print("\n📡 API Endpoints:")
    print("  POST /analyze   - Comprehensive analysis")
    print("  POST /convert   - Romanized-to-native conversion [FIX #10]")
    print("  POST /translate - Translation with auto-conversion")
    print("  POST /sentiment - Sentiment analysis only")
    print("  POST /toxicity  - Toxicity detection only")
    print("  GET  /health    - System health check")
    print("="*80 + "\n")


def analyze_text_comprehensive(text, normalization_level=None, preserve_emojis=True, 
                               punctuation_mode='preserve', check_profanity=True,
                               detect_domains=True, compact=False):
    """
    Comprehensive text analysis including all NLP features
    
    Args:
        text (str): Input text to analyze
        normalization_level (str): Text normalization level
        preserve_emojis (bool): Keep emojis in text
        punctuation_mode (str): How to handle punctuation
        check_profanity (bool): Enable profanity detection
        detect_domains (bool): Enable domain detection
        compact (bool): Return simplified/compact response (default: False)
    
    Returns:
        dict: Analysis results (compact or verbose based on `compact` param)
    """
    logger.info(f"Analyzing text: '{text[:50]}...'")
    
    profanity_result = None
    if check_profanity:
        profanity_filter = ProfanityFilter()
        profanity_result = profanity_filter.detect_profanity(text)
    
    domain_result = None
    if detect_domains:
        domain_processor = DomainProcessor()
        domain_result = domain_processor.detect_domains(text)
    
    cached_detection = check_cache_before_detection(text)
    if cached_detection:
        lang_detection = cached_detection
        lang_stats = {'language_detection': lang_detection}
    else:
        lang_stats = get_language_statistics(text)
        lang_detection = lang_stats['language_detection']
        store_successful_detection(text, lang_detection)
    
    cleaned_text = preprocess_text(text, preserve_emojis=preserve_emojis, 
                                   normalization_level=normalization_level,
                                   punctuation_mode=punctuation_mode)
    
    lang_code = lang_detection['language']
    sentiment_result = predict_sentiment(cleaned_text, language=lang_code)
    toxicity_result = predict_toxicity(cleaned_text)
    
    # Extract translation parameters
    base_lang = lang_code.split('_')[0]
    is_code_mixed = '_mixed' in lang_code or '_eng_mixed' in lang_code
    is_romanized = lang_detection.get('language_info', {}).get('is_romanized', False)
    translations = {}
    
    if base_lang not in ['eng', 'en']:
        # Determine source language for translation
        if is_code_mixed:
            source_lang = base_lang if base_lang in ['hin', 'mar', 'ben', 'tam', 'tel'] else 'auto'
        else:
            source_lang = base_lang
        
        # ENHANCED: Pass is_romanized flag for better translation
        english_translation = translate_text(
            text, 
            target_lang='en', 
            source_lang=source_lang,
            is_romanized=is_romanized  # NEW: Enable romanized conversion
        )
        if english_translation['success']:
            translations['english'] = english_translation['translated_text']
            # Add conversion info if available
            if english_translation.get('used_romanized_conversion'):
                translations['conversion_applied'] = True
                translations['converted_to_devanagari'] = english_translation.get('converted_text')
    else:
        hindi_translation = translate_text(text, target_lang='hi', source_lang='en')
        if hindi_translation['success']:
            translations['hindi'] = hindi_translation['translated_text']
    
    result = {
        'original_text': text,
        'cleaned_text': cleaned_text,
        'preprocessing': {
            'normalization_level': normalization_level,
            'preserve_emojis': preserve_emojis,
            'punctuation_mode': punctuation_mode
        },
        'profanity': profanity_result,
        'domains': domain_result,
        'language': lang_detection,
        'sentiment': sentiment_result,
        'toxicity': toxicity_result,
        'translations': translations,
        'statistics': lang_stats
    }
    
    # Return compact version if requested
    if compact:
        return _create_compact_response(result)
    
    failure_id = store_detection_failure_with_context(result)
    if failure_id:
        logger.warning(f"Detection issue stored: {failure_id}")
    
    return result


def _create_compact_response(full_result):
    """
    Create a simplified/compact API response with only essential fields
    
    Args:
        full_result (dict): Full verbose analysis result
    
    Returns:
        dict: Compact response with key information only
    """
    lang_info = full_result.get('language', {})
    sentiment = full_result.get('sentiment', {})
    profanity = full_result.get('profanity', {})
    
    compact = {
        'text': full_result.get('original_text'),
        'language': {
            'code': lang_info.get('language'),
            'name': lang_info.get('language_info', {}).get('language_name'),
            'confidence': round(lang_info.get('confidence', 0), 2),
            'is_romanized': lang_info.get('language_info', {}).get('is_romanized', False),
            'is_code_mixed': lang_info.get('language_info', {}).get('is_code_mixed', False)
        },
        'sentiment': {
            'label': sentiment.get('label'),
            'score': round(sentiment.get('confidence', 0), 2)
        },
        'profanity': {
            'detected': profanity.get('has_profanity', False) if profanity else False,
            'severity': profanity.get('max_severity') if profanity else None
        },
        'translation': full_result.get('translations', {}).get('english'),
        'toxicity_score': round(max(full_result.get('toxicity', {}).values()) if full_result.get('toxicity') else 0, 3)
    }
    
    # Add romanized conversion info if available
    if full_result.get('translations', {}).get('conversion_applied'):
        compact['romanized_conversion'] = {
            'applied': True,
            'native_script': full_result['translations'].get('converted_to_devanagari')
        }
    
    return compact

def main():
    """Main function with test cases"""
    
    test_cases = [
        {'text': "This is a wonderful product. I highly recommend it to everyone!",
         'description': "Clean Text", 'normalization': None, 'preserve_emojis': True, 'punctuation_mode': 'preserve'},
        {'text': "The stock price increased by $50 today. Market cap reached $1.5B USD.",
         'description': "Financial Domain", 'normalization': None, 'preserve_emojis': True, 'punctuation_mode': 'preserve'},
        {'text': "This fucking product is shit! I hate this damn thing.",
         'description': "English Profanity", 'normalization': None, 'preserve_emojis': True, 'punctuation_mode': 'preserve'},
        {'text': "Yaar ye movie bahut mast hai! Must watch bro, ekdum zabardast!",
         'description': "Hinglish Code-Mixed", 'normalization': None, 'preserve_emojis': True, 'punctuation_mode': 'preserve'}
    ]
    
    logger.info(f"Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*60}\nTest {i}: {test_case['description']}\n{'='*60}")
        
        result = analyze_text_comprehensive(
            test_case['text'], 
            normalization_level=test_case.get('normalization'),
            preserve_emojis=test_case.get('preserve_emojis', True),
            punctuation_mode=test_case.get('punctuation_mode', 'preserve')
        )
        
        logger.info(f"Test {i} complete")
    
    logger.info("\nAll tests complete")

if __name__ == "__main__":
    main()