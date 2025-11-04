"""Text Preprocessing Core

This module contains core text preprocessing functions for cleaning and normalizing text.

Extracted from preprocessing.py for better modularity.
"""

import emoji
from typing import Dict

from logger_config import get_logger, log_performance
from validators import TextValidator, validate_inputs, ValidationError
from text_normalizer import normalize as normalize_text
from .language_constants import (
    MENTION_PATTERN,
    HASHTAG_PATTERN,
    URL_PATTERN,
    HTML_ENTITY_PATTERN,
    WHITESPACE_PATTERN,
    NON_ESSENTIAL_PUNCT_PATTERN
)

logger = get_logger(__name__, level="INFO")


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
