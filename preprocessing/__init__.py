"""Preprocessing Package

Modular language detection and text preprocessing for multilingual NLP.

This package provides comprehensive language detection for Indian and international languages,
including support for romanized text, code-mixing, and multilingual content.

Modules:
    - language_constants: Language mappings, patterns, and constants
    - detection_config: Configuration management for detection thresholds
    - script_detection: Script-based language detection
    - romanized_detection: Romanized Indian language detection
    - code_mixing_detection: Code-mixing detection (Hinglish, etc.)
    - glotlid_detection: GLotLID model integration
    - language_utils: Language code normalization and utilities
    - text_preprocessing_core: Text cleaning and preprocessing
    - language_detection: Main language detection orchestration (to be created)

Public API (for backward compatibility):
    All main functions are re-exported in the parent preprocessing.py module.
"""

__version__ = "2.0.0"
__author__ = "NLP Project Team"

# Re-export main functions for convenience
from .detection_config import (
    DETECTION_CONFIG,
    update_detection_config,
    get_detection_config
)

from .language_constants import (
    INDIAN_LANGUAGES,
    INTERNATIONAL_LANGUAGES,
    OBSCURE_LANGUAGES,
    ROMANIZED_INDIAN_PATTERNS,
    COMMON_ENGLISH_WORDS,
    LANGUAGE_CODE_NORMALIZATION,
    CANONICAL_LANGUAGE_NAMES
)

from .language_utils import (
    normalize_language_code,
    get_language_display_name
)

from .script_detection import (
    detect_script_based_language,
    analyze_text_composition
)

from .romanized_detection import (
    detect_romanized_indian_language,
    detect_romanized_with_indic_nlp,
    detect_romanized_language,
    convert_romanized_to_native,
    is_english_token
)

from .code_mixing_detection import (
    detect_code_mixing
)

from .glotlid_detection import (
    get_glotlid_model,
    detect_glotlid_language,
    enable_glotlid_loading,
    unload_glotlid_model,
    is_glotlid_loaded,
    get_memory_usage_info
)

from .text_preprocessing_core import (
    preprocess_text
)

from .language_detection import (
    detect_language,
    get_language_statistics,
    detect_language_simple
)

__all__ = [
    # Config
    'DETECTION_CONFIG',
    'update_detection_config',
    'get_detection_config',
    
    # Constants
    'INDIAN_LANGUAGES',
    'INTERNATIONAL_LANGUAGES',
    'OBSCURE_LANGUAGES',
    'ROMANIZED_INDIAN_PATTERNS',
    'COMMON_ENGLISH_WORDS',
    'LANGUAGE_CODE_NORMALIZATION',
    'CANONICAL_LANGUAGE_NAMES',
    
    # Language utilities
    'normalize_language_code',
    'get_language_display_name',
    
    # Script detection
    'detect_script_based_language',
    'analyze_text_composition',
    
    # Romanized detection
    'detect_romanized_indian_language',
    'detect_romanized_with_indic_nlp',
    'detect_romanized_language',
    'convert_romanized_to_native',
    'is_english_token',
    
    # Code mixing
    'detect_code_mixing',
    
    # GLotLID
    'get_glotlid_model',
    'detect_glotlid_language',
    'enable_glotlid_loading',
    'unload_glotlid_model',
    'is_glotlid_loaded',
    'get_memory_usage_info',
    
    # Preprocessing
    'preprocess_text',
    
    # Language detection (main functions)
    'detect_language',
    'get_language_statistics',
    'detect_language_simple',
]
