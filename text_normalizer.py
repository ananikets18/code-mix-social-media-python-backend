# text_normalizer.py
# Advanced text normalization for informal/social media text

import re
import unicodedata
from typing import Dict, List, Optional

# Common social media slang and abbreviations
SLANG_DICT = {
    # Common abbreviations
    'tbh': 'to be honest',
    'imo': 'in my opinion',
    'imho': 'in my humble opinion',
    'btw': 'by the way',
    'fyi': 'for your information',
    'afaik': 'as far as i know',
    'lol': 'laughing out loud',
    'lmao': 'laughing my ass off',
    'rofl': 'rolling on floor laughing',
    'omg': 'oh my god',
    'wtf': 'what the fuck',
    'brb': 'be right back',
    'idk': 'i dont know',
    'irl': 'in real life',
    'dm': 'direct message',
    'pm': 'private message',
    'rn': 'right now',
    'asap': 'as soon as possible',
    'ttyl': 'talk to you later',
    'gtg': 'got to go',
    'nvm': 'never mind',
    'smh': 'shaking my head',
    'tho': 'though',
    'pls': 'please',
    'plz': 'please',
    'thx': 'thanks',
    'ty': 'thank you',
    'np': 'no problem',
    'ikr': 'i know right',
    'jk': 'just kidding',
    'yolo': 'you only live once',
    'fomo': 'fear of missing out',
    'bae': 'before anyone else',
    'lit': 'amazing',
    'salty': 'upset',
    'goat': 'greatest of all time',
    'sus': 'suspicious',
    'lowkey': 'slightly',
    'highkey': 'very',
    'ngl': 'not gonna lie',
    'fr': 'for real',
    'ong': 'on god',
    'fax': 'facts',
    'cap': 'lie',
    'bet': 'okay',
    'mood': 'relatable',
    'vibe': 'feeling',
    'stan': 'support',
    'simp': 'overly supportive',
    
    # Internet slang
    'bc': 'because',
    'b4': 'before',
    'gr8': 'great',
    'h8': 'hate',
    'l8r': 'later',
    'm8': 'mate',
    'w8': 'wait',
    'ur': 'your',
    'u': 'you',
    'r': 'are',
    'y': 'why',
    'c': 'see',
    'k': 'okay',
    'ok': 'okay',
    'gonna': 'going to',
    'wanna': 'want to',
    'gotta': 'got to',
    'kinda': 'kind of',
    'sorta': 'sort of',
    'dunno': 'dont know',
    'lemme': 'let me',
    'gimme': 'give me',
    'woulda': 'would have',
    'coulda': 'could have',
    'shoulda': 'should have',
    
    # Hinglish slang
    'yaar': 'friend',
    'bhai': 'brother',
    'bro': 'brother',
    'sis': 'sister',
    'dude': 'person',
    'didi': 'sister',
    'bhaiya': 'brother',
    'acha': 'okay',
    'accha': 'good',
    'theek': 'okay',
    'thik': 'okay',
    'hai': 'is',
    'hain': 'are',
    'nahi': 'no',
    'nahin': 'no',
    'haan': 'yes',
    'han': 'yes',
    'kya': 'what',
    'kyu': 'why',
    'kyun': 'why',
    'kaise': 'how',
    'kaisa': 'how',
    'kab': 'when',
    'kahan': 'where',
}

# Number word mappings
NUMBER_WORDS = {
    '1st': 'first',
    '2nd': 'second',
    '3rd': 'third',
    '4th': 'fourth',
    '5th': 'fifth',
    '6th': 'sixth',
    '7th': 'seventh',
    '8th': 'eighth',
    '9th': 'ninth',
    '10th': 'tenth',
}

# Compiled patterns for performance
REPEATED_CHAR_PATTERN = re.compile(r'(.)\1{2,}')  # 3+ repeated chars
WORD_BOUNDARY_PATTERN = re.compile(r'\b(\w+)\b')
NUMBER_ORDINAL_PATTERN = re.compile(r'\b(\d+)(st|nd|rd|th)\b')
ELONGATED_WORD_PATTERN = re.compile(r'\b(\w*?)(\w)\2{2,}(\w*)\b')  # hellooo -> hello

def normalize_unicode(text: str, form: str = 'NFKC') -> str:
    """
    Normalize Unicode characters to standard form
    
    Args:
        text (str): Input text
        form (str): Normalization form (NFC, NFD, NFKC, NFKD)
        
    Returns:
        str: Normalized text
    """
    if not text:
        return ""
    
    return unicodedata.normalize(form, text)

def reduce_repeated_characters(text: str, max_repeats: int = 2) -> str:
    """
    Reduce repeated characters (hellooooo -> hello)
    
    Args:
        text (str): Input text
        max_repeats (int): Maximum allowed repetitions
        
    Returns:
        str: Text with reduced repetitions
    """
    if not text:
        return ""
    
    # Reduce 3+ consecutive chars to max_repeats
    def replacer(match):
        char = match.group(1)
        return char * max_repeats
    
    return REPEATED_CHAR_PATTERN.sub(replacer, text)

