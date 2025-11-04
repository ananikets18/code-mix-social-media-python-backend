"""FastAPI REST API for Multilingual NLP Analysis System - PRODUCTION READY"""

from fastapi import FastAPI, HTTPException, status, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import uvicorn
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configuration
from config import settings

# Import our NLP analysis function
from main import analyze_text_comprehensive
from preprocessing import preprocess_text, detect_language, normalize_language_code
from inference import predict_sentiment, predict_toxicity
from translation import translate_text
from profanity_filter import ProfanityFilter
from domain_processors import DomainProcessor
from logger_config import get_logger
from adaptive_learning import (
    record_user_feedback,
    get_learning_statistics,
    log_detection_issue,
    analyze_failure_patterns,
    store_detection_failure_with_context
)
from request_cache import (
    store_request,
    get_cached_response,
    get_cache_stats,
    clear_cache,
    remove_request
)
from redis_cache import redis_cache, is_cache_enabled

logger = get_logger(__name__, level=settings.log_level)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_hour}/hour"])

app = FastAPI(
    title="Multilingual NLP Analysis API",
    description="Comprehensive NLP analysis supporting International, Indian, and Code-Mixed languages",
    version="1.0.0 - Production Ready",
    docs_url="/docs" if settings.is_development else None,  # Disable docs in production
    redoc_url="/redoc" if settings.is_development else None,
    debug=settings.debug
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS with environment-based origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Restrict methods
    allow_headers=["*"],
)

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints"""
    if settings.is_development:
        return True  # Skip in development
    
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True


class TextAnalysisRequest(BaseModel):
    """Request model for comprehensive text analysis"""
    text: str = Field(..., min_length=1, max_length=5000)
    normalization_level: Optional[str] = Field(None)
    preserve_emojis: bool = Field(True)
    punctuation_mode: str = Field('preserve')
    check_profanity: bool = Field(True)
    detect_domains: bool = Field(True)
    compact: bool = Field(False, description="Return compact/simplified response (default: False)")
    
    @validator('normalization_level')
    def validate_normalization(cls, v):
        if v is not None and v not in ['light', 'moderate', 'aggressive']:
            raise ValueError("normalization_level must be 'light', 'moderate', 'aggressive', or None")
        return v
    
    @validator('punctuation_mode')
    def validate_punctuation(cls, v):
        if v not in ['preserve', 'minimal', 'aggressive']:
            raise ValueError("punctuation_mode must be 'preserve', 'minimal', or 'aggressive'")
        return v


class SimpleTextRequest(BaseModel):
    """Simple request model for single-feature endpoints"""
    text: str = Field(..., min_length=1, max_length=5000)


class TranslationRequest(BaseModel):
    """Request model for translation endpoint"""
    text: str = Field(..., min_length=1, max_length=5000)
    target_lang: str = Field('en')
    source_lang: str = Field('auto')


class ConversionRequest(BaseModel):
    """FIX #10: Request model for romanized-to-native conversion endpoint"""
    text: str = Field(..., min_length=1, max_length=5000, description="Romanized text to convert")
    language: str = Field(..., description="Target language code (hin, mar, ben, tam, tel, pan)")
    preserve_english: bool = Field(True, description="Preserve English words (default: True)")
    
    @validator('language')
    def validate_language(cls, v):
        supported = ['hin', 'hi', 'mar', 'mr', 'ben', 'bn', 'tam', 'ta', 'tel', 'te', 'pan', 'pa']
        if v not in supported:
            raise ValueError(f"language must be one of {supported}")
        return v


