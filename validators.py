"""
Type Validation and Input Validation for NLP Pipeline
Provides runtime type checking and data validation
"""

from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import inspect


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class TypeValidator:
    """Runtime type validation utility"""
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, param_name: str = "value") -> None:
        """
        Validate that value matches expected type
        
        Args:
            value: Value to validate
            expected_type: Expected type or tuple of types
            param_name: Parameter name for error messages
        
        Raises:
            ValidationError: If type doesn't match
        """
        if not isinstance(value, expected_type):
            # Handle tuple of types
            if isinstance(expected_type, tuple):
                type_names = " or ".join(t.__name__ for t in expected_type)
            else:
                type_names = expected_type.__name__
            
            raise ValidationError(
                f"Invalid type for '{param_name}': expected {type_names}, "
                f"got {type(value).__name__}"
            )
    
    @staticmethod
    def validate_string(value: Any, param_name: str = "value", 
                       min_length: Optional[int] = None,
                       max_length: Optional[int] = None,
                       allow_empty: bool = True) -> None:
        """
        Validate string with length constraints
        
        Args:
            value: Value to validate
            param_name: Parameter name for error messages
            min_length: Minimum string length
            max_length: Maximum string length
            allow_empty: Whether empty strings are allowed
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_type(value, str, param_name)
        
        if not allow_empty and len(value.strip()) == 0:
            raise ValidationError(f"'{param_name}' cannot be empty")
        
        if min_length is not None and len(value) < min_length:
            raise ValidationError(
                f"'{param_name}' must be at least {min_length} characters, "
                f"got {len(value)}"
            )
        
        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"'{param_name}' must be at most {max_length} characters, "
                f"got {len(value)}"
            )
    
    @staticmethod
    def validate_number(value: Any, param_name: str = "value",
                       min_value: Optional[float] = None,
                       max_value: Optional[float] = None) -> None:
        """
        Validate numeric value with range constraints
        
        Args:
            value: Value to validate
            param_name: Parameter name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_type(value, (int, float), param_name)
        
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"'{param_name}' must be >= {min_value}, got {value}"
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"'{param_name}' must be <= {max_value}, got {value}"
            )
    
    @staticmethod
    def validate_dict(value: Any, param_name: str = "value",
                     required_keys: Optional[List[str]] = None) -> None:
        """
        Validate dictionary with required keys
        
        Args:
            value: Value to validate
            param_name: Parameter name for error messages
            required_keys: List of required keys
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_type(value, dict, param_name)
        
        if required_keys:
            missing_keys = set(required_keys) - set(value.keys())
            if missing_keys:
                raise ValidationError(
                    f"'{param_name}' missing required keys: {missing_keys}"
                )
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], param_name: str = "value") -> None:
        """
        Validate that value is in allowed choices
        
        Args:
            value: Value to validate
            choices: List of allowed values
            param_name: Parameter name for error messages
        
        Raises:
            ValidationError: If validation fails
        """
        if value not in choices:
            raise ValidationError(
                f"'{param_name}' must be one of {choices}, got '{value}'"
            )


def validate_inputs(**validators: Callable):
    """
    Decorator to validate function inputs
    
    Usage:
        @validate_inputs(
            text=lambda x: TypeValidator.validate_string(x, "text", min_length=1),
            language=lambda x: TypeValidator.validate_string(x, "language")
        )
        def process_text(text: str, language: str):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None:  # Skip None values
                        try:
                            validator(value)
                        except ValidationError as e:
                            raise ValidationError(f"In {func.__name__}: {e}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class TextValidator:
    """Specialized validators for text processing"""
    
    @staticmethod
    def validate_text_input(text: str, min_length: int = 1, max_length: int = 10000) -> None:
        """
        Validate text input for NLP processing
        
        Args:
            text: Input text
            min_length: Minimum text length
            max_length: Maximum text length (default 10k chars)
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_string(
            text, 
            "text", 
            min_length=min_length,
            max_length=max_length,
            allow_empty=False
        )
    
    @staticmethod
    def validate_language_code(language: str) -> None:
        """
        Validate language code format
        
        Args:
            language: Language code (e.g., 'en', 'hi')
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_string(language, "language", min_length=2, max_length=3)
        
        if not language.isalpha():
            raise ValidationError(f"Language code must be alphabetic, got '{language}'")
    
    @staticmethod
    def validate_confidence(confidence: float) -> None:
        """
        Validate confidence score (0.0 to 1.0)
        
        Args:
            confidence: Confidence score
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_number(confidence, "confidence", min_value=0.0, max_value=1.0)
    
    @staticmethod
    def validate_preprocessing_mode(mode: str) -> None:
        """
        Validate preprocessing mode
        
        Args:
            mode: Preprocessing mode
        
        Raises:
            ValidationError: If validation fails
        """
        valid_modes = ['preserve', 'remove', 'convert']
        TypeValidator.validate_choice(mode, valid_modes, "mode")


class ModelValidator:
    """Validators for model inputs and outputs"""
    
    @staticmethod
    def validate_sentiment_result(result: Dict[str, Any]) -> None:
        """
        Validate sentiment prediction result
        
        Args:
            result: Sentiment prediction dictionary
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_dict(result, "sentiment_result", 
                                    required_keys=['label', 'confidence'])
        
        valid_labels = ['negative', 'neutral', 'positive']
        if result['label'] not in valid_labels:
            raise ValidationError(
                f"Invalid sentiment label: {result['label']}, "
                f"expected one of {valid_labels}"
            )
        
        TextValidator.validate_confidence(result['confidence'])
    
    @staticmethod
    def validate_toxicity_result(result: Dict[str, float]) -> None:
        """
        Validate toxicity prediction result
        
        Args:
            result: Toxicity scores dictionary
        
        Raises:
            ValidationError: If validation fails
        """
        TypeValidator.validate_dict(result, "toxicity_result")
        
        for label, score in result.items():
            TextValidator.validate_confidence(score)
    
    @staticmethod
    def validate_language_result(result: Union[str, Dict[str, Any]]) -> None:
        """
        Validate language detection result
        
        Args:
            result: Language code or detailed result dict
        
        Raises:
            ValidationError: If validation fails
        """
        if isinstance(result, str):
            TextValidator.validate_language_code(result)
        elif isinstance(result, dict):
            TypeValidator.validate_dict(result, "language_result",
                                       required_keys=['language', 'confidence'])
            TextValidator.validate_language_code(result['language'])
            TextValidator.validate_confidence(result['confidence'])
        else:
            raise ValidationError(
                f"Language result must be str or dict, got {type(result).__name__}"
            )


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("TYPE VALIDATION EXAMPLES")
    print("=" * 60)
    
    # Example 1: String validation
    print("\n1. String Validation:")
    try:
        TypeValidator.validate_string("Hello", "text", min_length=3, max_length=10)
        print("   ✅ Valid string")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    try:
        TypeValidator.validate_string("AB", "text", min_length=3)
        print("   ✅ Valid string")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    # Example 2: Number validation
    print("\n2. Number Validation:")
    try:
        TypeValidator.validate_number(0.85, "confidence", min_value=0.0, max_value=1.0)
        print("   ✅ Valid confidence score")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    try:
        TypeValidator.validate_number(1.5, "confidence", min_value=0.0, max_value=1.0)
        print("   ✅ Valid confidence score")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    # Example 3: Text validation
    print("\n3. Text Input Validation:")
    try:
        TextValidator.validate_text_input("This is a test")
        print("   ✅ Valid text input")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    try:
        TextValidator.validate_text_input("")
        print("   ✅ Valid text input")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    # Example 4: Language code validation
    print("\n4. Language Code Validation:")
    try:
        TextValidator.validate_language_code("en")
        print("   ✅ Valid language code")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    try:
        TextValidator.validate_language_code("123")
        print("   ✅ Valid language code")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    # Example 5: Sentiment result validation
    print("\n5. Sentiment Result Validation:")
    try:
        result = {'label': 'positive', 'confidence': 0.95}
        ModelValidator.validate_sentiment_result(result)
        print("   ✅ Valid sentiment result")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    try:
        result = {'label': 'happy', 'confidence': 0.95}
        ModelValidator.validate_sentiment_result(result)
        print("   ✅ Valid sentiment result")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    # Example 6: Decorator usage
    print("\n6. Decorator Validation:")
    
    @validate_inputs(
        text=lambda x: TextValidator.validate_text_input(x),
        language=lambda x: TextValidator.validate_language_code(x)
    )
    def process_text(text: str, language: str):
        return f"Processing '{text}' in {language}"
    
    try:
        result = process_text("Hello world", "en")
        print(f"   ✅ {result}")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    try:
        result = process_text("", "en")
        print(f"   ✅ {result}")
    except ValidationError as e:
        print(f"   ❌ {e}")
    
    print("\n" + "=" * 60)
    print("✅ Validation system working correctly")
    print("=" * 60)
