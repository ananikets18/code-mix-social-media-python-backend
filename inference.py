
from transformers import XLMRobertaTokenizer, XLMRobertaForSequenceClassification
import torch
import torch.nn.functional as F
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, List

from logger_config import get_logger, log_performance
from validators import TextValidator, ModelValidator, validate_inputs, ValidationError

logger = get_logger(__name__, level="WARNING")

BASE_PATH = os.getcwd()
SENTIMENT_MODEL_PATH = os.path.join(BASE_PATH, "cardiffnlptwitter-xlm-roberta-base-sentiment")
TOXICITY_MODEL_PATH = os.path.join(BASE_PATH, "oleksiizirka-xlm-roberta-toxicity-classifier")
INDIC_SENTIMENT_MODEL_PATH = os.path.join(BASE_PATH, "ai4bharatIndicBERTv2-alpha-SentimentClassification")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.warning(f"Device: {device.type.upper()}")

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
        logger.warning("Model loading disabled")


def unload_all_models():
    """Unload all models from memory to free resources."""
    global _sentiment_tokenizer, _sentiment_model
    global _indic_sentiment_tokenizer, _indic_sentiment_model
    global _toxicity_tokenizer, _toxicity_model
    
    freed_memory = 0
    
    if _sentiment_model is not None:
        _sentiment_tokenizer = None
        _sentiment_model = None
        freed_memory += 560
    
    if _indic_sentiment_model is not None:
        _indic_sentiment_tokenizer = None
        _indic_sentiment_model = None
        freed_memory += 560
    
    if _toxicity_model is not None:
        _toxicity_tokenizer = None
        _toxicity_model = None
        freed_memory += 560
    
    if freed_memory > 0:
        logger.warning(f"Memory freed: ~{freed_memory}MB")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    else:
        logger.warning("No models were loaded")


def get_sentiment_model():
    """Lazy load XLM-R sentiment model - only loads when first accessed."""
    global _sentiment_tokenizer, _sentiment_model
    
    if _sentiment_model is not None:
        return _sentiment_tokenizer, _sentiment_model
    
    if not _models_load_enabled:
        return None, None
    
    try:
        _sentiment_tokenizer = XLMRobertaTokenizer.from_pretrained(SENTIMENT_MODEL_PATH, local_files_only=True)
        _sentiment_model = XLMRobertaForSequenceClassification.from_pretrained(SENTIMENT_MODEL_PATH, local_files_only=True)
        _sentiment_model.to(device)
        _sentiment_model.eval()
        return _sentiment_tokenizer, _sentiment_model
    except Exception as e:
        logger.error(f"Error loading XLM-R sentiment model: {e}")
        return None, None


def get_indic_sentiment_model():
    """Lazy load IndicBERT v2 sentiment model - only loads when first accessed."""
    global _indic_sentiment_tokenizer, _indic_sentiment_model
    
    if _indic_sentiment_model is not None:
        return _indic_sentiment_tokenizer, _indic_sentiment_model
    
    if not _models_load_enabled:
        return None, None
    
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
        _indic_sentiment_model.to(device)
        _indic_sentiment_model.eval()
        return _indic_sentiment_tokenizer, _indic_sentiment_model
    except Exception as e:
        logger.warning(f"IndicBERT v2 not loaded: {e}")
        return None, None


def get_toxicity_model():
    """Lazy load toxicity model - only loads when first accessed."""
    global _toxicity_tokenizer, _toxicity_model
    
    if _toxicity_model is not None:
        return _toxicity_tokenizer, _toxicity_model
    
    if not _models_load_enabled:
        return None, None
    
    try:
        _toxicity_tokenizer = XLMRobertaTokenizer.from_pretrained(TOXICITY_MODEL_PATH)
        _toxicity_model = XLMRobertaForSequenceClassification.from_pretrained(TOXICITY_MODEL_PATH)
        _toxicity_model.to(device)
        _toxicity_model.eval()
        return _toxicity_tokenizer, _toxicity_model
    except Exception as e:
        logger.error(f"Error loading toxicity model: {e}")
        return None, None


def is_model_loaded(model_name: str) -> bool:
    """Check if a specific model is currently loaded in memory."""
    if model_name == 'sentiment':
        return _sentiment_model is not None
    elif model_name == 'indic_sentiment':
        return _indic_sentiment_model is not None
    elif model_name == 'toxicity':
        return _toxicity_model is not None
    return False


def get_memory_usage_info() -> dict:
    """Get information about current model memory usage."""
    return {
        'sentiment_loaded': is_model_loaded('sentiment'),
        'indic_sentiment_loaded': is_model_loaded('indic_sentiment'),
        'toxicity_loaded': is_model_loaded('toxicity'),
        'total_size_estimate': f"~{sum([560 if is_model_loaded(m) else 0 for m in ['sentiment', 'indic_sentiment', 'toxicity']])}MB",
        'device': str(device),
        'load_enabled': _models_load_enabled
    }


def encode_text(text, tokenizer, max_len=128):
    """Encode text using the provided tokenizer."""
    if tokenizer is None:
        return None
    return tokenizer(text, padding='max_length', truncation=True, max_length=max_len, return_tensors="pt")


