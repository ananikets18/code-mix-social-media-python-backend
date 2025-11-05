"""
Adaptive Learning System for NLP Analysis
==========================================

This module implements a self-learning system that:
- Stores successful and failed language detections
- Learns patterns from real API usage
- Improves detection accuracy over time
- Handles unseen contexts intelligently
- Provides feedback loop for continuous improvement

Features:
1. Pattern Memory - Stores successful detection patterns
2. Failure Tracking - Logs misdetections for analysis
3. Confidence Scoring - Learns which patterns are reliable
4. Auto-correction - Suggests improvements based on history
5. User Feedback - Incorporates corrections from users
"""

import json
import os
import hashlib
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
import pickle
from logger_config import get_logger

logger = get_logger(__name__, level="INFO")

# ==================== CONFIGURATION ====================

LEARNING_CONFIG = {
    'pattern_cache_file': 'adaptive_learning/pattern_cache.json',
    'failure_log_file': 'adaptive_learning/failure_log.json',
    'user_corrections_file': 'adaptive_learning/user_corrections.json',
    'statistics_file': 'adaptive_learning/statistics.json',
    'min_pattern_confidence': 0.7,  # Minimum confidence to use cached pattern
    'pattern_reuse_threshold': 3,   # Use pattern after 3 successful detections
    'enable_auto_learning': True,   # Enable automatic pattern learning
    'enable_user_feedback': True,   # Enable user correction system
    'max_cache_size': 10000,        # Maximum cached patterns
    'cache_cleanup_threshold': 12000  # Cleanup when this size is reached
}

# ==================== ADAPTIVE LEARNING MANAGER ====================

