"""FastAPI REST API for Multilingual NLP Analysis System - STREAMLINED VERSION
Version: 2.0.0 - Only Essential Endpoints
"""

from fastapi import FastAPI, HTTPException, status, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
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
from inference import predict_sentiment
from translation import translate_text
from profanity_filter import ProfanityFilter
from domain_processors import DomainProcessor
from logger_config import get_logger
from adaptive_learning import (
    record_user_feedback,
    get_learning_statistics
)
from request_cache import store_request, get_cached_response
from redis_cache import redis_cache, is_cache_enabled

logger = get_logger(__name__, level=settings.log_level)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_hour}/hour"])

# ==================== LIFESPAN CONTEXT MANAGER ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("=" * 60)
    logger.info("NLP API v2.0.0 - Starting...")
    logger.info("=" * 60)
    
    # Create thread pool executor
    app.state.executor = ThreadPoolExecutor(max_workers=4)
    
    # Check Redis
    if is_cache_enabled():
        redis_health = redis_cache.health_check()
        if redis_health['status'] == 'healthy':
            logger.info(f"✓ Redis: Connected")
        else:
            logger.warning(f"✗ Redis: {redis_health.get('message', 'Not connected')}")
    
    logger.info("=" * 60)
    logger.info("API Ready - http://localhost:8000")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    app.state.executor.shutdown(wait=True)
    logger.info("API shutdown complete")

app = FastAPI(
    title="Multilingual NLP Analysis API",
    description="Comprehensive NLP analysis supporting International, Indian, and Code-Mixed languages",
    version="2.0.0 - Streamlined",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    debug=settings.debug,
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for protected endpoints"""
    if settings.is_development:
        return True
    
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return True


# ==================== REQUEST MODELS ====================

class TextAnalysisRequest(BaseModel):
    """Request model for comprehensive text analysis"""
    text: str = Field(..., min_length=1, max_length=5000)
    normalization_level: Optional[str] = Field(None)
    preserve_emojis: bool = Field(True)
    punctuation_mode: str = Field('preserve')
    check_profanity: bool = Field(True)
    detect_domains: bool = Field(True)
    compact: bool = Field(False)


class SimpleTextRequest(BaseModel):
    """Simple request model for single-feature endpoints"""
    text: str = Field(..., min_length=1, max_length=5000)


class TranslationRequest(BaseModel):
    """Request model for translation endpoint"""
    text: str = Field(..., min_length=1, max_length=5000)
    target_lang: str = Field('en')
    source_lang: str = Field('auto')


class ConversionRequest(BaseModel):
    """Request model for romanized-to-native conversion endpoint"""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(..., description="Target language code (hin, mar, ben, tam, tel, pan)")
    preserve_english: bool = Field(True)


class UserFeedbackRequest(BaseModel):
    """Request model for user feedback/corrections"""
    text: str = Field(..., min_length=1, max_length=5000)
    detected_language: str = Field(...)
    correct_language: str = Field(...)
    user_id: Optional[str] = Field("anonymous")
    comments: Optional[str] = Field(None)


class BatchTextRequest(BaseModel):
    """Request model for batch processing"""
    texts: List[str] = Field(..., min_length=1, max_length=100, description="List of texts to analyze (max 100)")
    compact: bool = Field(True)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    features: Dict[str, bool]


# ==================== ENDPOINT 1: GET / - API ROOT/INFO ====================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint - Information about available endpoints"""
    return {
        "message": "Multilingual NLP Analysis API",
        "version": "2.0.0 - Streamlined",
        "endpoints": {
            "root": "GET /",
            "health": "GET /health",
            "analyze": "POST /analyze",
            "batch": "POST /analyze/batch",
            "sentiment": "POST /sentiment",
            "translate": "POST /translate",
            "convert": "POST /convert",
            "feedback": "POST /feedback",
            "learning_stats": "GET /learning/stats",
            "status": "GET /status"
        },
        "docs": "/docs"
    }


# ==================== ENDPOINT 2: GET /health - SIMPLE HEALTH CHECK ====================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Simple health check endpoint"""
    redis_health = redis_cache.health_check() if is_cache_enabled() else {"status": "disabled"}
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="2.0.0 - Streamlined",
        features={
            "sentiment_analysis": True,
            "toxicity_detection": True,
            "translation": True,
            "profanity_filter": True,
            "redis_caching": redis_health["status"] in ["healthy", "disabled"],
            "batch_processing": True
        }
    )


