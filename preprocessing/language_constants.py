"""Language Constants and Pattern Definitions

This module contains all language mappings, regex patterns, and constant definitions
used for language detection and text processing.

Extracted from preprocessing.py for better modularity.
"""

import re

# =============================================================================
# Language Mappings
# =============================================================================

INDIAN_LANGUAGES = {
    'hi': 'Hindi', 'mr': 'Marathi', 'bn': 'Bengali', 'ta': 'Tamil',
    'te': 'Telugu', 'kn': 'Kannada', 'ml': 'Malayalam', 'gu': 'Gujarati',
    'pa': 'Punjabi', 'or': 'Odia', 'as': 'Assamese', 'sa': 'Sanskrit',
    'ne': 'Nepali', 'si': 'Sinhala', 'sd': 'Sindhi',
    'hin': 'Hindi', 'mar': 'Marathi', 'ben': 'Bengali', 'tam': 'Tamil',
    'tel': 'Telugu', 'kan': 'Kannada', 'mal': 'Malayalam', 'guj': 'Gujarati',
    'pan': 'Punjabi', 'ori': 'Odia', 'asm': 'Assamese', 'san': 'Sanskrit',
    'nep': 'Nepali', 'sin': 'Sinhala'
}

INTERNATIONAL_LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'tr': 'Turkish',
    'pl': 'Polish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish',
    'no': 'Norwegian', 'fi': 'Finnish', 'cs': 'Czech', 'hu': 'Hungarian',
    'el': 'Greek',
    'eng': 'English', 'spa': 'Spanish', 'fra': 'French', 'deu': 'German',
    'ita': 'Italian', 'por': 'Portuguese', 'rus': 'Russian', 'jpn': 'Japanese',
    'kor': 'Korean', 'zho': 'Chinese', 'ara': 'Arabic', 'tur': 'Turkish',
    'cmn': 'Chinese', 'arb': 'Arabic', 'ell': 'Greek'
}

# =============================================================================
# FIX #6: Language Code Normalization Mapping
# =============================================================================

LANGUAGE_CODE_NORMALIZATION = {
    # Hindi variants
    'hif': 'hin',      # Fiji Hindi → Standard Hindi
    'bho': 'hin',      # Bhojpuri → Hindi (closely related)
    'awa': 'hin',      # Awadhi → Hindi (dialect)
    'mag': 'hin',      # Magahi → Hindi (dialect)
    'mai': 'hin',      # Maithili → Hindi (closely related)
    
    # Urdu (close to Hindi, often interchangeable for NLP)
    'urd': 'hin',      # Urdu → Hindi (very similar, especially in romanized form)
    'ur': 'hin',       # Urdu (2-letter) → Hindi
    
    # Marathi variants
    'mr': 'mar',       # 2-letter → 3-letter
    'tcz': 'mar',      # Tagin (GLotLID misdetection for romanized Marathi)
    
    # Bengali variants
    'bn': 'ben',       # 2-letter → 3-letter
    
    # Tamil variants
    'ta': 'tam',       # 2-letter → 3-letter
    
    # Telugu variants
    'te': 'tel',       # 2-letter → 3-letter
    
    # Kannada variants
    'kn': 'kan',       # 2-letter → 3-letter
    
    # Malayalam variants
    'ml': 'mal',       # 2-letter → 3-letter
    
    # Gujarati variants
    'gu': 'guj',       # 2-letter → 3-letter
    
    # Punjabi variants
    'pa': 'pan',       # 2-letter → 3-letter
    'pnb': 'pan',      # Western Punjabi → Punjabi
    
    # Odia/Oriya variants
    'or': 'ori',       # 2-letter → 3-letter
    
    # Sindhi variants
    'sd': 'sin',       # Sindhi 2-letter → 3-letter
    'snd': 'sin',      # Sindhi variant
    
    # English variants
    'en': 'eng',       # 2-letter → 3-letter
    'en-us': 'eng',    # English US → English
    'en-gb': 'eng',    # English GB → English
    
    # Obscure/constructed languages → map to 'unknown'
    'ido': 'unknown',  # Ido (constructed language)
    'io': 'unknown',   # Ido variant
    'jbo': 'unknown',  # Lojban (constructed language)
    'lfn': 'unknown',  # Lingua Franca Nova
    'vol': 'unknown',  # Volapük
    'ia': 'unknown',   # Interlingua
    'ie': 'unknown',   # Interlingue
    'nov': 'unknown',  # Novial
    
    # Undetermined/No linguistic content
    'und': 'unknown',  # Undetermined
    'zxx': 'unknown',  # No linguistic content
    'mis': 'unknown',  # Uncoded languages
    
    # Rare languages that GLotLID might detect incorrectly
    'lua': 'unknown',  # Luba-Lulua (rare African language)
    'luo': 'unknown',  # Luo (rare African language)
    'kde': 'unknown',  # Makonde (rare)
    'kpe': 'unknown',  # Kpelle (rare)
    'kri': 'unknown',  # Krio (rare)
    'ksh': 'unknown',  # Kölsch (rare German dialect)
    'kua': 'unknown',  # Kuanyama (rare)
    'ekk': 'unknown',  # Standard Estonian
    'uzn': 'unknown',  # Northern Uzbek
}