class AdaptiveLearningManager:
    """
    Manages adaptive learning for language detection and analysis
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the adaptive learning system"""
        self.config = config or LEARNING_CONFIG
        self.pattern_cache = {}
        self.failure_log = []
        self.user_corrections = []
        self.statistics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'user_corrections': 0,
            'auto_improvements': 0,
            'language_distribution': defaultdict(int),
            'detection_methods': defaultdict(int),
            'avg_confidence_by_language': defaultdict(list)
        }
        
        # Create directory structure
        os.makedirs('adaptive_learning', exist_ok=True)
        
        # Load existing data
        self._load_data()
        
        logger.debug("Adaptive Learning System initialized")
    
    # ==================== PATTERN MANAGEMENT ====================
    
    def get_text_signature(self, text: str) -> str:
        """
        Create a unique signature for text based on structure, not exact content
        This allows similar texts to match
        """
        # Normalize text
        normalized = text.lower().strip()
        
        # Create signature based on:
        # 1. Length category
        length_cat = 'short' if len(normalized) < 20 else 'medium' if len(normalized) < 100 else 'long'
        
        # 2. Word count
        word_count = len(normalized.split())
        
        # 3. Script composition (Latin, Devanagari, etc.)
        has_latin = any('a' <= c <= 'z' for c in normalized)
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in normalized)
        has_mixed = has_latin and has_devanagari
        
        script_type = 'mixed' if has_mixed else 'latin' if has_latin else 'indic' if has_devanagari else 'other'
        
        # 4. Key words (first 3 words for pattern matching)
        key_words = ' '.join(normalized.split()[:3])
        
        # Create signature
        signature = f"{length_cat}_{word_count}_{script_type}_{hashlib.md5(key_words.encode()).hexdigest()[:8]}"
        
        return signature
    
    def check_pattern_cache(self, text: str) -> Optional[Dict]:
        """
        Check if we've seen similar text before and have a reliable pattern
        
        Returns cached detection result if confidence is high enough
        """
        if not self.config['enable_auto_learning']:
            return None
        
        signature = self.get_text_signature(text)
        
        if signature in self.pattern_cache:
            cached = self.pattern_cache[signature]
            
            # Check if pattern is reliable (used successfully multiple times)
            if (cached['use_count'] >= self.config['pattern_reuse_threshold'] and
                cached['avg_confidence'] >= self.config['min_pattern_confidence']):
                
                self.statistics['cache_hits'] += 1
                cached['last_used'] = datetime.now().isoformat()
                cached['use_count'] += 1
                
                logger.info(f"Cache HIT: Using cached pattern for signature {signature}")
                return cached['detection_result']
        
        self.statistics['cache_misses'] += 1
        return None
    
    def store_pattern(self, text: str, detection_result: Dict, confidence: float):
        """
        Store a successful detection pattern for future reuse
        """
        if not self.config['enable_auto_learning']:
            return
        
        signature = self.get_text_signature(text)
        
        if signature in self.pattern_cache:
            # Update existing pattern
            cached = self.pattern_cache[signature]
            cached['use_count'] += 1
            cached['confidences'].append(confidence)
            cached['avg_confidence'] = sum(cached['confidences']) / len(cached['confidences'])
            cached['last_used'] = datetime.now().isoformat()
            
            logger.debug(f"Pattern updated: {signature} (uses: {cached['use_count']}, conf: {cached['avg_confidence']:.2f})")
        else:
            # Create new pattern
            self.pattern_cache[signature] = {
                'signature': signature,
                'detection_result': detection_result,
                'use_count': 1,
                'confidences': [confidence],
                'avg_confidence': confidence,
                'first_seen': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat(),
                'example_text': text[:100]  # Store first 100 chars as example
            }
            
            logger.info(f"New pattern stored: {signature} (conf: {confidence:.2f})")
        
        # Cleanup if cache is too large
        if len(self.pattern_cache) > self.config['cache_cleanup_threshold']:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove least used patterns when cache is full"""
        logger.info(f"Cache cleanup: {len(self.pattern_cache)} patterns")
        
        # Sort by use_count and avg_confidence
        sorted_patterns = sorted(
            self.pattern_cache.items(),
            key=lambda x: (x[1]['use_count'], x[1]['avg_confidence']),
            reverse=True
        )
        
        # Keep only top patterns
        self.pattern_cache = dict(sorted_patterns[:self.config['max_cache_size']])
        
        logger.info(f"Cache cleaned: {len(self.pattern_cache)} patterns remaining")
    
    # ==================== FAILURE TRACKING ====================
    
    def log_detection_failure(self, text: str, detected_language: str, 
                             expected_language: str, confidence: float,
                             method: str, reason: str = ""):
        """
        Log a detection failure for analysis and improvement
        """
        failure_entry = {
            'timestamp': datetime.now().isoformat(),
            'text': text[:200],  # Store up to 200 chars
            'text_length': len(text),
            'detected_language': detected_language,
            'expected_language': expected_language,
            'confidence': confidence,
            'method': method,
            'reason': reason,
            'signature': self.get_text_signature(text)
        }
        
        self.failure_log.append(failure_entry)
        
        # Keep only last 1000 failures
        if len(self.failure_log) > 1000:
            self.failure_log = self.failure_log[-1000:]
        
        logger.warning(f"Detection failure logged: {detected_language} vs {expected_language} (conf: {confidence:.2f})")
    
    def analyze_failures(self) -> Dict:
        """
        Analyze failure patterns to identify common issues
        """
        if not self.failure_log:
            return {'message': 'No failures to analyze'}
        
        # Group failures by detected vs expected language
        misdetection_patterns = defaultdict(int)
        low_confidence_cases = []
        method_failures = defaultdict(int)
        
        for failure in self.failure_log:
            pattern = f"{failure['detected_language']} → {failure['expected_language']}"
            misdetection_patterns[pattern] += 1
            method_failures[failure['method']] += 1
            
            if failure['confidence'] < 0.6:
                low_confidence_cases.append(failure)
        
        return {
            'total_failures': len(self.failure_log),
            'common_misdetections': dict(sorted(
                misdetection_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            'method_failures': dict(method_failures),
            'low_confidence_count': len(low_confidence_cases),
            'avg_failure_confidence': sum(f['confidence'] for f in self.failure_log) / len(self.failure_log)
        }
    
    # ==================== USER FEEDBACK ====================
    
    def record_user_correction(self, text: str, detected_language: str,
                              correct_language: str, user_id: str = "anonymous"):
        """
        Record a user correction for learning
        This is crucial for improving the system with real user feedback
        """
        if not self.config['enable_user_feedback']:
            return
        
        correction = {
            'timestamp': datetime.now().isoformat(),
            'text': text[:200],
            'detected_language': detected_language,
            'correct_language': correct_language,
            'user_id': user_id,
            'signature': self.get_text_signature(text)
        }
        
        self.user_corrections.append(correction)
        self.statistics['user_corrections'] += 1
        
        # Update pattern cache with correction
        signature = self.get_text_signature(text)
        if signature in self.pattern_cache:
            # Invalidate incorrect pattern
            del self.pattern_cache[signature]
            logger.info(f"Invalidated incorrect pattern: {signature}")
        
        # Log as failure
        self.log_detection_failure(
            text, detected_language, correct_language, 
            0.0, "user_correction", "User provided correct language"
        )
        
        logger.info(f"User correction recorded: {detected_language} → {correct_language}")
    
    def get_correction_suggestions(self, text: str, current_detection: Dict) -> List[Dict]:
        """
        Get suggestions based on similar past corrections
        """
        suggestions = []
        signature = self.get_text_signature(text)
        
        # Check if similar texts were corrected before
        for correction in self.user_corrections:
            if correction['signature'] == signature:
                suggestions.append({
                    'suggested_language': correction['correct_language'],
                    'reason': 'Similar text was corrected by user',
                    'timestamp': correction['timestamp']
                })
        
        return suggestions
    
    # ==================== STATISTICS & ANALYTICS ====================
    
    def update_statistics(self, detection_result: Dict):
        """
        Update statistics from a detection result
        """
        self.statistics['total_requests'] += 1
        
        if 'language' in detection_result:
            lang = detection_result['language']
            self.statistics['language_distribution'][lang] += 1
        
        if 'method' in detection_result:
            self.statistics['detection_methods'][detection_result['method']] += 1
        
        if 'confidence' in detection_result and 'language' in detection_result:
            lang = detection_result['language']
            self.statistics['avg_confidence_by_language'][lang].append(detection_result['confidence'])
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics
        """
        # Calculate averages
        avg_conf_by_lang = {
            lang: sum(confs) / len(confs)
            for lang, confs in self.statistics['avg_confidence_by_language'].items()
        }
        
        cache_hit_rate = (
            self.statistics['cache_hits'] / 
            (self.statistics['cache_hits'] + self.statistics['cache_misses'])
            if (self.statistics['cache_hits'] + self.statistics['cache_misses']) > 0
            else 0
        )
        
        return {
            'total_requests': self.statistics['total_requests'],
            'cache_hit_rate': cache_hit_rate,
            'cached_patterns': len(self.pattern_cache),
            'total_failures': len(self.failure_log),
            'user_corrections': self.statistics['user_corrections'],
            'language_distribution': dict(self.statistics['language_distribution']),
            'detection_methods': dict(self.statistics['detection_methods']),
            'avg_confidence_by_language': avg_conf_by_lang,
            'failure_analysis': self.analyze_failures()
        }
    
    # ==================== PERSISTENCE ====================
    
    def _load_data(self):
        """Load saved data from disk"""
        try:
            # Load pattern cache
            if os.path.exists(self.config['pattern_cache_file']):
                with open(self.config['pattern_cache_file'], 'r', encoding='utf-8') as f:
                    self.pattern_cache = json.load(f)
                logger.debug(f"Loaded {len(self.pattern_cache)} cached patterns")
            
            # Load failure log
            if os.path.exists(self.config['failure_log_file']):
                with open(self.config['failure_log_file'], 'r', encoding='utf-8') as f:
                    self.failure_log = json.load(f)
                logger.debug(f"Loaded {len(self.failure_log)} failure logs")
            
            # Load user corrections
            if os.path.exists(self.config['user_corrections_file']):
                with open(self.config['user_corrections_file'], 'r', encoding='utf-8') as f:
                    self.user_corrections = json.load(f)
                logger.debug(f"Loaded {len(self.user_corrections)} user corrections")
            
            # Load statistics
            if os.path.exists(self.config['statistics_file']):
                with open(self.config['statistics_file'], 'r', encoding='utf-8') as f:
                    loaded_stats = json.load(f)
                    # Convert defaultdicts
                    self.statistics.update(loaded_stats)
                    for key in ['language_distribution', 'detection_methods', 'avg_confidence_by_language']:
                        if key in loaded_stats:
                            self.statistics[key] = defaultdict(
                                int if key != 'avg_confidence_by_language' else list,
                                loaded_stats[key]
                            )
                logger.debug("Loaded statistics")
                
        except Exception as e:
            logger.error(f"Error loading adaptive learning data: {e}")
    
    def save_data(self):
        """Save data to disk"""
        try:
            # Save pattern cache
            with open(self.config['pattern_cache_file'], 'w', encoding='utf-8') as f:
                json.dump(self.pattern_cache, f, indent=2, ensure_ascii=False)
            
            # Save failure log
            with open(self.config['failure_log_file'], 'w', encoding='utf-8') as f:
                json.dump(self.failure_log, f, indent=2, ensure_ascii=False)
            
            # Save user corrections
            with open(self.config['user_corrections_file'], 'w', encoding='utf-8') as f:
                json.dump(self.user_corrections, f, indent=2, ensure_ascii=False)
            
            # Save statistics
            with open(self.config['statistics_file'], 'w', encoding='utf-8') as f:
                # Convert defaultdicts to regular dicts for JSON
                stats_to_save = dict(self.statistics)
                for key in ['language_distribution', 'detection_methods', 'avg_confidence_by_language']:
                    if key in stats_to_save:
                        stats_to_save[key] = dict(stats_to_save[key])
                json.dump(stats_to_save, f, indent=2, ensure_ascii=False)
            
            logger.debug("Adaptive learning data saved")
            
        except Exception as e:
            logger.error(f"Error saving adaptive learning data: {e}")
    
    def auto_save(self):
        """Auto-save data periodically"""
        # Save every 100 requests
        if self.statistics['total_requests'] % 100 == 0:
            self.save_data()


