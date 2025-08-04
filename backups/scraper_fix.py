"""
Simple fix for the scraper functionality.
"""

import logging
from scrapers.base_scraper import BaseSneakerScraper

logger = logging.getLogger("SneakerBot")

# Monkey patch the BaseSneakerScraper class to add the scrape method
def scrape(self):
    """
    Alias for scrape_site to maintain compatibility.
    """
    logger.info(f"Scraping {self.name} with improved scrape method")
    return self.scrape_site()

# Apply the monkey patch
BaseSneakerScraper.scrape = scrape

print("Scraper fix applied. The bot should now work correctly.")
