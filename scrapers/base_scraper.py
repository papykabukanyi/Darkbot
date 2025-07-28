"""
Base scraper class that all scrapers will inherit from.
"""

import logging
import time
import random
import re
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Import from the correct config module
try:
    from config import HEADLESS_BROWSER, USE_SELENIUM, USE_PROXY, PROXY_CONFIG
except ImportError:
    # Fallback to root config if modular config import fails
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from config import HEADLESS_BROWSER, USE_SELENIUM, USE_PROXY, PROXY_CONFIG

from utils.proxy_manager import ProxyManager, ProxiedRequester

# User agent list for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

logger = logging.getLogger("SneakerBot")

def setup_selenium_driver(headless=True):
    """Simple function to set up a Chrome webdriver."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    
    try:
        # Try to detect Chrome binary path
        chrome_binary_locations = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/headless-chromium",
            "/chrome/chrome",
            "/usr/bin/google-chrome-stable"
        ]
        
        for location in chrome_binary_locations:
            if os.path.exists(location):
                logger.info(f"Chrome binary found at {location}")
                options.binary_location = location
                break
        
        # Try to use chrome directly with options
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(60)
            logger.info("Successfully initialized Chrome driver directly")
            return driver
        except Exception as direct_error:
            logger.warning(f"Direct Chrome driver initialization failed: {direct_error}")
            
            # Try with ChromeDriverManager
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(60)
                logger.info("Successfully initialized Chrome driver with ChromeDriverManager")
                return driver
            except Exception as manager_error:
                logger.warning(f"ChromeDriverManager initialization failed: {manager_error}")
                # Let it fall through to the fallback options
                raise
                
    except Exception as e:
        logger.error(f"All Chrome driver initialization attempts failed: {e}")
        # Fall back to requests-only mode by returning None
        logger.info("Falling back to requests-only mode")
        return None

def random_delay(min_seconds=1.0, max_seconds=3.0):
    """Sleep for a random amount of time to simulate human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def make_request(url, max_retries=3, delay=2, use_proxy=None):
    """
    Make an HTTP request with retries and random user agent.
    
    Args:
        url: URL to request
        max_retries: Maximum number of retry attempts
        delay: Delay between retries (will be multiplied by attempt number)
        use_proxy: Override to force proxy usage (True/False) instead of using config
        
    Returns:
        HTML content if successful, None otherwise
    """
    # Determine if we should use the proxy system
    should_use_proxy = USE_PROXY if use_proxy is None else use_proxy
    
    if should_use_proxy:
        # Use the proxy rotation system
        requester = BaseSneakerScraper.get_requester()
        if requester:
            for attempt in range(max_retries):
                response = requester.get(url)
                if response and response.status_code == 200:
                    return response.text
                
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                    # Force proxy rotation for next attempt
                    requester._rotate_session()
            
            return None
    
    # Fall back to standard requests if proxy is disabled or unavailable
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
    
    return None

def extract_price(text):
    """Extract a price from a string."""
    if not text:
        return 0.0
        
    # Remove currency symbols and other non-digit characters except for decimal point
    price_str = re.sub(r'[^\d.]', '', text)
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return 0.0
        
def format_price(text):
    """Format a price string to a float value."""
    return extract_price(text)

def calculate_profit_potential(retail_price, market_price):
    """Calculate profit potential for a deal."""
    if retail_price <= 0 or market_price <= 0:
        return {
            'profit_amount': 0,
            'profit_percentage': 0,
            'is_profitable': False
        }
    
    profit_amount = market_price - retail_price
    profit_percentage = (profit_amount / retail_price) * 100
    is_profitable = profit_percentage >= 20  # 20% threshold
    
    return {
        'profit_amount': profit_amount,
        'profit_percentage': profit_percentage,
        'is_profitable': is_profitable
    }

class BaseSneakerScraper(ABC):
    """Base class for all sneaker scrapers."""
    
    # Class-level shared proxy manager
    _proxy_manager = None
    _requester = None
    
    @classmethod
    def get_proxy_manager(cls):
        """Get or initialize the class-level proxy manager."""
        if cls._proxy_manager is None and USE_PROXY:
            # Use the PROXY_CONFIG if available
            cls._proxy_manager = ProxyManager(
                proxy_list_path=PROXY_CONFIG.get('proxy_file', 'proxies.json'),
                max_fails=PROXY_CONFIG.get('max_fails', 3),
                ban_time=PROXY_CONFIG.get('ban_time', 1800),
                verify_proxies=PROXY_CONFIG.get('verify_proxies', True),
                use_fallback=PROXY_CONFIG.get('use_fallback', True)
            )
        return cls._proxy_manager
    
    @classmethod
    def get_requester(cls):
        """Get or initialize the class-level proxied requester."""
        if cls._requester is None and USE_PROXY:
            cls._requester = ProxiedRequester(proxy_manager=cls.get_proxy_manager())
        return cls._requester
    
    def __init__(self, site_config):
        """Initialize the scraper with site-specific configuration."""
        self.name = site_config.get('name', 'Unknown Site')
        self.base_url = site_config.get('url', '')
        self.rate_limit = site_config.get('rate_limit', 10)
        self.driver = None
        
        # Use the proxied requester if proxy is enabled
        if USE_PROXY:
            self.requester = self.get_requester()
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
        
    def __enter__(self):
        """Set up resources when entering context."""
        if USE_SELENIUM:
            self.driver = setup_selenium_driver(headless=HEADLESS_BROWSER)
            
            # If using proxy with Selenium
            if USE_PROXY and self.get_proxy_manager():
                proxy = self.get_proxy_manager().get_next_proxy()
                if proxy:
                    try:
                        # Add proxy to Chrome options by recreating the driver
                        proxy_url = self.get_proxy_manager().get_proxy_url(proxy)
                        
                        # Close existing driver first
                        if self.driver:
                            self.driver.quit()
                        
                        # Create new options with proxy settings
                        options = Options()
                        if HEADLESS_BROWSER:
                            options.add_argument("--headless")
                        options.add_argument("--proxy-server=" + proxy_url)
                        options.add_argument("--no-sandbox")
                        options.add_argument("--disable-dev-shm-usage")
                        options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
                        
                        # Create new driver with proxy
                        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                        logger.info(f"Successfully configured Chrome with proxy")
                    except Exception as e:
                        logger.error(f"Failed to set up Chrome with proxy: {e}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        if self.driver:
            self.driver.quit()
        if hasattr(self, 'session'):
            self.session.close()
    
    def get_page(self, url):
        """Get a page and return its BeautifulSoup representation."""
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
            # Use the proxied requester if enabled
            if USE_PROXY and self.requester:
                response = self.requester.get(url)
                if response:
                    return BeautifulSoup(response.text, 'lxml')
            else:
                # Fall back to the old method
                response = make_request(url)
                if response:
                    return BeautifulSoup(response, 'lxml')
            return None
    
    @abstractmethod
    def search_products(self, keywords=None, category=None):
        """Search for products using keywords or category."""
        pass
    
    @abstractmethod
    def get_product_details(self, product_url):
        """Extract detailed information about a specific product."""
        pass
    
    def scrape_site(self):
        """Main method to scrape the site for deals."""
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
            
    def scrape(self):
        """Alias for scrape_site() for backward compatibility."""
        logger.info(f"Using scrape() method for {self.name}")
        return self.scrape_site()