class UserFeedbackRequest(BaseModel):
    """Request model for user feedback/corrections"""
    text: str = Field(..., min_length=1, max_length=5000)
    detected_language: str = Field(...)
    correct_language: str = Field(...)
    user_id: Optional[str] = Field("anonymous")
    comments: Optional[str] = Field(None)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    features: Dict[str, bool]


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "Multilingual NLP Analysis API",
        "version": "1.0.0 - FIX #10: Hybrid Conversion + Request Caching + Redis",
        "docs": "/docs",
        "endpoints": {
            "comprehensive": "POST /analyze  [AUTO-CACHED + REDIS]",
            "sentiment": "POST /sentiment  [REDIS CACHED]",
            "toxicity": "POST /toxicity  [REDIS CACHED]",
            "translation": "POST /translate  [REDIS CACHED]",
            "convert": "POST /convert  [NEW: FIX #10 - Hybrid romanized-to-native conversion]",
            "profanity": "POST /profanity",
            "domains": "POST /domains",
            "feedback": "POST /feedback",
            "learning_stats": "GET /learning/stats",
            "failure_analysis": "GET /learning/failures",
            "cache_stats": "GET /cache/stats  [Request cache statistics]",
            "cache_clear": "DELETE /cache/clear  [Clear request cache]",
            "cache_remove": "DELETE /cache/remove  [Remove specific cache entry]",
            "redis_stats": "GET /redis/stats  [NEW: Redis cache statistics]",
            "redis_clear": "DELETE /redis/clear  [NEW: Clear Redis cache]",
            "redis_health": "GET /redis/health  [NEW: Redis health check]",
            "health": "GET /health"
        },
        "recent_fixes": {
            "FIX #11": "Redis integration for performance optimization",
            "FIX #10": "Hybrid romanized-to-native conversion (preserves English, converts Indic)",
            "FIX #9": "Enhanced logging for code-mixing events",
            "FIX #8": "Ensemble fusion (GLotLID + Romanized detection)",
            "FIX #7": "Adaptive code-mixing thresholds",
            "FIX #6": "Robust language code normalization"
        },
        "new_features": {
            "redis_caching": "High-performance Redis caching for all ML operations",
            "request_caching": "All /analyze requests are cached in data/analyze_cache.json",
            "duplicate_handling": "Duplicate requests automatically replace previous cached entries",
            "cache_management": "Use /cache/* and /redis/* endpoints to view and manage caches"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    redis_health = redis_cache.health_check() if is_cache_enabled() else {"status": "disabled"}
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0 - FIX #11: Redis Integration",
        features={
            "profanity_filter": True,
            "domain_detection": True,
            "language_analysis": True,
            "sentiment_analysis": True,
            "toxicity_detection": True,
            "translation": True,
            "preprocessing": True,
            "hybrid_conversion": True,  # FIX #10
            "code_mixing_detection": True,  # FIX #7
            "ensemble_fusion": True,  # FIX #8
            "redis_caching": redis_health["status"] in ["healthy", "disabled"]  # FIX #11
        }
    )


@app.post("/analyze", tags=["Comprehensive Analysis"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def analyze_text(request: Request, text_request: TextAnalysisRequest, authorized: bool = Depends(verify_api_key)):
    """
    Comprehensive text analysis with all features
    
    **NEW: Multi-layer caching enabled!**
    - **Redis Cache**: Fast in-memory caching for instant responses
    - **File Cache**: Persistent storage in data/analyze_cache.json
    - **Duplicate Detection**: Automatically replaces old cached entries
    
    **NEW: Set `compact=true` for simplified response!**
    
    **Compact Response** (~200 bytes):
    ```json
    {
      "text": "Mi aaj khup khush ahe!",
      "language": {
        "code": "mar",
        "name": "Marathi",
        "confidence": 0.85,
        "is_romanized": true,
        "is_code_mixed": false
      },
      "sentiment": {"label": "positive", "score": 0.47},
      "profanity": {"detected": false, "severity": null},
      "translation": "I am very happy today!",
      "toxicity_score": 0.019,
      "romanized_conversion": {
        "applied": true,
        "native_script": "मी आज खूप खुश आहे!"
      }
    }
    ```
    
    **Verbose Response** (~2000 bytes): Full details with all fields
    
    **Caching**: 
    - Redis: TTL-based caching (default: 1 hour)
    - File: Permanent cache in data/analyze_cache.json
    """
    try:
        # FIX #9: Log incoming request with text preview
        logger.info(f"[API FIX #9] /analyze request: text_length={len(text_request.text)}, "
                   f"compact={text_request.compact}, text_preview='{text_request.text[:50]}{'...' if len(text_request.text) > 50 else ''}'")
        
        # FIX #11: Check Redis cache first
        request_params = {
            "normalization_level": text_request.normalization_level,
            "preserve_emojis": text_request.preserve_emojis,
            "punctuation_mode": text_request.punctuation_mode,
            "check_profanity": text_request.check_profanity,
            "detect_domains": text_request.detect_domains,
            "compact": text_request.compact
        }
        
        # Try to get from Redis cache
        cached_result = redis_cache.get_cached_analysis(text_request.text, request_params)
        
        if cached_result:
            logger.info(f"[REDIS CACHE HIT] Returning cached result for text: '{text_request.text[:30]}...'")
            # Add cache info
            if isinstance(cached_result, dict):
                cached_result["cache_info"] = {
                    "source": "redis",
                    "cached": True,
                    "from_cache": True
                }
            return JSONResponse(status_code=status.HTTP_200_OK, content=cached_result)
        
        # Cache miss - perform analysis
        logger.info(f"[REDIS CACHE MISS] Performing analysis for: '{text_request.text[:30]}...'")
        
        result = analyze_text_comprehensive(
            text=text_request.text,
            normalization_level=text_request.normalization_level,
            preserve_emojis=text_request.preserve_emojis,
            punctuation_mode=text_request.punctuation_mode,
            check_profanity=text_request.check_profanity,
            detect_domains=text_request.detect_domains,
            compact=text_request.compact  # NEW: Pass compact parameter
        )
        
        # FIX #9: Log if code-mixing was detected
        if isinstance(result, dict):
            lang_info = result.get('language', {})
            if isinstance(lang_info, dict):
                is_code_mixed = lang_info.get('is_code_mixed', False) or 'mixed' in str(lang_info.get('code', ''))
                if is_code_mixed:
                    logger.info(f"[API FIX #9] ⚡ Code-mixed content detected: {lang_info.get('code')}, "
                               f"confidence={lang_info.get('confidence', 0):.2f}, "
                               f"romanized={lang_info.get('is_romanized', False)}")
        
        # FIX #11: Store in Redis cache
        cache_key = redis_cache.cache_analysis_result(text_request.text, request_params, result)
        
        # Also store in file cache (backward compatibility)
        is_duplicate, text_hash = store_request(
            text=text_request.text,
            response=result,
            request_params=request_params
        )
        
        # Add cache info to response
        if isinstance(result, dict):
            result["cache_info"] = {
                "source": "fresh",
                "cached": True,
                "redis_key": cache_key if is_cache_enabled() else None,
                "file_cached": True,
                "is_duplicate": is_duplicate,
                "text_hash": text_hash,
                "cache_file": "data/analyze_cache.json"
            }
        
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/sentiment", tags=["Individual Features"])
async def analyze_sentiment(request: SimpleTextRequest):
    """Sentiment analysis only - WITH REDIS CACHING"""
    try:
        logger.info(f"[API FIX #9] /sentiment request: text_length={len(request.text)}")
        
        lang_result = detect_language(request.text, detailed=True)  # FIX #9: Get detailed result
        
        # FIX #6: Normalize language code before passing to inference
        # Handles GLotLID variants (hif→hin, urd→hin, snd→sin, etc.)
        raw_lang = lang_result['language']
        normalized_lang = normalize_language_code(raw_lang, keep_suffixes=False)
        
        if raw_lang != normalized_lang:
            logger.info(f"[API] Language code normalized for sentiment: {raw_lang} → {normalized_lang}")
        
        # FIX #11: Check Redis cache
        cached_sentiment = redis_cache.get_cached_sentiment(request.text, normalized_lang)
        if cached_sentiment:
            logger.info(f"[REDIS CACHE HIT] Sentiment for: '{request.text[:30]}...'")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "text": request.text,
                    "language": normalized_lang,
                    "sentiment": cached_sentiment,
                    "_cache": {"source": "redis", "hit": True}
                }
            )
        
        # FIX #9: Log if code-mixing detected
        lang_info = lang_result.get('language_info', {})
        if lang_info.get('is_code_mixed', False):
            logger.info(f"[API FIX #9] ⚡ Code-mixed sentiment analysis: {normalized_lang}, "
                       f"confidence={lang_result.get('confidence', 0):.2f}, "
                       f"method={lang_result.get('method', 'unknown')}")
        
        cleaned_text = preprocess_text(request.text)
        sentiment_result = predict_sentiment(cleaned_text, language=normalized_lang)
        
        # FIX #11: Cache in Redis
        redis_cache.cache_sentiment(request.text, normalized_lang, sentiment_result)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": request.text,
                "language": normalized_lang,  # Return normalized code
                "sentiment": sentiment_result,
                "_cache": {"source": "fresh", "hit": False}
            }
        )
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


