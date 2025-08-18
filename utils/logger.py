"""
Logger Utility Module for Healthcare Chatbot
Sets up logging configuration and formatting
"""

import os
import sys
import logging
from datetime import datetime
from loguru import logger
from config.settings import Config

def setup_logger():
    """Setup logging configuration for the healthcare chatbot"""
    
    # Remove default loguru handler
    logger.remove()
    
    # Get configuration
    config = Config()
    log_level = config.LOG_LEVEL
    log_file = config.LOG_FILE
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # File handler for all logs
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Error file handler for errors only
    error_log_file = log_file.replace('.log', '_errors.log')
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="5 MB",
        retention="90 days",
        compression="zip"
    )
    
    # Intercept standard logging
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )
    
    # Replace standard logging handlers
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set specific loggers to use loguru
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    
    logger.info("Logging system initialized successfully")
    logger.info(f"Log level set to: {log_level}")
    logger.info(f"Log file: {log_file}")

def get_logger(name: str = None):
    """Get a logger instance"""
    if name:
        return logger.bind(name=name)
    return logger

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling function: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed with error: {str(e)}")
            raise
    return wrapper

def log_performance(func):
    """Decorator to log function performance"""
    import time
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Starting function: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.debug(f"Function {func.__name__} completed in {duration:.4f} seconds")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Function {func.__name__} failed after {duration:.4f} seconds with error: {str(e)}")
            raise
    return wrapper 