# Reverse mapping for display names
CANONICAL_LANGUAGE_NAMES = {
    **INDIAN_LANGUAGES,
    **INTERNATIONAL_LANGUAGES,
    'unknown': 'Unknown'
}

# Obscure/constructed languages that are rarely seen in real usage
OBSCURE_LANGUAGES = [
    'ido', 'jbo', 'lfn', 'vol', 'io', 'ia', 'ie', 'nov',  # Constructed languages
    'lua', 'luo', 'kde', 'kpe', 'kri', 'ksh', 'kua',      # Very rare languages
]

# =============================================================================
# Regex Patterns
# =============================================================================

MENTION_PATTERN = re.compile(r'@\w+')
HASHTAG_PATTERN = re.compile(r'#(\w+)')
URL_PATTERN = re.compile(r'http\S+|www\.\S+')
HTML_ENTITY_PATTERN = re.compile(r'&\w+;')
WHITESPACE_PATTERN = re.compile(r'\s+')
NON_ESSENTIAL_PUNCT_PATTERN = re.compile(
    r'[^\w\s\u0900-\u097F\u0A00-\u0A7F\u0A80-\u0AFF\u0B00-\u0B7F\u0B80-\u0BFF'
    r'\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F\u0D80-\u0DFF\u0E00-\u0E7F'
    r'\u0F00-\u0FFF\.\!\?]'
)

# =============================================================================
# Romanized Indian Language Patterns
# =============================================================================

ROMANIZED_INDIAN_PATTERNS = {
    'marathi': [
        r'\b(ahe|ahes|aahe|aahes|ahet|ahot)\b',
        r'\b(khup|khoop|khupach)\b',
        r'\b(mhanje|mhanun|mhanoon|mhantoy)\b',
        r'\b(bolat|bolta|bolto|bolte|boltes)\b',
        r'\b(chukicha|chukla|chuk|chukicha)\b',
        r'\b(bhet|bheta|bhetla|bheto)\b',
        r'\b(chup|choop|chupchap)\b',
        r'\b(tu|mi|me|mala|tula|tyala|tila|aapan|aamhi|tumhi)\b',
        r'\b(kashala|kasa|kase|kay|kuthay|kevha)\b',
        r'\b(sangu|sang|sanga|sangtoy)\b',
        r'\b(yenar|yeil|yete|yeto)\b',
        r'\b(ghari|ghara|gharun)\b',
        r'\b(kal|aaj|udya)\b',
        r'\b(thik|thiik|bara)\b',
        r'\b(nako|nakos)\b',
        # FIX: Enhanced verb patterns - added future tense variations
        r'\b(honar|hotay|hota|hoti|hoin|hoeil|hoel|hoil|hoeen|hoet)\b',
        r'\b(zala|zali|zale|zalya|jhala|jhali|jhale)\b',  # happened/became
        r'\b(pahije|paahije|pahijet|pahijela)\b',  # needed/should
        r'\b(aikla|aiklay|aiklas|aikle|aiku|aikun)\b',  # heard/listened
        r'\b(la|var|madhye)\b',
    ],
    'hindi': [
        r'\b(hai|hain|hoon|ho|hoga|hogi)\b',
        r'\b(bahut|bohot|bahoot|bahoth)\b',
        r'\b(kar|kara|karte|karti|karo|karenge)\b',
        r'\b(achha|accha|acha|achhe)\b',
        r'\b(chalo|chala|chale|chalte|chalenge)\b',
        r'\b(main|mein|mai|hum|tum|tumhe|tumhare)\b',
        r'\b(mujhe|mujhko|hamko|hamara)\b',
        r'\b(kya|kaise|kese|kyun|kyon|kab|kaha|kahan)\b',
        r'\b(yaar|yaara|yar|bhai|bhaiya)\b',
        r'\b(dekh|dekha|dekho|dekhte|dekhenge)\b',
        r'\b(bol|bola|bolo|bolte|bolenge)\b',
        r'\b(thik|theek|thiik)\b',
        r'\b(abhi|ab|phir|fir)\b',
        r'\b(jaana|jana|jao|jaate|jayenge|jaa|jaa raha|jaa rahe)\b',
        r'\b(aana|ana|aao|aate|aayenge)\b',
        r'\b(ye|yeh|vo|voh|woh|yahi|wohi)\b',
        r'\b(mast|mazaa|maja|bindass|kamaal|zabardast)\b',
    ],
    'tamil': [
        # Pronouns
        r'\b(naan|naa|nee|neengal|avan|aval|avar|avanga)\b',
        # Common verbs with present/past/future markers
        r'\b(ren|ran|raan|raal|raar|rom|ranga|raanga)\b',
        r'\b(tten|ten|then|ttu|chu|dhu|ttom|tanga|ttanga)\b',
        r'\b(ven|veen|ppen|ppom|vom|venga|ppanga|vaanga)\b',
        # Common Tamil verbs
        r'\b(pathukaren|paathukkaren|poi|poren|varen|pannuren|pannuven)\b',
        r'\b(mudichiduven|mudichidaren|mudichitten|theduren|thedi)\b',
        r'\b(irukku|irukkum|irundhuchu|pannu|panna|po|poga|vaa|vara)\b',
        r'\b(sollu|solla|paaru|paakka|kelu|saapidu)\b',
        # Tamil-specific words
        r'\b(ippo|ippodhu|inniki|innaiku|naalai|nethu|appuram)\b',
        r'\b(romba|rombha|konjam|koncham|enna|yenna|epdi|eppadi)\b',
        r'\b(illa|illai|mudiyaathu|vendam|venda|aam|aama|seri)\b',
        # Tamil particles and connectors
        r'\b(dhan|dhaan|than|thaan|nu|nnu|oda|kuda|kooda)\b',
        r'\b(lendhu|lerndhu|kku|ku|la|le|layum)\b',
        # Tamil question words
        r'\b(enga|yeppodhu|yen|evlo|yaaru|yaar)\b',
    ],
    'generic_indic': [
        r'\b(nahi|nahin|na|nai|nay)\b',
        r'\b(tha|thi|the|thee)\b',
        r'\b(ka|ki|ke|ko|ka|ki)\b',
        r'\b(se|sai|say)\b',
        r'\b(par|pe|pe)\b',
    ]
}