@app.post("/toxicity", tags=["Individual Features"])
async def analyze_toxicity(request: SimpleTextRequest):
    """
    Toxicity detection only
    
    Detects toxic content in 6 categories:
    - toxic, severe_toxic, obscene, threat, insult, identity_hate
    
    Returns scores (0-1) for each category.
    """
    try:
        logger.info(f"[API FIX #9] /toxicity request: text_length={len(request.text)}")
        
        # FIX #6: Detect and normalize language code
        lang_result = detect_language(request.text, detailed=True)  # FIX #9: Get detailed result
        raw_lang = lang_result.get('language', 'unknown')
        normalized_lang = normalize_language_code(raw_lang, keep_suffixes=False)
        
        if raw_lang != normalized_lang:
            logger.info(f"[API] Language code normalized for toxicity: {raw_lang} → {normalized_lang}")
        
        # FIX #9: Log if code-mixing detected
        lang_info = lang_result.get('language_info', {})
        if lang_info.get('is_code_mixed', False):
            logger.info(f"[API FIX #9] ⚡ Code-mixed toxicity analysis: {normalized_lang}, "
                       f"confidence={lang_result.get('confidence', 0):.2f}, "
                       f"method={lang_result.get('method', 'unknown')}")
        
        # Preprocess text
        cleaned_text = preprocess_text(request.text)
        
        # Get toxicity scores (XLM-R toxicity model handles normalized codes)
        toxicity_result = predict_toxicity(cleaned_text)
        
        # Find highest risk
        max_category = max(toxicity_result.items(), key=lambda x: x[1])
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": request.text,
                "language": normalized_lang,  # Include normalized language
                "toxicity_scores": toxicity_result,
                "highest_risk": {
                    "category": max_category[0],
                    "score": max_category[1]
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error in toxicity analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Toxicity analysis failed: {str(e)}"
        )


