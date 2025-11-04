"""
Multilingual Profanity/Bad Words Filter
Supports: International languages + Indian regional languages
Features: Detection, masking, severity scoring, context-aware filtering
"""

import re
from typing import Dict, List, Tuple, Optional, Set
from logger_config import get_logger

# Setup logger
logger = get_logger(__name__, level="INFO")

# ============================================================================
# BAD WORDS DATABASE - International Languages
# ============================================================================

ENGLISH_BAD_WORDS = {
    # Severity 3 - Highly offensive
    'extreme': [
        'fuck', 'fucking', 'motherfucker', 'fucker', 'fck', 'fuk', 'f**k',
        'shit', 'shit', 'bullshit', 'horseshit', 'shitty',
        'bitch', 'bitches', 'bastard', 'asshole', 'assholes', 'ass',
        'dick', 'dickhead', 'cock', 'pussy', 'cunt',
        'damn', 'dammit', 'goddamn', 'hell',
        'whore', 'slut', 'prostitute', 'piss', 'pissed'
    ],
    
    # Severity 2 - Moderately offensive
    'moderate': [
        'stupid', 'idiot', 'dumb', 'moron', 'fool', 'foolish',
        'hate', 'hatred', 'suck', 'sucks', 'sucked',
        'loser', 'losers', 'pathetic', 'worthless',
        'crap', 'crappy', 'jerk', 'jerks'
    ],
    
    # Severity 1 - Mild/slang
    'mild': [
        'dang', 'darn', 'heck', 'wtf', 'omfg',
        'bloody', 'blimey', 'bugger'
    ]
}

# ============================================================================
# BAD WORDS DATABASE - Indian Languages (Transliterated + Native Script)
# ============================================================================

HINDI_BAD_WORDS = {
    'extreme': [
        # Hindi profanity (transliterated)
        'chutiya', 'chutiye', 'chodu', 'lodu', 'lode', 'lund',
        'bhenchod', 'behenchod', 'behen chod', 'bc',
        'madarchod', 'maderchod', 'mc',
        'gandu', 'gand', 'gaandu',
        'harami', 'haramzada', 'haraamzaada',
        'kutta', 'kutte', 'kutiya', 'saala', 'sala',
        # Devanagari script
        'चूतिया', 'चूतिये', 'चोदू', 'लोडू', 'लोड़े', 'लंड',
        'भेनचोद', 'बहनचोद', 'मादरचोद',
        'गांडू', 'गांड', 'हरामी', 'हरामज़ादा',
        'कुत्ता', 'कुत्ते', 'कुतिया', 'साला'
    ],
    'moderate': [
        'bewakoof', 'bevkoof', 'pagal', 'budhu', 'ullu',
        'kamina', 'kameena', 'badtameez',
        'बेवकूफ', 'पागल', 'बुद्धू', 'उल्लू', 'कमीना', 'बदतमीज़'
    ],
    'mild': [
        'besharam', 'badmash', 'ghatiya',
        'बेशरम', 'बदमाश', 'घटिया'
    ]
}

MARATHI_BAD_WORDS = {
    'extreme': [
        'zhavadya', 'zhavnya', 'zavadya', 'zhav',
        'ghaan', 'ghand', 'aaichi', 'aai chi',
        'झवाड्या', 'झवणे', 'घाण', 'आईची'
    ],
    'moderate': [
        'veda', 'vedya', 'shendi',
        'वेडा', 'शेंडी'
    ]
}

TAMIL_BAD_WORDS = {
    'extreme': [
        'punda', 'pundai', 'otha', 'oombu',
        'panni', 'naaye', 'thevidiya',
        'புண்டை', 'ஓத்த', 'ஊம்பு', 'பன்னி', 'நாயே', 'தேவிடியா'
    ],
    'moderate': [
        'loosu', 'karumam', 'மூடு', 'லூசு'
    ]
}

TELUGU_BAD_WORDS = {
    'extreme': [
        'dengu', 'dengey', 'puka', 'modda',
        'gudda', 'lanjakoduku', 'lanjala',
        'దెంగు', 'పూక', 'మొద్ద', 'గుద్ద', 'లంజ'
    ],
    'moderate': [
        'erripuka', 'edava', 'erri',
        'ఎర్రిపూక', 'ఎదవ'
    ]
}

