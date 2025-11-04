#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLotLID Language Detection Wrapper
Uses the downloaded cis-lmu/glotlid model for advanced language detection
"""

import fasttext
import numpy as np
import os
from logger_config import get_logger

logger = get_logger(__name__, level="INFO")

class GLotLID:
    """Wrapper class for GLotLID language identification"""
    
    def __init__(self, model_path="cis-lmuglotlid/model.bin"):
        """
        Initialize GLotLID model
        
        Args:
            model_path: Path to the GLotLID model.bin file
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"GLotLID model not found at: {model_path}")
        
        # Load FastText model
        self.model = fasttext.load_model(model_path)
        logger.info(f"✅ GLotLID model loaded from: {model_path}")
        
        # Adaptive confidence thresholds based on text length
        self.threshold_config = {
            'very_short': {'min_chars': 0, 'max_chars': 10, 'threshold': 0.40},
            'short': {'min_chars': 10, 'max_chars': 50, 'threshold': 0.55},
            'medium': {'min_chars': 50, 'max_chars': 200, 'threshold': 0.70},
            'long': {'min_chars': 200, 'max_chars': 500, 'threshold': 0.80},
            'very_long': {'min_chars': 500, 'max_chars': float('inf'), 'threshold': 0.85}
        }
    
    def _get_adaptive_threshold(self, text):
        """
        Get adaptive confidence threshold based on text length
        
        Shorter texts are harder to classify accurately, so lower thresholds.
        Longer texts provide more context, so higher thresholds.
        
        Args:
            text: Input text
            
        Returns:
            float: Confidence threshold for this text
        """
        text_length = len(text.strip())
        
        for category, config in self.threshold_config.items():
            if config['min_chars'] <= text_length < config['max_chars']:
                logger.debug(f"Text length: {text_length} chars, Category: {category}, Threshold: {config['threshold']}")
                return config['threshold']
        
        # Fallback
        return 0.70
    
    def _normalize_text(self, text):
        """Normalize input text"""
        import re
        replacement_map = {ord(c): ' ' for c in '\n'}
        text = text.translate(replacement_map)
        return re.sub(r'\s+', ' ', text).strip()
    
    def predict(self, text, k=1):
        """
        Predict language(s) for given text
        
        Args:
            text: Input text to identify language
            k: Number of top predictions to return
            
        Returns:
            tuple: (labels, probabilities)
            - labels: tuple of language codes (e.g., '__label__eng_Latn')
            - probabilities: numpy array of confidence scores
        """
        normalized_text = self._normalize_text(text)
        try:
            labels, probs = self.model.predict(normalized_text, k=k)
        except ValueError:
            # Handle NumPy 2.x compatibility issue
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Use threshold parameter instead
                labels, probs = self.model.predict(normalized_text, k=k, threshold=0.0)
        
        # Ensure probs is a numpy array
        if not isinstance(probs, np.ndarray):
            probs = np.asarray(probs)
        
        return labels, probs
    
    def predict_language(self, text, k=1, threshold=None):
        """
        Predict language with detailed information
        
        Args:
            text: Input text
            k: Number of predictions
            threshold: Minimum confidence for code-mixed detection (auto-calculated if None)
            
        Returns:
            dict: {
                'primary_language': ISO 639-3 code (e.g., 'eng'),
                'script': Script code (e.g., 'Latn'),
                'confidence': float (0-1),
                'is_code_mixed': bool,
                'all_predictions': list of (lang, script, confidence) tuples,
                'adaptive_threshold': float (threshold used),
                'text_length_category': str
            }
        """
        # Use adaptive threshold if not provided
        if threshold is None:
            threshold = self._get_adaptive_threshold(text)
        
        labels, probs = self.predict(text, k=min(k, 5))
        
        # Determine text length category for reporting
        text_length = len(text.strip())
        category = 'unknown'
        for cat, config in self.threshold_config.items():
            if config['min_chars'] <= text_length < config['max_chars']:
                category = cat
                break
        
        # Parse first prediction
        primary_label = labels[0].replace('__label__', '')
        parts = primary_label.split('_')
        
        if len(parts) >= 2:
            primary_lang = parts[0]
            primary_script = parts[1]
        else:
            primary_lang = primary_label
            primary_script = 'Unknown'
        
        primary_confidence = float(probs[0])
        
        # IMPROVED: Code-mixed detection logic
        is_code_mixed = False
        if len(labels) > 1:
            # Check if secondary language has significant probability (>20%)
            secondary_confidence = float(probs[1])
            if secondary_confidence > 0.20:
                is_code_mixed = True
            # OR if primary confidence is low (<70%) with multiple detections
            elif primary_confidence < 0.70:
                is_code_mixed = True
        
        # Parse all predictions
        all_preds = []
        for label, prob in zip(labels, probs):
            clean_label = label.replace('__label__', '')
            parts = clean_label.split('_')
            lang = parts[0] if len(parts) >= 1 else clean_label
            script = parts[1] if len(parts) >= 2 else 'Unknown'
            all_preds.append((lang, script, float(prob)))
        
        return {
            'primary_language': primary_lang,
            'script': primary_script,
            'confidence': primary_confidence,
            'is_code_mixed': is_code_mixed,
            'all_predictions': all_preds,
            'adaptive_threshold': threshold,
            'text_length_category': category
        }
    
    def get_language_name(self, iso_code):
        """
        Get human-readable language name from ISO 639-3 code
        
        Args:
            iso_code: 3-letter ISO language code
            
        Returns:
            str: Language name
        """
        # Comprehensive language mappings (50+ languages)
        lang_names = {
            # Indian Languages
            'hin': 'Hindi',
            'ben': 'Bengali',
            'tel': 'Telugu',
            'mar': 'Marathi',
            'tam': 'Tamil',
            'urd': 'Urdu',
            'guj': 'Gujarati',
            'kan': 'Kannada',
            'mal': 'Malayalam',
            'pan': 'Punjabi',
            'ori': 'Odia',
            'asm': 'Assamese',
            'mai': 'Maithili',
            'san': 'Sanskrit',
            'nep': 'Nepali',
            'sin': 'Sinhala',
            
            # International Languages
            'eng': 'English',
            'spa': 'Spanish',
            'fra': 'French',
            'deu': 'German',
            'por': 'Portuguese',
            'rus': 'Russian',
            'jpn': 'Japanese',
            'kor': 'Korean',
            'arb': 'Arabic',
            'zho': 'Chinese',
            'cmn': 'Mandarin Chinese',
            'yue': 'Cantonese',
            'ita': 'Italian',
            'nld': 'Dutch',
            'pol': 'Polish',
            'tur': 'Turkish',
            'vie': 'Vietnamese',
            'tha': 'Thai',
            'ind': 'Indonesian',
            'msa': 'Malay',
            'fas': 'Persian',
            'heb': 'Hebrew',
            'swa': 'Swahili',
            'ell': 'Greek',
            
            # Code-mixed indicators
            'mixed': 'Code-Mixed',
            'unknown': 'Unknown'
        }
        return lang_names.get(iso_code.lower(), iso_code.upper())
    
    def predict_with_romanized_boost(self, text, k=1, threshold=None):
        """
        Enhanced prediction with romanized Indian language detection boost
        
        Uses ensemble approach:
        1. GLotLID prediction
        2. Romanized pattern detection (if text is Latin script)
        3. Combines both for better Indian language detection
        
        Args:
            text: Input text
            k: Number of predictions
            threshold: Confidence threshold (auto if None)
            
        Returns:
            dict: Enhanced prediction with romanized boost info
        """
        # Get standard GLotLID prediction
        glotlid_result = self.predict_language(text, k=k, threshold=threshold)
        
        # Check if text is primarily Latin script (potential romanized)
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        
        if total_chars > 0:
            latin_percentage = (latin_chars / total_chars) * 100
        else:
            latin_percentage = 0
        
        # Romanized pattern detection for Indian languages
        romanized_hints = {
            'hindi': ['hai', 'hain', 'hoon', 'bahut', 'kya', 'main', 'mein', 'yaar', 'bhai'],
            'marathi': ['aahe', 'ahe', 'khup', 'mi', 'tu', 'kay', 'kashala', 'la', 'var'],
            'bengali': ['ache', 'ami', 'tumi', 'khub', 'bhalo', 'keno', 'kothay'],
            'tamil': ['irukku', 'naan', 'nee', 'romba', 'enna', 'epdi', 'inniki'],
            'telugu': ['undi', 'nenu', 'nuvvu', 'chala', 'enti', 'ela', 'indu'],
            'punjabi': ['hai', 'main', 'tu', 'bahut', 'ki', 'kive', 'hun']
        }
        
        romanized_lang = None
        romanized_confidence = 0.0
        
        # Only check if text is mostly Latin script
        if latin_percentage > 70:
            text_lower = text.lower()
            words = text_lower.split()
            
            for lang, patterns in romanized_hints.items():
                matches = sum(1 for pattern in patterns if pattern in text_lower)
                if matches > 0:
                    # Calculate confidence based on pattern matches
                    match_confidence = min(matches / len(patterns), 1.0) * 0.85
                    if match_confidence > romanized_confidence:
                        romanized_lang = lang
                        romanized_confidence = match_confidence
        
        # Ensemble decision
        final_language = glotlid_result['primary_language']
        final_confidence = glotlid_result['confidence']
        detection_method = 'glotlid'
        
        # If romanized detection found Indian language with good confidence
        if romanized_lang and romanized_confidence > 0.30:
            # Map romanized lang to ISO code
            lang_to_iso = {
                'hindi': 'hin', 'marathi': 'mar', 'bengali': 'ben',
                'tamil': 'tam', 'telugu': 'tel', 'punjabi': 'pan'
            }
            romanized_iso = lang_to_iso.get(romanized_lang)
            
            # If GLotLID confidence is low, trust romanized detection
            if glotlid_result['confidence'] < 0.60 and romanized_iso:
                final_language = romanized_iso
                final_confidence = romanized_confidence
                detection_method = 'romanized_ensemble'
                logger.info(f"🔄 Romanized boost: {romanized_lang} ({romanized_confidence:.2f}) overrides GLotLID")
        
        return {
            **glotlid_result,
            'final_language': final_language,
            'final_confidence': final_confidence,
            'detection_method': detection_method,
            'romanized_detection': {
                'detected': romanized_lang is not None,
                'language': romanized_lang,
                'confidence': romanized_confidence,
                'latin_percentage': latin_percentage
            }
        }
    
    def visualize_predictions(self, text, k=5):
        """
        Visualize language probability distribution as text-based chart
        
        Args:
            text: Input text
            k: Number of top predictions to show
            
        Returns:
            str: Text-based visualization of predictions
        """
        result = self.predict_language(text, k=k)
        
        # Build visualization
        output = []
        output.append("=" * 70)
        output.append("LANGUAGE DETECTION PROBABILITY DISTRIBUTION")
        output.append("=" * 70)
        output.append(f"\n📝 Text: {text[:60]}{'...' if len(text) > 60 else ''}")
        output.append(f"   Length: {len(text)} chars ({result['text_length_category']})")
        output.append(f"   Threshold: {result['adaptive_threshold']:.2f}")
        output.append("")
        output.append("Top Predictions:")
        output.append("-" * 70)
        
        max_bar_width = 50
        for i, (lang, script, conf) in enumerate(result['all_predictions'], 1):
            # Create bar chart
            bar_length = int(conf * max_bar_width)
            bar = "█" * bar_length + "░" * (max_bar_width - bar_length)
            
            # Get language name
            lang_name = self.get_language_name(lang)
            
            # Indicator for primary language
            indicator = "👉" if i == 1 else "  "
            
            output.append(f"{indicator} {i}. {lang_name:20} ({lang}_{script})")
            output.append(f"    {bar} {conf:.2%}")
            output.append("")
        
        # Show code-mixed status
        if result['is_code_mixed']:
            output.append("⚠️  Code-Mixed Language Detected!")
        
        output.append("=" * 70)
        
        return "\n".join(output)
    
    def ensemble_predict(self, text, romanized_lang=None, romanized_confidence=0.0, 
                        glotlid_high_conf_threshold=0.90, k=3):
        """
        FIX #8: Advanced ensemble prediction combining GLotLID and romanized detection
        
        Uses weighted confidence scoring to make intelligent decisions:
        - Prefer GLotLID when confidence is very high (>0.9)
        - Leverage romanized detection for medium/low GLotLID confidence
        - Combine insights for hybrid social-media style texts
        
        Args:
            text: Input text to analyze
            romanized_lang: Language detected by romanized detection (optional)
            romanized_confidence: Confidence of romanized detection (0.0-1.0)
            glotlid_high_conf_threshold: Threshold for GLotLID preference (default: 0.90)
            k: Number of top predictions to consider
            
        Returns:
            dict: {
                'final_language': str (ISO code),
                'final_confidence': float (0-1),
                'detection_method': str (glotlid_preferred/romanized_preferred/ensemble_weighted),
                'ensemble_scores': dict (breakdown of scoring),
                'glotlid_prediction': dict,
                'romanized_prediction': dict,
                'decision_explanation': str
            }
        """
        # Get GLotLID prediction
        glotlid_result = self.predict_language(text, k=k)
        glotlid_lang = glotlid_result['primary_language']
        glotlid_conf = glotlid_result['confidence']
        
        # Analyze text composition
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        latin_percentage = (latin_chars / total_chars * 100) if total_chars > 0 else 0
        
        # Decision framework
        final_language = glotlid_lang
        final_confidence = glotlid_conf
        detection_method = 'glotlid_default'
        decision_explanation = ''
        
        ensemble_scores = {
            'glotlid_score': glotlid_conf,
            'romanized_score': romanized_confidence,
            'latin_percentage': latin_percentage,
            'combined_score': 0.0
        }
        
        # DECISION LOGIC
        # Case 1: GLotLID very high confidence (>0.9) - Trust it completely
        if glotlid_conf > glotlid_high_conf_threshold:
            final_language = glotlid_lang
            final_confidence = glotlid_conf
            detection_method = 'glotlid_preferred_high_confidence'
            decision_explanation = (f"GLotLID confidence ({glotlid_conf:.3f}) exceeds threshold "
                                  f"({glotlid_high_conf_threshold}). Trusting GLotLID completely.")
            ensemble_scores['combined_score'] = glotlid_conf
            
            logger.info(f"[Ensemble] GLotLID HIGH CONFIDENCE: {glotlid_lang} ({glotlid_conf:.3f}) > {glotlid_high_conf_threshold}")
        
        # Case 2: Romanized detection available with good confidence
        elif romanized_lang and romanized_confidence > 0.0:
            # Check if text is mostly Latin (potential romanized)
            if latin_percentage > 60:
                # Weighted ensemble approach
                # Weight distribution: GLotLID=0.6, Romanized=0.4 (adjustable based on text)
                
                # Adjust weights based on Latin percentage
                # More Latin = more weight to romanized
                if latin_percentage > 80:
                    glotlid_weight = 0.5
                    romanized_weight = 0.5
                elif latin_percentage > 70:
                    glotlid_weight = 0.55
                    romanized_weight = 0.45
                else:
                    glotlid_weight = 0.6
                    romanized_weight = 0.4
                
                # Calculate combined confidence score
                combined_score = (glotlid_conf * glotlid_weight) + (romanized_confidence * romanized_weight)
                ensemble_scores['combined_score'] = combined_score
                ensemble_scores['glotlid_weight'] = glotlid_weight
                ensemble_scores['romanized_weight'] = romanized_weight
                
                # Decision: Choose method with highest individual confidence if gap is large
                conf_gap = abs(glotlid_conf - romanized_confidence)
                
                if conf_gap > 0.30:
                    # Large confidence gap - trust the more confident method
                    if glotlid_conf > romanized_confidence:
                        final_language = glotlid_lang
                        final_confidence = glotlid_conf
                        detection_method = 'glotlid_preferred_conf_gap'
                        decision_explanation = (f"GLotLID confidence ({glotlid_conf:.3f}) significantly higher "
                                              f"than romanized ({romanized_confidence:.3f}). Gap: {conf_gap:.3f}")
                        logger.info(f"[Ensemble] GLotLID preferred (conf gap): {glotlid_lang} ({glotlid_conf:.3f})")
                    else:
                        final_language = romanized_lang
                        final_confidence = romanized_confidence
                        detection_method = 'romanized_preferred_conf_gap'
                        decision_explanation = (f"Romanized confidence ({romanized_confidence:.3f}) significantly higher "
                                              f"than GLotLID ({glotlid_conf:.3f}). Gap: {conf_gap:.3f}")
                        logger.info(f"[Ensemble] Romanized preferred (conf gap): {romanized_lang} ({romanized_confidence:.3f})")
                else:
                    # Small confidence gap - use weighted ensemble
                    # Check if both methods agree on language family
                    indian_langs = ['hin', 'mar', 'ben', 'tam', 'tel', 'kan', 'mal', 'guj', 'pan', 'ori']
                    glotlid_is_indian = glotlid_lang in indian_langs
                    romanized_is_indian = romanized_lang in indian_langs
                    
                    if romanized_confidence > glotlid_conf and romanized_is_indian:
                        # Romanized has higher confidence for Indian language
                        final_language = romanized_lang
                        final_confidence = combined_score
                        detection_method = 'ensemble_weighted_romanized'
                        decision_explanation = (f"Weighted ensemble (Latin {latin_percentage:.1f}%): "
                                              f"Romanized {romanized_lang} ({romanized_confidence:.3f}) > "
                                              f"GLotLID {glotlid_lang} ({glotlid_conf:.3f}). "
                                              f"Combined score: {combined_score:.3f}")
                        logger.info(f"[Ensemble] Weighted ROMANIZED: {romanized_lang} (combined: {combined_score:.3f})")
                    elif glotlid_is_indian and not romanized_is_indian:
                        # GLotLID detected Indian lang, romanized didn't - trust GLotLID
                        final_language = glotlid_lang
                        final_confidence = combined_score
                        detection_method = 'ensemble_weighted_glotlid'
                        decision_explanation = (f"Weighted ensemble: GLotLID detected Indian language {glotlid_lang}, "
                                              f"romanized detected {romanized_lang}. Using GLotLID. "
                                              f"Combined score: {combined_score:.3f}")
                        logger.info(f"[Ensemble] Weighted GLOTLID (Indian): {glotlid_lang} (combined: {combined_score:.3f})")
                    else:
                        # Use higher confidence method with combined score
                        if glotlid_conf >= romanized_confidence:
                            final_language = glotlid_lang
                            final_confidence = combined_score
                            detection_method = 'ensemble_weighted_glotlid'
                            decision_explanation = (f"Weighted ensemble (Latin {latin_percentage:.1f}%): "
                                                  f"GLotLID {glotlid_lang} ({glotlid_conf:.3f}) >= "
                                                  f"Romanized {romanized_lang} ({romanized_confidence:.3f}). "
                                                  f"Combined score: {combined_score:.3f}")
                            logger.info(f"[Ensemble] Weighted GLOTLID: {glotlid_lang} (combined: {combined_score:.3f})")
                        else:
                            final_language = romanized_lang
                            final_confidence = combined_score
                            detection_method = 'ensemble_weighted_romanized'
                            decision_explanation = (f"Weighted ensemble (Latin {latin_percentage:.1f}%): "
                                                  f"Romanized {romanized_lang} ({romanized_confidence:.3f}) > "
                                                  f"GLotLID {glotlid_lang} ({glotlid_conf:.3f}). "
                                                  f"Combined score: {combined_score:.3f}")
                            logger.info(f"[Ensemble] Weighted ROMANIZED: {romanized_lang} (combined: {combined_score:.3f})")
            else:
                # Not much Latin text - trust GLotLID
                final_language = glotlid_lang
                final_confidence = glotlid_conf
                detection_method = 'glotlid_preferred_low_latin'
                decision_explanation = (f"Low Latin percentage ({latin_percentage:.1f}%). "
                                      f"Trusting GLotLID {glotlid_lang} ({glotlid_conf:.3f})")
                ensemble_scores['combined_score'] = glotlid_conf
                logger.info(f"[Ensemble] GLotLID (low Latin): {glotlid_lang} ({glotlid_conf:.3f})")
        
        # Case 3: No romanized detection - use GLotLID
        else:
            final_language = glotlid_lang
            final_confidence = glotlid_conf
            detection_method = 'glotlid_only'
            decision_explanation = f"No romanized detection available. Using GLotLID {glotlid_lang} ({glotlid_conf:.3f})"
            ensemble_scores['combined_score'] = glotlid_conf
            logger.info(f"[Ensemble] GLotLID only: {glotlid_lang} ({glotlid_conf:.3f})")
        
        return {
            'final_language': final_language,
            'final_confidence': final_confidence,
            'detection_method': detection_method,
            'ensemble_scores': ensemble_scores,
            'glotlid_prediction': {
                'language': glotlid_lang,
                'confidence': glotlid_conf,
                'all_predictions': glotlid_result['all_predictions']
            },
            'romanized_prediction': {
                'language': romanized_lang,
                'confidence': romanized_confidence
            },
            'decision_explanation': decision_explanation,
            'is_code_mixed': glotlid_result['is_code_mixed']
        }
    
    def get_prediction_summary(self, text, include_visualization=False):
        """
        Get comprehensive prediction summary
        
        Args:
            text: Input text
            include_visualization: Include text-based chart
            
        Returns:
            dict: Complete analysis with optional visualization
        """
        # Get ensemble prediction
        result = self.predict_with_romanized_boost(text, k=5)
        
        summary = {
            'text': text,
            'text_length': len(text),
            'final_language': result['final_language'],
            'final_language_name': self.get_language_name(result['final_language']),
            'confidence': result['final_confidence'],
            'detection_method': result['detection_method'],
            'is_code_mixed': result['is_code_mixed'],
            'adaptive_threshold': result['adaptive_threshold'],
            'text_category': result['text_length_category'],
            'top_3_predictions': [
                {
                    'language': lang,
                    'language_name': self.get_language_name(lang),
                    'script': script,
                    'confidence': conf
                }
                for lang, script, conf in result['all_predictions'][:3]
            ]
        }
        
        # Add romanized info if detected
        if result['romanized_detection']['detected']:
            summary['romanized_info'] = result['romanized_detection']
        
        # Add visualization if requested
        if include_visualization:
            summary['visualization'] = self.visualize_predictions(text, k=5)
        
        return summary


