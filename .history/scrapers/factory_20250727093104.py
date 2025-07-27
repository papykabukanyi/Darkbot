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
    # Map of site names to their actual module and class names
    scraper_mapping = {
        "sneakers": ("scrapers.sneakers", "SneakersScraper"),
        "champssports": ("scrapers.champssports", "ChampsScraper"), 
        "footlocker": ("scrapers.footlocker", "FootlockerScraper"),
        "idsports": ("scrapers.idsports", "IDSportsScraper"),
    }
    
    # Try to import site-specific scraper
    try:
        if site_name in scraper_mapping:
            module_name, class_name = scraper_mapping[site_name]
            try:
                module = import_module(module_name)
                scraper_class = getattr(module, class_name)
                logger.info(f"Using {class_name} for {site_name}")
                return scraper_class(site_config)
            except (ImportError, AttributeError) as e:
                logger.warning(f"Could not find specific scraper for {site_name}: {e}")
        else:
            logger.warning(f"No scraper configured for {site_name}")
            raise ValueError(f"Unknown site: {site_name}")
        else:
            logger.warning(f"No scraper configured for {site_name}")
            raise ValueError(f"Unknown site: {site_name}")
            
        # Fall back to base scraper if specific scraper fails
        from scrapers.base_scraper import BaseSneakerScraper
        logger.info(f"Using BaseSneakerScraper for {site_name}")
        return BaseSneakerScraper(site_config)
            
    except Exception as e:
        logger.error(f"Error getting scraper for {site_name}: {e}")
        raise