# ==================== GLOBAL INSTANCE ====================

# Create global instance
adaptive_learning_manager = AdaptiveLearningManager()

# Auto-save on exit
import atexit
atexit.register(adaptive_learning_manager.save_data)


# ==================== HELPER FUNCTIONS ====================

def check_cache_before_detection(text: str) -> Optional[Dict]:
    """
    Check if we have a cached pattern for this text
    Use this before running full detection
    """
    return adaptive_learning_manager.check_pattern_cache(text)


def store_successful_detection(text: str, result: Dict):
    """
    Store a successful detection for future reuse
    Call this after successful detection
    """
    if 'language' in result and 'confidence' in result:
        adaptive_learning_manager.store_pattern(text, result, result['confidence'])
        adaptive_learning_manager.update_statistics(result)
        adaptive_learning_manager.auto_save()


def log_detection_issue(text: str, detected: str, expected: str, 
                       confidence: float, method: str, reason: str = ""):
    """
    Log a detection issue for analysis
    """
    adaptive_learning_manager.log_detection_failure(
        text, detected, expected, confidence, method, reason
    )


def record_user_feedback(text: str, detected_language: str, correct_language: str, 
                        user_id: str = "anonymous", comments: Optional[str] = None) -> str:
    """
    Record user correction
    Use this when user provides feedback
    
    Returns correction_id for tracking
    """
    correction_id = adaptive_learning_manager.record_user_correction(
        text, detected_language, correct_language, user_id, comments
    )
    adaptive_learning_manager.save_data()
    return correction_id


