# inference.py

from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification
import torch
import torch.nn.functional as F
import os
from typing import Dict, Optional

from logger_config import get_logger, log_performance
from validators import TextValidator, ModelValidator, validate_inputs, ValidationError

logger = get_logger(__name__, level="INFO")

BASE_PATH = os.getcwd()
SENTIMENT_MODEL_PATH = os.path.join(BASE_PATH, "cardiffnlptwitter-xlm-roberta-base-sentiment")
TOXICITY_MODEL_PATH = os.path.join(BASE_PATH, "oleksiizirka-xlm-roberta-toxicity-classifier")
INDIC_SENTIMENT_MODEL_PATH = os.path.join(BASE_PATH, "ai4bharatIndicBERTv2-alpha-SentimentClassification")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Device: {device.type.upper()}")

_sentiment_tokenizer = None
_sentiment_model = None
_indic_sentiment_tokenizer = None
_indic_sentiment_model = None
_toxicity_tokenizer = None
_toxicity_model = None
_models_load_enabled = True

SENTIMENT_LABELS = ["negative", "neutral", "positive"]
INDIC_SENTIMENT_LABELS = {0: "negative", 1: "neutral", 2: "positive"}
INDIC_LANGUAGES = ['hi', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'pa', 'or', 'as', 'en']
TOXICITY_LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]


def enable_model_loading(enable: bool = True):
    global _models_load_enabled
    _models_load_enabled = enable
    if not enable:
        logger.warning("Model loading disabled. Models will not be loaded on demand.")


def unload_all_models():
    """
    Unload all models from memory to free resources
    Useful for long-running applications or memory management
    """
    global _sentiment_tokenizer, _sentiment_model
    global _indic_sentiment_tokenizer, _indic_sentiment_model
    global _toxicity_tokenizer, _toxicity_model
    
    freed_memory = 0
    
    if _sentiment_model is not None:
        _sentiment_tokenizer = None
        _sentiment_model = None
        freed_memory += 560  # ~560MB
        logger.info("XLM-R Sentiment model unloaded (~560MB freed)")
    
    if _indic_sentiment_model is not None:
        _indic_sentiment_tokenizer = None
        _indic_sentiment_model = None
        freed_memory += 560  # ~560MB
        logger.info("IndicBERT v2 Sentiment model unloaded (~560MB freed)")
    
    if _toxicity_model is not None:
        _toxicity_tokenizer = None
        _toxicity_model = None
        freed_memory += 560  # ~560MB
        logger.info("Toxicity model unloaded (~560MB freed)")
    
    if freed_memory > 0:
        logger.info(f"Total memory freed: ~{freed_memory}MB")
        # Clear PyTorch cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared")
    else:
        logger.info("No models were loaded")


def get_sentiment_model():
    """Lazy load XLM-R sentiment model - only loads when first accessed"""
    global _sentiment_tokenizer, _sentiment_model
    
    if _sentiment_model is not None:
        return _sentiment_tokenizer, _sentiment_model
    
    if not _models_load_enabled:
        return None, None
    
    logger.info("Loading XLM-R Sentiment model (first use)...")
    try:
        _sentiment_tokenizer = XLMRobertaTokenizer.from_pretrained(SENTIMENT_MODEL_PATH, local_files_only=True)
        _sentiment_model = XLMRobertaForSequenceClassification.from_pretrained(SENTIMENT_MODEL_PATH, local_files_only=True)
        _sentiment_model.to(device)  # Move to GPU if available
        _sentiment_model.eval()  # Set to evaluation mode
        logger.info("XLM-R Sentiment model loaded successfully")
        return _sentiment_tokenizer, _sentiment_model
    except Exception as e:
        logger.error(f"Error loading XLM-R sentiment model: {e}")
        return None, None


def get_indic_sentiment_model():
    """Lazy load IndicBERT v2 sentiment model - only loads when first accessed"""
    global _indic_sentiment_tokenizer, _indic_sentiment_model
    
    if _indic_sentiment_model is not None:
        return _indic_sentiment_tokenizer, _indic_sentiment_model
    
    if not _models_load_enabled:
        return None, None
    
    logger.info("Loading IndicBERT v2 Sentiment model (first use)...")
    try:
        from transformers import AutoModelForSequenceClassification, PreTrainedTokenizerFast
        _indic_sentiment_tokenizer = PreTrainedTokenizerFast.from_pretrained(
            INDIC_SENTIMENT_MODEL_PATH,
            local_files_only=True
        )
        _indic_sentiment_model = AutoModelForSequenceClassification.from_pretrained(
            INDIC_SENTIMENT_MODEL_PATH,
            local_files_only=True
        )
        _indic_sentiment_model.to(device)  # Move to GPU if available
        _indic_sentiment_model.eval()  # Set to evaluation mode
        logger.info("IndicBERT v2 Sentiment model loaded successfully")
        return _indic_sentiment_tokenizer, _indic_sentiment_model
    except Exception as e:
        logger.warning(f"IndicBERT v2 not loaded: {e}")
        logger.info("Will use XLM-R for all languages")
        return None, None


