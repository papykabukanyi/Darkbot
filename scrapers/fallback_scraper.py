"""
Fallback scraper implementation for sites without a dedicated scraper.
"""

import logging
from typing import Dict, List, Optional, Any
from scrapers.base_scraper import BaseSneakerScraper

logger = logging.getLogger("SneakerBot")

class FallbackScraper(BaseSneakerScraper):
    """
    A concrete implementation of BaseSneakerScraper to use as a fallback for unknown sites.
    This implementation provides basic functionality to prevent errors with unknown sites.
    """
    
    def __init__(self, site_config):
        """Initialize the fallback scraper with site configuration."""
        super().__init__(site_config)
        logger.info(f"Created fallback scraper for {self.name}")
    
    def search_products(self, keywords=None, category=None):
        """
        Basic implementation of search_products for unknown sites.
        
        Args:
            keywords: Search keywords (optional)
            category: Product category (optional)
            
        Returns:
            Empty list as we don't know how to scrape unknown sites
        """
        logger.warning(f"Using fallback search_products for {self.name} - no products will be found")
        return []
    
    def get_product_details(self, product_url):
        """
        Basic implementation of get_product_details for unknown sites.
        
        Args:
            product_url: URL of the product
            
        Returns:
            None as we don't know how to scrape unknown sites
        """
        logger.warning(f"Using fallback get_product_details for {self.name} - no details will be found")
        return None