@app.post("/translate", tags=["Individual Features"])
async def translate(request: TranslationRequest):
    """
    Translation only - WITH REDIS CACHING (24-hour TTL)
    
    Translates text from source language to target language.
    Supports auto-detection of source language.
    **NEW: Automatically detects and converts romanized Indian languages to Devanagari before translation!**
    
    Common language codes: en (English), hi (Hindi), es (Spanish), etc.
    
    **Examples:**
    - "Aaj traffic khup heavy aahe" → Detects romanized Marathi → Converts to Devanagari → Translates to "Traffic is very heavy today"
    - "Mai bahut khush hoon" → Detects romanized Hindi → Converts to Devanagari → Translates to "I am very happy"
    """
    try:
        logger.info(f"[API FIX #9] /translate request: text_length={len(request.text)}, target={request.target_lang}")
        
        # Detect if text is romanized Indian language
        lang_result = detect_language(request.text, detailed=True)  # FIX #9: Get detailed result
        
        # FIX #6: Normalize language code
        raw_lang = lang_result.get('language', 'unknown')
        normalized_lang = normalize_language_code(raw_lang, keep_suffixes=False)
        
        if raw_lang != normalized_lang:
            logger.info(f"[API] Language code normalized for translation: {raw_lang} → {normalized_lang}")
        
        source_lang_for_cache = request.source_lang if request.source_lang != 'auto' else normalized_lang
        
        # FIX #11: Check Redis cache for translation
        cached_translation = redis_cache.get_cached_translation(
            request.text, 
            source_lang_for_cache, 
            request.target_lang
        )
        if cached_translation:
            logger.info(f"[REDIS CACHE HIT] Translation for: '{request.text[:30]}...'")
            cached_translation["_cache"] = {"source": "redis", "hit": True}
            return JSONResponse(status_code=status.HTTP_200_OK, content=cached_translation)
        
        # FIX #9: Log if code-mixing detected
        lang_info = lang_result.get('language_info', {})
        if lang_info.get('is_code_mixed', False):
            logger.info(f"[API FIX #9] ⚡ Code-mixed translation: {normalized_lang}, "
                       f"confidence={lang_result.get('confidence', 0):.2f}, "
                       f"method={lang_result.get('method', 'unknown')}")
        
        is_romanized = lang_result.get('is_romanized', False)
        
        logger.info(f"Translation - Language: {normalized_lang}, Romanized: {is_romanized}")
        
        # Translate text (with automatic romanized conversion if needed)
        translation_result = translate_text(
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang,
            is_romanized=is_romanized
        )
        
        if translation_result['success']:
            response_content = {
                "original_text": request.text,
                "translated_text": translation_result['translated_text'],
                "source_language": translation_result.get('detected_source_lang', normalized_lang),  # Use normalized
                "target_language": request.target_lang,
                "success": True,
                "_cache": {"source": "fresh", "hit": False}
            }
            
            # Add romanized conversion info if applicable
            if is_romanized and 'converted_to_devanagari' in translation_result:
                response_content['romanized_detected'] = True
                response_content['converted_to_devanagari'] = translation_result['converted_to_devanagari']
                response_content['conversion_info'] = translation_result.get('conversion_info', {})
                logger.info(f"Romanized text converted: {translation_result['converted_to_devanagari']}")
            
            # FIX #11: Cache the translation in Redis (24-hour TTL)
            redis_cache.cache_translation(
                request.text,
                source_lang_for_cache,
                request.target_lang,
                response_content,
                ttl=86400  # 24 hours
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_content
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=translation_result.get('error', 'Translation failed')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@app.post("/convert", tags=["Individual Features"])
async def convert_romanized_to_native(request: ConversionRequest):
    """
    FIX #10: Hybrid Romanized-to-Native Script Conversion
    
    Intelligently converts romanized Indic text to native script while preserving English words.
    
    **Key Features:**
    - **Selective Conversion**: Only converts romanized Indic tokens, preserves English
    - **Proper Noun Preservation**: Keeps capitalized words (John, Mumbai, Google)
    - **Smart Detection**: Uses both dictionary and ITRANS transliteration
    - **Mixed Language Support**: Handles Hinglish, Marathi-English, etc.
    - **Detailed Statistics**: Shows conversion rate, preserved tokens, etc.
    
    **Supported Languages:**
    - Hindi (hin/hi)
    - Marathi (mar/mr)
    - Bengali (ben/bn)
    - Tamil (tam/ta)
    - Telugu (tel/te)
    - Punjabi (pan/pa)
    
    **Examples:**
    
    *Pure Romanized:*
    ```
    Input: "aaj mausam bahut acha hai"
    Output: "आज मौसम् बहुत अच है"
    ```
    
    *Mixed Language (Hinglish):*
    ```
    Input: "I am going to office, bahut traffic hai"
    Output: "I am going to ऑफिस, बहुत ट्रैफिक है"
    (Preserves: I, am, going, to; Converts: office, bahut, traffic, hai)
    ```
    
    *Proper Nouns:*
    ```
    Input: "John Mumbai la gaya, Google madhe kaam karto"
    Output: "John Mumbai ला गय, Google मधे काम कर्तो"
    (Preserves: John, Mumbai, Google)
    ```
    
    **Response Format:**
    ```json
    {
      "original_text": "aaj I am going bahut khush",
      "converted_text": "आज I am going बहुत खुश",
      "language": "hin",
      "conversion_method": "hybrid",
      "statistics": {
        "total_tokens": 6,
        "converted_tokens": 3,
        "preserved_tokens": 3,
        "failed_tokens": 0,
        "conversion_rate": 50.0
      },
      "token_details": [
        {"original": "aaj", "converted": "आज", "status": "converted", "method": "dictionary"},
        {"original": "I", "converted": "I", "status": "preserved_english", "method": "none"},
        ...
      ]
    }
    ```
    """
    try:
        logger.info(f"[API FIX #10] /convert request: text_length={len(request.text)}, "
                   f"language={request.language}, preserve_english={request.preserve_english}")
        
        # Import conversion function
        from preprocessing import convert_romanized_to_native
        
        # Perform hybrid conversion
        result = convert_romanized_to_native(
            text=request.text,
            lang_code=request.language,
            preserve_english=request.preserve_english
        )
        
        # Enhance response with language info
        response = {
            "original_text": result['original_text'],
            "converted_text": result['converted_text'],
            "language": request.language,
            "conversion_method": result['conversion_method'],
            "statistics": result['statistics'],
            "token_details": result['token_details']
        }
        
        logger.info(f"[API FIX #10] Conversion complete: {result['statistics']['converted_tokens']}/"
                   f"{result['statistics']['total_tokens']} tokens, method={result['conversion_method']}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response
        )
        
    except Exception as e:
        logger.error(f"[API FIX #10] Error in conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )


@app.post("/profanity", tags=["Individual Features"])
async def check_profanity(request: SimpleTextRequest):
    """
    Profanity check only
    
    Detects profanity/bad words in 10 languages:
    English, Hindi, Marathi, Tamil, Telugu, Kannada, Punjabi, Gujarati, Bengali, Malayalam
    
    Returns severity levels: extreme, moderate, mild
    """
    try:
        logger.info(f"Profanity check request: text_length={len(request.text)}")
        
        # Initialize profanity filter
        profanity_filter = ProfanityFilter()
        
        # Detect profanity
        profanity_result = profanity_filter.detect_profanity(request.text)
        
        # Get statistics
        stats = profanity_filter.get_statistics(request.text)
        
        # Mask profanity for display
        censored_text = profanity_filter.mask_profanity(request.text) if profanity_result['has_profanity'] else request.text
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": request.text,
                "has_profanity": profanity_result['has_profanity'],
                "severity": profanity_result['max_severity'],
                "severity_score": profanity_result['severity_score'],
                "detected_words": profanity_result['detected_words'],
                "censored_text": censored_text,
                "statistics": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error in profanity check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profanity check failed: {str(e)}"
        )


@app.post("/domains", tags=["Individual Features"])
async def detect_domains(request: SimpleTextRequest):
    """
    Domain detection only
    
    Detects domain-specific content:
    - Financial: currencies, amounts, financial terms
    - Temporal: dates, times, relative dates
    - Technical: code, functions, programming keywords
    
    Also extracts relevant entities from the text.
    """
    try:
        logger.info(f"Domain detection request: text_length={len(request.text)}")
        
        # Initialize domain processor
        domain_processor = DomainProcessor()
        
        # Detect domains
        domain_result = domain_processor.detect_domains(request.text)
        
        # Extract entities
        entities = domain_processor.extract_all_entities(request.text)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": request.text,
                "domains": domain_result,
                "entities": entities
            }
        )
        
    except Exception as e:
        logger.error(f"Error in domain detection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Domain detection failed: {str(e)}"
        )


