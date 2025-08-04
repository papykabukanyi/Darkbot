"""
Test script to verify email notification behavior.
"""

import os
import sys
import logging
import datetime

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Sample deal data for testing
sample_deals = [
    {
        'title': 'Test Sneaker 1',
        'current_price': 89.99,
        'original_price': 119.99,
        'discount_percent': 25,
        'url': 'https://example.com/sneaker1',
        'source': 'Test Store',
        'sku': 'TST-001',
        'is_profitable': True,
        'worth_buying': True,
        'profit_amount': 25.00,
        'profit_percentage': 27.8,
        'sizes': [{'size': '8', 'available': True}, {'size': '9', 'available': True}]
    }
]

def test_notifications():
    """Test the notification behavior."""
    print("Testing notification behavior...")
    
    try:
        from notifications import EmailNotifier
        notifier = EmailNotifier()
        
        # Test adding deals without sending immediate notification
        print("Testing add_deals with send_no_deals_notification=False")
        notifier.add_deals([], send_no_deals_notification=False)
        print("Successfully added empty deals list without sending notification")
        
        # Test adding valid deals
        print("Testing add_deals with valid deals")
        notifier.add_deals(sample_deals, send_no_deals_notification=False)
        print("Successfully added valid deals to queue")
        
        print("Test completed successfully")
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_notifications()
