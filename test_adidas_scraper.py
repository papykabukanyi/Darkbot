#!/usr/bin/env python
"""
Test script specifically for the Adidas scraper to verify it handles the site correctly
"""

import sys
import os
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AdidasScraperTest")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import scraper modules
from scrapers.factory import get_scraper_for_site
from config.sites import SNEAKER_SITES
import html
from bs4 import BeautifulSoup

def test_adidas_scraper():
    """Test the Adidas scraper to ensure it can retrieve and process deals"""
    print("=" * 50)
    print("Testing Adidas scraper with new sale URL")
    print("=" * 50)
    
    # Get the site config from imported settings
    site_config = SNEAKER_SITES.get('adidas')
    
    if not site_config:
        print("❌ Failed to find Adidas site config!")
        return
    
    print(f"Site URL: {site_config['url']}")
    print(f"Sale URL: {site_config['sale_url']}")
    
    try:
        # Get the scraper instance
        scraper_class = get_scraper_for_site('adidas', site_config)
        
        with scraper_class as scraper:
            print("\nScraping Adidas sale page...")
            start_time = time.time()
            
            # Test the get_page method directly with the sale URL
            soup = scraper.get_page(site_config['sale_url'])
            
            if soup is None:
                print("❌ Failed to get page or parse HTML!")
                return
                
            print(f"✅ Successfully fetched and parsed page: {site_config['sale_url']}")
            print(f"Time taken: {time.time() - start_time:.2f} seconds")
            
            # Try to extract product information
            # Since different sites have different HTML structures,
            # we'll try various common selectors
            
            products = []
            
            # Try common product selectors
            selectors = [
                '.product-card', 
                '.product-item',
                '.glass-product-card',
                '.grid-product__wrapper',
                '.product',
                '[data-auto-id="product-card"]',
                '[data-auto-id="glass-product-card"]'
            ]
            
            for selector in selectors:
                products = soup.select(selector)
                if products:
                    print(f"Found products using selector: {selector}")
                    break
            
            if not products:
                # If no products found with common selectors, let's look at the page structure
                print("Could not find products with common selectors.")
                print("Analyzing page structure...")
                
                # Save the HTML to a file for inspection
                with open("adidas_page_debug.html", "w", encoding="utf-8") as f:
                    f.write(str(soup))
                
                print("Saved page HTML to adidas_page_debug.html for inspection")
                
                # Let's try to find anything that might be a product
                links = soup.find_all('a')
                product_links = [link for link in links if '/products/' in link.get('href', '') or 'product' in link.get('href', '')]
                
                if product_links:
                    print(f"Found {len(product_links)} potential product links")
                    for i, link in enumerate(product_links[:5]):
                        print(f"Link {i+1}: {link.get('href')}")
                
                return
            
            print(f"Found {len(products)} products on the page")
            
            # Display a sample of products
            deals_found = []
            for i, product in enumerate(products[:5], 1):
                try:
                    # Try various selectors for title
                    title = None
                    title_selectors = ['.title', '.name', '.product-name', '.product-title', 'h3', 'h2', '.gl-product-card__name']
                    for selector in title_selectors:
                        title_elem = product.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text().strip()
                            break
                    
                    # Try various selectors for price
                    price = None
                    price_selectors = ['.price', '.money', '.product-price', '.gl-price', '.sale-price', '[data-auto-id="sale-price"]']
                    for selector in price_selectors:
                        price_elem = product.select_one(selector)
                        if price_elem:
                            price = price_elem.get_text().strip()
                            break
                    
                    # Look for original price/discount
                    original_price = None
                    original_price_selectors = ['.original-price', '.compare-at-price', '.standard-price', '[data-auto-id="standard-price"]']
                    for selector in original_price_selectors:
                        original_price_elem = product.select_one(selector)
                        if original_price_elem:
                            original_price = original_price_elem.get_text().strip()
                            break
                    
                    # Try to find the product link
                    link = None
                    a_tag = product.find('a')
                    if a_tag and 'href' in a_tag.attrs:
                        link = a_tag['href']
                        if not link.startswith('http'):
                            link = site_config['url'] + link
                    
                    print(f"Product {i}:")
                    print(f"  Title: {title or 'Unknown'}")
                    print(f"  Price: {price or 'Unknown'}")
                    if original_price:
                        print(f"  Original Price: {original_price}")
                    if link:
                        print(f"  URL: {link}")
                    print()
                    
                    # If we have enough info, add to deals list
                    if title and price:
                        deal = {
                            'title': title,
                            'price': price,
                            'original_price': original_price,
                            'url': link,
                            'site': 'adidas',
                            'found_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        deals_found.append(deal)
                        
                except Exception as e:
                    print(f"Error parsing product {i}: {e}")
            
            if deals_found:
                print(f"\n✅ Successfully found {len(deals_found)} deals on Adidas site")
                
                # Save deals to a file for debugging
                import json
                with open("adidas_deals_debug.json", "w") as f:
                    json.dump(deals_found, f, indent=2)
                print("Saved deals to adidas_deals_debug.json for inspection")
            else:
                print("\n❌ Could not extract deal information from products")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_adidas_scraper()
