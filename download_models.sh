#!/bin/bash
# Download models from HuggingFace at runtime
# This allows using hosting providers with storage limits

echo "Checking for models..."

MODEL_DIR="/app/models"
mkdir -p "$MODEL_DIR"

# Check if models already downloaded
if [ -f "$MODEL_DIR/.models_downloaded" ]; then
    echo "Models already present, skipping download..."
    exit 0
fi

echo "Downloading models from HuggingFace Hub..."
echo "This will take 5-10 minutes on first startup..."

# Download using transformers library
python3 << 'PYEOF'
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from pathlib import Path

models = {
    "glotlid": "cis-lmu/glotlid",
    "sentiment": "cardiffnlp/twitter-xlm-roberta-base-sentiment",
    "toxicity": "unitary/toxic-bert",
    "indic_sentiment": "ai4bharat/indic-bert"
}

for name, model_id in models.items():
    print(f"Downloading {name} ({model_id})...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSequenceClassification.from_pretrained(model_id)
        print(f"✓ {name} downloaded")
    except Exception as e:
        print(f"✗ Failed to download {name}: {e}")

print("All models downloaded!")
PYEOF

# Mark as complete
touch "$MODEL_DIR/.models_downloaded"
echo "Model download complete!"
