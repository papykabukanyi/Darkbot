"""
Factory function to get the appropriate scraper for a site.
"""

import logging
from importlib import import_module
from typing import Dict, Any, Optional, Type

from scrapers.base_scraper import BaseSneakerScraper

# Set up logging
logger = logging.getLogger("SneakerBot")

def get_scraper_for_site(site_name: str, site_config: Dict[str, Any]) -> Type[BaseSneakerScraper]:
    """
    Get the appropriate scraper class for a site.
    
    Args:
        site_name: Name of the site
        site_config: Configuration for the site
        
    Returns:
        Scraper class for the site
    """
    # Try to import site-specific scraper
    try:
        module_name = f"scrapers.{site_name}_scraper"
        class_name = f"{site_name.capitalize()}Scraper"
        
        # Adjust for special cases
        if site_name == "champssports":
            class_name = "ChampsScraper"
        elif site_name == "footlocker":
            class_name = "FootlockerScraper"
        elif site_name == "idsports":
            class_name = "IDSportsScraper"
        elif site_name == "jdsports":
            class_name = "JDSportsScraper"
        elif site_name == "finishline":
            class_name = "FinishlineScraper"
        elif site_name == "stockx":
            class_name = "StockXScraper"
        
        try:
            module = import_module(module_name)
            scraper_class = getattr(module, class_name)
            logger.info(f"Using {class_name} for {site_name}")
            return scraper_class(site_config)
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not find specific scraper for {site_name}: {e}")
            
            # Fall back to base scraper
            from scrapers.base_scraper import BaseSneakerScraper
            logger.info(f"Using BaseSneakerScraper for {site_name}")
            return BaseSneakerScraper(site_config)
            
    except Exception as e:
        logger.error(f"Error getting scraper for {site_name}: {e}")
        raise
