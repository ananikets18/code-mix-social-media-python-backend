"""
Centralized Logging Configuration for NLP Project
Provides structured logging with multiple levels and output formats
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
LOG_FILE = LOGS_DIR / f"nlp_pipeline_{datetime.now().strftime('%Y%m%d')}.log"
ERROR_LOG_FILE = LOGS_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.log"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color coding for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Setup a logger with file and console handlers
    
    Args:
        name (str): Logger name (usually __name__)
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file (bool): Enable file logging
        log_to_console (bool): Enable console logging
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Detailed format for file logs
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simpler format for console
    console_formatter = ColoredFormatter(
        '%(levelname)s | %(name)s | %(message)s'
    )
    
    # File handler (all logs)
    if log_to_file:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Error file handler (errors only)
    if log_to_file:
        error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get or create a logger instance
    
    Args:
        name (str): Logger name
        level (str): Logging level
    
    Returns:
        logging.Logger: Logger instance
    """
    return setup_logger(name, level)


def set_global_log_level(level: str):
    """
    Set logging level for all loggers
    
    Args:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.getLogger().setLevel(getattr(logging, level.upper()))
    print(f"📝 Global logging level set to: {level.upper()}")


# Performance monitoring decorator
def log_performance(logger: logging.Logger):
    """Decorator to log function execution time"""
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Starting {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000  # ms
                logger.debug(f"Completed {func.__name__} in {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"Failed {func.__name__} after {elapsed:.2f}ms: {e}")
                raise
        
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    # Create test logger
    logger = get_logger("test_logger", "DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print(f"\n✅ Logs written to:")
    print(f"   - All logs: {LOG_FILE}")
    print(f"   - Errors: {ERROR_LOG_FILE}")
