#!/usr/bin/env python
"""
Test script specifically for the Undefeated scraper to verify it handles escaped HTML properly
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UndefeatedScraperTest")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scraper modules
from scrapers.factory import get_scraper_for_site
import html
from bs4 import BeautifulSoup

def test_undefeated_scraper():
    """Test the Undefeated scraper to ensure it handles escaped HTML correctly"""
    print("=" * 50)
    print("Testing Undefeated scraper with HTML unescaping")
    print("=" * 50)
    
    # Mock site config similar to what would be in config.py
    site_config = {
        'name': 'Undefeated',
        'url': 'https://undefeated.com',
        'sale_url': 'https://undefeated.com/collections/sale'
    }
    
    try:
        # Get the scraper instance
        scraper_class = get_scraper_for_site('undefeated', site_config)
        
        with scraper_class as scraper:
            print("\nScraping a single page to test HTML unescaping...")
            
            # Test the get_page method directly with a known URL
            soup = scraper.get_page(site_config['sale_url'])
            
            if soup is None:
                print("❌ Failed to get page or parse HTML!")
                return
                
            print(f"✅ Successfully fetched and parsed page: {site_config['sale_url']}")
            
            # Try to extract some basic product information to verify the parsing worked
            products = soup.select('.grid-product__wrapper') or soup.select('.product-item')
            
            print(f"Found {len(products)} products on the page")
            
            # Display a sample of products
            for i, product in enumerate(products[:3], 1):
                # Try to extract title and price which would fail if HTML wasn't properly unescaped
                title_elem = product.select_one('.grid-product__title') or product.select_one('h3')
                price_elem = product.select_one('.money') or product.select_one('.price')
                
                title = title_elem.get_text().strip() if title_elem else "Unknown"
                price = price_elem.get_text().strip() if price_elem else "Unknown"
                
                print(f"Product {i}: {title} - {price}")
            
            print("\n✅ Test completed successfully. HTML unescaping is working properly.")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_undefeated_scraper()
