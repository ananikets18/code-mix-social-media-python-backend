"""Language Utilities

This module contains utility functions for language code normalization and display names.

Extracted from preprocessing.py for better modularity.
"""

from typing import Optional

from logger_config import get_logger
from .language_constants import (
    LANGUAGE_CODE_NORMALIZATION,
    CANONICAL_LANGUAGE_NAMES,
    INDIAN_LANGUAGES,
    INTERNATIONAL_LANGUAGES
)

logger = get_logger(__name__, level="INFO")


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