# ==================== ADAPTIVE LEARNING ENDPOINTS (NEW) ====================

@app.post("/feedback", 
          summary="Submit Feedback/Corrections",
          description="Submit user corrections to improve language detection accuracy over time",
          tags=["Adaptive Learning"])
async def submit_user_feedback(request: UserFeedbackRequest):
    """
    **NEW ENDPOINT - Adaptive Learning System**
    
    Submit feedback when the system incorrectly detects a language.
    The system will learn from this correction and improve future detections.
    
    **Parameters:**
    - **text**: The text that was analyzed
    - **detected_language**: What the system detected
    - **correct_language**: The actual correct language
    - **user_id**: (Optional) User identifier for tracking
    - **comments**: (Optional) Additional context
    
    **Returns:**
    - Confirmation message
    - Correction ID
    - Current statistics
    
    **Example:**
    ```
    POST /feedback
    {
        "text": "Tu Khup chukicha",
        "detected_language": "hin",
        "correct_language": "mar",
        "user_id": "user123",
        "comments": "This is Marathi in romanized form"
    }
    ```
    """
    try:
        logger.info(f"User feedback received from {request.user_id}")
        
        # Record the correction in adaptive learning system
        correction_id = record_user_feedback(
            text=request.text,
            detected_language=request.detected_language,
            correct_language=request.correct_language,
            user_id=request.user_id,
            comments=request.comments
        )
        
        # Get updated statistics
        stats = get_learning_statistics()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Feedback recorded successfully. Thank you for helping improve the system!",
                "correction_id": correction_id,
                "statistics": {
                    "total_corrections": stats.get('user_corrections_count', 0),
                    "total_patterns_learned": stats.get('cached_patterns_count', 0),
                    "cache_hit_rate": stats.get('cache_hit_rate', 0.0)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error recording user feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )


