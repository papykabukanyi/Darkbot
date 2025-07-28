"""
Test for the multi-site deal intelligence system
"""

import sys
import os
import logging
import colorama
from datetime import datetime

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sites import SNEAKER_SITES, DEFAULT_SITES
from scrapers.factory import get_scraper_for_site
from utils.price_comparison import PriceComparer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DealIntelligenceTest")

# Initialize colorama for colored output
colorama.init()

def get_timestamp():
    """Get current timestamp for display."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_deals_from_site(site_name, site_config):
    """Get deals from a specific site."""
    print(f"{colorama.Fore.YELLOW}Scraping {site_name}...{colorama.Style.RESET_ALL}")
    
    try:
        scraper = get_scraper_for_site(site_name, site_config)
        deals = scraper.search_products(category='sale')
        
        print(f"{colorama.Fore.GREEN}Found {len(deals)} deals on {site_name}{colorama.Style.RESET_ALL}")
        return deals
    except Exception as e:
        print(f"{colorama.Fore.RED}Error scraping {site_name}: {str(e)}{colorama.Style.RESET_ALL}")
        return []

def find_same_product_across_sites(all_deals, threshold=80):
    """
    Find the same product across different sites.
    
    Args:
        all_deals: Dictionary of {site: [deals]}
        threshold: Similarity threshold (0-100)
        
    Returns:
        List of product matches
    """
    from difflib import SequenceMatcher
    
    def similar(a, b):
        """Calculate string similarity percentage."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100
    
    matches = []
    
    # Get all products as a flat list with site info
    products = []
    for site, deals in all_deals.items():
        for deal in deals:
            products.append({**deal, 'site': site})
    
    # Look for matches
    for i, product1 in enumerate(products):
        for j, product2 in enumerate(products[i+1:], i+1):
            # Skip if from same site
            if product1['site'] == product2['site']:
                continue
                
            # Compare titles
            title1 = product1.get('title', '')
            title2 = product2.get('title', '')
            
            similarity = similar(title1, title2)
            
            if similarity >= threshold:
                # Found a match
                matches.append({
                    'similarity': similarity,
                    'product1': product1,
                    'product2': product2,
                    'price_diff': product1.get('price', 0) - product2.get('price', 0)
                })
    
    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches

def test_deal_intelligence():
    """Test the multi-site deal intelligence system."""
    print(f"{colorama.Fore.CYAN}=== Multi-Site Deal Intelligence Test ==={colorama.Style.RESET_ALL}")
    print(f"Started at: {get_timestamp()}")
    print()
    
    # We'll test with a subset of sites for speed
    test_sites = ["nike", "adidas", "footlocker", "undefeated"]
    
    # Get deals from each site
    all_deals = {}
    for site in test_sites:
        if site in SNEAKER_SITES:
            site_config = SNEAKER_SITES[site]
            deals = get_deals_from_site(site, site_config)
            if deals:
                all_deals[site] = deals
    
    print(f"\n{colorama.Fore.YELLOW}Finding identical products across sites...{colorama.Style.RESET_ALL}")
    
    # Find matches
    matches = find_same_product_across_sites(all_deals, threshold=70)
    
    if matches:
        print(f"{colorama.Fore.GREEN}Found {len(matches)} potential product matches across different sites!{colorama.Style.RESET_ALL}")
        
        # Show the top 5 matches
        for i, match in enumerate(matches[:5], 1):
            product1 = match['product1']
            product2 = match['product2']
            
            print(f"\n{colorama.Fore.CYAN}Match #{i} (Similarity: {match['similarity']:.1f}%){colorama.Style.RESET_ALL}")
            print(f"  Product 1: {product1.get('title')} from {product1.get('site')}")
            print(f"  Price 1: ${product1.get('price', 0):.2f}")
            print(f"  Product 2: {product2.get('title')} from {product2.get('site')}")
            print(f"  Price 2: ${product2.get('price', 0):.2f}")
            print(f"  Price difference: ${abs(match['price_diff']):.2f}")
            
            if match['price_diff'] > 0:
                print(f"  Better deal: {product2.get('site')} is ${match['price_diff']:.2f} cheaper!")
            elif match['price_diff'] < 0:
                print(f"  Better deal: {product1.get('site')} is ${abs(match['price_diff']):.2f} cheaper!")
            else:
                print(f"  Same price on both sites.")
    else:
        print(f"{colorama.Fore.RED}No product matches found across sites.{colorama.Style.RESET_ALL}")
    
    print(f"\n{colorama.Fore.CYAN}Test completed at: {get_timestamp()}{colorama.Style.RESET_ALL}")

if __name__ == "__main__":
    test_deal_intelligence()