KANNADA_BAD_WORDS = {
    'extreme': [
        'thika', 'thikamuchko', 'kati', 'boli',
        'kathe', 'ತೀಕ', 'ಕತ್ತೆ', 'ಬೋಳಿ'
    ],
    'moderate': [
        'bevakoof', 'buddi', 'ಬುದ್ದಿ'
    ]
}

PUNJABI_BAD_WORDS = {
    'extreme': [
        'bhen di', 'bhendi', 'khotya', 'panchod',
        'ਭੈਣ ਦੀ', 'ਪੰਚੋਦ', 'ਖੋਤਿਆ'
    ],
    'moderate': [
        'gadha', 'gadhe', 'kutta',
        'ਗਧਾ', 'ਕੁੱਤਾ'
    ]
}

GUJARATI_BAD_WORDS = {
    'extreme': [
        'lavde', 'lavdu', 'lodu', 'bhosdi',
        'લવડે', 'લોડું', 'ભોસડી'
    ],
    'moderate': [
        'bewakoof', 'nadan',
        'બેવકૂફ', 'નાદાન'
    ]
}

BENGALI_BAD_WORDS = {
    'extreme': [
        'choda', 'chudi', 'madarchod', 'magir pola',
        'চোদা', 'চুদি', 'মাগির পোলা', 'মাদারচোদ'
    ],
    'moderate': [
        'buddhu', 'gadha', 'boka',
        'বুদ্ধু', 'গাধা', 'বোকা'
    ]
}

MALAYALAM_BAD_WORDS = {
    'extreme': [
        'myre', 'myran', 'kunna', 'punda', 'thayoli',
        'മൈര്', 'കുണ്ണ', 'പുണ്ട', 'തായോളി'
    ],
    'moderate': [
        'patti', 'pattikaran',
        'പട്ടി'
    ]
}

# ============================================================================
# COMBINED DATABASE
# ============================================================================

ALL_BAD_WORDS_DB = {
    'english': ENGLISH_BAD_WORDS,
    'hindi': HINDI_BAD_WORDS,
    'marathi': MARATHI_BAD_WORDS,
    'tamil': TAMIL_BAD_WORDS,
    'telugu': TELUGU_BAD_WORDS,
    'kannada': KANNADA_BAD_WORDS,
    'punjabi': PUNJABI_BAD_WORDS,
    'gujarati': GUJARATI_BAD_WORDS,
    'bengali': BENGALI_BAD_WORDS,
    'malayalam': MALAYALAM_BAD_WORDS
}

# Severity scores
SEVERITY_SCORES = {
    'extreme': 3,
    'moderate': 2,
    'mild': 1
}


