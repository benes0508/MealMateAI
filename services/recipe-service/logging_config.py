#!/usr/bin/env python3
"""
Centralized logging configuration for Recipe Service
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m'   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging(
    name: str = "recipe-service",
    level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True
):
    """
    Setup comprehensive logging configuration
    
    Args:
        name: Logger name (used for log file naming)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output to console
        file_output: Whether to output to log files
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)
    
    if file_output:
        # Generate timestamp for session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Main log file (INFO and above)
        main_log_file = LOGS_DIR / f"{name}_{timestamp}.log"
        main_handler = logging.FileHandler(main_log_file)
        main_handler.setLevel(logging.INFO)
        main_handler.setFormatter(detailed_formatter)
        logger.addHandler(main_handler)
        
        # Debug log file (ALL messages)
        debug_log_file = LOGS_DIR / f"{name}_debug_{timestamp}.log"
        debug_handler = logging.FileHandler(debug_log_file)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(detailed_formatter)
        logger.addHandler(debug_handler)
        
        # Error log file (ERROR and CRITICAL only)
        error_log_file = LOGS_DIR / f"{name}_errors_{timestamp}.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
        
        # Latest symlinks for easy access
        try:
            latest_main = LOGS_DIR / f"{name}_latest.log"
            latest_debug = LOGS_DIR / f"{name}_debug_latest.log"
            latest_error = LOGS_DIR / f"{name}_errors_latest.log"
            
            # Remove existing symlinks
            for symlink in [latest_main, latest_debug, latest_error]:
                if symlink.is_symlink() or symlink.exists():
                    symlink.unlink()
            
            # Create new symlinks
            latest_main.symlink_to(main_log_file.name)
            latest_debug.symlink_to(debug_log_file.name)
            latest_error.symlink_to(error_log_file.name)
            
        except Exception as e:
            # Symlink creation might fail on some systems, that's OK
            pass
    
    return logger

def get_session_logger(name: str = None) -> logging.Logger:
    """Get or create a session logger"""
    logger_name = name or "recipe-service"
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        setup_logging(logger_name)
    
    return logger

class LogCapture:
    """Context manager to capture print statements and redirect to logger"""
    
    def __init__(self, logger: logging.Logger, level: int = logging.INFO):
        self.logger = logger
        self.level = level
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def write(self, message):
        # Log non-empty messages
        if message.strip():
            self.logger.log(self.level, message.strip())
        # Also write to original stdout for immediate feedback
        self.original_stdout.write(message)
        
    def flush(self):
        self.original_stdout.flush()

# Example usage functions
def log_system_info(logger: logging.Logger):
    """Log system and environment information"""
    logger.info("=== SYSTEM INFORMATION ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.executable}")
    
    # Environment variables
    logger.info("=== ENVIRONMENT VARIABLES ===")
    relevant_vars = ['GOOGLE_API_KEY', 'QDRANT_URL', 'DATABASE_URL']
    for var in relevant_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                masked = value[:8] + '...' if len(value) > 8 else '***'
                logger.info(f"{var}: {masked}")
            else:
                logger.info(f"{var}: {value}")
        else:
            logger.info(f"{var}: Not set")

def log_dependencies(logger: logging.Logger):
    """Log installed package versions"""
    logger.info("=== PACKAGE VERSIONS ===")
    
    packages = [
        'fastapi', 'uvicorn', 'httpx', 'qdrant-client', 
        'sentence-transformers', 'google-genai', 'torch'
    ]
    
    for package in packages:
        try:
            module = __import__(package.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            logger.info(f"{package}: {version}")
        except ImportError:
            logger.warning(f"{package}: Not installed")
        except Exception as e:
            logger.warning(f"{package}: Error getting version - {e}")

if __name__ == "__main__":
    # Test the logging system
    logger = setup_logging("test", level="DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test print capture
    with LogCapture(logger):
        print("This print statement will be logged!")
        
    log_system_info(logger)
    log_dependencies(logger)
    
    print(f"Logs written to: {LOGS_DIR}")