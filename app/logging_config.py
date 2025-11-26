import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

def setup_logging():
    """Configure logging for the application"""
    
    # Create logger
    logger = logging.getLogger("banking_service")
    logger.setLevel(logging.INFO)
    
    # Formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler for Transactions
    transaction_handler = RotatingFileHandler(
        "logs/transactions.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    transaction_handler.setFormatter(formatter)
    transaction_handler.setLevel(logging.INFO)
    logger.addHandler(transaction_handler)
    
    return logger

# Create global logger instance
logger = setup_logging()
