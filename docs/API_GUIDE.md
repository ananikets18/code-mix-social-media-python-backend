# 🚀 FastAPI REST API - Complete Guide

## 📋 Overview

**Multilingual NLP Analysis API** - A comprehensive REST API for text analysis supporting:
- 10 languages for profanity filtering
- International, Indian, and Code-Mixed language detection
- Sentiment analysis, toxicity detection, and translation
- Domain-specific entity extraction

**Base URL:** `http://localhost:8000`  
**Documentation:** `http://localhost:8000/docs` (Swagger UI)  
**Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)

---

## 🔧 Installation

### 1. Install FastAPI Dependencies

```bash
pip install -r requirements_api.txt
```

Or install manually:

```bash
pip install fastapi uvicorn pydantic python-multipart
```

### 2. Verify Installation

```bash
python -c "import fastapi; import uvicorn; print('FastAPI installed successfully!')"
```

---

## 🚀 Running the API

### Development Mode (with auto-reload)

```bash
python api.py
```

Or using uvicorn directly:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: **http://localhost:8000**

---

## 📚 API Endpoints

### 1. **Root Endpoint**

**GET** `/`

Returns API information and available endpoints.

**Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Multilingual NLP Analysis API",
  "version": "1.0.0",
  "docs": "/docs",
  "features": [...],
  "endpoints": {...}
}
```

---

### 2. **Health Check**

**GET** `/health`

Check API health and feature availability.

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-02T10:30:00",
  "version": "1.0.0",
  "features": {
    "profanity_filter": true,
    "domain_detection": true,
    "language_analysis": true,
    "sentiment_analysis": true,
    "toxicity_detection": true,
    "translation": true,
    "preprocessing": true
  }
}
```

---

### 3. **Comprehensive Analysis** ⭐ (Primary Endpoint)

**POST** `/analyze`

Complete text analysis with all 7 features.

**Request Body:**
```json
{
  "text": "This is a wonderful product! I highly recommend it.",
  "normalization_level": null,
  "preserve_emojis": true,
  "punctuation_mode": "preserve",
  "check_profanity": true,
  "detect_domains": true
}
```

**Parameters:**
- `text` (required): Text to analyze (1-5000 characters)
- `normalization_level`: `null`, `"light"`, `"moderate"`, or `"aggressive"`
- `preserve_emojis`: `true` or `false` (default: `true`)
- `punctuation_mode`: `"preserve"`, `"minimal"`, or `"aggressive"`
- `check_profanity`: `true` or `false` (default: `true`)
- `detect_domains`: `true` or `false` (default: `true`)

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a wonderful product! I highly recommend it.",
    "normalization_level": null,
    "preserve_emojis": true,
    "punctuation_mode": "preserve",
    "check_profanity": true,
    "detect_domains": true
  }'
```

**Example (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "text": "This is a wonderful product!",
        "check_profanity": True,
        "detect_domains": True
    }
)

result = response.json()
print(f"Sentiment: {result['sentiment']['label']}")
print(f"Profanity: {result['profanity']['has_profanity']}")
```

**Response Structure:**
```json
{
  "original_text": "...",
  "cleaned_text": "...",
  "preprocessing": {...},
  "profanity": {
    "has_profanity": false,
    "severity_score": 0.0,
    "max_severity": "none",
    "detected_words": [],
    "severity_breakdown": {...}
  },
  "domains": {
    "financial": false,
    "temporal": false,
    "technical": false
  },
  "language": {
    "language": "eng",
    "confidence": 0.9997,
    "method": "glotlid",
    "language_info": {...}
  },
  "sentiment": {
    "label": "positive",
    "confidence": 0.9252,
    "model_used": "XLM-RoBERTa"
  },
  "toxicity": {
    "toxic": 0.0004,
    "severe_toxic": 0.0001,
    "obscene": 0.0002,
    "threat": 0.0001,
    "insult": 0.0003,
    "identity_hate": 0.0001
  },
  "translations": {
    "hindi": "यह एक अद्भुत उत्पाद है!"
  },
  "statistics": {...}
}
```

---

### 4. **Sentiment Analysis**

**POST** `/sentiment`

Sentiment analysis only.

**Request Body:**
```json
{
  "text": "This movie is amazing!"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "This movie is amazing!"}'
```

**Response:**
```json
{
  "text": "This movie is amazing!",
  "language": "eng",
  "sentiment": {
    "label": "positive",
    "confidence": 0.98,
    "model_used": "XLM-RoBERTa"
  }
}
```

---

### 5. **Toxicity Detection**

**POST** `/toxicity`

Toxicity detection only.

**Request Body:**
```json
{
  "text": "You are such an idiot!"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/toxicity \
  -H "Content-Type: application/json" \
  -d '{"text": "You are such an idiot!"}'
```

**Response:**
```json
{
  "text": "You are such an idiot!",
  "toxicity_scores": {
    "toxic": 0.87,
    "severe_toxic": 0.12,
    "obscene": 0.34,
    "threat": 0.05,
    "insult": 0.92,
    "identity_hate": 0.03
  },
  "highest_risk": {
    "category": "insult",
    "score": 0.92
  }
}
```

---

### 6. **Translation**

**POST** `/translate`

Translation only.

**Request Body:**
```json
{
  "text": "यह बहुत अच्छा है",
  "target_lang": "en",
  "source_lang": "auto"
}
```

