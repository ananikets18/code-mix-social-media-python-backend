# Preprocessing Package

This package contains modularized language detection and text preprocessing functionality.

## Module Structure

### Core Modules

1. **language_constants.py** (~350 lines)
   - Language mappings (INDIAN_LANGUAGES, INTERNATIONAL_LANGUAGES)
   - Regex patterns for romanized text detection
   - Language code normalization mappings
   - English word patterns for code-mixing detection

2. **detection_config.py** (~120 lines)
   - Centralized configuration for all detection thresholds
   - Functions to update and retrieve configuration
   - Adaptive thresholds for different text lengths

3. **script_detection.py** (~120 lines)
   - Unicode script-based language detection
   - Text composition analysis (script percentages)
   - Vectorized numpy operations for performance

4. **romanized_detection.py** (~550 lines)
   - Pattern-based romanized language detection
   - ITRANS transliteration-based detection
   - Hybrid romanized-to-native script conversion (FIX #10)
   - English token detection for code-mixed text

5. **code_mixing_detection.py** (~400 lines)
   - Advanced code-mixing detection with adaptive thresholds
   - Multi-method detection (patterns, scripts, tokens)
   - Comprehensive diagnostic logging (FIX #9)

6. **glotlid_detection.py** (~150 lines)
   - GLotLID model integration and lazy loading
   - Memory management (load/unload/status)
   - Configurable confidence thresholds

7. **language_utils.py** (~120 lines)
   - Language code normalization (FIX #6)
   - Display name generation for language codes
   - Helper functions for language mapping

8. **text_preprocessing_core.py** (~80 lines)
   - Text cleaning and normalization
   - Social media artifact removal
   - Emoji handling and punctuation modes

9. **language_detection.py** (NOT YET CREATED - ~600 lines)
   - Main `detect_language()` function
   - Detection orchestration and decision logic
   - Integration of all detection methods
   - Statistical analysis functions

## Benefits of Modularization

### Before (Single File)
- **2,198 lines** in one file
- Difficult to navigate and maintain
- All functionality loaded at once
- Hard to test individual components

### After (Modular)
- **9 focused modules** averaging ~250 lines each
- Clear separation of concerns
- Easy to understand and modify
- Independent testing possible
- Backward compatible through facade pattern

## Usage

### Direct Import from Modules
```python
from preprocessing.script_detection import detect_script_based_language
from preprocessing.romanized_detection import detect_romanized_language
from preprocessing.code_mixing_detection import detect_code_mixing
```

### Import from Package (Recommended)
```python
from preprocessing import (
    detect_language,  # Main function
    detect_code_mixing,
    preprocess_text,
    update_detection_config
)
```

### Backward Compatible Import (Legacy Code)
```python
from preprocessing import detect_language, preprocess_text
# Works exactly as before - no code changes needed!
```

## Configuration

Update detection thresholds:
```python
from preprocessing import update_detection_config

update_detection_config(
    glotlid_threshold=0.6,
    adaptive_threshold_short_text=0.15
)
```

## Memory Management

Control GLotLID model loading:
```python
from preprocessing import (
    get_glotlid_model,
    unload_glotlid_model,
    is_glotlid_loaded
)

# Check if loaded
if is_glotlid_loaded():
    print("Model is loaded")

# Unload to free memory
unload_glotlid_model()  # Frees ~1.6GB
```

## Testing

Each module can be tested independently:
```bash
# Test script detection only
pytest tests/test_script_detection.py

# Test romanized detection only
pytest tests/test_romanized_detection.py

# Test full integration
pytest tests/test_preprocessing.py
```

## Migration Notes

**The original `preprocessing.py` will remain as a facade** that imports and re-exports all functions for backward compatibility. No changes needed in existing code that uses:
- `from preprocessing import detect_language`
- `from preprocessing import preprocess_text`
- etc.

## Future Work

1. Complete `language_detection.py` with full `detect_language()` implementation
2. Create comprehensive unit tests for each module
3. Add performance benchmarks
4. Document each FIX (# 1-10) in detail
5. Create migration guide for advanced users

## Module Dependencies

```
language_constants.py (no internal deps)
    ↓
detection_config.py (imports constants)
    ↓
language_utils.py (imports constants)
    ↓
script_detection.py (imports logger, indicnlp)
    ↓
romanized_detection.py (imports constants, config, script_detection)
code_mixing_detection.py (imports constants, config, script_detection)
glotlid_detection.py (imports config, glotlid_wrapper)
    ↓
language_detection.py (imports ALL above - main orchestration)
    ↓
text_preprocessing_core.py (standalone, imports validators)
```

## Lines of Code Comparison

| Module | Lines | Responsibility |
|--------|-------|----------------|
| language_constants.py | 350 | Constants & patterns |
| detection_config.py | 120 | Configuration |
| script_detection.py | 120 | Script analysis |
| romanized_detection.py | 550 | Romanized detection |
| code_mixing_detection.py | 400 | Code-mixing detection |
| glotlid_detection.py | 150 | GLotLID integration |
| language_utils.py | 120 | Utilities |
| text_preprocessing_core.py | 80 | Text preprocessing |
| language_detection.py | 600 | Main detection (TBD) |
| **Total** | **2,490** | **(+13% for modularity)** |

Note: Slight increase in total lines due to:
- Module docstrings
- Import statements in each file
- __init__.py for package structure
- This README documentation

The improved maintainability far outweighs the modest line count increase.
