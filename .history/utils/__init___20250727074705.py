"""
Package initialization for utils.
"""

from datetime import datetime

def get_timestamp() -> str:
    """
    Get a formatted timestamp for the current time.
    
    Returns:
        Formatted timestamp
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