def get_toxicity_model():
    """Lazy load toxicity model - only loads when first accessed"""
    global _toxicity_tokenizer, _toxicity_model
    
    if _toxicity_model is not None:
        return _toxicity_tokenizer, _toxicity_model
    
    if not _models_load_enabled:
        return None, None
    
    logger.info("Loading Toxicity model (first use)...")
    try:
        _toxicity_tokenizer = XLMRobertaTokenizer.from_pretrained(TOXICITY_MODEL_PATH)
        _toxicity_model = XLMRobertaForSequenceClassification.from_pretrained(TOXICITY_MODEL_PATH)
        _toxicity_model.to(device)  # Move to GPU if available
        _toxicity_model.eval()  # Set to evaluation mode
        logger.info("Toxicity model loaded successfully")
        return _toxicity_tokenizer, _toxicity_model
    except Exception as e:
        logger.error(f"Error loading toxicity model: {e}")
        return None, None


def is_model_loaded(model_name: str) -> bool:
    """
    Check if a specific model is currently loaded in memory
    
    Args:
        model_name: One of 'sentiment', 'indic_sentiment', 'toxicity'
    
    Returns:
        bool: True if loaded, False otherwise
    """
    if model_name == 'sentiment':
        return _sentiment_model is not None
    elif model_name == 'indic_sentiment':
        return _indic_sentiment_model is not None
    elif model_name == 'toxicity':
        return _toxicity_model is not None
    return False


def get_memory_usage_info() -> dict:
    """
    Get information about current model memory usage
    
    Returns:
        Dict with memory usage information
    """
    return {
        'sentiment_loaded': is_model_loaded('sentiment'),
        'indic_sentiment_loaded': is_model_loaded('indic_sentiment'),
        'toxicity_loaded': is_model_loaded('toxicity'),
        'total_size_estimate': f"~{sum([560 if is_model_loaded(m) else 0 for m in ['sentiment', 'indic_sentiment', 'toxicity']])}MB",
        'device': str(device),
        'load_enabled': _models_load_enabled
    }

def encode_text(text, tokenizer, max_len=128):
    """Encodes text using the provided tokenizer for the correct model."""
    if tokenizer is None:
        return None
    return tokenizer(text, padding='max_length', truncation=True, max_length=max_len, return_tensors="pt")

def test_model_loading():
    """Test function to verify all models are working correctly (lazy loading)"""
    logger.info("Testing model functionality (will trigger lazy loading)...")
    
    # Test XLM-R sentiment model
    try:
        test_result = predict_sentiment("This is a test message", language='en')
        logger.info(f"XLM-R Sentiment test: {test_result['label']} ({test_result['confidence']:.2%}) - {test_result.get('model_used', 'unknown')}")
    except Exception as e:
        logger.error(f"XLM-R Sentiment test failed: {e}")
    
    # Test IndicBERT v2 sentiment model
    try:
        test_result = predict_sentiment("यह बहुत अच्छा है", language='hi')
        logger.info(f"IndicBERT v2 test: {test_result['label']} ({test_result['confidence']:.2%}) - {test_result.get('model_used', 'unknown')}")
    except Exception as e:
        logger.error(f"IndicBERT v2 test failed: {e}")
    
    # Test toxicity model  
    try:
        test_result = predict_toxicity("This is a test message")
        max_toxicity = max(test_result.items(), key=lambda x: x[1])
        logger.info(f"Toxicity model test: {max_toxicity[0]} ({max_toxicity[1]:.2%})")
    except Exception as e:
        logger.error(f"Toxicity model test failed: {e}")
    
    print("🧪 Model testing complete!")


def check_models_loaded() -> bool:
    """Check if all required models are loaded - for backward compatibility"""
    # Lazy loading: This will now always return True, models load on demand
    return True

