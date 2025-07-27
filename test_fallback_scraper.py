#!/usr/bin/env python3
"""
Test script to verify the fallback scraper works.
"""

import sys
import logging
import argparse
from config import SNEAKER_SITES
from scrapers.factory import get_scraper_for_site

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TEST")

def parse_args():
    parser = argparse.ArgumentParser(description="Test the fallback scraper")
    parser.add_argument("--site", required=True, help="Site to test")
    return parser.parse_args()

def main():
    args = parse_args()
    site_name = args.site
    
    print(f"Testing factory with site: {site_name}")
    
    # Get site config if it exists, otherwise create a dummy one
    if site_name in SNEAKER_SITES:
        site_config = SNEAKER_SITES[site_name]
    else:
        site_config = {
            "name": site_name,
            "url": f"https://{site_name}.com"
        }
    
    try:
        # Get the scraper class for this site
        print(f"Getting scraper for {site_name}...")
        scraper_instance = get_scraper_for_site(site_name, site_config)
        print(f"Got scraper type: {type(scraper_instance).__name__}")
        
        # Test using the scraper in a context manager
        print(f"Testing with context manager...")
        with scraper_instance as scraper:
            print(f"Inside context manager with scraper type: {type(scraper).__name__}")
            
            # Test calling search_products
            print(f"Testing search_products...")
            products = scraper.search_products(category="sale")
            print(f"Found {len(products)} products")
            
            # Test calling get_product_details
            if products and products[0].get('url'):
                print(f"Testing get_product_details...")
                details = scraper.get_product_details(products[0]['url'])
                print(f"Got details: {details is not None}")
            else:
                print("No products found to test get_product_details")
                
        print("Test completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error testing scraper: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
