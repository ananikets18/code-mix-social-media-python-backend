"""
Character N-gram Language Detector for Romanized Indic Languages
Integrated into the NLP preprocessing pipeline
"""

from collections import Counter
from typing import Dict, Tuple, List
import pickle
import os

from logger_config import get_logger

logger = get_logger(__name__, level="INFO")


class CharacterNgramDetector:
    """Character n-gram based language detector"""
    
    def __init__(self, ngram_sizes: List[int] = None):
        self.ngram_sizes = ngram_sizes or [2, 3, 4]
        self.language_profiles = {}
        self.language_total_ngrams = {}
        self._initialized = False
    
    def _extract_ngrams(self, text: str) -> Counter:
        """Extract character n-grams from text"""
        text = text.lower().strip()
        all_ngrams = Counter()
        
        for n in self.ngram_sizes:
            for i in range(len(text) - n + 1):
                ngram = text[i:i+n]
                if ngram.strip() and any(c.isalnum() for c in ngram):
                    all_ngrams[ngram] += 1
        
        return all_ngrams
    
    def _initialize_default_profiles(self):
        """Initialize with minimal training data"""
        training_data = {
            'mar': [
                "aaj mala late hoeil thik ahe",
                "tu kasa ahes mala sangu kay jhala",
                "mi ghari jaat ahe udya bhetnar ahe",
                "khup bara aahe mhanje thik ahe",
                "tu kashala jatos mi pan yenar ahe",
                "aaj kal udya parva sakal sandhyakal",
                "mala tyala tila tumhala kay pahije",
                "kar kara karaycha jaa ja yaa yeil",
                "honar hotay hota hoti hoeil zala zali",
                "mi tu tula tumhi maza mazi maze",
            ],
            'hin': [
                "main thik hoon yaar bahut mast hai",
                "kya kar raha hai bhai kaise ho",
                "tum kahan ja rahe ho abhi",
                "mujhe bahut achha lagta hai yaar",
                "hum sab milke chalenge phir se",
                "kal main market jaunga tumhe bhi",
                "ye bahut zabardast hai dekho toh",
                "kab aayega wo hamko batao na",
                "main bol raha hoon sach mein",
                "aaj kal phir ab ye wo woh",
            ],
            'tam': [
                "naan pathukaren nee enna panra",
                "ippo romba late aachu poi thongalam",
                "nee enga pora naanum varen da",
                "avan avanga kitta poi sollu",
                "ippodhu mudichiduven aprom thaan",
                "naan avan aval avar avanga",
                "pathukaren pannuren varen poren",
                "ippo ippodhu romba illa illai",
                "poi vaa poda thoongu thedi",
                "ren ran raan tten ven veen",
            ],
            'ben': [
                "ami bhalo achi tumi kemon acho",
                "tumi kothay jachcho ekhon",
                "ami market jaabo tomar sathe",
                "eta khub bhalo lagche amar",
                "tumi ki korcho ekhon bolo",
                "ami tomake bhalobashi khub",
                "kal ami jabo tomar bari",
                "eta dekho khub sundor hoyeche",
            ],
            'pan': [
                "main theek haan tusi kiven ho",
                "tusi kithe ja rahe ho",
                "main kal bazaar jaana",
                "eh bahut vadiya hai",
                "tusi ki kar rahe ho",
                "main tuhanu pyaar karda",
                "kal main tuhade ghar aana",
            ],
        }
        
        logger.info("Initializing N-gram detector with default profiles...")
        
        for language, texts in training_data.items():
            language_ngrams = Counter()
            for text in texts:
                ngrams = self._extract_ngrams(text)
                language_ngrams.update(ngrams)
            
            total = sum(language_ngrams.values())
            self.language_profiles[language] = {
                ngram: count / total 
                for ngram, count in language_ngrams.items()
            }
            self.language_total_ngrams[language] = total
        
        self._initialized = True
        logger.info(f"N-gram detector initialized with {len(self.language_profiles)} languages")
    
    def _calculate_similarity(self, text_ngrams: Counter, language: str) -> float:
        """Calculate similarity score"""
        profile = self.language_profiles.get(language, {})
        if not profile:
            return 0.0
        
        score = 0.0
        text_total = sum(text_ngrams.values())
        if text_total == 0:
            return 0.0
        
        for ngram, count in text_ngrams.items():
            text_freq = count / text_total
            profile_freq = profile.get(ngram, 0)
            if profile_freq > 0:
                score += text_freq * profile_freq * 100
        
        return score
    
    def predict(self, text: str, top_k: int = 3) -> Tuple[str, float, Dict]:
        """Predict language"""
        if not self._initialized:
            self._initialize_default_profiles()
        
        if not text or len(text.strip()) < 2:
            return None, 0.0, {}
        
        text_ngrams = self._extract_ngrams(text)
        
        scores = {}
        for language in self.language_profiles:
            scores[language] = self._calculate_similarity(text_ngrams, language)
        
        sorted_languages = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_languages or sorted_languages[0][1] == 0:
            return None, 0.0, scores
        
        best_lang, best_score = sorted_languages[0]
        total_score = sum(s for _, s in sorted_languages)
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        return best_lang, confidence, dict(sorted_languages[:top_k])


# Global instance
_ngram_detector = None


def get_ngram_detector() -> CharacterNgramDetector:
    """Get or create global n-gram detector instance"""
    global _ngram_detector
    if _ngram_detector is None:
        _ngram_detector = CharacterNgramDetector()
    return _ngram_detector


def detect_with_ngrams(text: str) -> Tuple[str, float]:
    """
    Detect romanized language using n-grams
    
    Args:
        text: Romanized text
        
    Returns:
        (language_code, confidence)
    """
    detector = get_ngram_detector()
    lang, conf, _ = detector.predict(text)
    return lang, conf
