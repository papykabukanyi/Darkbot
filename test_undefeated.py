"""
Test script for Undefeated.com scraper
"""

import sys
import os
import logging
import colorama

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sites import SNEAKER_SITES
from scrapers.undefeated import UndefeatedScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UndefeatedTest")

# Initialize colorama for colored output
colorama.init()

def test_undefeated_scraper():
    """Test the Undefeated scraper"""
    print(f"{colorama.Fore.YELLOW}Testing Undefeated.com scraper...{colorama.Style.RESET_ALL}")
    
    # Get the site config
    site_config = SNEAKER_SITES.get('undefeated', {})
    if not site_config:
        print(f"{colorama.Fore.RED}Error: Undefeated site config not found{colorama.Style.RESET_ALL}")
        return
    
    # Create the scraper
    scraper = UndefeatedScraper(site_config)
    
    # Test basic product search
    print(f"\n{colorama.Fore.CYAN}Testing basic product search...{colorama.Style.RESET_ALL}")
    products = scraper.search_products()
    
    if products:
        print(f"{colorama.Fore.GREEN}Found {len(products)} products!{colorama.Style.RESET_ALL}")
        
        # Print the first 3 products
        for i, product in enumerate(products[:3], 1):
            print(f"\n{colorama.Fore.CYAN}Product #{i}:{colorama.Style.RESET_ALL}")
            print(f"  Title: {product.get('title', 'N/A')}")
            print(f"  Brand: {product.get('brand', 'N/A')}")
            print(f"  Price: ${product.get('price', 0):.2f}")
            
            if product.get('original_price') and product.get('original_price') > product.get('price', 0):
                print(f"  Original Price: ${product.get('original_price', 0):.2f}")
                print(f"  Discount: {product.get('discount_percent', 0)}%")
            
            print(f"  URL: {product.get('url', 'N/A')}")
    else:
        print(f"{colorama.Fore.RED}No products found in basic search{colorama.Style.RESET_ALL}")
    
    # Test sale products search
    print(f"\n{colorama.Fore.CYAN}Testing sale products search...{colorama.Style.RESET_ALL}")
    sale_products = scraper.search_products(category='sale')
    
    if sale_products:
        print(f"{colorama.Fore.GREEN}Found {len(sale_products)} sale products!{colorama.Style.RESET_ALL}")
        
        # Print the first 3 sale products
        for i, product in enumerate(sale_products[:3], 1):
            print(f"\n{colorama.Fore.CYAN}Sale Product #{i}:{colorama.Style.RESET_ALL}")
            print(f"  Title: {product.get('title', 'N/A')}")
            print(f"  Brand: {product.get('brand', 'N/A')}")
            print(f"  Price: ${product.get('price', 0):.2f}")
            
            if product.get('original_price') and product.get('original_price') > product.get('price', 0):
                print(f"  Original Price: ${product.get('original_price', 0):.2f}")
                print(f"  Discount: {product.get('discount_percent', 0)}%")
            
            print(f"  URL: {product.get('url', 'N/A')}")
    else:
        print(f"{colorama.Fore.RED}No sale products found{colorama.Style.RESET_ALL}")
    
    # Test product details
    if products:
        print(f"\n{colorama.Fore.CYAN}Testing product details...{colorama.Style.RESET_ALL}")
        
        # Get details for the first product
        product_url = products[0].get('url')
        if product_url:
            print(f"Getting details for: {product_url}")
            
            details = scraper.get_product_details(product_url)
            
            if details:
                print(f"{colorama.Fore.GREEN}Product details retrieved!{colorama.Style.RESET_ALL}")
                
                # Print important details
                print(f"  Title: {details.get('title', 'N/A')}")
                print(f"  Brand: {details.get('brand', 'N/A')}")
                print(f"  Price: ${details.get('price', 0):.2f}")
                
                if details.get('original_price') and details.get('original_price') > details.get('price', 0):
                    print(f"  Original Price: ${details.get('original_price', 0):.2f}")
                    print(f"  Discount: {details.get('discount_percent', 0)}%")
                
                print(f"  SKU: {details.get('sku', 'N/A')}")
                print(f"  In Stock: {'Yes' if details.get('in_stock', False) else 'No'}")
                
                if 'description' in details:
                    desc = details['description']
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    print(f"  Description: {desc}")
                
                if 'images' in details:
                    print(f"  Number of Images: {len(details['images'])}")
                    print(f"  First Image: {details['images'][0]}")
            else:
                print(f"{colorama.Fore.RED}Failed to get product details{colorama.Style.RESET_ALL}")
    
    print(f"\n{colorama.Fore.GREEN}Undefeated.com scraper test completed!{colorama.Style.RESET_ALL}")

if __name__ == "__main__":
    test_undefeated_scraper()