class ProfanityFilter:
    """
    Multilingual profanity filter with detection, masking, and severity scoring
    """
    
    def __init__(self, languages: Optional[List[str]] = None):
        """
        Initialize profanity filter
        
        Args:
            languages (list): List of languages to check (default: all)
        """
        self.languages = languages or list(ALL_BAD_WORDS_DB.keys())
        self.bad_words_set = self._build_bad_words_set()
        self.patterns = self._compile_patterns()
        logger.info(f"Profanity filter initialized for languages: {', '.join(self.languages)}")
        logger.info(f"Total bad words loaded: {len(self.bad_words_set)}")
    
    def _build_bad_words_set(self) -> Dict[str, Set[str]]:
        """Build set of bad words for quick lookup"""
        bad_words = {}
        for severity in ['extreme', 'moderate', 'mild']:
            words = set()
            for lang in self.languages:
                if lang in ALL_BAD_WORDS_DB:
                    words.update(ALL_BAD_WORDS_DB[lang].get(severity, []))
            bad_words[severity] = words
        return bad_words
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficient matching"""
        patterns = {}
        for severity in ['extreme', 'moderate', 'mild']:
            severity_patterns = []
            for word in self.bad_words_set[severity]:
                # Create pattern with word boundaries
                # Also handle common obfuscations (a$$ -> ass, f**k -> fuck)
                pattern = re.escape(word)
                pattern = pattern.replace(r'\*', r'[\*\w]')
                pattern = pattern.replace(r'\$', r'[\$s]')
                pattern = pattern.replace(r'@', r'[@a]')
                pattern = r'\b' + pattern + r'\b'
                severity_patterns.append(re.compile(pattern, re.IGNORECASE | re.UNICODE))
            patterns[severity] = severity_patterns
        return patterns
    
    def detect_profanity(self, text: str) -> Dict:
        """
        Detect profanity in text
        
        Args:
            text (str): Input text
        
        Returns:
            dict: Detection results with details
        """
        results = {
            'has_profanity': False,
            'severity_score': 0,
            'max_severity': None,
            'detected_words': [],
            'word_count': 0,
            'severity_breakdown': {
                'extreme': [],
                'moderate': [],
                'mild': []
            }
        }
        
        # Check each severity level
        for severity in ['extreme', 'moderate', 'mild']:
            for pattern in self.patterns[severity]:
                matches = pattern.findall(text)
                if matches:
                    unique_matches = list(set(matches))
                    results['detected_words'].extend(unique_matches)
                    results['severity_breakdown'][severity].extend(unique_matches)
                    results['word_count'] += len(unique_matches)
        
        # Calculate overall results
        if results['word_count'] > 0:
            results['has_profanity'] = True
            
            # Determine max severity
            if results['severity_breakdown']['extreme']:
                results['max_severity'] = 'extreme'
                results['severity_score'] = 3
            elif results['severity_breakdown']['moderate']:
                results['max_severity'] = 'moderate'
                results['severity_score'] = 2
            elif results['severity_breakdown']['mild']:
                results['max_severity'] = 'mild'
                results['severity_score'] = 1
        
        logger.debug(f"Profanity detection: {results['has_profanity']}, "
                    f"words={results['word_count']}, severity={results['max_severity']}")
        
        return results
    
    def mask_profanity(self, text: str, mask_char: str = '*', 
                       keep_first_last: bool = True) -> str:
        """
        Mask profane words in text
        
        Args:
            text (str): Input text
            mask_char (str): Character to use for masking (default: *)
            keep_first_last (bool): Keep first and last character visible
        
        Returns:
            str: Text with profanity masked
        """
        masked_text = text
        
        for severity in ['extreme', 'moderate', 'mild']:
            for pattern in self.patterns[severity]:
                def replace_func(match):
                    word = match.group(0)
                    if keep_first_last and len(word) > 2:
                        return word[0] + mask_char * (len(word) - 2) + word[-1]
                    else:
                        return mask_char * len(word)
                
                masked_text = pattern.sub(replace_func, masked_text)
        
        return masked_text
    
    def remove_profanity(self, text: str, replacement: str = '[REMOVED]') -> str:
        """
        Remove profane words from text
        
        Args:
            text (str): Input text
            replacement (str): Replacement text
        
        Returns:
            str: Text with profanity removed
        """
        cleaned_text = text
        
        for severity in ['extreme', 'moderate', 'mild']:
            for pattern in self.patterns[severity]:
                cleaned_text = pattern.sub(replacement, cleaned_text)
        
        return cleaned_text
    
    def is_safe(self, text: str, max_severity: str = 'extreme') -> bool:
        """
        Check if text is safe based on severity threshold
        
        Args:
            text (str): Input text
            max_severity (str): Maximum allowed severity ('extreme', 'moderate', 'mild')
        
        Returns:
            bool: True if text is safe
        """
        detection = self.detect_profanity(text)
        
        if not detection['has_profanity']:
            return True
        
        severity_levels = {'mild': 1, 'moderate': 2, 'extreme': 3}
        max_allowed = severity_levels[max_severity]
        detected_level = detection['severity_score']
        
        return detected_level <= max_allowed
    
    def get_statistics(self, text: str) -> Dict:
        """
        Get detailed statistics about profanity in text
        
        Args:
            text (str): Input text
        
        Returns:
            dict: Detailed statistics
        """
        detection = self.detect_profanity(text)
        word_count = len(text.split())
        
        return {
            'total_words': word_count,
            'profane_words': detection['word_count'],
            'profanity_percentage': (detection['word_count'] / word_count * 100) if word_count > 0 else 0,
            'has_profanity': detection['has_profanity'],
            'severity_score': detection['severity_score'],
            'max_severity': detection['max_severity'],
            'detected_words': detection['detected_words'],
            'severity_breakdown': detection['severity_breakdown'],
            'is_safe': not detection['has_profanity'] or detection['severity_score'] == 1
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global filter instance (lazy loaded)
_global_filter = None

def get_profanity_filter(languages: Optional[List[str]] = None) -> ProfanityFilter:
    """Get or create global profanity filter instance"""
    global _global_filter
    if _global_filter is None:
        _global_filter = ProfanityFilter(languages=languages)
    return _global_filter


def contains_profanity(text: str) -> bool:
    """Quick check if text contains profanity"""
    filter_instance = get_profanity_filter()
    return filter_instance.detect_profanity(text)['has_profanity']


def censor_text(text: str, mask_char: str = '*') -> str:
    """Quick censor profanity in text"""
    filter_instance = get_profanity_filter()
    return filter_instance.mask_profanity(text, mask_char=mask_char)


def clean_text(text: str) -> str:
    """Quick remove profanity from text"""
    filter_instance = get_profanity_filter()
    return filter_instance.remove_profanity(text)


# ============================================================================
# DEMO / TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("MULTILINGUAL PROFANITY FILTER DEMO")
    print("=" * 80)
    
    # Initialize filter
    profanity_filter = ProfanityFilter()
    
    # Test cases
    test_cases = [
        ("This is a clean message", "English - Clean"),
        ("You are a stupid idiot", "English - Moderate"),
        ("What the fuck is this shit?", "English - Extreme"),
        ("Yaar ye bahut ghatiya hai, bevkoof log", "Hindi - Mixed"),
        ("तुम बहुत बेवकूफ हो", "Hindi Devanagari - Moderate"),
        ("This f**king product sucks!", "English - Obfuscated"),
        ("Great product, highly recommended!", "Clean review"),
        ("पागल मत बनाओ यार", "Hindi - Mild"),
    ]
    
    print("\n" + "=" * 80)
    print("DETECTION TESTS")
    print("=" * 80)
    
    for text, description in test_cases:
        print(f"\n{description}")
        print(f"Text: {text}")
        print("-" * 80)
        
        # Detection
        detection = profanity_filter.detect_profanity(text)
        print(f"Has Profanity: {detection['has_profanity']}")
        if detection['has_profanity']:
            print(f"Severity: {detection['max_severity']} (score: {detection['severity_score']})")
            print(f"Detected Words: {detection['detected_words']}")
            print(f"Breakdown: {detection['severity_breakdown']}")
    
    print("\n" + "=" * 80)
    print("MASKING TESTS")
    print("=" * 80)
    
    mask_tests = [
        "What the fuck is this shit?",
        "You stupid idiot!",
        "बेवकूफ मत बनाओ"
    ]
    
    for text in mask_tests:
        masked = profanity_filter.mask_profanity(text)
        removed = profanity_filter.remove_profanity(text)
        print(f"\nOriginal: {text}")
        print(f"Masked:   {masked}")
        print(f"Removed:  {removed}")
    
    print("\n" + "=" * 80)
    print("SAFETY CHECK TESTS")
    print("=" * 80)
    
    safety_tests = [
        ("Great product!", "Should be safe"),
        ("This is stupid", "Moderate - may not be safe"),
        ("What the fuck", "Extreme - not safe"),
    ]
    
    for text, expectation in safety_tests:
        is_safe_extreme = profanity_filter.is_safe(text, max_severity='extreme')
        is_safe_moderate = profanity_filter.is_safe(text, max_severity='moderate')
        print(f"\nText: {text}")
        print(f"Expectation: {expectation}")
        print(f"Safe (extreme allowed): {is_safe_extreme}")
        print(f"Safe (moderate allowed): {is_safe_moderate}")
    
    print("\n" + "=" * 80)
    print("STATISTICS TEST")
    print("=" * 80)
    
    stats_text = "This fucking product is stupid shit, what a waste!"
    stats = profanity_filter.get_statistics(stats_text)
    print(f"\nText: {stats_text}")
    print(f"Total Words: {stats['total_words']}")
    print(f"Profane Words: {stats['profane_words']}")
    print(f"Profanity %: {stats['profanity_percentage']:.1f}%")
    print(f"Max Severity: {stats['max_severity']}")
    print(f"Is Safe: {stats['is_safe']}")
    
    print("\n" + "=" * 80)
    print("CONVENIENCE FUNCTIONS TEST")
    print("=" * 80)
    
    test_text = "This is fucking awesome shit!"
    print(f"\nOriginal: {test_text}")
    print(f"Contains profanity: {contains_profanity(test_text)}")
    print(f"Censored: {censor_text(test_text)}")
    print(f"Cleaned: {clean_text(test_text)}")
    
    print("\n" + "=" * 80)
    print("PROFANITY FILTER READY FOR USE")
    print("=" * 80)
    print(f"Supported Languages: {len(ALL_BAD_WORDS_DB)}")
    print(f"Total Bad Words Database: {sum(len(words) for lang_db in ALL_BAD_WORDS_DB.values() for words in lang_db.values())}")
    print("=" * 80)