# ==================== ENDPOINT 3: POST /analyze - FULL COMPREHENSIVE ANALYSIS ====================

@app.post("/analyze", tags=["Comprehensive Analysis"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def analyze_text(request: Request, text_request: TextAnalysisRequest, authorized: bool = Depends(verify_api_key)):
    """Full comprehensive analysis with all features"""
    try:
        logger.info(f"[/analyze] text_length={len(text_request.text)}")
        
        # Check Redis cache
        request_params = {
            "normalization_level": text_request.normalization_level,
            "preserve_emojis": text_request.preserve_emojis,
            "punctuation_mode": text_request.punctuation_mode,
            "check_profanity": text_request.check_profanity,
            "detect_domains": text_request.detect_domains,
            "compact": text_request.compact
        }
        
        cached_result = redis_cache.get_cached_analysis(text_request.text, request_params)
        if cached_result:
            logger.info(f"[CACHE HIT] /analyze")
            cached_result["cache_info"] = {"source": "redis", "hit": True}
            return JSONResponse(status_code=status.HTTP_200_OK, content=cached_result)
        
        # Perform analysis
        result = analyze_text_comprehensive(
            text=text_request.text,
            normalization_level=text_request.normalization_level,
            preserve_emojis=text_request.preserve_emojis,
            punctuation_mode=text_request.punctuation_mode,
            check_profanity=text_request.check_profanity,
            detect_domains=text_request.detect_domains,
            compact=text_request.compact
        )
        
        # Cache result
        redis_cache.cache_analysis_result(text_request.text, request_params, result)
        store_request(text=text_request.text, response=result, request_params=request_params)
        
        if isinstance(result, dict):
            result["cache_info"] = {"source": "fresh", "hit": False}
        
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


# ==================== ENDPOINT 4: POST /analyze/batch - BATCH ANALYSIS ====================

@app.post("/analyze/batch", tags=["Batch Processing"])
@limiter.limit("10/minute")
async def analyze_batch(request: Request, batch_request: BatchTextRequest, authorized: bool = Depends(verify_api_key)):
    """Batch text analysis - process up to 100 texts"""
    try:
        logger.info(f"[/analyze/batch] Processing {len(batch_request.texts)} texts")
        
        results = []
        cache_hits = 0
        cache_misses = 0
        
        request_params = {
            "compact": batch_request.compact
        }
        
        for text in batch_request.texts:
            cached = redis_cache.get_cached_analysis(text, request_params)
            if cached:
                results.append(cached)
                cache_hits += 1
            else:
                result = analyze_text_comprehensive(text=text, compact=batch_request.compact)
                redis_cache.cache_analysis_result(text, request_params, result)
                results.append(result)
                cache_misses += 1
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "total_texts": len(batch_request.texts),
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


# ==================== ENDPOINT 5: POST /sentiment - SENTIMENT ONLY ====================

@app.post("/sentiment", tags=["Individual Features"])
async def analyze_sentiment(request: Request, text_request: SimpleTextRequest):
    """Sentiment analysis only"""
    try:
        logger.info(f"[/sentiment] Analyzing sentiment")
        
        lang_result = detect_language(text_request.text, detailed=True)
        raw_lang = lang_result['language']
        normalized_lang = normalize_language_code(raw_lang, keep_suffixes=False)
        
        # Check Redis cache
        cached_sentiment = redis_cache.get_cached_sentiment(text_request.text, normalized_lang)
        if cached_sentiment:
            logger.info(f"[CACHE HIT] /sentiment")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "text": text_request.text,
                    "language": normalized_lang,
                    "sentiment": cached_sentiment,
                    "cached": True
                }
            )
        
        cleaned_text = preprocess_text(text_request.text)
        
        from inference import predict_sentiment_async
        sentiment_result = await predict_sentiment_async(
            cleaned_text, 
            language=normalized_lang,
            executor=request.app.state.executor
        )
        
        # Cache result
        redis_cache.cache_sentiment(text_request.text, normalized_lang, sentiment_result)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "text": text_request.text,
                "language": normalized_lang,
                "sentiment": sentiment_result,
                "cached": False
            }
        )
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


