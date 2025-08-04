#!/usr/bin/env python
"""
Test email notification.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestEmail")

# Load environment variables
load_dotenv()

# Import after loading env variables
from notifications import EmailNotifier

def test_no_deals_notification():
    """Test sending a 'no deals found' notification."""
    logger.info("Testing 'no deals found' notification...")
    notifier = EmailNotifier()
    notifier.send_no_deals_notification()
    
def test_deals_notification():
    """Test sending deals notification with some sample deals."""
    logger.info("Testing deals notification...")
    
    # Create sample deals
    sample_deals = [
        {
            "title": "Nike Air Max 90",
            "brand": "Nike",
            "price": 120.00,
            "original_price": 160.00,
            "discount_percent": 25.0,
            "site": "Test Site",
            "url": "https://example.com/product1",
            "image_url": "https://example.com/image1.jpg",
            "profit_percentage": 33.33,
            "profit_amount": 40.0,
            "is_profitable": True
        },
        {
            "title": "Adidas Ultraboost",
            "brand": "Adidas",
            "price": 140.00,
            "original_price": 180.00,
            "discount_percent": 22.22,
            "site": "Test Site",
            "url": "https://example.com/product2",
            "image_url": "https://example.com/image2.jpg",
            "profit_percentage": 28.57,
            "profit_amount": 40.0,
            "is_profitable": True
        }
    ]
    
    notifier = EmailNotifier()
    notifier.send_deals_email(sample_deals)

if __name__ == "__main__":
    print("Email Notification Test")
    print("======================")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--deals':
        test_deals_notification()
    else:
        test_no_deals_notification()
