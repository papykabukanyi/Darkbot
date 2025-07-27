"""
Base scraper class that all site-specific scrapers will inherit from.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
from selenium import webdriver
from bs4 import BeautifulSoup

# Import necessary functions directly or define them here
import random
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config import HEADLESS_BROWSER, USE_SELENIUM

logger = logging.getLogger("SneakerBot")

class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, site_config: Dict[str, Any]):
        """
        Initialize the scraper with site-specific configuration.
        
        Args:
            site_config: Dictionary with site configuration
        """
        self.name = site_config.get('name', 'Unknown Site')
        self.base_url = site_config.get('url', '')
        self.rate_limit = site_config.get('rate_limit', 10)
        self.driver = None
        self.session = requests.Session()
        
    def __enter__(self):
        """Set up resources when entering context."""
        if USE_SELENIUM:
            self.driver = setup_selenium_driver(headless=HEADLESS_BROWSER)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        if self.driver:
            self.driver.quit()
        self.session.close()
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get a page and return its BeautifulSoup representation.
        
        Args:
            url: The URL to scrape
            
        Returns:
            BeautifulSoup object or None if failed
        """
        logger.info(f"Scraping {url}")
        
        if USE_SELENIUM and self.driver:
            try:
                self.driver.get(url)
                random_delay(1.0, 3.0)  # Slight delay to let JavaScript load
                html = self.driver.page_source
                return BeautifulSoup(html, 'lxml')
            except Exception as e:
                logger.error(f"Selenium error on {url}: {e}")
                return None
        else:
            response = make_request(url)
            if response and response.status_code == 200:
                return BeautifulSoup(response.text, 'lxml')
            return None
    
    @abstractmethod
    def search_products(self, keywords: List[str] = None, category: str = None) -> List[Dict]:
        """
        Search for products using keywords or category.
        
        Args:
            keywords: List of keywords to search for
            category: Category to browse
            
        Returns:
            List of product dictionaries
        """
        pass
    
    @abstractmethod
    def get_product_details(self, product_url: str) -> Dict:
        """
        Extract detailed information about a specific product.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with product details
        """
        pass
    
    def scrape_site(self) -> List[Dict]:
        """
        Main method to scrape the site for deals.
        
        Returns:
            List of product dictionaries with deal information
        """
        logger.info(f"Starting scrape of {self.name}")
        
        try:
            # Search for products in the sale/discount section
            products = self.search_products(category="sale")
            
            # Get detailed information for each product
            detailed_products = []
            for product in products[:10]:  # Limit to 10 products for testing
                random_delay(self.rate_limit * 0.8, self.rate_limit * 1.2)
                if product.get('url'):
                    details = self.get_product_details(product['url'])
                    if details:
                        # Add profit potential calculation
                        if 'price' in details and 'original_price' in details:
                            profit_info = calculate_profit_potential(
                                details['price'], 
                                details['original_price'] * 0.9  # Estimated market value
                            )
                            details.update(profit_info)
                            
                        detailed_products.append(details)
            
            logger.info(f"Found {len(detailed_products)} products with details from {self.name}")
            return detailed_products
            
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
            return []
