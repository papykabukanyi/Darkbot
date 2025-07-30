"""
Adidas website scraper.
"""

import logging
import re
import json
import time
import random
from typing import Dict, List, Any, Optional

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from scrapers.base_scraper import BaseSneakerScraper, random_delay

logger = logging.getLogger("SneakerBot")

class AdidasScraper(BaseSneakerScraper):
    """Scraper for Adidas website."""
    
    def __init__(self, site_config):
        """Initialize the scraper with site-specific configuration."""
        super().__init__(site_config)
        self.name = "Adidas"
        self.base_url = site_config.get('url', 'https://www.adidas.com')
        self.sale_url = site_config.get('sale_url', 'https://www.adidas.com/us/new_to_sale')
    
    def extract_product_data(self, product_element):
        """
        Extract product data from a product element.
        
        Args:
            product_element: BeautifulSoup element representing a product
            
        Returns:
            Dict with product data
        """
        try:
            # Extract product details (adapt selectors based on actual HTML structure)
            # Title
            title_element = product_element.select_one('.glass-product-card__title')
            if not title_element:
                title_element = product_element.select_one('[data-auto-id="product-card-title"]')
            if not title_element:
                title_element = product_element.select_one('h3')
                
            title = title_element.get_text().strip() if title_element else "Unknown Product"
            
            # Price
            price_element = product_element.select_one('[data-auto-id="sale-price"]')
            if not price_element:
                price_element = product_element.select_one('.price__sale')
            if not price_element:
                price_element = product_element.select_one('.gl-price-item--sale')
                
            price_text = price_element.get_text().strip() if price_element else None
            
            # Original price
            original_price_element = product_element.select_one('[data-auto-id="standard-price"]')
            if not original_price_element:
                original_price_element = product_element.select_one('.price__standard')
            if not original_price_element:
                original_price_element = product_element.select_one('.gl-price-item--crossed')
                
            original_price_text = original_price_element.get_text().strip() if original_price_element else None
            
            # Image URL
            img_element = product_element.select_one('img')
            image_url = img_element['src'] if img_element and 'src' in img_element.attrs else None
            
            # Product URL
            link_element = product_element.find('a')
            product_url = link_element['href'] if link_element and 'href' in link_element.attrs else None
            
            if product_url and not product_url.startswith('http'):
                product_url = self.base_url + (product_url if product_url.startswith('/') else '/' + product_url)
            
            # Extract numeric price values
            price = self.extract_price(price_text) if price_text else None
            original_price = self.extract_price(original_price_text) if original_price_text else price
            
            # Calculate discount percentage
            discount_percent = 0
            if price and original_price and original_price > price:
                discount_percent = round(((original_price - price) / original_price) * 100, 1)
            
            # Identify brand (always Adidas for this scraper)
            brand = "Adidas"
            
            # Get SKU/model number from URL or title
            sku = None
            if product_url:
                # Extract SKU from URL if possible
                sku_match = re.search(r'([A-Z0-9]{6})', product_url)
                if sku_match:
                    sku = sku_match.group(1)
            
            # Construct the product data dictionary
            product_data = {
                'title': title,
                'brand': brand,
                'price': price,
                'original_price': original_price,
                'discount_percent': discount_percent,
                'url': product_url,
                'image_url': image_url,
                'sku': sku,
                'site': self.name,
                'is_on_sale': discount_percent > 0,
                'currency': 'USD'  # Assuming USD for Adidas US site
            }
            
            return product_data
        
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None
    
    def extract_price(self, price_text):
        """
        Extract numeric price from text.
        
        Args:
            price_text: String containing the price
            
        Returns:
            Float price
        """
        if not price_text:
            return None
        
        # Remove currency symbols and other non-numeric characters, keep the decimal point
        price_match = re.search(r'(\d+\.?\d*)', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group(1))
        
        return None
    
    def search_products(self, keywords=None, category=None):
        """
        Search for products using keywords or category.
        
        Args:
            keywords: Search keywords
            category: Product category
            
        Returns:
            List of product data dictionaries
        """
        if keywords:
            url = f"{self.base_url}/us/search?q={'+'.join(keywords.split())}"
        elif category:
            url = f"{self.base_url}/us/{category}"
        else:
            url = self.sale_url
        
        logger.info(f"Searching products at URL: {url}")
        
        # Get the page
        soup = self.get_page(url)
        if not soup:
            return []
        
        # Find all product elements
        product_elements = soup.select('[data-auto-id="product-card"]')
        if not product_elements:
            product_elements = soup.select('.glass-product-card')
        
        logger.info(f"Found {len(product_elements)} product elements")
        
        # Extract data for each product
        products = []
        for product_element in product_elements:
            product_data = self.extract_product_data(product_element)
            if product_data:
                products.append(product_data)
        
        logger.info(f"Successfully extracted data for {len(products)} products")
        return products
    
    def get_product_details(self, product_url):
        """
        Extract detailed information about a specific product.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dict with detailed product information
        """
        logger.info(f"Getting product details from {product_url}")
        
        soup = self.get_page(product_url)
        if not soup:
            logger.error("Failed to get product page")
            return None
        
        try:
            # Extract product details
            # Title
            title_element = soup.select_one('h1.gl-heading')
            title = title_element.get_text().strip() if title_element else "Unknown Product"
            
            # Price
            price_element = soup.select_one('[data-auto-id="sale-price"]')
            if not price_element:
                price_element = soup.select_one('.gl-price-item--sale')
            price_text = price_element.get_text().strip() if price_element else None
            
            # Original price
            original_price_element = soup.select_one('[data-auto-id="standard-price"]')
            if not original_price_element:
                original_price_element = soup.select_one('.gl-price-item--crossed')
            original_price_text = original_price_element.get_text().strip() if original_price_element else None
            
            # Extract numeric price values
            price = self.extract_price(price_text) if price_text else None
            original_price = self.extract_price(original_price_text) if original_price_text else price
            
            # Calculate discount percentage
            discount_percent = 0
            if price and original_price and original_price > price:
                discount_percent = round(((original_price - price) / original_price) * 100, 1)
            
            # Brand (always Adidas)
            brand = "Adidas"
            
            # SKU/model number
            sku_element = soup.select_one('[data-auto-id="product-specification-value"]')
            sku = sku_element.get_text().strip() if sku_element else None
            
            # Description
            description_element = soup.select_one('.gl-vspace')
            description = description_element.get_text().strip() if description_element else None
            
            # Images
            images = []
            img_elements = soup.select('.img___31YYR')
            for img in img_elements:
                if 'src' in img.attrs:
                    images.append(img['src'])
            
            # Available sizes (if any)
            sizes = []
            size_elements = soup.select('[data-auto-id="size-selector"] button')
            for size_elem in size_elements:
                size_text = size_elem.get_text().strip()
                if size_text:
                    sizes.append(size_text)
            
            # Construct detailed product data
            product_details = {
                'title': title,
                'brand': brand,
                'price': price,
                'original_price': original_price,
                'discount_percent': discount_percent,
                'url': product_url,
                'images': images,
                'sku': sku,
                'description': description,
                'available_sizes': sizes,
                'site': self.name,
                'is_on_sale': discount_percent > 0,
                'currency': 'USD'  # Assuming USD for Adidas US site
            }
            
            return product_details
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None
    
    def scrape(self):
        """
        Main method to scrape the site for deals.
        
        Returns:
            List of deal dictionaries
        """
        logger.info("Starting Adidas scraper...")
        
        # Check if using Selenium for dynamic content
        if self.driver:
            try:
                logger.info(f"Navigating to {self.sale_url}")
                self.driver.get(self.sale_url)
                
                # Wait for product cards to load
                try:
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-auto-id="product-card"]'))
                    )
                except TimeoutException:
                    logger.warning("Timeout waiting for product cards to load, trying alternative selector")
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.glass-product-card'))
                        )
                    except TimeoutException:
                        logger.error("Could not find product cards with any selector")
                
                # Scroll down to load more products (infinite scroll handling)
                self.scroll_for_more_products()
                
                # Now parse the page content with BeautifulSoup
                html_content = self.driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Find all product elements
                product_elements = soup.select('[data-auto-id="product-card"]')
                if not product_elements:
                    product_elements = soup.select('.glass-product-card')
                
                logger.info(f"Found {len(product_elements)} product elements")
                
                # Extract data for each product
                deals = []
                for product_element in product_elements:
                    product_data = self.extract_product_data(product_element)
                    if product_data:
                        deals.append(product_data)
                
                logger.info(f"Successfully extracted data for {len(deals)} products")
                return deals
                
            except Exception as e:
                logger.error(f"Error in Adidas scraper: {e}")
                return []
        else:
            # Fallback to non-Selenium approach
            return self.search_products()
    
    def scroll_for_more_products(self, max_scrolls=5):
        """
        Scroll down the page to load more products in infinite scroll layouts.
        
        Args:
            max_scrolls: Maximum number of scrolls to perform
        """
        if not self.driver:
            return
        
        logger.info("Scrolling for more products...")
        
        # Get initial product count
        initial_products = len(self.driver.find_elements(By.CSS_SELECTOR, '[data-auto-id="product-card"]'))
        if initial_products == 0:
            initial_products = len(self.driver.find_elements(By.CSS_SELECTOR, '.glass-product-card'))
        
        logger.info(f"Initial product count: {initial_products}")
        
        # Scroll down multiple times with random delays to simulate human behavior
        for i in range(max_scrolls):
            # Scroll down
            self.driver.execute_script("window.scrollBy(0, 800);")
            
            # Random delay
            delay = random.uniform(1.0, 2.5)
            time.sleep(delay)
            
            # Check if new products loaded
            current_products = len(self.driver.find_elements(By.CSS_SELECTOR, '[data-auto-id="product-card"]'))
            if current_products == 0:
                current_products = len(self.driver.find_elements(By.CSS_SELECTOR, '.glass-product-card'))
            
            # If no new products after two scrolls, stop
            if i >= 2 and current_products <= initial_products:
                logger.info("No more products loading, stopping scrolling")
                break
            
            initial_products = current_products
            
        logger.info(f"Final product count after scrolling: {initial_products}")
