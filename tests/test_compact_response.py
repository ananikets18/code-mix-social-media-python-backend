"""Test compact vs verbose API responses"""

import json
import sys

# Mock the analysis to show response difference
def create_verbose_response():
    """Full verbose response (current)"""
    return {
        "original_text": "Mi aaj khup khush ahe!",
        "cleaned_text": "mi aaj khup khush ahe!",
        "preprocessing": {
            "normalization_level": None,
            "preserve_emojis": True,
            "punctuation_mode": "preserve"
        },
        "profanity": {
            "has_profanity": False,
            "severity_score": 0,
            "max_severity": None,
            "detected_words": [],
            "word_count": 0,
            "severity_breakdown": {
                "extreme": [],
                "moderate": [],
                "mild": []
            }
        },
        "domains": {
            "financial": False,
            "temporal": False,
            "technical": False
        },
        "language": {
            "language": "mar",
            "confidence": 0.85,
            "method": "romanized_indic_early_detection",
            "text_length": 22,
            "is_short_text": False,
            "composition": {
                "indic_percentage": 0.0,
                "latin_percentage": 77.27,
                "numeric_percentage": 0.0,
                "punctuation_percentage": 4.55,
                "other_percentage": 18.18,
                "script_counts": {},
                "is_code_mixed": False,
                "dominant_script": "latin"
            },
            "script_analysis": {
                "detected_script": None,
                "script_counts": {}
            },
            "glotlid_analysis": {
                "detected_language": None,
                "confidence": 0.0,
                "is_code_mixed": False,
                "note": "Skipped GlotLID due to early romanized detection"
            },
            "language_info": {
                "is_indian_language": True,
                "is_international_language": False,
                "is_code_mixed": False,
                "is_romanized": True,
                "language_name": "Marathi"
            },
            "detection_config": {
                "min_text_length": 3,
                "glotlid_threshold": 0.5,
                "high_confidence_threshold": 0.8,
                "medium_confidence_threshold": 0.6,
                "low_confidence_threshold": 0.4,
                "strong_script_threshold": 50,
                "code_mixed_min_threshold": 20,
                "code_mixed_max_threshold": 50,
                "minor_script_min_threshold": 5,
                "minor_script_max_threshold": 20,
                "latin_dominance_threshold": 70,
                "short_text_threshold": 10,
                "use_indic_nlp_enhanced": True
            }
        },
        "sentiment": {
            "label": "positive",
            "confidence": 0.46879518032073975,
            "model_used": "XLM-RoBERTa",
            "all_probabilities": [[0.23945440351963043, 0.29175040125846863, 0.46879518032073975]]
        },
        "toxicity": {
            "toxic": 0.019121166318655014,
            "severe_toxic": 6.107195076765493e-05,
            "obscene": 0.0017707792576402426,
            "threat": 0.00010370507516199723,
            "insult": 0.001417171093635261,
            "identity_hate": 0.00024882034631446004
        },
        "translations": {
            "english": "I am very happy today!",
            "conversion_applied": True,
            "converted_to_devanagari": "मी आज खूप खुश आहे!"
        },
        "statistics": {
            "text_length": 22,
            "word_count": 5,
            "language_detection": {},
            "preprocessing_preview": {
                "original": "Mi aaj khup khush ahe!",
                "cleaned": "mi aaj khup khush ahe!"
            }
        }
    }


def create_compact_response():
    """Compact/simplified response (NEW)"""
    return {
        "text": "Mi aaj khup khush ahe!",
        "language": {
            "code": "mar",
            "name": "Marathi",
            "confidence": 0.85,
            "is_romanized": True,
            "is_code_mixed": False
        },
        "sentiment": {
            "label": "positive",
            "score": 0.47
        },
        "profanity": {
            "detected": False,
            "severity": None
        },
        "translation": "I am very happy today!",
        "toxicity_score": 0.019,
        "romanized_conversion": {
            "applied": True,
            "native_script": "मी आज खूप खुश आहे!"
        }
    }


def compare_responses():
    """Compare verbose vs compact responses"""
    
    verbose = create_verbose_response()
    compact = create_compact_response()
    
    verbose_json = json.dumps(verbose, indent=2)
    compact_json = json.dumps(compact, indent=2)
    
    verbose_size = len(verbose_json)
    compact_size = len(compact_json)
    reduction = ((verbose_size - compact_size) / verbose_size) * 100
    
    print("=" * 80)
    print("RESPONSE SIZE COMPARISON")
    print("=" * 80)
    
    print(f"\n📊 Size Statistics:")
    print(f"  Verbose Response:  {verbose_size:,} bytes")
    print(f"  Compact Response:  {compact_size:,} bytes")
    print(f"  Size Reduction:    {reduction:.1f}%")
    print(f"  Bytes Saved:       {verbose_size - compact_size:,} bytes")
    
    print(f"\n🔢 Field Count:")
    
    def count_fields(obj, depth=0):
        count = 0
        if isinstance(obj, dict):
            count += len(obj)
            for v in obj.values():
                count += count_fields(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                count += count_fields(item, depth + 1)
        return count
    
    verbose_fields = count_fields(verbose)
    compact_fields = count_fields(compact)
    
    print(f"  Verbose Fields:    {verbose_fields}")
    print(f"  Compact Fields:    {compact_fields}")
    print(f"  Field Reduction:   {((verbose_fields - compact_fields) / verbose_fields) * 100:.1f}%")
    
    print(f"\n" + "=" * 80)
    print("VERBOSE RESPONSE (compact=false)")
    print("=" * 80)
    print(verbose_json[:500] + "\n  ... (truncated) ...")
    
    print(f"\n" + "=" * 80)
    print("COMPACT RESPONSE (compact=true)")
    print("=" * 80)
    print(compact_json)
    
    print(f"\n" + "=" * 80)
    print("USAGE IN POSTMAN")
    print("=" * 80)
    
    print("""
🔸 For COMPACT response (recommended for production):
POST http://localhost:8000/analyze
{
  "text": "Mi aaj khup khush ahe!",
  "compact": true
}

🔸 For VERBOSE response (debugging/development):
POST http://localhost:8000/analyze
{
  "text": "Mi aaj khup khush ahe!",
  "compact": false
}

🔸 Default (if compact not specified): VERBOSE
""")
    
    print("=" * 80)
    print("✅ Summary")
    print("=" * 80)
    print(f"""
• Compact response is {reduction:.0f}% smaller
• Contains all essential information
• Perfect for mobile apps, dashboards, and production use
• Verbose response still available for debugging
• Set "compact": true in request body to enable
""")


if __name__ == "__main__":
    compare_responses()
