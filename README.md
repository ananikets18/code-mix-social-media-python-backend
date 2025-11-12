# 🤖 Code-Mix Research Project — Backend  
![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

Hey there! 👋  
Welcome to the **backend engine** of our Code-Mix Research Project — the system that makes sense of the wonderfully messy, multilingual world of social media text 🇮🇳🌍.

This **FastAPI** service powers the entire NLP workflow for our frontend — from **language detection** and **sentiment analysis** to **toxicity detection**, **translation**, and **romanized Indic text conversion** — all optimized for **speed**, **scalability**, and **multilingual accuracy**.

### Summary

This backend provides advanced NLP capabilities tailored for code-mixed and multilingual Indian social media text. It features fast, scalable APIs with intelligent language detection, sentiment and toxicity analysis, and enhanced translation handling including romanized to native script conversion.

### Key Features

- Detects 2000+ languages and code-mixed texts with GLotLID  
- Sentiment analysis fine-tuned on Indic datasets using `xlm-roberta` & `indic-bert`  
- Toxicity detection across 6 categories with an XLM-RoBERTa classifier  
- Batch and auto language pair translation using Google Translate API  
- Hybrid transliteration combining ITRANS and dictionary-based methods  
- Fast backend optimizations: model caching, async APIs, and Redis caching  
- Easy local setup with environment variables and Docker support  

***

## Table of Contents

- [Tech Stack & Models](#-tech-stack--models)  
- [Backend Optimizations](#backend-optimizations)
- [Run Locally](#-run-locally)  
- [API Endpoints](#-api-endpoints)  
- [Example Requests](#-example-requests)  
- [Example Response](#-example-response)  
- [Why This Project Exists](#why-this-project-exists)  
- [Contributing and Documentation](#-contributing-and-documentation)  

***

## 🧠 Tech Stack & Models

| Component / Model                  | Purpose / Description                                  | Implementation Details                                                           |
| --------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------- |
| **GLotLID (Language Detection)**   | Detects 2000+ languages & code-mixed text             | Identifies base + mixed languages before routing text to sub-models             |
| **Sentiment Analysis Models**      | Multilingual sentiment classification                 | `xlm-roberta` & `indic-bert` sub-models fine-tuned on Indic datasets            |
| **Toxicity Detection**             | Detects 6 toxicity categories (hate, insult, threat)  | `oleksiizirka/xlm-roberta-toxicity-classifier`                                   |
| **Translation Library**            | Translation between languages                         | Google Translate API via `googletrans`                                           |
| **IndicNLP Library**               | Romanized → Native transliteration                    | `indicnlp.transliterate.unicode_transliterate` (ITRANS method)                  |
| **Hybrid Conversion Logic**        | Enhances translation accuracy                         | Combines ITRANS + dictionary-based transliteration                                |
| **Romanized Text Handling**        | Improves Indic text understanding                     | Converts text like “aaj traffic bahut hai” → “आज ट्रैफिक बहुत है” before translation |
| **Auto Language Detection**        | Intelligent source detection                          | Detects language pair automatically (source → target)                            |
| **Multi-Language Translation**     | Batch translations                                    | Translates to multiple targets simultaneously                                    |

***

## ⚙️ Backend Optimizations

* ⚡ **Model Caching:** Loads lightweight models first, upgrades to full weights in background → reduces cold-start delays.  
* 🧠 **Model Memory Persistence:** Keeps models in memory across API requests → reduces response time by **40–60%**.  
* 🔁 **Redis Integration (Upstash):** Caches analysis results & translations globally.  
  - Endpoint-level caching (`/analyze`, `/translate`)  
  - Smart TTL per request type  
  - Fallback to live inference when cache misses  
* 🚀 **Async API Handling:** FastAPI async I/O ensures concurrent batch inference → low latency under load.

***

## 🧩 Run Locally

```bash
git clone https://github.com/ananikets18/Code-Mix-Research-Project-Backend.git
cd Code-Mix-Research-Project-Backend

# Setup environment variables
cp .env.example .env
# Fill details like MODEL_PATH, REDIS_URL, API_KEYS, etc.

# Install dependencies
pip install -r requirements_api.txt

# Run locally
python api.py
```

The server runs at:

```
http://127.0.0.1:8000
```

✅ For production:

```bash
docker compose up --build -d
```

***

## 🚀 API Endpoints

| Endpoint     | Method | Purpose                                                 |
| ------------ | ------ | ------------------------------------------------------- |
| `/analyze`   | POST   | Full pipeline: language → sentiment → toxicity → domain |
| `/sentiment` | POST   | Sentiment-only analysis                                 |
| `/translate` | POST   | Translation between languages                           |
| `/convert`   | POST   | Romanized → Native script conversion                    |
| `/health`    | GET    | API health status                                       |

***

## 📝 Example Requests

**Analyze:**

```bash
POST http://127.0.0.1:8000/analyze
Content-Type: application/json

{
  "text": "Yeh movie bahut awesome thi!"
}
```

**Translate:**

```bash
POST http://127.0.0.1:8000/translate
Content-Type: application/json

{
  "text": "Mujhe pizza chahiye",
  "target_lang": "en"
}
```

**Health Check:**

```bash
curl http://127.0.0.1:8000/health
```

***

## 🧪 Example Response

```json
{
  "language": "hi-en",
  "sentiment": "positive",
  "toxicity": {
    "is_toxic": false,
    "categories": []
  },
  "translation": "This movie was very awesome!",
  "romanized_conversion": "यह मूवी बहुत ऑसम थी!"
}
```

***

## ❤️ Why This Project Exists

India’s social media language is rarely pure — it’s *code-mixed*, expressive, and context-rich.  
This backend helps researchers and developers work with real-world, multilingual data efficiently and accessibly.

Built with curiosity, focus, patience, and lots of testing 😅

***

## 🤝 Contributing and Documentation

Contributions to improve the backend are welcome! Please follow these guidelines:  

- Fork the repository and create your feature branch from `main`.  
- Ensure any install or build dependencies are removed before the end of the layer when doing a build.  
- Update the README with details of changes to the interface, including new environment variables, exposed endpoints, etc.  
- Write clear, concise commit messages and PR descriptions.  
- Run tests and ensure API responses are as expected before submitting a PR.  
