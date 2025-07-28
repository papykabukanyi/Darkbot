"""
Test script to verify the sale URLs for Nike, JD Sports, and Footlocker.
"""

import sys
import os
import logging
import colorama
from datetime import datetime

# Add parent directory to path so we can import from the main application
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SaleURLTester")

# Initialize colorama for colored output
colorama.init()

def test_sale_urls():
    """Test the updated sale URLs."""
    print(colorama.Fore.CYAN + "Testing updated sale URLs..." + colorama.Style.RESET_ALL)
    
    try:
        # Import necessary modules
        from config.sites import SNEAKER_SITES
        from scrapers.factory import get_scraper_for_site
        
        # Test sites
        sites_to_test = ["nike", "jdsports", "footlocker"]
        results = {}
        
        for site_name in sites_to_test:
            print(f"\n{colorama.Fore.YELLOW}Testing {site_name.upper()}...{colorama.Style.RESET_ALL}")
            
            if site_name not in SNEAKER_SITES:
                print(f"{colorama.Fore.RED}Error: {site_name} not found in SNEAKER_SITES config{colorama.Style.RESET_ALL}")
                results[site_name] = {"status": "error", "message": "Not found in SNEAKER_SITES"}
                continue
            
            site_config = SNEAKER_SITES[site_name]
            print(f"Base URL: {site_config.get('url')}")
            print(f"Sale URL: {site_config.get('sale_url')}")
            
            # Create scraper
            scraper = get_scraper_for_site(site_name, site_config)
            print(f"Using scraper: {type(scraper).__name__}")
            
            # Test scraper
            try:
                print(f"Searching for products...")
                products = scraper.search_products(category="sale")
                
                if products:
                    print(f"{colorama.Fore.GREEN}Success! Found {len(products)} products{colorama.Style.RESET_ALL}")
                    
                    # Print the first 3 products
                    for i, product in enumerate(products[:3], 1):
                        print(f"\nProduct #{i}:")
                        print(f"  Title: {product.get('title', 'N/A')}")
                        print(f"  Price: ${product.get('price', 0):.2f}")
                        print(f"  URL: {product.get('url', 'N/A')}")
                    
                    results[site_name] = {"status": "success", "product_count": len(products)}
                else:
                    print(f"{colorama.Fore.YELLOW}Warning: No products found for {site_name}{colorama.Style.RESET_ALL}")
                    results[site_name] = {"status": "warning", "product_count": 0}
            
            except Exception as e:
                print(f"{colorama.Fore.RED}Error testing {site_name}: {e}{colorama.Style.RESET_ALL}")
                import traceback
                traceback.print_exc()
                results[site_name] = {"status": "error", "message": str(e)}
        
        # Print summary
        print(f"\n{colorama.Fore.CYAN}Summary:{colorama.Style.RESET_ALL}")
        for site_name, result in results.items():
            status = result["status"]
            if status == "success":
                print(f"  {colorama.Fore.GREEN}✓ {site_name}: Found {result['product_count']} products{colorama.Style.RESET_ALL}")
            elif status == "warning":
                print(f"  {colorama.Fore.YELLOW}⚠ {site_name}: No products found{colorama.Style.RESET_ALL}")
            else:
                print(f"  {colorama.Fore.RED}✗ {site_name}: Error - {result.get('message')}{colorama.Style.RESET_ALL}")
    
    except Exception as e:
        print(f"{colorama.Fore.RED}Error in test_sale_urls: {e}{colorama.Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sale_urls()