# Test function
def test_glotlid():
    """Test GLotLID with various text samples - ENHANCED VERSION"""
    print("\n" + "=" * 80)
    print("🧪 TESTING ENHANCED GLOTLID MODEL")
    print("=" * 80)
    
    try:
        # Initialize model
        lid = GLotLID()
        
        # Test cases with varying lengths
        test_texts = [
            # Very short text
            ("Hi", "Very Short English"),
            
            # Short text
            ("Hello world!", "Short English"),
            
            # Romanized Hindi - short
            ("mai khush hoon", "Short Romanized Hindi"),
            
            # Medium length - Romanized Marathi
            ("Mi aaj office jat ahe. Traffic khup heavy aahe!", "Medium Romanized Marathi"),
            
            # Code-mixed
            ("Yeh bahut achha hai, very good! Must try karo yaar.", "Code-mixed Hinglish"),
            
            # Long text - English
            ("This is a wonderful product. I highly recommend it to everyone. The quality is excellent and the service is outstanding. I will definitely buy again in the future.", "Long English"),
            
            # Romanized Bengali
            ("ami aaj khub bhalo achi. Tumi kemon acho?", "Romanized Bengali"),
        ]
        
        print("\n" + "=" * 80)
        print("TEST 1: Adaptive Threshold Tuning")
        print("=" * 80)
        
        for text, description in test_texts:
            result = lid.predict_language(text, k=3)
            
            print(f"\n📝 Text: '{text}'")
            print(f"   Description: {description}")
            print(f"   ├─ Length: {len(text)} chars ({result['text_length_category']})")
            print(f"   ├─ Adaptive Threshold: {result['adaptive_threshold']:.2f}")
            print(f"   ├─ Language: {lid.get_language_name(result['primary_language'])} ({result['primary_language']})")
            print(f"   ├─ Confidence: {result['confidence']:.2%}")
            print(f"   └─ Code-mixed: {result['is_code_mixed']}")
        
        print("\n" + "=" * 80)
        print("TEST 2: Ensemble Approach with Romanized Boost")
        print("=" * 80)
        
        romanized_tests = [
            "mai bahut khush hoon aaj",
            "Mi khup khush ahe",
            "ami tomake bhalobashi",
            "naan romba sandhosham",
            "This is pure English text"
        ]
        
        for text in romanized_tests:
            result = lid.predict_with_romanized_boost(text, k=3)
            
            print(f"\n📝 Text: '{text}'")
            print(f"   GLotLID: {result['primary_language']} ({result['confidence']:.2%})")
            
            if result['romanized_detection']['detected']:
                rom = result['romanized_detection']
                print(f"   Romanized: {rom['language']} ({rom['confidence']:.2%})")
                print(f"   Latin %: {rom['latin_percentage']:.1f}%")
            
            print(f"   👉 FINAL: {lid.get_language_name(result['final_language'])} " +
                  f"({result['final_confidence']:.2%}) via {result['detection_method']}")
        
        print("\n" + "=" * 80)
        print("TEST 3: Probability Distribution Visualization")
        print("=" * 80)
        
        viz_test = "Yaar ye movie bahut mast hai! Must watch bro, ekdum zabardast!"
        print(lid.visualize_predictions(viz_test, k=5))
        
        print("\n" + "=" * 80)
        print("TEST 4: Comprehensive Summary")
        print("=" * 80)
        
        summary = lid.get_prediction_summary(
            "Mi aaj khup khush ahe! Traffic heavy aahe.",
            include_visualization=True
        )
        
        print(f"\n📊 Comprehensive Analysis:")
        print(f"   Text: {summary['text']}")
        print(f"   Final Language: {summary['final_language_name']} ({summary['final_language']})")
        print(f"   Confidence: {summary['confidence']:.2%}")
        print(f"   Method: {summary['detection_method']}")
        print(f"   Category: {summary['text_category']}")
        print(f"   Code-Mixed: {summary['is_code_mixed']}")
        
        if 'romanized_info' in summary:
            print(f"\n   Romanized Detection:")
            print(f"   └─ {summary['romanized_info']['language']} " +
                  f"({summary['romanized_info']['confidence']:.2%})")
        
        print(f"\n   Top 3 Predictions:")
        for i, pred in enumerate(summary['top_3_predictions'], 1):
            print(f"   {i}. {pred['language_name']:15} - {pred['confidence']:.2%}")
        
        if 'visualization' in summary:
            print(f"\n{summary['visualization']}")
        
        print("\n" + "=" * 80)
        print("✅ ENHANCED GLOTLID TESTING COMPLETE!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error testing GLotLID: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_glotlid()
