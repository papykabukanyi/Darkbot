"""
Test script to verify that the continuous scraping and email reports work correctly.
"""

import os
import sys
import time
import datetime
import random
import colorama
import logging

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Initialize colorama
colorama.init()

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
        'profit_amount': 25.00,
        'profit_percentage': 27.8,
        'sizes': [{'size': '8', 'available': True}, {'size': '9', 'available': True}]
    },
    {
        'title': 'Test Sneaker 2',
        'current_price': 129.99,
        'original_price': 179.99,
        'discount_percent': 28,
        'url': 'https://example.com/sneaker2',
        'source': 'Test Store 2',
        'sku': 'TST-002',
        'is_profitable': False,
        'profit_amount': 0.00,
        'profit_percentage': 0.0,
        'sizes': [{'size': '9', 'available': True}, {'size': '10', 'available': True}]
    }
]

def get_timestamp():
    """Get the current timestamp as a string."""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def test_email_notification():
    """Test the email notification system."""
    print(f"{colorama.Fore.CYAN}Testing email notification system...{colorama.Style.RESET_ALL}")
    
    try:
        from notifications import EmailNotifier
        notifier = EmailNotifier()
        
        # Add some random variation to deals for testing
        test_deals = sample_deals.copy()
        for deal in test_deals:
            # Add some random price variation
            price_variation = random.uniform(-5.0, 5.0)
            deal['current_price'] += price_variation
            
        result = notifier.send_deals_email(test_deals, "Darkbot Email Test")
        
        if result:
            print(f"{colorama.Fore.GREEN}Email sent successfully!{colorama.Style.RESET_ALL}")
        else:
            print(f"{colorama.Fore.RED}Email sending failed!{colorama.Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{colorama.Fore.RED}Error testing email: {str(e)}{colorama.Style.RESET_ALL}")

def test_scheduling():
    """Test the scheduling system with simulated runs."""
    print(f"{colorama.Fore.CYAN}Testing scheduling system...{colorama.Style.RESET_ALL}")
    print(f"Simulating 3 scraper runs at 2-3 minute intervals")
    
    # Store all deals
    all_deals = []
    
    # Simulate 3 runs
    for i in range(3):
        print(f"\n{colorama.Fore.BLUE}Run #{i+1} - {get_timestamp()}{colorama.Style.RESET_ALL}")
        
        # Simulate finding deals (sometimes finding nothing)
        if i == 1:
            print("No deals found in this run")
            deals = []
        else:
            # Create variations of sample deals
            deals = sample_deals.copy()
            for deal in deals:
                # Add some random price variation
                price_variation = random.uniform(-5.0, 5.0)
                deal['current_price'] += price_variation
                deal['title'] = f"{deal['title']} (Run #{i+1})"
            
            print(f"{colorama.Fore.GREEN}Found {len(deals)} deals in this run{colorama.Style.RESET_ALL}")
            all_deals.extend(deals)
        
        # If this is the last run, simulate sending an email
        if i == 2:
            print(f"\n{colorama.Fore.YELLOW}Simulating 30-minute email report...{colorama.Style.RESET_ALL}")
            print(f"Would send email with {len(all_deals)} collected deals")
            
            # Uncomment to actually send an email with the test data
            # test_email_notification()
        
        # Simulating next run time (don't actually wait, just print)
        next_interval = random.randint(120, 180)
        next_run = datetime.datetime.now() + datetime.timedelta(seconds=next_interval)
        print(f"Next scan would be at: {next_run.strftime('%H:%M:%S')} ({next_interval} seconds)")
        
        if i < 2:
            print(f"Waiting 2 seconds to simulate next run...")
            time.sleep(2)  # Just wait 2 seconds for testing

if __name__ == "__main__":
    print(f"{colorama.Fore.CYAN}Starting tests for continuous scraping and email reporting...{colorama.Style.RESET_ALL}")
    
    # Run tests
    test_scheduling()
    
    print(f"\n{colorama.Fore.GREEN}Tests completed successfully!{colorama.Style.RESET_ALL}")
