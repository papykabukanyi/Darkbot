"""
Main script for the sneaker deal finder bot.
"""

import argparse
import logging
from typing import Dict, List, Any
import colorama
from tqdm import tqdm

from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH)
from scrapers import (SneakersScraper, ChampsScraper, 
                     FootlockerScraper, IDSportsScraper)
from storage import DealStorage
from utils import get_timestamp

# Initialize colorama for colored console output
colorama.init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sneaker_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SneakerBot")

def get_scraper_for_site(site_name: str, site_config: Dict[str, Any]):
    """
    Get the appropriate scraper for a site.
    
    Args:
        site_name: Name of the site
        site_config: Configuration for the site
        
    Returns:
        Initialized scraper instance
    """
    site_config['name'] = site_name.capitalize()
    
    if site_name == 'sneakers':
        return SneakersScraper(site_config)
    elif site_name == 'champs':
        return ChampsScraper(site_config)
    elif site_name == 'footlocker':
        return FootlockerScraper(site_config)
    elif site_name == 'idsports':
        return IDSportsScraper(site_config)
    else:
        raise ValueError(f"Unknown site: {site_name}")

def print_deal(deal: Dict[str, Any]):
    """
    Print deal information to the console with color formatting.
    
    Args:
        deal: Dictionary with deal information
    """
    # Set up colors
    RESET = colorama.Style.RESET_ALL
    BOLD = colorama.Style.BRIGHT
    GREEN = colorama.Fore.GREEN
    RED = colorama.Fore.RED
    BLUE = colorama.Fore.BLUE
    YELLOW = colorama.Fore.YELLOW
    
    # Format the deal information
    title = f"{BOLD}{deal['title']}{RESET}"
    price = f"{GREEN}${deal['price']:.2f}{RESET}"
    original = f"{RED}${deal['original_price']:.2f}{RESET}"
    discount = f"{BOLD}{YELLOW}{deal.get('discount_percent', 0)}%{RESET}"
    source = f"{BLUE}{deal['source']}{RESET}"
    
    profit_info = ""
    if 'profit' in deal:
        profit_color = GREEN if deal['profit'] > 0 else RED
        profit_info = f" | Potential profit: {profit_color}${deal['profit']:.2f}{RESET} ({deal['roi']})"
    
    # Print the formatted deal
    print(f"\n{title}")
    print(f"Price: {price} (was {original}) - {discount} off{profit_info}")
    print(f"Source: {source}")
    
    # Print URL
    print(f"URL: {deal['url']}")
    
    # Print available sizes if present
    if 'sizes' in deal:
        available_sizes = [s['size'] for s in deal['sizes'] if s['available']]
        if available_sizes:
            sizes_str = ", ".join(available_sizes)
            print(f"Available sizes: {sizes_str}")
    
    print("-" * 80)

def run_scraper(scraper_instance, category='sale'):
    """
    Run a scraper for a specific site.
    
    Args:
        scraper_instance: Instance of a scraper
        category: Category to scrape (default: 'sale')
        
    Returns:
        List of deals found
    """
    deals = []
    
    try:
        logger.info(f"Scraping {scraper_instance.name}...")
        site_deals = scraper_instance.scrape_site()
        
        if site_deals:
            # Filter deals by minimum discount
            filtered_deals = [
                deal for deal in site_deals 
                if deal.get('discount_percent', 0) >= MIN_DISCOUNT_PERCENT
            ]
            
            # Filter by brand if configured
            if BRANDS_OF_INTEREST:
                filtered_deals = [
                    deal for deal in filtered_deals
                    if deal.get('brand', '').lower() in [b.lower() for b in BRANDS_OF_INTEREST]
                ]
            
            logger.info(f"Found {len(filtered_deals)} deals on {scraper_instance.name} meeting criteria")
            deals.extend(filtered_deals)
    
    except Exception as e:
        logger.error(f"Error running scraper for {scraper_instance.name}: {e}")
    
    return deals

def main():
    """Main entry point for the script."""
    
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Sneaker Deal Finder Bot')
    parser.add_argument('--sites', nargs='+', choices=list(WEBSITES.keys()), 
                        default=list(WEBSITES.keys()),
                        help='Sites to scrape (default: all)')
    parser.add_argument('--brands', nargs='+', default=BRANDS_OF_INTEREST,
                        help=f'Brands to look for (default: {BRANDS_OF_INTEREST})')
    parser.add_argument('--min-discount', type=int, default=MIN_DISCOUNT_PERCENT,
                        help=f'Minimum discount percentage (default: {MIN_DISCOUNT_PERCENT}%%)')
    parser.add_argument('--quiet', action='store_true', help='Suppress console output')
    parser.add_argument('--export-json', action='store_true', help='Export results to JSON')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode with mock data')
    
    args = parser.parse_args()
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    print(f"{colorama.Fore.CYAN}{colorama.Style.BRIGHT}Sneaker Deal Finder Bot{colorama.Style.RESET_ALL}")
    print(f"Started at: {get_timestamp()}")
    print(f"Scraping sites: {', '.join(args.sites)}")
    print(f"Looking for brands: {', '.join(args.brands)}")
    print(f"Minimum discount: {args.min_discount}%")
    print("-" * 80)
    
    # Debug output for websites config
    logger.debug(f"Website configurations:")
    for site, config in WEBSITES.items():
        logger.debug(f"{site}: {config}")
    
    all_deals = []
    
    # Initialize storage
    storage = DealStorage(
        csv_filename=CSV_FILENAME,
        db_enabled=DATABASE_ENABLED,
        db_path=DATABASE_PATH
    )
    
    # Scrape each site
    for site_name in tqdm(args.sites, desc="Scraping websites"):
        if site_name in WEBSITES:
            site_config = WEBSITES[site_name]
            
            try:
                scraper_class = get_scraper_for_site(site_name, site_config)
                with scraper_class as scraper:
                    site_deals = run_scraper(scraper)
                    all_deals.extend(site_deals)
            
            except Exception as e:
                logger.error(f"Error with {site_name}: {e}")
    
    # Sort deals by discount percentage
    all_deals.sort(key=lambda x: x.get('discount_percent', 0), reverse=True)
    
    # Save deals if there are any
    if all_deals:
        if SAVE_TO_CSV:
            storage.save_deals(all_deals)
        
        if args.export_json:
            storage.export_to_json()
        
        # Print deals to console
        if not args.quiet:
            print(f"\nFound {len(all_deals)} deals matching your criteria:")
            for deal in all_deals:
                print_deal(deal)
        
        print(f"\n{colorama.Style.BRIGHT}Summary:{colorama.Style.RESET_ALL}")
        print(f"Total deals found: {len(all_deals)}")
        print(f"Deals by site:")
        for site in args.sites:
            site_count = sum(1 for deal in all_deals if deal['source'].lower() == site.capitalize())
            print(f"  - {site.capitalize()}: {site_count}")
        
        if SAVE_TO_CSV:
            print(f"\nResults saved to {CSV_FILENAME}")
        if args.export_json:
            print(f"Results exported to deals_export.json")
    
    else:
        print(f"\n{colorama.Fore.YELLOW}No deals found matching your criteria.{colorama.Style.RESET_ALL}")
    
    print(f"\nFinished at: {get_timestamp()}")

if __name__ == "__main__":
    main()
