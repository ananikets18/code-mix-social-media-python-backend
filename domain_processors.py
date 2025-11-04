"""
Domain-Specific Text Processing
Handles financial, date/time, and technical text with specialized processing
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
from logger_config import get_logger
from validators import TextValidator, validate_inputs, ValidationError

logger = get_logger(__name__)

# ============================================================================
# FINANCIAL TEXT PROCESSING
# ============================================================================

class FinancialTextProcessor:
    """
    Processes financial text including currencies, amounts, percentages, etc.
    Handles multiple currency formats and financial terminology
    """
    
    # Currency symbols and codes
    CURRENCY_SYMBOLS = {
        '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR',
        '₽': 'RUB', '₩': 'KRW', '₪': 'ILS', '₦': 'NGN', '₨': 'PKR',
        'Rs': 'INR', 'Rs.': 'INR', '₨.': 'PKR'
    }
    
    CURRENCY_CODES = [
        'USD', 'EUR', 'GBP', 'JPY', 'INR', 'CNY', 'AUD', 'CAD', 'CHF',
        'RUB', 'KRW', 'BRL', 'ZAR', 'MXN', 'SGD', 'HKD', 'SEK', 'NOK'
    ]
    
    # Financial patterns (compiled for performance)
    CURRENCY_AMOUNT_PATTERN = re.compile(
        r'(?P<symbol>[₹$€£¥₽₩₪₦₨]|Rs\.?|INR|USD|EUR|GBP)\s*'
        r'(?P<amount>[\d,]+\.?\d*)\s*'
        r'(?P<unit>K|M|B|T|thousand|million|billion|trillion|lakh|crore)?',
        re.IGNORECASE
    )
    
    PERCENTAGE_PATTERN = re.compile(r'(\d+\.?\d*)\s*%')
    
    STOCK_TICKER_PATTERN = re.compile(r'\b[A-Z]{2,5}\b(?=\s|$|[,.])')
    
    FINANCIAL_TERMS = {
        # Market terms
        'bull market', 'bear market', 'dividend', 'equity', 'stock',
        'bond', 'portfolio', 'investment', 'capital', 'liquidity',
        'volatility', 'market cap', 'p/e ratio', 'roi', 'rsi',
        
        # Banking terms
        'interest rate', 'apr', 'loan', 'mortgage', 'deposit',
        'withdrawal', 'transfer', 'balance', 'overdraft', 'credit',
        
        # Trading terms
        'buy', 'sell', 'trade', 'bid', 'ask', 'spread', 'volume',
        'option', 'future', 'derivative', 'hedge', 'arbitrage',
        
        # Analysis terms
        'profit', 'loss', 'revenue', 'earnings', 'ebitda', 'cash flow',
        'debt', 'asset', 'liability', 'margin', 'yield', 'return'
    }
    
    @staticmethod
    def normalize_currency(text: str, mode: str = 'preserve') -> str:
        """
        Normalize currency mentions in text
        
        Args:
            text (str): Input text
            mode (str): 'preserve', 'expand', or 'remove'
                - preserve: Keep original format
                - expand: Convert to full form (e.g., "$100K" → "100 thousand USD")
                - remove: Remove currency mentions
        
        Returns:
            str: Normalized text
        """
        if mode == 'remove':
            return FinancialTextProcessor.CURRENCY_AMOUNT_PATTERN.sub('', text)
        
        if mode == 'expand':
            def expand_currency(match):
                symbol = match.group('symbol')
                amount = match.group('amount').replace(',', '')
                unit = match.group('unit') or ''
                
                # Get currency code
                currency = FinancialTextProcessor.CURRENCY_SYMBOLS.get(symbol, symbol)
                
                # Expand unit
                unit_map = {
                    'K': 'thousand', 'M': 'million', 'B': 'billion', 'T': 'trillion',
                    'lakh': 'lakh', 'crore': 'crore'
                }
                unit_text = unit_map.get(unit.upper(), unit.lower()) if unit else ''
                
                # Build expanded form
                parts = [amount]
                if unit_text:
                    parts.append(unit_text)
                parts.append(currency)
                
                return ' '.join(parts)
            
            return FinancialTextProcessor.CURRENCY_AMOUNT_PATTERN.sub(expand_currency, text)
        
        # preserve mode
        return text
    
    @staticmethod
    def extract_financial_entities(text: str) -> Dict[str, List[str]]:
        """
        Extract financial entities from text
        
        Args:
            text (str): Input text
        
        Returns:
            dict: Extracted entities by type
        """
        entities = {
            'currencies': [],
            'amounts': [],
            'percentages': [],
            'tickers': [],
            'terms': []
        }
        
        # Extract currency amounts
        for match in FinancialTextProcessor.CURRENCY_AMOUNT_PATTERN.finditer(text):
            symbol = match.group('symbol')
            amount = match.group('amount')
            unit = match.group('unit') or ''
            
            currency = FinancialTextProcessor.CURRENCY_SYMBOLS.get(symbol, symbol)
            entities['currencies'].append(currency)
            entities['amounts'].append(f"{amount}{unit}")
        
        # Extract percentages
        for match in FinancialTextProcessor.PERCENTAGE_PATTERN.finditer(text):
            entities['percentages'].append(match.group(1) + '%')
        
        # Extract stock tickers (simple heuristic)
        potential_tickers = FinancialTextProcessor.STOCK_TICKER_PATTERN.findall(text)
        entities['tickers'] = [t for t in potential_tickers if len(t) >= 2]
        
        # Extract financial terms
        text_lower = text.lower()
        for term in FinancialTextProcessor.FINANCIAL_TERMS:
            if term in text_lower:
                entities['terms'].append(term)
        
        logger.debug(f"Extracted financial entities: {len(entities['amounts'])} amounts, "
                    f"{len(entities['percentages'])} percentages")
        
        return entities
    
    @staticmethod
    def is_financial_text(text: str, threshold: float = 0.15) -> bool:
        """
        Detect if text is financial/business related
        
        Args:
            text (str): Input text
            threshold (float): Minimum ratio of financial indicators (default 0.15 = 15%)
        
        Returns:
            bool: True if likely financial text
        """
        entities = FinancialTextProcessor.extract_financial_entities(text)
        
        # Count financial indicators
        indicators = (
            len(entities['currencies']) +
            len(entities['amounts']) +
            len(entities['percentages']) +
            len(entities['terms'])
        )
        
        # Calculate ratio
        words = len(text.split())
        if words == 0:
            return False
        
        ratio = indicators / words
        is_financial = ratio >= threshold
        
        logger.debug(f"Financial text detection: {ratio:.2%} >= {threshold:.0%} = {is_financial}")
        return is_financial


# ============================================================================
# DATE/TIME TEXT PROCESSING
# ============================================================================

class DateTimeProcessor:
    """
    Processes date and time mentions with multiple format support
    Handles relative dates, absolute dates, and time expressions
    """
    
    # Date patterns
    DATE_PATTERNS = {
        'iso': re.compile(r'\b\d{4}-\d{2}-\d{2}\b'),  # 2024-11-02
        'us': re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'),  # 11/02/2024
        'eu': re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b'),  # 02.11.2024
        'written': re.compile(
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',
            re.IGNORECASE
        ),  # November 2, 2024
        'indian': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')  # 02-11-2024
    }
    
    # Time patterns
    TIME_PATTERNS = {
        '24h': re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\b'),  # 14:30 or 14:30:00
        '12h': re.compile(r'\b\d{1,2}:\d{2}\s*(?:AM|PM)\b', re.IGNORECASE),  # 2:30 PM
    }
    
    # Relative date patterns
    RELATIVE_PATTERNS = {
        'days': re.compile(
            r'\b(?:yesterday|today|tomorrow|day before yesterday|day after tomorrow)\b',
            re.IGNORECASE
        ),
        'relative': re.compile(
            r'\b(?:last|next|this)\s+(?:week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            re.IGNORECASE
        ),
        'ago': re.compile(r'\b(\d+)\s+(day|week|month|year)s?\s+ago\b', re.IGNORECASE),
        'in': re.compile(r'\bin\s+(\d+)\s+(day|week|month|year)s?\b', re.IGNORECASE)
    }
    
    MONTHS = [
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december'
    ]
    
    DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    @staticmethod
    def normalize_dates(text: str, mode: str = 'preserve', format: str = 'iso') -> str:
        """
        Normalize date mentions in text
        
        Args:
            text (str): Input text
            mode (str): 'preserve', 'normalize', or 'remove'
            format (str): Target format ('iso', 'us', 'written')
        
        Returns:
            str: Normalized text
        """
        if mode == 'remove':
            result = text
            for pattern in DateTimeProcessor.DATE_PATTERNS.values():
                result = pattern.sub('', result)
            return result
        
        if mode == 'normalize':
            # For now, just mark dates (full normalization requires parsing)
            result = text
            for name, pattern in DateTimeProcessor.DATE_PATTERNS.items():
                result = pattern.sub(f'[DATE:{name.upper()}]', result)
            return result
        
        # preserve mode
        return text
    
    @staticmethod
    def extract_temporal_entities(text: str) -> Dict[str, List[str]]:
        """
        Extract date/time entities from text
        
        Args:
            text (str): Input text
        
        Returns:
            dict: Extracted temporal entities
        """
        entities = {
            'dates': [],
            'times': [],
            'relative_dates': [],
            'months': [],
            'days': []
        }
        
        # Extract dates
        for name, pattern in DateTimeProcessor.DATE_PATTERNS.items():
            matches = pattern.findall(text)
            entities['dates'].extend([(m, name) for m in matches])
        
        # Extract times
        for name, pattern in DateTimeProcessor.TIME_PATTERNS.items():
            matches = pattern.findall(text)
            entities['times'].extend([(m, name) for m in matches])
        
        # Extract relative dates
        for name, pattern in DateTimeProcessor.RELATIVE_PATTERNS.items():
            matches = pattern.findall(text)
            if name in ['ago', 'in']:
                # These return tuples (number, unit)
                entities['relative_dates'].extend([f"{m[0]} {m[1]}s {name}" for m in matches])
            else:
                entities['relative_dates'].extend([m if isinstance(m, str) else m[0] for m in matches])
        
        # Extract month mentions
        text_lower = text.lower()
        for month in DateTimeProcessor.MONTHS:
            if month in text_lower:
                entities['months'].append(month)
        
        # Extract day mentions
        for day in DateTimeProcessor.DAYS:
            if day in text_lower:
                entities['days'].append(day)
        
        logger.debug(f"Extracted temporal entities: {len(entities['dates'])} dates, "
                    f"{len(entities['times'])} times, {len(entities['relative_dates'])} relative")
        
        return entities
    
    @staticmethod
    def is_temporal_text(text: str, threshold: float = 0.10) -> bool:
        """
        Detect if text contains significant temporal information
        
        Args:
            text (str): Input text
            threshold (float): Minimum ratio of temporal indicators (default 0.10 = 10%)
        
        Returns:
            bool: True if likely temporal text
        """
        entities = DateTimeProcessor.extract_temporal_entities(text)
        
        indicators = (
            len(entities['dates']) +
            len(entities['times']) +
            len(entities['relative_dates'])
        )
        
        words = len(text.split())
        if words == 0:
            return False
        
        ratio = indicators / words
        is_temporal = ratio >= threshold
        
        logger.debug(f"Temporal text detection: {ratio:.2%} >= {threshold:.0%} = {is_temporal}")
        return is_temporal


# ============================================================================
# TECHNICAL TEXT PROCESSING
# ============================================================================

class TechnicalTextProcessor:
    """
    Processes technical text including code, formulas, units, etc.
    Handles programming languages, scientific notation, technical terms
    """
    
    # Code patterns
    CODE_PATTERNS = {
        'function': re.compile(r'\b\w+\s*\([^)]*\)'),  # function_name(args)
        'variable': re.compile(r'\b[a-z_][a-z0-9_]*\b', re.IGNORECASE),
        'camelCase': re.compile(r'\b[a-z]+(?:[A-Z][a-z]*)+\b'),
        'snake_case': re.compile(r'\b[a-z]+(?:_[a-z]+)+\b'),
        'CONSTANT': re.compile(r'\b[A-Z][A-Z0-9_]+\b'),
    }
    
    # Scientific notation
    SCIENTIFIC_NOTATION = re.compile(r'\b\d+\.?\d*[eE][+-]?\d+\b')
    
    # Units (SI and common)
    UNITS_PATTERN = re.compile(
        r'\b(\d+\.?\d*)\s*(km|m|cm|mm|kg|g|mg|L|mL|s|ms|Hz|kHz|MHz|GHz|'
        r'MB|GB|TB|KB|Mbps|Gbps|V|A|W|°C|°F|K|Pa|kPa|MPa)\b'
    )
    
    # Programming keywords (common across languages)
    PROGRAMMING_KEYWORDS = {
        'if', 'else', 'for', 'while', 'return', 'function', 'def', 'class',
        'import', 'from', 'try', 'catch', 'except', 'finally', 'async', 'await',
        'const', 'let', 'var', 'public', 'private', 'static', 'void',
        'int', 'float', 'string', 'bool', 'array', 'list', 'dict', 'map'
    }
    
    # Technical domains
    TECH_DOMAINS = {
        'programming': {
            'algorithm', 'data structure', 'api', 'database', 'frontend',
            'backend', 'server', 'client', 'http', 'rest', 'json', 'xml',
            'debugging', 'testing', 'deployment', 'git', 'version control'
        },
        'ai_ml': {
            'machine learning', 'deep learning', 'neural network', 'ai',
            'model', 'training', 'inference', 'dataset', 'accuracy', 'loss',
            'gradient', 'backpropagation', 'transformer', 'lstm', 'cnn'
        },
        'engineering': {
            'voltage', 'current', 'resistance', 'circuit', 'transistor',
            'frequency', 'amplitude', 'signal', 'noise', 'filter', 'amplifier'
        },
        'science': {
            'hypothesis', 'experiment', 'theory', 'data', 'analysis',
            'measurement', 'error', 'precision', 'accuracy', 'validation'
        }
    }
    
    @staticmethod
    def normalize_code(text: str, mode: str = 'preserve') -> str:
        """
        Normalize code snippets in text
        
        Args:
            text (str): Input text
            mode (str): 'preserve', 'placeholder', or 'remove'
        
        Returns:
            str: Normalized text
        """
        if mode == 'remove':
            result = text
            # Remove code-like patterns
            result = TechnicalTextProcessor.CODE_PATTERNS['function'].sub('', result)
            return result
        
        if mode == 'placeholder':
            # Replace code with placeholders
            result = TechnicalTextProcessor.CODE_PATTERNS['function'].sub('[FUNCTION]', text)
            result = TechnicalTextProcessor.SCIENTIFIC_NOTATION.sub('[SCIENTIFIC_NUMBER]', result)
            return result
        
        # preserve mode
        return text
    
    @staticmethod
    def extract_technical_entities(text: str) -> Dict[str, List[str]]:
        """
        Extract technical entities from text
        
        Args:
            text (str): Input text
        
        Returns:
            dict: Extracted technical entities
        """
        entities = {
            'functions': [],
            'variables': [],
            'units': [],
            'scientific_numbers': [],
            'keywords': [],
            'domains': []
        }
        
        # Extract function calls
        entities['functions'] = TechnicalTextProcessor.CODE_PATTERNS['function'].findall(text)
        
        # Extract scientific notation
        entities['scientific_numbers'] = TechnicalTextProcessor.SCIENTIFIC_NOTATION.findall(text)
        
        # Extract measurements with units
        for match in TechnicalTextProcessor.UNITS_PATTERN.finditer(text):
            entities['units'].append(f"{match.group(1)} {match.group(2)}")
        
        # Extract programming keywords
        text_lower = text.lower()
        for keyword in TechnicalTextProcessor.PROGRAMMING_KEYWORDS:
            if f' {keyword} ' in f' {text_lower} ':
                entities['keywords'].append(keyword)
        
        # Detect technical domains
        for domain, terms in TechnicalTextProcessor.TECH_DOMAINS.items():
            for term in terms:
                if term in text_lower:
                    if domain not in entities['domains']:
                        entities['domains'].append(domain)
        
        logger.debug(f"Extracted technical entities: {len(entities['functions'])} functions, "
                    f"{len(entities['units'])} units, {len(entities['keywords'])} keywords")
        
        return entities
    
    @staticmethod
    def is_technical_text(text: str, threshold: float = 0.15) -> bool:
        """
        Detect if text is technical/programming related
        
        Args:
            text (str): Input text
            threshold (float): Minimum ratio of technical indicators
        
        Returns:
            bool: True if likely technical text
        """
        entities = TechnicalTextProcessor.extract_technical_entities(text)
        
        indicators = (
            len(entities['functions']) +
            len(entities['keywords']) * 2 +  # Keywords are strong indicators
            len(entities['scientific_numbers']) +
            len(entities['units'])
        )
        
        words = len(text.split())
        if words == 0:
            return False
        
        ratio = indicators / words
        is_technical = ratio >= threshold
        
        logger.debug(f"Technical text detection: {ratio:.2%} >= {threshold:.0%} = {is_technical}")
        return is_technical


# ============================================================================
# UNIFIED DOMAIN PROCESSOR
# ============================================================================

class DomainProcessor:
    """
    Unified processor for domain-specific text handling
    Combines financial, temporal, and technical processing
    """
    
    @staticmethod
    def detect_domains(text: str) -> Dict[str, bool]:
        """
        Detect all relevant domains in text
        
        Args:
            text (str): Input text
        
        Returns:
            dict: Domain detection results
        """
        return {
            'financial': FinancialTextProcessor.is_financial_text(text),
            'temporal': DateTimeProcessor.is_temporal_text(text),
            'technical': TechnicalTextProcessor.is_technical_text(text)
        }
    
    @staticmethod
    def process_domain_text(
        text: str,
        financial_mode: str = 'preserve',
        temporal_mode: str = 'preserve',
        technical_mode: str = 'preserve'
    ) -> str:
        """
        Process text with domain-specific handling
        
        Args:
            text (str): Input text
            financial_mode (str): How to handle financial text
            temporal_mode (str): How to handle temporal text
            technical_mode (str): How to handle technical text
        
        Returns:
            str: Processed text
        """
        logger.info("Processing domain-specific text")
        
        # Apply domain-specific processing
        result = text
        
        # Financial processing
        if financial_mode != 'preserve':
            result = FinancialTextProcessor.normalize_currency(result, financial_mode)
        
        # Temporal processing
        if temporal_mode != 'preserve':
            result = DateTimeProcessor.normalize_dates(result, temporal_mode)
        
        # Technical processing
        if technical_mode != 'preserve':
            result = TechnicalTextProcessor.normalize_code(result, technical_mode)
        
        logger.info(f"Domain processing complete (financial={financial_mode}, "
                   f"temporal={temporal_mode}, technical={technical_mode})")
        
        return result
    
    @staticmethod
    def extract_all_entities(text: str) -> Dict[str, Dict]:
        """
        Extract all domain-specific entities
        
        Args:
            text (str): Input text
        
        Returns:
            dict: All extracted entities by domain
        """
        return {
            'financial': FinancialTextProcessor.extract_financial_entities(text),
            'temporal': DateTimeProcessor.extract_temporal_entities(text),
            'technical': TechnicalTextProcessor.extract_technical_entities(text)
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("DOMAIN-SPECIFIC TEXT PROCESSING DEMO")
    print("=" * 80)
    
    # Financial text example
    print("\n1️⃣  FINANCIAL TEXT")
    print("-" * 80)
    financial_text = "Apple stock rose 5% to $150.25, with market cap reaching $2.5T. The company reported Q3 earnings of ₹1,250 crore."
    print(f"Text: {financial_text}")
    print(f"\nIs financial: {FinancialTextProcessor.is_financial_text(financial_text)}")
    
    entities = FinancialTextProcessor.extract_financial_entities(financial_text)
    print(f"Currencies: {entities['currencies']}")
    print(f"Amounts: {entities['amounts']}")
    print(f"Percentages: {entities['percentages']}")
    
    # Date/time example
    print("\n2️⃣  DATE/TIME TEXT")
    print("-" * 80)
    temporal_text = "Meeting scheduled for 2024-11-15 at 14:30. The project deadline is next Friday."
    print(f"Text: {temporal_text}")
    print(f"\nIs temporal: {DateTimeProcessor.is_temporal_text(temporal_text)}")
    
    entities = DateTimeProcessor.extract_temporal_entities(temporal_text)
    print(f"Dates: {entities['dates']}")
    print(f"Times: {entities['times']}")
    print(f"Relative: {entities['relative_dates']}")
    
    # Technical text example
    print("\n3️⃣  TECHNICAL TEXT")
    print("-" * 80)
    technical_text = "The algorithm processes data at 1.5e6 ops/sec. Use function calculate_mean() with array of 1000 values."
    print(f"Text: {technical_text}")
    print(f"\nIs technical: {TechnicalTextProcessor.is_technical_text(technical_text)}")
    
    entities = TechnicalTextProcessor.extract_technical_entities(technical_text)
    print(f"Functions: {entities['functions']}")
    print(f"Scientific numbers: {entities['scientific_numbers']}")
    print(f"Keywords: {entities['keywords']}")
    
    print("\n" + "=" * 80)
    print("✅ Domain processing functional!")
    print("=" * 80)
