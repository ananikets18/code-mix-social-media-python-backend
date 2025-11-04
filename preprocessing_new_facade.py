"""Enhanced Multilingual Text Processing and Language Detection System

This is a facade module that provides backward compatibility with the original preprocessing.py.
All functionality has been modularized into the preprocessing package for better maintainability.

For new code, consider importing directly from the preprocessing package:
    from preprocessing import detect_language, preprocess_text

Modular structure:
    preprocessing/
    ├── language_constants.py      - Constants and patterns
    ├── detection_config.py         - Configuration management
    ├── script_detection.py         - Script-based detection
    ├── romanized_detection.py      - Romanized language detection
    ├── code_mixing_detection.py    - Code-mixing detection
    ├── glotlid_detection.py       - GLotLID model integration
    ├── language_utils.py          - Language utilities
    ├── text_preprocessing_core.py - Text preprocessing
    └── language_detection.py      - Main detection orchestration
"""

import sys
import os
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

# Initialize paths (for backward compatibility)
BASE_PATH = os.getcwd()
INDIC_NLP_RESOURCES_PATH = os.path.join(BASE_PATH, "indic_nlp_resources")
GLOTLID_MODEL_PATH = os.path.join(BASE_PATH, "cis-lmuglotlid", "model.bin")

sys.path.append(os.path.join(BASE_PATH, "indic_nlp_library"))

# Initialize indic_nlp library
from indicnlp import common
from indicnlp.transliterate import unicode_transliterate as indic_transliterate

common.set_resources_path(INDIC_NLP_RESOURCES_PATH)
indic_transliterate.init()

# =============================================================================
# Import all public functions from the modular preprocessing package
# =============================================================================

from preprocessing import (
    # Configuration
    DETECTION_CONFIG,
    update_detection_config,
    get_detection_config,
    
    # Constants
    INDIAN_LANGUAGES,
    INTERNATIONAL_LANGUAGES,
    OBSCURE_LANGUAGES,
    ROMANIZED_INDIAN_PATTERNS,
    COMMON_ENGLISH_WORDS,
    LANGUAGE_CODE_NORMALIZATION,
    CANONICAL_LANGUAGE_NAMES,
    
    # Language utilities
    normalize_language_code,
    get_language_display_name,
    
    # Script detection
    detect_script_based_language,
    analyze_text_composition,
    
    # Romanized detection
    detect_romanized_indian_language,
    detect_romanized_with_indic_nlp,
    detect_romanized_language,
    convert_romanized_to_native,
    is_english_token,
    
    # Code mixing
    detect_code_mixing,
    
    # GLotLID
    get_glotlid_model,
    detect_glotlid_language,
    enable_glotlid_loading,
    unload_glotlid_model,
    is_glotlid_loaded,
    get_memory_usage_info,
    
    # Main detection
    detect_language,
    get_language_statistics,
    detect_language_simple,
    
    # Preprocessing
    preprocess_text,
)

# =============================================================================
# Re-export for backward compatibility
# =============================================================================

__all__ = [
    # Paths (backward compatibility)
    'BASE_PATH',
    'INDIC_NLP_RESOURCES_PATH',
    'GLOTLID_MODEL_PATH',
    
    # Configuration
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
    
    # Main detection
    'detect_language',
    'get_language_statistics',
    'detect_language_simple',
    
    # Preprocessing
    'preprocess_text',
]

# Informational message (only shown once)
if __name__ != "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("preprocessing.py now uses modular structure from preprocessing/ package")
