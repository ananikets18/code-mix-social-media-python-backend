"""Detection Configuration Management

This module manages configuration settings for language detection,
including thresholds, parameters, and configurable behaviors.

Extracted from preprocessing.py for better modularity.
"""

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
