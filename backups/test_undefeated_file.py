"""
Test script for Undefeated.com scraper with file output
"""

import sys
import os
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UndefeatedTest")

# Add parent directory to path so we can import from the main application
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def write_to_file(text):
    """Write text to the output file."""
    with open("undefeated_test_output.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def test_undefeated_scraper():
    """Test the Undefeated scraper"""
    write_to_file("=" * 50)
    write_to_file(f"Undefeated Scraper Test - {datetime.now()}")
    write_to_file("=" * 50)
    write_to_file("")
    
    try:
        write_to_file("Importing required modules...")
        from config.sites import SNEAKER_SITES
        write_to_file("[OK] Successfully imported SNEAKER_SITES from config.sites")
        
        from scrapers.undefeated import UndefeatedScraper
        write_to_file("[OK] Successfully imported UndefeatedScraper")
        
        # Get the site config
        site_config = SNEAKER_SITES.get('undefeated', {})
        if not site_config:
            write_to_file("[ERROR] Undefeated site config not found")
            return
        write_to_file(f"Site config: {site_config}")
        
        # Create the scraper
        write_to_file("\nCreating UndefeatedScraper instance...")
        scraper = UndefeatedScraper(site_config)
        write_to_file("[OK] Successfully created UndefeatedScraper instance")
        
        # Test basic product search
        write_to_file("\nTesting basic product search...")
        products = scraper.search_products()
        
        if products:
            write_to_file(f"[SUCCESS] Found {len(products)} products!")
            
            # Print the first 3 products
            for i, product in enumerate(products[:3], 1):
                write_to_file(f"\nProduct #{i}:")
                write_to_file(f"  Title: {product.get('title', 'N/A')}")
                write_to_file(f"  Brand: {product.get('brand', 'N/A')}")
                write_to_file(f"  Price: ${product.get('price', 0):.2f}")
                
                if product.get('original_price') and product.get('original_price') > product.get('price', 0):
                    write_to_file(f"  Original Price: ${product.get('original_price', 0):.2f}")
                    write_to_file(f"  Discount: {product.get('discount_percent', 0)}%")
                
                write_to_file(f"  URL: {product.get('url', 'N/A')}")
        else:
            write_to_file("[FAIL] No products found in basic search")
        
        # Test sale products search
        write_to_file("\nTesting sale products search...")
        sale_products = scraper.search_products(category='sale')
        
        if sale_products:
            write_to_file(f"[SUCCESS] Found {len(sale_products)} sale products!")
            
            # Print the first 3 sale products
            for i, product in enumerate(sale_products[:3], 1):
                write_to_file(f"\nSale Product #{i}:")
                write_to_file(f"  Title: {product.get('title', 'N/A')}")
                write_to_file(f"  Brand: {product.get('brand', 'N/A')}")
                write_to_file(f"  Price: ${product.get('price', 0):.2f}")
                
                if product.get('original_price') and product.get('original_price') > product.get('price', 0):
                    write_to_file(f"  Original Price: ${product.get('original_price', 0):.2f}")
                    write_to_file(f"  Discount: {product.get('discount_percent', 0)}%")
                
                write_to_file(f"  URL: {product.get('url', 'N/A')}")
        else:
            write_to_file("[FAIL] No sale products found")
        
        # Test product details
        if products:
            write_to_file("\nTesting product details...")
            
            # Get details for the first product
            product_url = products[0].get('url')
            if product_url:
                write_to_file(f"Getting details for: {product_url}")
                
                details = scraper.get_product_details(product_url)
                
                if details:
                    write_to_file(f"[SUCCESS] Product details retrieved!")
                    
                    # Print important details
                    write_to_file(f"  Title: {details.get('title', 'N/A')}")
                    write_to_file(f"  Brand: {details.get('brand', 'N/A')}")
                    write_to_file(f"  Price: ${details.get('price', 0):.2f}")
                    
                    if details.get('original_price') and details.get('original_price') > details.get('price', 0):
                        write_to_file(f"  Original Price: ${details.get('original_price', 0):.2f}")
                        write_to_file(f"  Discount: {details.get('discount_percent', 0)}%")
                    
                    write_to_file(f"  SKU: {details.get('sku', 'N/A')}")
                    write_to_file(f"  In Stock: {'Yes' if details.get('in_stock', False) else 'No'}")
                    
                    if 'description' in details:
                        desc = details['description']
                        if len(desc) > 100:
                            desc = desc[:100] + "..."
                        write_to_file(f"  Description: {desc}")
                    
                    if 'images' in details:
                        write_to_file(f"  Number of Images: {len(details['images'])}")
                        if details['images']:
                            write_to_file(f"  First Image: {details['images'][0]}")
                else:
                    write_to_file("[FAIL] Failed to get product details")
    
    except Exception as e:
        write_to_file(f"[ERROR] An exception occurred: {str(e)}")
        write_to_file(traceback.format_exc())
    
    write_to_file("\nUndefeated.com scraper test completed!")

if __name__ == "__main__":
    # Clear the output file before starting
    with open("undefeated_test_output.txt", "w", encoding="utf-8") as f:
        f.write("")
    
    test_undefeated_scraper()
    print(f"Test completed! Check undefeated_test_output.txt for results.")