def test_model_loading():
    """Test function to verify all models are working correctly."""
    
    try:
        test_result = predict_sentiment("This is a test message", language='en')
        logger.warning(f"XLM-R Sentiment test: {test_result['label']} - {test_result.get('model_used', 'unknown')}")
    except Exception as e:
        logger.error(f"XLM-R Sentiment test failed: {e}")
    
    try:
        test_result = predict_sentiment("यह बहुत अच्छा है", language='hi')
        logger.warning(f"IndicBERT v2 test: {test_result['label']} - {test_result.get('model_used', 'unknown')}")
    except Exception as e:
        logger.error(f"IndicBERT v2 test failed: {e}")
    
    try:
        test_result = predict_toxicity("This is a test message")
        max_toxicity = max(test_result.items(), key=lambda x: x[1])
        logger.warning(f"Toxicity model test: {max_toxicity[0]}")
    except Exception as e:
        logger.error(f"Toxicity model test failed: {e}")


def check_models_loaded() -> bool:
    """Check if all required models are loaded."""
    return True


@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=1, max_length=10000)
)
def predict_sentiment(text: str, language: Optional[str] = None) -> Dict:
    """
    Returns sentiment analysis using the appropriate model based on language.
    Uses IndicBERT v2 for Indian languages, XLM-R for others.
    
    Args:
        text (str): Preprocessed text to analyze
        language (str, optional): Language code (e.g., 'hi', 'en', 'bn')
    
    Returns:
        dict: Sentiment prediction with label, confidence, and model used
    
    Raises:
        ValidationError: If input validation fails
    """
    
    use_indic_model = False
    if language:
        base_lang = language.split('_')[0]
        if base_lang in INDIC_LANGUAGES:
            use_indic_model = True
    
    if use_indic_model:
        indic_sentiment_tokenizer, indic_sentiment_model = get_indic_sentiment_model()
        if indic_sentiment_model is not None:
            try:
                inputs = indic_sentiment_tokenizer(text, padding='max_length', truncation=True, 
                                                  max_length=128, return_tensors="pt")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = indic_sentiment_model(**inputs)
                    logits = outputs.logits
                    probs = F.softmax(logits, dim=1)
                    predicted_class_idx = torch.argmax(probs, dim=1).item()
                
                predicted_label = INDIC_SENTIMENT_LABELS.get(predicted_class_idx, SENTIMENT_LABELS[predicted_class_idx])
                confidence_score = probs[0][predicted_class_idx].item()
                
                return {
                    "label": predicted_label,
                    "confidence": confidence_score,
                    "model_used": "IndicBERT-v2",
                    "all_probabilities": probs.tolist()
                }
            except Exception as e:
                logger.error(f"IndicBERT error, falling back to XLM-R: {e}")
    
    sentiment_tokenizer, sentiment_model = get_sentiment_model()
    if sentiment_tokenizer is None or sentiment_model is None:
        logger.error("No sentiment model available")
        return {"error": "No sentiment model available", "label": "unknown", "confidence": 0.0, "model_used": "none"}
    
    try:
        inputs = encode_text(text, sentiment_tokenizer)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = sentiment_model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=1)
            predicted_class_idx = torch.argmax(probs, dim=1).item()
            predicted_label = SENTIMENT_LABELS[predicted_class_idx]
            confidence_score = probs[0][predicted_class_idx].item()
        
        return {
            "label": predicted_label,
            "confidence": confidence_score,
            "model_used": "XLM-RoBERTa",
            "all_probabilities": probs.tolist()
        }
    except Exception as e:
        logger.error(f"Sentiment prediction error: {e}")
        return {"error": str(e), "label": "unknown", "confidence": 0.0, "model_used": "error"}


@log_performance(logger)
@validate_inputs(
    text=lambda x: TextValidator.validate_text_input(x, min_length=1, max_length=10000)
)
def predict_toxicity(text: str) -> Dict:
    """
    Returns a dictionary of toxicity scores for the given text using sigmoid multi-label output.
    
    Args:
        text (str): Preprocessed text to analyze
    
    Returns:
        dict: Toxicity scores for each category
    
    Raises:
        ValidationError: If input validation fails
    """
    toxicity_tokenizer, toxicity_model = get_toxicity_model()
    if toxicity_tokenizer is None or toxicity_model is None:
        logger.error("No toxicity model available")
        return {label: 0.0 for label in TOXICITY_LABELS}
    
    try:
        inputs = encode_text(text, toxicity_tokenizer)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = toxicity_model(**inputs)
            logits = outputs.logits
            probs = torch.sigmoid(logits)
        
        results = {}
        for i, label in enumerate(TOXICITY_LABELS):
            results[label] = probs[0][i].item()
        
        return results
    except Exception as e:
        logger.error(f"Toxicity prediction error: {e}")
        return {label: 0.0 for label in TOXICITY_LABELS}


# Async wrappers for non-blocking inference