def store_detection_failure_with_context(full_analysis_result: Dict, 
                                         expected_language: Optional[str] = None,
                                         user_correction: bool = False) -> str:
    """
    Store complete detection failure with full context for learning
    
    This automatically identifies failures based on:
    - Low confidence (<0.5)
    - Unknown/obscure languages (like 'ido', 'jbo', etc.)
    - User-reported corrections
    
    Args:
        full_analysis_result: Complete analysis result from analyze_text_comprehensive
        expected_language: Optional - What the language should be
        user_correction: Whether this is a user-reported failure
    
    Returns:
        failure_id for tracking
    """
    try:
        # Extract language analysis
        lang_info = full_analysis_result.get('language', {})
        detected_lang = lang_info.get('language', 'unknown')
        confidence = lang_info.get('confidence', 0.0)
        method = lang_info.get('method', 'unknown')
        
        # Determine if this is a failure
        is_failure = False
        failure_reason = []
        
        # Check 1: Low confidence
        if confidence < 0.5:
            is_failure = True
            failure_reason.append(f"low_confidence_{confidence:.2f}")
        
        # Check 2: Obscure/unlikely languages
        obscure_languages = ['ido', 'jbo', 'lfn', 'nov', 'vol', 'io', 'ia', 'ie', 'eo']
        if detected_lang in obscure_languages:
            is_failure = True
            failure_reason.append(f"obscure_language_{detected_lang}")
        
        # Check 3: Unknown language
        if detected_lang == 'unknown' or lang_info.get('language_name') == 'Unknown':
            is_failure = True
            failure_reason.append("unknown_language")
        
        # Check 4: User correction
        if user_correction:
            is_failure = True
            failure_reason.append("user_reported")
        
        # Check 5: Confidence-method mismatch (high confidence but low-tier method)
        if confidence > 0.6 and 'fallback' in method:
            is_failure = True
            failure_reason.append("suspicious_confidence")
        
        # If not a failure, don't store
        if not is_failure and not expected_language:
            return None
        
        # Generate failure ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_hash = hashlib.md5(full_analysis_result.get('original_text', '').encode()).hexdigest()[:8]
        failure_id = f"fail_{timestamp}_{text_hash}"
        
        # Build failure record
        failure_record = {
            "failure_id": failure_id,
            "timestamp": datetime.now().isoformat(),
            "detection_summary": {
                "text": full_analysis_result.get('original_text', ''),
                "detected_language": detected_lang,
                "confidence": confidence,
                "method": method,
                "expected_language": expected_language,
                "failure_reasons": failure_reason
            },
            "full_analysis": full_analysis_result,
            "metadata": {
                "text_length": len(full_analysis_result.get('original_text', '')),
                "word_count": full_analysis_result.get('statistics', {}).get('word_count', 0),
                "is_code_mixed": lang_info.get('language_info', {}).get('is_code_mixed', False),
                "is_romanized": lang_info.get('language_info', {}).get('is_romanized', False),
                "dominant_script": lang_info.get('composition', {}).get('dominant_script', 'unknown')
            }
        }
        
        # Load existing failures
        failures_file = 'data/detection_failures.json'
        os.makedirs(os.path.dirname(failures_file), exist_ok=True)
        
        try:
            with open(failures_file, 'r', encoding='utf-8') as f:
                failures = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            failures = []
        
        # Add new failure
        failures.append(failure_record)
        
        # Keep only last 500 failures (prevent file from growing too large)
        if len(failures) > 500:
            failures = failures[-500:]
        
        # Save
        with open(failures_file, 'w', encoding='utf-8') as f:
            json.dump(failures, f, indent=2, ensure_ascii=False)
        
        logger.warning(f"Detection failure stored: {failure_id} - {', '.join(failure_reason)}")
        logger.warning(f"  Text: '{full_analysis_result.get('original_text', '')[:50]}...'")
        logger.warning(f"  Detected: {detected_lang} (confidence: {confidence:.2f})")
        
        return failure_id
        
    except Exception as e:
        logger.error(f"Error storing detection failure: {e}")
        return None