# ==================== ENDPOINT 6: POST /translate - TRANSLATION ONLY ====================

@app.post("/translate", tags=["Individual Features"])
async def translate(request: TranslationRequest):
    """Translation only - with romanized detection"""
    try:
        logger.info(f"[/translate] Translating to {request.target_lang}")
        
        lang_result = detect_language(request.text, detailed=True)
        raw_lang = lang_result.get('language', 'unknown')
        normalized_lang = normalize_language_code(raw_lang, keep_suffixes=False)
        
        source_lang_for_cache = request.source_lang if request.source_lang != 'auto' else normalized_lang
        
        # Check Redis cache
        cached_translation = redis_cache.get_cached_translation(
            request.text, 
            source_lang_for_cache, 
            request.target_lang
        )
        if cached_translation:
            logger.info(f"[CACHE HIT] /translate")
            cached_translation["cached"] = True
            return JSONResponse(status_code=status.HTTP_200_OK, content=cached_translation)
        
        is_romanized = lang_result.get('is_romanized', False)
        
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
                "source_language": translation_result.get('detected_source_lang', normalized_lang),
                "target_language": request.target_lang,
                "success": True,
                "cached": False
            }
            
            if is_romanized and 'converted_to_devanagari' in translation_result:
                response_content['romanized_detected'] = True
                response_content['converted_to_devanagari'] = translation_result['converted_to_devanagari']
            
            # Cache the translation
            redis_cache.cache_translation(
                request.text,
                source_lang_for_cache,
                request.target_lang,
                response_content,
                ttl=86400
            )
            
            return JSONResponse(status_code=status.HTTP_200_OK, content=response_content)
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


# ==================== ENDPOINT 7: POST /convert - ROMANIZED TO NATIVE ====================