@app.get("/learning/stats",
         summary="Get Learning Statistics",
         description="Retrieve statistics and analytics from the adaptive learning system",
         tags=["Adaptive Learning"])
async def get_learning_stats():
    """
    **NEW ENDPOINT - Adaptive Learning System**
    
    Get comprehensive statistics about the adaptive learning system:
    - Pattern cache size and performance
    - User correction history
    - Detection failures logged
    - Cache hit rates
    - Top detected languages
    
    **Returns:**
    - Complete statistics dashboard
    - Performance metrics
    - Learning trends
    
    **Example Response:**
    ```json
    {
        "cache_statistics": {
            "total_patterns": 234,
            "total_requests": 1523,
            "cache_hits": 892,
            "cache_hit_rate": 58.57
        },
        "user_corrections": {
            "total_corrections": 12,
            "recent_corrections": [...]
        },
        "detection_failures": {
            "total_failures": 8,
            "common_failure_languages": ["mar", "hin"]
        }
    }
    ```
    """
    try:
        logger.info("Learning statistics requested")
        
        # Get comprehensive statistics
        stats = get_learning_statistics()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "statistics": stats,
                "system_info": {
                    "adaptive_learning_enabled": True,
                    "auto_save_threshold": 100,
                    "pattern_reuse_threshold": 3,
                    "confidence_threshold": 0.70,
                    "max_cache_size": 10000
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving learning statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@app.get("/learning/failures",
         summary="Analyze Detection Failures",
         description="Get insights and patterns from stored detection failures",
         tags=["Adaptive Learning"])
async def analyze_failures(limit: int = 50):
    """
    **NEW ENDPOINT - Failure Pattern Analysis**
    
    Analyzes stored detection failures to identify patterns and suggest improvements.
    
    **Query Parameters:**
    - **limit**: Number of recent failures to analyze (default: 50, max: 500)
    
    **Returns:**
    - Common failure reasons
    - Most misdetected languages
    - Problematic scripts/patterns
    - Recommendations for improvement
    
    **Example:**
    ```
    GET /learning/failures?limit=100
    ```
    
    **Response:**
    ```json
    {
        "total_failures_analyzed": 100,
        "top_failure_reasons": [
            ["obscure_language_ido", 23],
            ["low_confidence_0.22", 18],
            ["unknown_language", 12]
        ],
        "most_misdetected_as": [
            ["ido", 23],
            ["unknown", 12]
        ],
        "problematic_scripts": [
            ["latin", 67],
            ["unknown", 15]
        ],
        "recommendations": [
            {
                "issue": "Frequent 'ido' detection for romanized Indic languages",
                "solution": "Add romanized Indic language detection before GlotLID",
                "priority": "HIGH"
            }
        ]
    }
    ```
    """
    try:
        # Validate limit
        if limit < 1 or limit > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 500"
            )
        
        logger.info(f"Failure pattern analysis requested (limit: {limit})")
        
        # Get failure analysis
        insights = analyze_failure_patterns(limit=limit)
        
        if "error" in insights:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=insights["error"]
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "analysis": insights,
                "info": {
                    "analyzed_failures": limit,
                    "data_source": "data/detection_failures.json",
                    "analysis_date": datetime.now().strftime("%Y-%m-%d")
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing failure patterns: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze failures: {str(e)}"
        )


# ==================== REQUEST CACHE MANAGEMENT ENDPOINTS (NEW) ====================

@app.get("/cache/stats",
         summary="Get Cache Statistics",
         description="Get statistics about the /analyze endpoint request cache",
         tags=["Cache Management"])