def analyze_failure_patterns(limit: int = 50) -> Dict:
    """
    Analyze stored failures to identify patterns and suggest improvements
    
    Returns insights like:
    - Most common failure reasons
    - Problematic language pairs
    - Scripts/patterns that cause issues
    """
    try:
        failures_file = 'data/detection_failures.json'
        
        with open(failures_file, 'r', encoding='utf-8') as f:
            failures = json.load(f)
        
        # Get recent failures
        recent_failures = failures[-limit:]
        
        # Analyze patterns
        failure_reasons = []
        detected_langs = []
        expected_langs = []
        scripts = []
        confidence_scores = []
        methods = []
        
        for failure in recent_failures:
            summary = failure.get('detection_summary', {})
            metadata = failure.get('metadata', {})
            
            failure_reasons.extend(summary.get('failure_reasons', []))
            detected_langs.append(summary.get('detected_language'))
            if summary.get('expected_language'):
                expected_langs.append(summary.get('expected_language'))
            scripts.append(metadata.get('dominant_script'))
            confidence_scores.append(summary.get('confidence', 0))
            methods.append(summary.get('method'))
        
        # Count patterns
        reason_counts = Counter(failure_reasons)
        lang_counts = Counter(detected_langs)
        expected_counts = Counter(expected_langs)
        script_counts = Counter(scripts)
        method_counts = Counter(methods)
        
        # Generate insights
        insights = {
            "total_failures_analyzed": len(recent_failures),
            "top_failure_reasons": reason_counts.most_common(5),
            "most_misdetected_as": lang_counts.most_common(5),
            "most_missed_languages": expected_counts.most_common(5),
            "problematic_scripts": script_counts.most_common(5),
            "methods_with_failures": method_counts.most_common(5),
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "recommendations": []
        }
        
        # Generate recommendations
        if reason_counts.get('obscure_language_ido', 0) > 3:
            insights['recommendations'].append({
                "issue": "Frequent 'ido' detection for romanized Indic languages",
                "solution": "Add romanized Indic language detection before GlotLID",
                "priority": "HIGH"
            })
        
        if any('low_confidence' in reason for reason in failure_reasons):
            insights['recommendations'].append({
                "issue": "Many low-confidence detections",
                "solution": "Consider fallback to script-based detection or user prompt",
                "priority": "MEDIUM"
            })
        
        if script_counts.get('latin', 0) > len(recent_failures) * 0.5:
            insights['recommendations'].append({
                "issue": "Over 50% failures are Latin script (likely romanized Indic)",
                "solution": "Implement romanized Indic language detector",
                "priority": "HIGH"
            })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error analyzing failure patterns: {e}")
        return {"error": str(e)}


def get_learning_statistics() -> Dict:
    """Get current learning statistics"""
    return adaptive_learning_manager.get_statistics()