# =============================================================================
# English Word Detection Patterns (FIX #10)
# =============================================================================

# Common English words for token detection (top 500 most frequent words)
COMMON_ENGLISH_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
    'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
    'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
    'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us',
    'is', 'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did', 'having',
    'may', 'should', 'am', 'being', 'might', 'must', 'shall', 'could', 'would',
    'very', 'much', 'many', 'more', 'such', 'long', 'same', 'through', 'between',
    'find', 'man', 'here', 'thing', 'give', 'many', 'well', 'every', 'much', 'own',
    'say', 'part', 'place', 'case', 'week', 'company', 'where', 'system', 'think',
    'each', 'person', 'point', 'hand', 'high', 'follow', 'act', 'why', 'ask', 'try',
    'need', 'feel', 'become', 'leave', 'put', 'mean', 'keep', 'let', 'begin', 'seem',
    'help', 'talk', 'turn', 'start', 'show', 'hear', 'play', 'run', 'move', 'live',
    'believe', 'hold', 'bring', 'happen', 'write', 'provide', 'sit', 'stand', 'lose',
    'pay', 'meet', 'include', 'continue', 'set', 'learn', 'change', 'lead', 'understand',
    'watch', 'far', 'call', 'ask', 'may', 'end', 'among', 'ever', 'across', 'although',
    'both', 'under', 'last', 'never', 'before', 'always', 'several', 'until', 'away',
    'something', 'fact', 'less', 'though', 'far', 'put', 'head', 'yet', 'government',
    'number', 'night', 'another', 'mr', 'mrs', 'miss', 'ms', 'dr', 'sir', 'madam',
    'yeah', 'yes', 'no', 'ok', 'okay', 'hi', 'hello', 'bye', 'thanks', 'please',
    'really', 'actually', 'basically', 'literally', 'totally', 'definitely', 'probably',
    'obviously', 'generally', 'usually', 'normally', 'typically', 'mostly', 'mainly',
    'right', 'wrong', 'true', 'false', 'big', 'small', 'great', 'little', 'old', 'young',
    'next', 'few', 'public', 'bad', 'able', 'late', 'hard', 'real', 'best', 'better',
    'traffic', 'heavy', 'today', 'tomorrow', 'yesterday', 'morning', 'evening', 'night',
    'meeting', 'office', 'start', 'wait', 'finish', 'complete', 'done', 'ready', 'busy',
    'free', 'available', 'schedule', 'appointment', 'conference', 'call', 'email', 'message',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'january', 'february', 'march', 'april', 'june', 'july', 'august', 'september',
    'october', 'november', 'december', 'am', 'pm', 'going', 'coming', 'doing', 'making',
    'taking', 'seeing', 'looking', 'feeling', 'thinking', 'trying', 'working', 'playing'
}

# English-specific patterns
ENGLISH_PATTERNS = {
    'contractions': re.compile(r"\b(don't|won't|can't|isn't|aren't|wasn't|weren't|hasn't|haven't|hadn't|doesn't|didn't|i'm|you're|he's|she's|it's|we're|they're|i'll|you'll|he'll|she'll|we'll|they'll|i've|you've|we've|they've|i'd|you'd|he'd|she'd|we'd|they'd)\b", re.IGNORECASE),
    'suffixes': re.compile(r'\b\w+(ing|ed|ly|er|est|tion|sion|ness|ment|ful|less|able|ible|ous|ious|ive|al|ial)\b', re.IGNORECASE),
    'all_caps': re.compile(r'\b[A-Z]{2,}\b'),  # Acronyms like USA, OK, ASAP
}