def expand_contractions(text: str) -> str:
    """
    Expand common English contractions
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with expanded contractions
    """
    if not text:
        return ""
    
    contractions = {
        "n't": " not",
        "'re": " are",
        "'s": " is",
        "'d": " would",
        "'ll": " will",
        "'ve": " have",
        "'m": " am",
        "can't": "cannot",
        "won't": "will not",
        "shan't": "shall not",
    }
    
    result = text
    for contraction, expansion in contractions.items():
        result = result.replace(contraction, expansion)
    
    return result

def expand_slang_abbreviations(text: str, preserve_case: bool = False) -> str:
    """
    Expand common slang and abbreviations
    
    Args:
        text (str): Input text
        preserve_case (bool): Whether to preserve original case
        
    Returns:
        str: Text with expanded slang
    """
    if not text:
        return ""
    
    def replace_word(match):
        word = match.group(1)
        word_lower = word.lower()
        
        if word_lower in SLANG_DICT:
            expansion = SLANG_DICT[word_lower]
            
            # Preserve case if requested
            if preserve_case and word.isupper():
                return expansion.upper()
            elif preserve_case and word[0].isupper():
                return expansion.capitalize()
            else:
                return expansion
        
        return word
    
    return WORD_BOUNDARY_PATTERN.sub(replace_word, text)

def normalize_numbers(text: str) -> str:
    """
    Normalize number formats (1st -> first, 2nd -> second)
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with normalized numbers
    """
    if not text:
        return ""
    
    def replace_ordinal(match):
        number = match.group(1)
        suffix = match.group(2)
        ordinal = f"{number}{suffix}"
        
        # Check if we have a direct mapping
        if ordinal in NUMBER_WORDS:
            return NUMBER_WORDS[ordinal]
        
        # For larger numbers, keep as is
        return ordinal
    
    return NUMBER_ORDINAL_PATTERN.sub(replace_ordinal, text)

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace (multiple spaces, tabs, newlines)
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def normalize_text_comprehensive(
    text: str,
    unicode_norm: bool = True,
    reduce_repeats: bool = True,
    expand_contract: bool = True,
    expand_slang: bool = True,
    normalize_nums: bool = True,
    normalize_ws: bool = True
) -> str:
    """
    Comprehensive text normalization with all features
    
    Args:
        text (str): Input text
        unicode_norm (bool): Apply Unicode normalization
        reduce_repeats (bool): Reduce repeated characters
        expand_contract (bool): Expand contractions
        expand_slang (bool): Expand slang and abbreviations
        normalize_nums (bool): Normalize number formats
        normalize_ws (bool): Normalize whitespace
        
    Returns:
        str: Fully normalized text
    """
    if not text:
        return ""
    
    # Apply normalizations in order
    if unicode_norm:
        text = normalize_unicode(text)
    
    if reduce_repeats:
        text = reduce_repeated_characters(text)
    
    if expand_contract:
        text = expand_contractions(text)
    
    if expand_slang:
        text = expand_slang_abbreviations(text)
    
    if normalize_nums:
        text = normalize_numbers(text)
    
    if normalize_ws:
        text = normalize_whitespace(text)
    
    return text

# Convenience function for quick normalization
def normalize(text: str, level: str = 'moderate') -> str:
    """
    Quick normalization with preset levels
    
    Args:
        text (str): Input text
        level (str): Normalization level - 'light', 'moderate', 'aggressive'
        
    Returns:
        str: Normalized text
    """
    if level == 'light':
        return normalize_text_comprehensive(
            text,
            unicode_norm=True,
            reduce_repeats=False,
            expand_contract=False,
            expand_slang=False,
            normalize_nums=False,
            normalize_ws=True
        )
    
    elif level == 'moderate':
        return normalize_text_comprehensive(
            text,
            unicode_norm=True,
            reduce_repeats=True,
            expand_contract=True,
            expand_slang=False,
            normalize_nums=True,
            normalize_ws=True
        )
    
    elif level == 'aggressive':
        return normalize_text_comprehensive(
            text,
            unicode_norm=True,
            reduce_repeats=True,
            expand_contract=True,
            expand_slang=True,
            normalize_nums=True,
            normalize_ws=True
        )
    
    else:
        return text

# Test function
def test_normalizer():
    """Test the text normalizer with various examples"""
    print("\n🔤 TEXT NORMALIZER TEST")
    print("=" * 70)
    
    test_cases = [
        "hellooooo worlddddd!!!",
        "I can't believe it's 1st time lol",
        "tbh idk what's happening rn smh",
        "u r gr8 m8 😂",
        "Gonna wanna kinda sorta maybe",
        "yaar bhai yeh kya hai?",
        "OMG this is sooooo lit fr fr 🔥",
        "Won't shouldn't couldn't",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"  Original:   {text}")
        print(f"  Light:      {normalize(text, 'light')}")
        print(f"  Moderate:   {normalize(text, 'moderate')}")
        print(f"  Aggressive: {normalize(text, 'aggressive')}")
    
    print("\n" + "=" * 70)
    print("✅ Normalization test complete!")

if __name__ == "__main__":
    test_normalizer()
