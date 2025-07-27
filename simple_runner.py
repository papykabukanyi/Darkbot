"""
Simple runner script for the sneaker bot.
"""

import argparse
import logging
import sys
from scrapers.factory import get_scraper_for_site
from config import WEBSITES, MIN_DISCOUNT_PERCENT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SneakerBot")

def main(args):
    """Main function to run the scraper."""
    print("\n=== Sneaker Deal Finder ===\n")
    
    # Determine which sites to scrape
    if args.sites:
        sites_to_scrape = {k: v for k, v in WEBSITES.items() if k in args.sites}
    else:
        sites_to_scrape = WEBSITES
    
    all_deals = []
    
    # Scrape each website
    for site_name, site_config in sites_to_scrape.items():
        print(f"Scraping {site_name}...")
        
        try:
            # Get the appropriate scraper
            with get_scraper_for_site(site_name, site_config) as scraper:
                if not scraper:
                    logger.error(f"Could not create scraper for {site_name}")
                    continue
                
                # Start scraping
                deals = scraper.scrape_site()
                
                # Filter deals by minimum discount
                if deals:
                    filtered_deals = [
                        deal for deal in deals 
                        if deal.get('discount_percent', 0) >= MIN_DISCOUNT_PERCENT
                    ]
                    
                    print(f"Found {len(filtered_deals)} deals with at least {MIN_DISCOUNT_PERCENT}% discount")
                    all_deals.extend(filtered_deals)
                else:
                    print(f"No deals found on {site_name}")
                
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
    
    # Print summary of deals
    if all_deals:
        print(f"\nFound {len(all_deals)} total deals")
        
        # Display top 5 deals
        print("\nTop deals:")
        all_deals.sort(key=lambda x: x.get('discount_percent', 0), reverse=True)
        
        for i, deal in enumerate(all_deals[:5], 1):
            print(f"{i}. {deal.get('title', 'Unknown')} - ${deal.get('price', 0):.2f} " + 
                  f"(${deal.get('original_price', 0):.2f}) - {deal.get('discount_percent', 0):.1f}% off")
    else:
        print("\nNo deals found that match the criteria.")
    
    return all_deals

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Sneaker Deal Finder Bot')
    parser.add_argument('--sites', nargs='+', help='Specific sites to scrape')
    args = parser.parse_args()
    
    # Run the bot
    main(args)
