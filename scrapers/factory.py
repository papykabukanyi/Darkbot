"""
Factory function to get the appropriate scraper for a site.
"""

import logging
import importlib
from importlib import import_module
from typing import Dict, Any, Optional, Type

from scrapers.base_scraper import BaseSneakerScraper
from scrapers.fallback_scraper import FallbackScraper

# Set up logging
logger = logging.getLogger("SneakerBot")

def get_scraper_for_site(site_name: str, site_config: Dict[str, Any]):
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
                # Fall back to fallback scraper if specific scraper fails
                logger.info(f"Using FallbackScraper for {site_name}")
                return FallbackScraper(site_config)
        else:
            logger.warning(f"No scraper configured for {site_name}, using fallback scraper")
            # Use fallback scraper for unknown sites instead of crashing
            return FallbackScraper(site_config)
            
    except Exception as e:
        logger.error(f"Error getting scraper for {site_name}: {e}")
        # Return a fallback scraper that won't crash the program
        logger.info(f"Using FallbackScraper for {site_name} due to error")
        return FallbackScraper(site_config)