async def get_request_cache_stats():
    """
    **NEW ENDPOINT - Request Cache Statistics**
    
    Get detailed statistics about cached requests from the /analyze endpoint.
    
    **Returns:**
    - Total unique requests cached
    - Total duplicate requests (cache hits)
    - Cache hit rate
    - Top 5 most requested texts
    - Cache creation and last update time
    
    **Example:**
    ```
    GET /cache/stats
    ```
    
    **Response:**
    ```json
    {
        "cache_info": {
            "description": "Cache for /analyze endpoint requests",
            "created": "2025-11-03T10:30:00",
            "total_requests": 42,
            "last_updated": "2025-11-03T12:15:00"
        },
        "total_unique_requests": 42,
        "total_duplicate_hits": 18,
        "cache_hit_rate": 0.43,
        "top_requested": [
            {
                "text": "Hello world...",
                "request_count": 5,
                "last_timestamp": "2025-11-03T12:15:00"
            }
        ]
    }
    ```
    """
    try:
        logger.info("[CACHE API] Cache statistics requested")
        
        stats = get_cache_stats()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "statistics": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@app.delete("/cache/clear",
            summary="Clear Request Cache",
            description="Clear all cached requests from the /analyze endpoint",
            tags=["Cache Management"])
async def clear_request_cache():
    """
    **NEW ENDPOINT - Clear Request Cache**
    
    Clear all cached requests from the /analyze endpoint.
    This removes all entries from `data/analyze_cache.json`.
    
    **Returns:**
    - Success status
    - Number of requests cleared
    
    **Example:**
    ```
    DELETE /cache/clear
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Cache cleared successfully",
        "requests_cleared": 42
    }
    ```
    """
    try:
        logger.info("[CACHE API] Cache clear requested")
        
        # Get current stats before clearing
        stats = get_cache_stats()
        requests_cleared = stats.get("total_unique_requests", 0)
        
        # Clear the cache
        success = clear_cache()
        
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Cache cleared successfully",
                    "requests_cleared": requests_cleared,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cache"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


class RemoveCacheRequest(BaseModel):
    """Request model for removing specific cache entry"""
    text: str = Field(..., min_length=1, description="The text to remove from cache")


@app.delete("/cache/remove",
            summary="Remove Specific Cache Entry",
            description="Remove a specific request from the cache by text",
            tags=["Cache Management"])
async def remove_cache_entry(request: RemoveCacheRequest):
    """
    **NEW ENDPOINT - Remove Specific Cache Entry**
    
    Remove a specific cached request by providing the exact text.
    
    **Parameters:**
    - **text**: The exact text to remove from cache (case-insensitive)
    
    **Returns:**
    - Success status
    - Whether the entry was found and removed
    
    **Example:**
    ```json
    {
        "text": "Hello world"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Cache entry removed",
        "text_preview": "Hello world"
    }
    ```
    """
    try:
        logger.info(f"[CACHE API] Cache entry removal requested: text_preview='{request.text[:50]}...'")
        
        # Try to remove the entry
        removed = remove_request(request.text)
        
        if removed:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "message": "Cache entry removed",
                    "text_preview": request.text[:50] + "..." if len(request.text) > 50 else request.text,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found in cache"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing cache entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove cache entry: {str(e)}"
        )


# ==================== REDIS CACHE MANAGEMENT ENDPOINTS (NEW - FIX #11) ====================

@app.get("/redis/stats",
         summary="Get Redis Cache Statistics",
         description="Get detailed statistics about Redis cache usage and performance",
         tags=["Redis Cache"])
async def get_redis_stats():
    """
    **NEW ENDPOINT - FIX #11: Redis Cache Statistics**
    
    Get comprehensive statistics about the Redis cache:
    - Connection status
    - Redis version and memory usage
    - Total keys and breakdown by type
    - Performance metrics
    
    **Returns:**
    - Redis server information
    - Cache statistics
    - Key counts by category
    
    **Example Response:**
    ```json
    {
        "enabled": true,
        "status": "connected",
        "redis_version": "7.0.0",
        "used_memory_human": "2.5M",
        "connected_clients": 3,
        "total_keys": 156,
        "keys_by_type": {
            "analysis": 42,
            "lang_detect": 38,
            "sentiment": 45,
            "translation": 31
        },
        "ttl": 3600
    }
    ```
    """
    try:
        logger.info("[REDIS API] Redis statistics requested")
        
        stats = redis_cache.get_stats()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "redis": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting Redis stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Redis statistics: {str(e)}"
        )


@app.get("/redis/health",
         summary="Redis Health Check",
         description="Check if Redis is connected and responsive",
         tags=["Redis Cache"])
async def redis_health():
    """
    **NEW ENDPOINT - FIX #11: Redis Health Check**
    
    Check the health and connectivity of the Redis cache.
    
    **Returns:**
    - Connection status
    - Health message
    - Redis URL (sanitized)
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "message": "Redis is connected and responsive",
        "url": "redis://localhost:6379"
    }
    ```
    """
    try:
        logger.info("[REDIS API] Redis health check requested")
        
        health = redis_cache.health_check()
        
        status_code = status.HTTP_200_OK if health["status"] in ["healthy", "disabled"] else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content={
                "timestamp": datetime.now().isoformat(),
                **health
            }
        )
        
    except Exception as e:
        logger.error(f"Error checking Redis health: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.delete("/redis/clear",
            summary="Clear Redis Cache",
            description="Clear all cached data from Redis (USE WITH CAUTION)",
            tags=["Redis Cache"])