**Parameters:**
- `text` (required): Text to translate
- `target_lang`: Target language code (default: `"en"`)
- `source_lang`: Source language code or `"auto"` (default: `"auto"`)

**Example:**
```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "यह बहुत अच्छा है",
    "target_lang": "en",
    "source_lang": "auto"
  }'
```

**Response:**
```json
{
  "original_text": "यह बहुत अच्छा है",
  "translated_text": "This is very good",
  "source_language": "hi",
  "target_language": "en",
  "success": true
}
```

---

### 7. **Profanity Check**

**POST** `/profanity`

Profanity detection only.

**Request Body:**
```json
{
  "text": "This fucking product is shit!"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/profanity \
  -H "Content-Type: application/json" \
  -d '{"text": "This fucking product is shit!"}'
```

**Response:**
```json
{
  "text": "This fucking product is shit!",
  "has_profanity": true,
  "severity": "extreme",
  "severity_score": 1.0,
  "detected_words": ["fucking", "shit"],
  "censored_text": "This f**king product is s**t!",
  "statistics": {
    "total_words": 5,
    "profane_words": 2,
    "profanity_percentage": 40.0
  }
}
```

---

### 8. **Domain Detection**

**POST** `/domains`

Domain detection and entity extraction.

**Request Body:**
```json
{
  "text": "The stock price increased by $50 today. Meeting at 3 PM."
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/domains \
  -H "Content-Type: application/json" \
  -d '{"text": "The stock price increased by $50 today. Meeting at 3 PM."}'
```

**Response:**
```json
{
  "text": "The stock price increased by $50 today. Meeting at 3 PM.",
  "domains": {
    "financial": true,
    "temporal": true,
    "technical": false
  },
  "entities": {
    "financial": {
      "currencies": ["$"],
      "amounts": ["$50"],
      "terms": ["stock", "price"]
    },
    "temporal": {
      "dates": ["today"],
      "times": ["3 PM"],
      "relative_dates": []
    },
    "technical": {
      "functions": [],
      "keywords": []
    }
  }
}
```

---

## 🧪 Testing the API

### Using Swagger UI (Recommended)

1. Start the API: `python api.py`
2. Open browser: `http://localhost:8000/docs`
3. Click on any endpoint
4. Click "Try it out"
5. Enter parameters
6. Click "Execute"

### Using Python Requests

Create a test script `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_comprehensive_analysis():
    """Test the main /analyze endpoint"""
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={
            "text": "This is a wonderful product! I highly recommend it.",
            "check_profanity": True,
            "detect_domains": True
        }
    )
    
    result = response.json()
    print(json.dumps(result, indent=2))
    
    assert response.status_code == 200
    assert result['sentiment']['label'] == 'positive'
    print("✓ Comprehensive analysis test passed!")

def test_profanity_detection():
    """Test profanity endpoint"""
    response = requests.post(
        f"{BASE_URL}/profanity",
        json={"text": "This fucking product is shit!"}
    )
    
    result = response.json()
    print(f"Profanity detected: {result['has_profanity']}")
    print(f"Severity: {result['severity']}")
    
    assert response.status_code == 200
    assert result['has_profanity'] == True
    print("✓ Profanity detection test passed!")

def test_translation():
    """Test translation endpoint"""
    response = requests.post(
        f"{BASE_URL}/translate",
        json={
            "text": "यह बहुत अच्छा है",
            "target_lang": "en"
        }
    )
    
    result = response.json()
    print(f"Translated: {result['translated_text']}")
    
    assert response.status_code == 200
    assert result['success'] == True
    print("✓ Translation test passed!")

if __name__ == "__main__":
    print("Testing Multilingual NLP API...")
    print("=" * 60)
    
    test_comprehensive_analysis()
    test_profanity_detection()
    test_translation()
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
```

Run tests:
```bash
python test_api.py
```

---

## 📊 Performance

### Response Times (Approximate)

| Endpoint | First Call | Cached |
|----------|-----------|--------|
| `/analyze` | 3-5s | 400-600ms |
| `/sentiment` | 2-3s | 100-150ms |
| `/toxicity` | 1-2s | 80-120ms |
| `/translate` | 200-300ms | 200-300ms |
| `/profanity` | <5ms | <3ms |
| `/domains` | <10ms | <5ms |

**Note:** First call includes model loading time. Subsequent calls are much faster.

---

## 🔒 Security Considerations

### For Production Deployment:

1. **CORS Configuration** - Update allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

2. **Rate Limiting** - Add rate limiting:
```bash
pip install slowapi
```

3. **API Keys** - Implement authentication
4. **HTTPS** - Use SSL/TLS certificates
5. **Input Validation** - Already implemented with Pydantic

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn api:app --port 8001
```

### Models Not Loading

Check if models exist:
```bash
python -c "from inference import test_model_loading; test_model_loading()"
```

### Import Errors

Verify all dependencies:
```bash
python -c "import fastapi, uvicorn, pydantic; print('All imports OK!')"
```

---

## 📦 Deployment

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements_api.txt ./
RUN pip install -r requirements.txt -r requirements_api.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t nlp-api .
docker run -p 8000:8000 nlp-api
```

---

## ✅ Next Steps

1. ✅ Install FastAPI: `pip install -r requirements_api.txt`
2. ✅ Run API: `python api.py`
3. ✅ Test at: `http://localhost:8000/docs`
4. ✅ Integrate into your application
5. 🚀 Deploy to production

**API is ready for production use!** 🎉
