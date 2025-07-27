"""
Package initialization for utils.
"""

from datetime import datetime
import random
import time
import re
import logging
from typing import Dict, Any

logger = logging.getLogger("SneakerBot")

def get_timestamp() -> str:
    """
    Get a formatted timestamp for the current time.
    
    Returns:
        Formatted timestamp
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Sleep for a random amount of time to simulate human behavior.
    
    Args:
        min_seconds: Minimum sleep time in seconds
        max_seconds: Maximum sleep time in seconds
    """
    time.sleep(random.uniform(min_seconds, max_seconds))

def format_price(price: float) -> str:
    """
    Format a price value as a string.
    
    Args:
        price: Price value
        
    Returns:
        Formatted price string
    """
    return f"${price:.2f}"

def calculate_profit_potential(retail_price: float, market_price: float) -> Dict[str, Any]:
    """
    Calculate profit potential for a deal.
    
    Args:
        retail_price: Retail price
        market_price: Market price
        
    Returns:
        Dictionary with profit amount and percentage
    """
    if retail_price <= 0 or market_price <= 0:
        return {
            'profit_amount': 0,
            'profit_percentage': 0,
            'is_profitable': False
        }
    
    profit_amount = market_price - retail_price
    profit_percentage = (profit_amount / retail_price) * 100
    is_profitable = profit_percentage >= 20  # 20% threshold
    
    return {
        'profit_amount': profit_amount,
        'profit_percentage': profit_percentage,
        'is_profitable': is_profitable
    }