@app.post("/convert", tags=["Individual Features"])
async def convert_romanized_to_native(request: ConversionRequest):
    """Romanized to native script conversion"""
    try:
        logger.info(f"[/convert] Converting to {request.language}")
        
        from preprocessing import convert_romanized_to_native
        
        result = convert_romanized_to_native(
            text=request.text,
            lang_code=request.language,
            preserve_english=request.preserve_english
        )
        
        response = {
            "original_text": result['original_text'],
            "converted_text": result['converted_text'],
            "language": request.language,
            "conversion_method": result['conversion_method'],
            "statistics": result['statistics'],
            "token_details": result['token_details']
        }
        
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
        
    except Exception as e:
        logger.error(f"Error in conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )


# ==================== ENDPOINT 8: POST /feedback - ADAPTIVE LEARNING ====================

@app.post("/feedback", tags=["Adaptive Learning"])
async def submit_user_feedback(request: UserFeedbackRequest):
    """Submit user corrections for adaptive learning"""
    try:
        logger.info(f"[/feedback] Recording user feedback")
        
        correction_id = record_user_feedback(
            text=request.text,
            detected_language=request.detected_language,
            correct_language=request.correct_language,
            user_id=request.user_id,
            comments=request.comments
        )
        
        stats = get_learning_statistics()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Feedback recorded successfully",
                "correction_id": correction_id,
                "statistics": {
                    "total_corrections": stats.get('user_corrections_count', 0),
                    "cache_hit_rate": stats.get('cache_hit_rate', 0.0)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )


# ==================== ENDPOINT 9: GET /learning/stats - LEARNING STATISTICS ====================

@app.get("/learning/stats", tags=["Adaptive Learning"])
async def get_learning_stats():
    """Get adaptive learning system statistics"""
    try:
        logger.info(f"[/learning/stats] Retrieving statistics")
        
        stats = get_learning_statistics()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "statistics": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# ==================== ENDPOINT 10: GET /status - VERBOSE DIAGNOSTICS ====================

@app.get("/status", tags=["Health"])
async def system_status():
    """Verbose system diagnostics including ML model loading status"""
    try:
        logger.info(f"[/status] Retrieving verbose diagnostics")
        
        # Get Redis health
        redis_health = redis_cache.health_check()
        
        # Check ML model loading status
        ml_models_status = {}
        
        try:
            # Check GLotLID (Language Detection)
            from glotlid_wrapper import is_glotlid_loaded
            ml_models_status["glotlid"] = {
                "name": "GLotLID Language Detection",
                "status": "loaded" if is_glotlid_loaded() else "not_loaded",
                "purpose": "100+ language detection",
                "size": "~1.6GB"
            }
        except Exception as e:
            ml_models_status["glotlid"] = {
                "name": "GLotLID Language Detection",
                "status": "error",
                "error": str(e)
            }
        
        try:
            # Check Sentiment Models
            from inference import get_sentiment_model_status
            sentiment_status = get_sentiment_model_status()
            ml_models_status["sentiment"] = {
                "name": "Sentiment Analysis Models",
                "status": sentiment_status.get("status", "unknown"),
                "models": {
                    "xlm_roberta": sentiment_status.get("xlm_roberta", "not_loaded"),
                    "indic_bert": sentiment_status.get("indic_bert", "not_loaded")
                },
                "purpose": "Multilingual sentiment classification"
            }
        except Exception as e:
            ml_models_status["sentiment"] = {
                "name": "Sentiment Analysis Models",
                "status": "error",
                "error": str(e)
            }
        
        try:
            # Check Toxicity Model
            from inference import get_toxicity_model_status
            toxicity_status = get_toxicity_model_status()
            ml_models_status["toxicity"] = {
                "name": "Toxicity Detection Model",
                "status": toxicity_status.get("status", "unknown"),
                "model": "XLM-RoBERTa Toxicity Classifier",
                "purpose": "Toxic content detection (6 categories)"
            }
        except Exception as e:
            ml_models_status["toxicity"] = {
                "name": "Toxicity Detection Model",
                "status": "error",
                "error": str(e)
            }
        
        try:
            # Check Translation Model
            from translation import get_translation_model_status
            translation_status = get_translation_model_status()
            ml_models_status["translation"] = {
                "name": "Translation Model",
                "status": translation_status.get("status", "unknown"),
                "dictionaries_loaded": translation_status.get("dictionaries_loaded", 0),
                "purpose": "Multilingual translation"
            }
        except Exception as e:
            ml_models_status["translation"] = {
                "name": "Translation Model",
                "status": "error",
                "error": str(e)
            }
        
        # Calculate overall ML readiness
        loaded_models = sum(1 for m in ml_models_status.values() if m.get("status") == "loaded")
        total_models = len(ml_models_status)
        ml_readiness_percentage = (loaded_models / total_models * 100) if total_models > 0 else 0
        
        # Determine alerts
        alerts = []
        
        if redis_health.get("status") == "disabled":
            alerts.append({
                "level": "info",
                "service": "redis",
                "message": "Redis caching is disabled - using file cache only"
            })
        elif redis_health.get("status") != "healthy":
            alerts.append({
                "level": "warning",
                "service": "redis",
                "message": redis_health.get("message", "Redis connection issue")
            })
        
        if ml_readiness_percentage < 100:
            alerts.append({
                "level": "warning",
                "service": "ml_models",
                "message": f"Not all ML models loaded ({loaded_models}/{total_models})",
                "impact": "Some features may be slower on first use"
            })
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "api": {
                    "status": "operational",
                    "version": "2.0.0 - Streamlined",
                    "environment": settings.api_env,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "ml_models": {
                    "overall_status": "ready" if ml_readiness_percentage == 100 else "partial",
                    "loaded_models": loaded_models,
                    "total_models": total_models,
                    "readiness_percentage": round(ml_readiness_percentage, 2),
                    "models": ml_models_status
                },
                "redis": {
                    "active": redis_health.get("active", False),
                    "status": redis_health.get("status", "unknown"),
                    "provider": redis_health.get("provider"),
                    "message": redis_health.get("message", "")
                },
                "cache": {
                    "redis_enabled": settings.redis_enabled,
                    "file_cache_enabled": settings.cache_enabled,
                    "fallback_available": True
                },
                "features": {
                    "sentiment_analysis": True,
                    "toxicity_detection": True,
                    "translation": True,
                    "batch_processing": True,
                    "adaptive_learning": True
                },
                "alerts": alerts,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error in system status: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "api": {"status": "error", "version": "2.0.0"},
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
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


# ==================== MAIN ====================

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        workers=1 if settings.is_development else settings.workers
    )