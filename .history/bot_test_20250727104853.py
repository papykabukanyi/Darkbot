#!/usr/bin/env python

import logging
import os
import sys

# Set up logging to file and console
log_file = "bot_test.log"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("BotTest")

# Apply scraper fix
logger.info("Applying scraper fix...")
from scraper_fix import scrape

def main():
    """Test the bot's operation and log results."""
    logger.info("Starting bot test script")
    
    try:
        # Import necessary modules
        logger.info("Importing modules...")
        from config import SNEAKER_SITES, DEFAULT_SITES
        logger.info(f"Found {len(SNEAKER_SITES)} sites in config")
        logger.info(f"Default sites: {DEFAULT_SITES}")
        
        from scrapers.factory import get_scraper_for_site
        logger.info("Factory module imported")
        
        # Test creating a scraper
        site_name = "sneakers"
        site_config = SNEAKER_SITES[site_name]
        logger.info(f"Testing scraper for {site_name}")
        
        scraper_class = get_scraper_for_site(site_name, site_config)
        logger.info(f"Created scraper class: {scraper_class}")
        
        # Test scraping
        logger.info("Starting test scrape...")
        with scraper_class as scraper:
            logger.info(f"Using scraper: {scraper.name} ({scraper.base_url})")
            logger.info("Beginning scrape operation...")
            deals = scraper.scrape()
            logger.info(f"Scraping complete! Found {len(deals)} deals")
            
            if deals:
                logger.info("First few deals found:")
                for i, deal in enumerate(deals[:3]):
                    logger.info(f"Deal #{i+1}: {deal.get('title', 'N/A')} - ${deal.get('price', 0):.2f}")
            else:
                logger.warning("No deals found!")
        
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    print(f"\nTest completed. Check {os.path.abspath(log_file)} for detailed logs.")
    sys.exit(0 if success else 1)
