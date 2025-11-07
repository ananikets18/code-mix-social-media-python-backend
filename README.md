## 🤖 Code-Mix Research Project (Backend)

Hey there! 👋
Welcome to the **backend engine** of our Code-Mix Research Project — the system that makes sense of the wonderfully messy, multilingual world of social media text 🇮🇳🌍.

This FastAPI service powers the entire NLP workflow for our frontend — from **language detection** and **sentiment analysis** to **toxicity detection**, **translation**, and **romanized Indic text conversion** — all optimized for **speed**, **scalability**, and **multilingual accuracy**.

🔗 **Frontend Repo:** [Code-Mix Research Project (Frontend)](https://github.com/ananikets18/Code-Mix-Research-Project_Frontend)
🌐 **Live Demo (Frontend):** [https://code-mix-research-project.netlify.app](https://code-mix-research-project.netlify.app)

---

### 🧠 What We Built With

| **Component / Model**            | **Purpose / Description**                                  | **Implementation Details**                                                           |
| -------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **GLotLID (Language Detection)** | Detects 2000+ languages & code-mixed text                  | Used to identify base + mixed languages before routing text to sub-models            |
| **Sentiment Analysis Models**    | Multilingual sentiment classification                      | Uses `xlm-roberta` & `indic-bert` sub-models fine-tuned on Indic datasets            |
| **Toxicity Detection**           | Detects 6 toxicity categories (hate, insult, threat, etc.) | Model: `oleksiizirka/xlm-roberta-toxicity-classifier`                                |
| **Translation Library**          | Translation between languages                              | Google Translate API via `googletrans`                                               |
| **IndicNLP Library**             | Romanized → Native transliteration                         | Uses `indicnlp.transliterate.unicode_transliterate` (ITRANS method)                  |
| **Hybrid Conversion Logic**      | Enhances translation accuracy                              | Combines ITRANS + dictionary-based transliteration                                   |
| **Romanized Text Handling**      | Improves Indic text understanding                          | Converts text like “aaj traffic bahut hai” → “आज ट्रैफिक बहुत है” before translation |
| **Auto Language Detection**      | Intelligent source detection                               | Automatically detects language pair (source → target)                                |
| **Multi-Language Translation**   | Batch translations                                         | Translates to multiple targets simultaneously                                        |

---

### ⚙️ Under-the-Hood Techniques

We’ve tuned performance through smart backend optimization 👇

* ⚡ **Model Caching:**
  The app loads **lightweight versions** of models first (for warm startup) → then **upgrades to full model weights** in the background.
  This hybrid loading drastically reduces cold-start delays.

* 🧠 **Model Memory Persistence:**
  Loaded models are **kept in memory** across API requests — avoiding repeated reinitialization and reducing response times by up to **40–60%**.

* 🔁 **Redis Integration (Upstash):**
  A **Redis caching layer** stores frequently used analysis results and translation pairs.

  * Response caching at endpoint level (e.g., `/analyze`, `/translate`)
  * Smart TTL (time-to-live) per request type
  * Fallback to live model inference when cache misses
  * Deployed via **Upstash Redis** (serverless, globally distributed)

* 🚀 **Async API Handling:**
  Using FastAPI’s async I/O ensures model inference and translation run concurrently for batch inputs — optimizing latency under high load.

---

### 🧩 Run It Locally

```bash
git clone https://github.com/ananikets18/Code-Mix-Research-Project-Backend.git
cd Code-Mix-Research-Project-Backend

# Setup env
cp .env.example .env
# Fill details like MODEL_PATH, REDIS_URL, API_KEYS, etc.

pip install -r requirements_api.txt

# Run locally
python api.py
```

Once the server starts, it will be available at:

```
http://127.0.0.1:8000
```

✅ For production:

```bash
docker compose up --build -d
```

### 🚀 Key API Endpoints

| **Endpoint** | **Method** | **Purpose**                                                    |
| ------------ | ---------- | -------------------------------------------------------------- |
| `/analyze`   | POST       | Full pipeline: detect language → sentiment → toxicity → domain |
| `/sentiment` | POST       | Sentiment-only analysis                                        |
| `/translate` | POST       | Translation between languages                                  |
| `/convert`   | POST       | Romanized → Native script conversion                           |
| `/health`    | GET        | Health status of the API                                       |

#### Example Usage (via curl or Postman)

```bash
POST http://127.0.0.1:8000/analyze
Content-Type: application/json

{
  "text": "Yeh movie bahut awesome thi!"
}
```

#### Translation Example:

```bash
POST http://127.0.0.1:8000/translate
Content-Type: application/json

{
  "text": "Mujhe pizza chahiye",
  "target_lang": "en"
}
```

#### Health Check:

```bash
curl http://127.0.0.1:8000/health
```

---


### 🧪 Example Response

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

---

### ❤️ Why This Project Exists

India’s social media language is rarely pure — it’s *code-mixed*, expressive, and context-rich.
This backend was built to help researchers and developers work with such real-world, multilingual data — efficiently and accessibly.

Built with curiosity, focus, patience, and lots of testing 😅

— **Aniket S.**
