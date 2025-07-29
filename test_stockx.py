#!/usr/bin/env python
"""
Test script for StockX scraper
"""

import sys
import os
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StockXTest")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sites import SNEAKER_SITES
from scrapers.stockx import StockXScraper

def test_stockx_scraper():
    """Test the StockX scraper"""
    print("Testing StockX.com scraper...")
    
    # Get the site config
    site_config = SNEAKER_SITES.get('stockx', {})
    if not site_config:
        print("Error: StockX site config not found")
        return
    
    print(f"Site config: {site_config}")
    
    # Create the scraper
    scraper = StockXScraper(site_config)
    
    # Test popular products search
    print("\nTesting popular products search...")
    with scraper as s:
        popular_products = s.search_products()
    
    if popular_products:
        print(f"Found {len(popular_products)} popular products!")
        
        # Print the first 3 popular products
        for i, product in enumerate(popular_products[:3], 1):
            print(f"\nPopular Product #{i}:")
            print(f"  Title: {product.get('title', 'N/A')}")
            print(f"  Brand: {product.get('brand', 'N/A')}")
            print(f"  Price: ${product.get('price', 0):.2f}")
            print(f"  URL: {product.get('url', 'N/A')}")
    else:
        print("No popular products found")
    
    # Test keyword search
    print("\nTesting keyword search...")
    keywords = ["jordan", "1", "chicago"]
    with scraper as s:
        search_products = s.search_products(keywords=keywords)
    
    if search_products:
        print(f"Found {len(search_products)} products for keywords {keywords}!")
        
        # Print the first 3 search products
        for i, product in enumerate(search_products[:3], 1):
            print(f"\nSearch Product #{i}:")
            print(f"  Title: {product.get('title', 'N/A')}")
            print(f"  Brand: {product.get('brand', 'N/A')}")
            print(f"  Price: ${product.get('price', 0):.2f}")
            print(f"  URL: {product.get('url', 'N/A')}")
    else:
        print(f"No products found for keywords {keywords}")
    
    # Test product details
    if search_products:
        print("\nTesting product details...")
        
        # Get details for the first product
        product_url = search_products[0].get('url')
        if product_url:
            print(f"Getting details for: {product_url}")
            
            with scraper as s:
                details = s.get_product_details(product_url)
            
            if details:
                print("Product details retrieved!")
                
                # Print important details
                print(f"  Title: {details.get('title', 'N/A')}")
                print(f"  Brand: {details.get('brand', 'N/A')}")
                print(f"  Price: ${details.get('price', 0):.2f}")
                
                if 'original_price' in details:
                    print(f"  Retail Price: ${details.get('original_price', 0):.2f}")
                
                print(f"  SKU: {details.get('sku', 'N/A')}")
                print(f"  Release Date: {details.get('release_date', 'N/A')}")
                
                if 'last_sale' in details:
                    print(f"  Last Sale: ${details.get('last_sale', 0):.2f}")
                
                if 'resale_value' in details:
                    print(f"  Resale Value: {details.get('resale_value', 0)}%")
                
                if 'description' in details:
                    desc = details['description']
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    print(f"  Description: {desc}")
                
                if 'images' in details:
                    print(f"  Number of Images: {len(details['images'])}")
                    if details['images']:
                        print(f"  First Image: {details['images'][0]}")
                
                if 'sizes' in details:
                    print(f"  Available Sizes: {len(details['sizes'])}")
                    if details['sizes']:
                        print(f"  Size Example: {details['sizes'][0]}")
            else:
                print("Failed to get product details")
    
    print("\nStockX.com scraper test completed!")

if __name__ == "__main__":
    print("=" * 50)
    test_stockx_scraper()
    print("=" * 50)
