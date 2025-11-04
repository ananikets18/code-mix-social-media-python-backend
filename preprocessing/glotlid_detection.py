"""GLotLID Language Detection Integration

This module provides integration with the GLotLID language detection model.
Includes lazy loading, caching, and memory management.

Extracted from preprocessing.py for better modularity.
"""

import os
from typing import Dict, Optional, Tuple

from logger_config import get_logger
from glotlid_wrapper import GLotLID
from .detection_config import DETECTION_CONFIG

logger = get_logger(__name__, level="INFO")

BASE_PATH = os.getcwd()
GLOTLID_MODEL_PATH = os.path.join(BASE_PATH, "cis-lmuglotlid", "model.bin")

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
