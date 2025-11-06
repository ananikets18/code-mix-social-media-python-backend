from preprocessing import detect_language, preprocess_text, get_language_statistics
from inference import predict_sentiment, predict_toxicity
from translation import translate_text, detect_and_translate_to_english
from model_downloader import all_models_present, download_and_unzip_models
from fastapi import FastAPI
from domain_processors import DomainProcessor
from profanity_filter import ProfanityFilter
from logger_config import get_logger
from adaptive_learning import (
    check_cache_before_detection,
    store_successful_detection,
    get_learning_statistics,
    store_detection_failure_with_context
)

logger = get_logger(__name__, level="WARNING")

# If FastAPI app is not yet instantiated, add this
app = FastAPI()


def analyze_text_comprehensive(text, normalization_level=None, preserve_emojis=True, 
                               punctuation_mode='preserve', check_profanity=True,
                               detect_domains=True, compact=False):
    """
    Comprehensive text analysis including language detection, sentiment, toxicity, and translation.
    
    Args:
        text (str): Input text to analyze
        normalization_level (str): Text normalization level
        preserve_emojis (bool): Keep emojis in text
        punctuation_mode (str): How to handle punctuation
        check_profanity (bool): Enable profanity detection
        detect_domains (bool): Enable domain detection
        compact (bool): Return simplified response
    
    Returns:
        dict: Analysis results (compact or verbose based on `compact` param)
    """
    logger.info(f"[/analyze] text_length={len(text)}")
    
    profanity_result = None
    if check_profanity:
        profanity_filter = ProfanityFilter()
        profanity_result = profanity_filter.detect_profanity(text)
    
    domain_result = None
    if detect_domains:
        domain_processor = DomainProcessor()
        domain_result = domain_processor.detect_domains(text)
    
    # Use cache to avoid repeated language detection overhead
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
    
    base_lang = lang_code.split('_')[0]
    is_code_mixed = '_mixed' in lang_code or '_eng_mixed' in lang_code
    is_romanized = lang_detection.get('language_info', {}).get('is_romanized', False)
    translations = {}
    
    if base_lang not in ['eng', 'en']:
        # Determine source language for translation
        source_lang = base_lang if base_lang in ['hin', 'mar', 'ben', 'tam', 'tel'] else 'auto'
        english_translation = translate_text(text, target_lang='en', source_lang=source_lang, is_romanized=is_romanized)
        if english_translation['success']:
            translations['english'] = english_translation['translated_text']
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
    
    # Return compact version if requested (reduces API response size for clients)
    if compact:
        return _create_compact_response(result)
    
    failure_id = store_detection_failure_with_context(result)
    if failure_id:
        logger.warning(f"Detection issue stored: {failure_id}")
    
    return result


def _create_compact_response(full_result):
    """
    Create a simplified/compact API response with only essential fields.
    
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
    """Run test cases for NLP analysis."""
    
    test_cases = [
        "This is a wonderful product. I highly recommend it to everyone!",
        "The stock price increased by $50 today. Market cap reached $1.5B USD.",
        "This fucking product is shit! I hate this damn thing.",
        "Yaar ye movie bahut mast hai! Must watch bro, ekdum zabardast!"
    ]
    
    logger.info(f"Starting {len(test_cases)} test cases")
    
    for i, text in enumerate(test_cases, 1):
        analyze_text_comprehensive(text)
    
    logger.info("Test cases complete")


if __name__ == "__main__":
    main()