@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=1, max_length=10000)
)
def predict_sentiment(text: str, language: Optional[str] = None) -> Dict:
    """
    Returns sentiment analysis using the appropriate model based on language.
    Uses IndicBERT v2 for Indian languages, XLM-R for others.
    Now with lazy loading - models load on first use
    
    Args:
        text (str): Preprocessed text to analyze
        language (str, optional): Language code (e.g., 'hi', 'en', 'bn')
    
    Returns:
        dict: Sentiment prediction with label, confidence, and model used
    
    Raises:
        ValidationError: If input validation fails
    """
    logger.debug(f"Predicting sentiment for text (length={len(text)}, language={language})")
    
    # Determine which model to use
    use_indic_model = False
    if language:
        # Extract base language code (remove suffixes like _mixed)
        base_lang = language.split('_')[0]
        if base_lang in INDIC_LANGUAGES:
            use_indic_model = True
            logger.info(f"Using IndicBERT model for language: {base_lang}")
    
    # Use IndicBERT v2 for Indian languages
    if use_indic_model:
        indic_sentiment_tokenizer, indic_sentiment_model = get_indic_sentiment_model()
        if indic_sentiment_model is not None:
            try:
                inputs = indic_sentiment_tokenizer(text, padding='max_length', truncation=True, 
                                                  max_length=128, return_tensors="pt")
                # Move inputs to GPU if available
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():  # Disable gradient computation for inference
                    outputs = indic_sentiment_model(**inputs)
                    logits = outputs.logits
                    probs = F.softmax(logits, dim=1)
                    predicted_class_idx = torch.argmax(probs, dim=1).item()
                
                # Map to sentiment label
                predicted_label = INDIC_SENTIMENT_LABELS.get(predicted_class_idx, SENTIMENT_LABELS[predicted_class_idx])
                confidence_score = probs[0][predicted_class_idx].item()
                
                result = {
                    "label": predicted_label,
                    "confidence": confidence_score,
                    "model_used": "IndicBERT-v2",
                    "all_probabilities": probs.tolist()
                }
                logger.info(f"Sentiment prediction: {predicted_label} ({confidence_score:.2%}) using IndicBERT")
                return result
            except Exception as e:
                logger.error(f"IndicBERT error, falling back to XLM-R: {e}")
                # Fall through to XLM-R model
    
    # Use XLM-R for English and international languages (or fallback)
    sentiment_tokenizer, sentiment_model = get_sentiment_model()
    if sentiment_tokenizer is None or sentiment_model is None:
        logger.error("No sentiment model available")
        return {"error": "No sentiment model available", "label": "unknown", "confidence": 0.0, "model_used": "none"}
    
    try:
        inputs = encode_text(text, sentiment_tokenizer)
        # Move inputs to GPU if available
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():  # Disable gradient computation for inference
            outputs = sentiment_model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=1)
            predicted_class_idx = torch.argmax(probs, dim=1).item()
            predicted_label = SENTIMENT_LABELS[predicted_class_idx]
            confidence_score = probs[0][predicted_class_idx].item()
        
        result = {
            "label": predicted_label,
            "confidence": confidence_score,
            "model_used": "XLM-RoBERTa",
            "all_probabilities": probs.tolist()
        }
        logger.info(f"Sentiment prediction: {predicted_label} ({confidence_score:.2%}) using XLM-RoBERTa")
        return result
    except Exception as e:
        logger.error(f"Sentiment prediction error: {e}")
        return {"error": str(e), "label": "unknown", "confidence": 0.0, "model_used": "error"}

@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=1, max_length=10000)
)
def predict_toxicity(text: str) -> Dict:
    """
    Returns a dictionary of toxicity scores for the given text using a sigmoid multi-label output.
    Now with lazy loading - model loads on first use
    
    Args:
        text (str): Preprocessed text to analyze
    
    Returns:
        dict: Toxicity scores for each category
    
    Raises:
        ValidationError: If input validation fails
    """
    logger.debug(f"Predicting toxicity for text (length={len(text)})")
    toxicity_tokenizer, toxicity_model = get_toxicity_model()
    if toxicity_tokenizer is None or toxicity_model is None:
        logger.error("No toxicity model available")
        return {label: 0.0 for label in TOXICITY_LABELS}
    
    try:
        inputs = encode_text(text, toxicity_tokenizer)
        # Move inputs to GPU if available
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():  # Disable gradient computation for inference
            outputs = toxicity_model(**inputs)
            logits = outputs.logits
            probs = torch.sigmoid(logits)
        
        results = {}
        for i, label in enumerate(TOXICITY_LABELS):
            results[label] = probs[0][i].item()
        
        # Log the maximum toxicity category
        max_toxic = max(results.items(), key=lambda x: x[1])
        logger.info(f"Toxicity prediction: max={max_toxic[0]} ({max_toxic[1]:.2%})")
        
        return results
    except Exception as e:
        logger.error(f"Toxicity prediction error: {e}")
        return {label: 0.0 for label in TOXICITY_LABELS}

# Models are now lazy-loaded - no automatic initialization on import
# Call test_model_loading() manually if you want to pre-load and test models
# Or just use predict_sentiment()/predict_toxicity() and models will load on first use