async def clear_redis_cache(pattern: Optional[str] = None):
    """
    **NEW ENDPOINT - FIX #11: Clear Redis Cache**
    
    Clear cached data from Redis. Can clear all data or specific patterns.
    
    **Query Parameters:**
    - **pattern**: Optional pattern to match keys (e.g., "analysis:*", "sentiment:*")
                  If not provided, clears ALL cache data
    
    **WARNING**: This is a destructive operation!
    
    **Returns:**
    - Success status
    - Number of keys deleted
    
    **Examples:**
    ```
    DELETE /redis/clear                    # Clear ALL cache
    DELETE /redis/clear?pattern=analysis:* # Clear only analysis cache
    DELETE /redis/clear?pattern=sentiment:* # Clear only sentiment cache
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "message": "Redis cache cleared",
        "keys_deleted": 156,
        "pattern": "analysis:*"
    }
    ```
    """
    try:
        logger.warning(f"[REDIS API] Redis cache clear requested (pattern: {pattern or 'ALL'})")
        
        if not is_cache_enabled():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redis caching is not enabled"
            )
        
        if pattern:
            # Clear specific pattern
            deleted = redis_cache.clear_by_pattern(pattern)
            message = f"Redis cache cleared for pattern: {pattern}"
        else:
            # Clear all cache
            success = redis_cache.clear_all()
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to clear Redis cache"
                )
            deleted = "all"
            message = "All Redis cache cleared"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": message,
                "keys_deleted": deleted,
                "pattern": pattern or "all",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing Redis cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear Redis cache: {str(e)}"
        )


# ==================== ERROR HANDLERS ====================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )


# ==================== STARTUP/SHUTDOWN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    """Execute on API startup - Preload models for better performance"""
    logger.info("=" * 80)
    logger.info("Multilingual NLP Analysis API Starting...")
    logger.info(f"Version: 1.1.0 - Async Inference + Batch Processing")
    logger.info(f"Environment: {settings.api_env}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"Allowed Origins: {settings.get_allowed_origins_list()}")
    logger.info(f"Rate Limit: {settings.rate_limit_per_minute}/min, {settings.rate_limit_per_hour}/hr")
    logger.info("Features: Profanity Filter, Domain Detection, Language Analysis,")
    logger.info("          Sentiment Analysis, Toxicity Detection, Translation")
    logger.info(f"Redis Caching: {'ENABLED' if is_cache_enabled() else 'DISABLED'}")
    logger.info("=" * 80)
    
    # NEW: Create thread pool executor for CPU-bound ML inference
    app.state.executor = ThreadPoolExecutor(max_workers=4)
    logger.info("✓ Thread pool executor created (4 workers for async inference)")
    logger.info("=" * 80)
    
    # Check Redis connection
    if is_cache_enabled():
        redis_health = redis_cache.health_check()
        logger.info(f"Redis Status: {redis_health['status'].upper()}")
        if redis_health['status'] == 'healthy':
            logger.info(f"✓ Redis connected: {redis_health.get('url', 'N/A')}")
            stats = redis_cache.get_stats()
            logger.info(f"✓ Redis Version: {stats.get('redis_version', 'unknown')}")
            logger.info(f"✓ Redis Memory: {stats.get('used_memory_human', 'unknown')}")
            logger.info(f"✓ Total Cached Keys: {stats.get('total_keys', 0)}")
        else:
            logger.warning(f"⚠ Redis not healthy: {redis_health.get('message', 'Unknown error')}")
    else:
        logger.info("Redis caching is disabled (set REDIS_ENABLED=true to enable)")
    
    # Preload models at startup for better performance
    try:
        logger.info("Preloading ML models...")
        # Import here to trigger model loading
        from inference import predict_sentiment, predict_toxicity
        from preprocessing import detect_language
        
        # Warm up models with dummy data
        detect_language("test", detailed=False)
        logger.info("✓ Models preloaded successfully")
    except Exception as e:
        logger.warning(f"Model preloading failed (will load on first request): {e}")
    
    logger.info("=" * 80)
    logger.info("API READY - Accepting requests")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on API shutdown"""
    logger.info("Shutting down thread pool executor...")
    app.state.executor.shutdown(wait=True)
    logger.info("✓ Thread pool executor shut down")
    logger.info("Multilingual NLP Analysis API Shutting Down...")


# ==================== MAIN ====================

if __name__ == "__main__":
    # Run the API server
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Workers: {settings.workers}")
    logger.info(f"Environment: {settings.api_env}")
    
    uvicorn.run(
        "api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,  # Only reload in development
        log_level=settings.log_level.lower(),
        workers=1 if settings.is_development else settings.workers  # Multi-process in production
    )