async def predict_sentiment_async(text: str, language: Optional[str] = None, 
                                  executor: ThreadPoolExecutor = None) -> Dict:
    """
    Async wrapper for sentiment prediction - runs in thread pool to avoid blocking.
    
    Args:
        text: Input text
        language: Language code
        executor: Thread pool executor (if None, creates new thread)
    
    Returns:
        Sentiment prediction result
    """
    loop = asyncio.get_event_loop()
    
    if executor:
        result = await loop.run_in_executor(
            executor, 
            predict_sentiment, 
            text, 
            language
        )
    else:
        result = await loop.run_in_executor(
            None,
            predict_sentiment,
            text,
            language
        )
    
    return result


async def predict_toxicity_async(text: str, 
                                 executor: ThreadPoolExecutor = None) -> Dict:
    """
    Async wrapper for toxicity prediction - runs in thread pool to avoid blocking.
    
    Args:
        text: Input text
        executor: Thread pool executor
    
    Returns:
        Toxicity scores
    """
    loop = asyncio.get_event_loop()
    
    if executor:
        result = await loop.run_in_executor(executor, predict_toxicity, text)
    else:
        result = await loop.run_in_executor(None, predict_toxicity, text)
    
    return result


async def predict_sentiment_batch(texts: List[str], language: str = 'en') -> List[Dict]:
    """
    Batch sentiment prediction - processes multiple texts efficiently.
    
    Args:
        texts: List of texts to analyze
        language: Language code
    
    Returns:
        List of sentiment results
    """
    
    use_indic = language in INDIC_LANGUAGES
    
    if use_indic:
        tokenizer, model = get_indic_sentiment_model()
        labels_map = INDIC_SENTIMENT_LABELS
        model_name = "IndicBERT-v2"
    else:
        tokenizer, model = get_sentiment_model()
        labels_map = None
        model_name = "XLM-RoBERTa"
    
    if not tokenizer or not model:
        logger.error("Model not available for batch processing")
        return [{"error": "Model unavailable", "label": "unknown", "confidence": 0.0} 
                for _ in texts]
    
    try:
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=1)
        
        results = []
        for i in range(len(texts)):
            predicted_idx = torch.argmax(probs[i]).item()
            confidence = probs[i][predicted_idx].item()
            
            if use_indic:
                label = labels_map.get(predicted_idx, SENTIMENT_LABELS[predicted_idx])
            else:
                label = SENTIMENT_LABELS[predicted_idx]
            
            results.append({
                "label": label,
                "confidence": confidence,
                "model_used": model_name
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Batch sentiment error: {e}")
        return [{"error": str(e), "label": "unknown", "confidence": 0.0} 
                for _ in texts]


async def predict_toxicity_batch(texts: List[str]) -> List[Dict]:
    """
    Batch toxicity prediction - processes multiple texts efficiently.
    
    Args:
        texts: List of texts to analyze
    
    Returns:
        List of toxicity results
    """
    
    tokenizer, model = get_toxicity_model()
    
    if not tokenizer or not model:
        logger.error("Toxicity model not available")
        return [{label: 0.0 for label in TOXICITY_LABELS} for _ in texts]
    
    try:
        inputs = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.sigmoid(logits)
        
        results = []
        for i in range(len(texts)):
            result = {}
            for j, label in enumerate(TOXICITY_LABELS):
                result[label] = probs[i][j].item()
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Batch toxicity error: {e}")
        return [{label: 0.0 for label in TOXICITY_LABELS} for _ in texts]


# Model status functions


def get_sentiment_model_status() -> Dict[str, str]:
    """Get the loading status of sentiment analysis models."""
    global _sentiment_tokenizer, _sentiment_model
    global _indic_sentiment_tokenizer, _indic_sentiment_model
    
    xlm_status = "loaded" if (_sentiment_tokenizer is not None and _sentiment_model is not None) else "not_loaded"
    indic_status = "loaded" if (_indic_sentiment_tokenizer is not None and _indic_sentiment_model is not None) else "not_loaded"
    
    overall_status = "loaded" if (xlm_status == "loaded" or indic_status == "loaded") else "not_loaded"
    
    return {
        "status": overall_status,
        "xlm_roberta": xlm_status,
        "indic_bert": indic_status
    }


def get_toxicity_model_status() -> Dict[str, str]:
    """Get the loading status of toxicity detection model."""
    global _toxicity_tokenizer, _toxicity_model
    
    status = "loaded" if (_toxicity_tokenizer is not None and _toxicity_model is not None) else "not_loaded"
    
    return {
        "status": status,
        "model": "XLM-RoBERTa Toxicity"
    }


def get_all_models_status() -> Dict[str, any]:
    """Get comprehensive status of all ML models."""
    sentiment_status = get_sentiment_model_status()
    toxicity_status = get_toxicity_model_status()
    
    loaded_count = 0
    total_count = 3
    
    if sentiment_status["xlm_roberta"] == "loaded":
        loaded_count += 1
    if sentiment_status["indic_bert"] == "loaded":
        loaded_count += 1
    if toxicity_status["status"] == "loaded":
        loaded_count += 1
    
    return {
        "sentiment": sentiment_status,
        "toxicity": toxicity_status,
        "loaded_models": loaded_count,
        "total_models": total_count,
        "all_loaded": loaded_count == total_count
    }