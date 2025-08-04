"""
Scraper for StockX.com
"""

import logging
import time
import random
import json
import re
import html
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

from scrapers.base_scraper import BaseSneakerScraper, format_price, extract_price, random_delay

logger = logging.getLogger("SneakerBot")

class StockXScraper(BaseSneakerScraper):
    """Scraper for StockX.com that behaves like a human user"""
    
    def __init__(self, site_config):
        super().__init__(site_config)
        self.name = "StockX"
        self.site_config = site_config
        # StockX is heavily dependent on JavaScript, so we should use Selenium
        self.requires_selenium = True
        # Rate limits to avoid detection
        self.rate_limit = site_config.get('rate_limit', 20)
        # Track session cookies
        self.cookies = {}
        # Use random user agent rotation
        self.rotate_user_agent = True
    
    def _prepare_driver(self):
        """
        Prepare the Selenium driver with additional settings to avoid detection
        """
        if not self.driver:
            return
            
        # StockX-specific browser settings to avoid detection
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                // Overwrite navigator properties to appear as a normal browser
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
                
                // Make sure chrome automation extension isn't detected
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {
                                type: "application/x-google-chrome-pdf",
                                description: "Portable Document Format"
                            },
                            name: "Chrome PDF Plugin",
                            filename: "internal-pdf-viewer"
                        }
                    ],
                });
                
                // Modify other detection mechanisms
                window.chrome = {
                    runtime: {}
                };
            """
        })
        
        # Add a random mouse movement simulation
        self.driver.execute_script("""
            // Create a fake mouse movement
            const createMouseEvent = function() {
                const event = new MouseEvent('mousemove', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true,
                    'clientX': Math.floor(Math.random() * window.innerWidth),
                    'clientY': Math.floor(Math.random() * window.innerHeight)
                });
                document.dispatchEvent(event);
            };
            
            // Schedule random mouse movements
            setInterval(createMouseEvent, Math.floor(Math.random() * 2000) + 500);
        """)
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get page with additional human-like behavior
        """
        # Apply rate limiting
        random_delay(self.rate_limit)
        
        # First try with regular requests if enabled
        if not self.requires_selenium:
            try:
                response = self.session.get(url, headers=self.get_headers(), timeout=30)
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                logger.warning(f"Failed to get page with requests: {response.status_code}. Trying with Selenium")
            except Exception as e:
                logger.error(f"Error with requests: {e}")
        
        # Fall back to Selenium or use it directly if required
        if not self.driver:
            self._initialize_selenium()
            
        if not self.driver:
            logger.error("Failed to initialize Selenium driver")
            return None
            
        # Apply additional preparations
        self._prepare_driver()
        
        try:
            # Navigate to the page
            self.driver.get(url)
            
            # Human-like scrolling behavior
            self._scroll_page_like_human()
            
            # Extra wait for JavaScript execution
            time.sleep(random.uniform(2, 5))
            
            # Save cookies from the session
            for cookie in self.driver.get_cookies():
                self.cookies[cookie['name']] = cookie['value']
            
            # Get the page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            
            # Check if we got escaped HTML (common issue with some sites)
            if '\\u003C' in page_source:
                logger.info("Detected escaped HTML content, applying unescape")
                # Unescape the HTML content
                unescaped_html = html.unescape(page_source)
                # Replace common unicode escape sequences
                unescaped_html = unescaped_html.replace('\\u003C', '<').replace('\\u003E', '>')
                return BeautifulSoup(unescaped_html, 'lxml')
            
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error getting page with Selenium: {e}")
            return None
    
    def _scroll_page_like_human(self):
        """
        Scroll the page in a way that mimics human behavior
        """
        if not self.driver:
            return
            
        try:
            # Get total height of page
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Calculate number of scroll steps
            num_steps = random.randint(5, 10)
            scroll_step = total_height / num_steps
            
            # Execute scrolling
            for i in range(num_steps):
                # Calculate target position with some randomness
                target = int((i+1) * scroll_step * random.uniform(0.8, 1.2))
                target = min(target, total_height)
                
                # Execute scroll
                self.driver.execute_script(f"window.scrollTo(0, {target});")
                
                # Add random pauses
                time.sleep(random.uniform(0.5, 2.0))
                
                # Sometimes jiggle a bit
                if random.random() > 0.7:
                    jiggle = random.randint(-100, 100)
                    self.driver.execute_script(f"window.scrollBy(0, {jiggle});")
                    time.sleep(random.uniform(0.2, 0.5))
        except Exception as e:
            logger.error(f"Error during scrolling: {e}")
    
    def search_products(self, keywords: List[str] = None, category: str = None) -> List[Dict]:
        """
        Search for products on StockX
        
        Args:
            keywords: List of keywords to search for
            category: Category to browse (e.g., 'sale')
            
        Returns:
            List of product dictionaries with basic info
        """
        products = []
        
        # Determine the URL to scrape
        if category and category.lower() == 'sale':
            url = self.site_config.get('sale_url', f"{self.base_url}/sneakers/under-retail")
        elif keywords:
            search_term = ' '.join(keywords)
            encoded_search = quote_plus(search_term)
            url = f"{self.base_url}/search/sneakers?s={encoded_search}"
        else:
            url = f"{self.base_url}/sneakers/most-popular"
        
        # Get the page
        logger.info(f"Scraping StockX URL: {url}")
        soup = self.get_page(url)
        if not soup:
            logger.error(f"Failed to get page content from {url}")
            return products
        
        # StockX uses data-testid attributes extensively
        product_elements = soup.select('[data-testid="product-tile"]')
        
        # If no products found via data-testid, try other selectors
        if not product_elements:
            product_elements = soup.select('.css-1ibvugw-GridProductTileContainer') or \
                               soup.select('.tile') or \
                               soup.select('.product-tile')
        
        logger.info(f"Found {len(product_elements)} product elements on StockX")
        
        for product_element in product_elements:
            try:
                # Extract product information
                
                # Find product link - StockX uses <a> tags with nested product info
                link_element = product_element.select_one('a')
                if not link_element:
                    continue
                    
                product_url = urljoin(self.base_url, link_element.get('href', ''))
                
                # Find title
                title_element = product_element.select_one('[data-testid="product-tile-title"]') or \
                                product_element.select_one('.css-1f15vqz-ProductTileTitle') or \
                                product_element.select_one('.product-title')
                                
                title = title_element.get_text().strip() if title_element else "Unknown"
                
                # Find price - current market price
                price_element = product_element.select_one('[data-testid="product-tile-price"]') or \
                                product_element.select_one('.css-wpooly-LatestSalePriceContainer') or \
                                product_element.select_one('.sale-price')
                                
                price_text = price_element.get_text().strip() if price_element else ""
                price = extract_price(price_text)
                
                # Find retail price (original price)
                retail_element = product_element.select_one('[data-testid="product-tile-retail-price"]') or \
                                 product_element.select_one('.css-88grjm-RetailPriceContainer') or \
                                 product_element.select_one('.retail-price')
                                 
                if retail_element:
                    retail_text = retail_element.get_text().strip()
                    original_price = extract_price(retail_text)
                else:
                    original_price = price  # If no retail price found, use market price
                
                # Find image
                image_element = product_element.select_one('img')
                image_url = ""
                
                if image_element:
                    # StockX uses data-src for lazy loading or src attribute
                    image_url = image_element.get('data-src') or image_element.get('src', '')
                    if image_url and not image_url.startswith('http'):
                        image_url = urljoin(self.base_url, image_url)
                
                # Create product dictionary
                product = {
                    'title': title,
                    'price': price,
                    'url': product_url,
                    'image': image_url,
                    'site': 'stockx',
                    'brand': self.extract_brand_from_title(title),
                }
                
                # Add original price and calculate discount if applicable
                if original_price and original_price > price:
                    product['original_price'] = original_price
                    product['discount_percent'] = round(((original_price - price) / original_price) * 100, 2)
                
                # Only add products with valid data
                if product['title'] != "Unknown" and product['price'] > 0 and product['url']:
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error processing StockX product: {e}")
        
        logger.info(f"Found {len(products)} products on StockX")
        return products
    
    def get_product_details(self, product_url: str) -> Dict:
        """
        Get detailed information about a product
        
        Args:
            product_url: URL of the product
            
        Returns:
            Dictionary with product details
        """
        product_info = {}
        
        try:
            logger.info(f"Getting product details from {product_url}")
            soup = self.get_page(product_url)
            if not soup:
                logger.error(f"Failed to load product page: {product_url}")
                return product_info
            
            # Extract product title
            title_element = soup.select_one('[data-testid="product-title"]') or \
                           soup.select_one('.css-1ou6bb2-Title')
            if title_element:
                product_info['title'] = title_element.get_text().strip()
            
            # Extract price - current lowest ask
            price_element = soup.select_one('[data-testid="product-market-value"]') or \
                           soup.select_one('.css-1l1l5y-ValueText')
            if price_element:
                product_info['price'] = extract_price(price_element.get_text())
            
            # Extract retail price
            retail_element = soup.select_one('[data-testid="product-retail-price"]') or \
                            soup.select_one('.css-1l1l5y-RetailText')
            if retail_element:
                retail_text = retail_element.get_text().strip()
                product_info['original_price'] = extract_price(retail_text)
                
                # Calculate discount if applicable
                if 'price' in product_info and product_info['original_price'] > product_info['price']:
                    product_info['discount_percent'] = round(
                        ((product_info['original_price'] - product_info['price']) / product_info['original_price']) * 100, 2
                    )
            
            # Extract style/SKU
            sku_element = soup.select_one('[data-testid="product-style-id"]') or \
                         soup.select_one('.css-1bmnjdv-StyleIdHeader')
            if sku_element:
                product_info['sku'] = sku_element.get_text().strip().replace('Style: ', '')
            
            # Extract release date
            release_element = soup.select_one('[data-testid="product-release-date"]') or \
                             soup.select_one('.css-1bmnjdv-ReleaseDate')
            if release_element:
                product_info['release_date'] = release_element.get_text().strip().replace('Release Date: ', '')
            
            # Extract description
            desc_element = soup.select_one('[data-testid="product-description"]') or \
                          soup.select_one('.css-hpmkd3-ProductDescription')
            if desc_element:
                product_info['description'] = desc_element.get_text().strip()
            
            # Extract brand
            brand = self.extract_brand_from_title(product_info.get('title', ''))
            if brand:
                product_info['brand'] = brand
            
            # Extract images
            image_elements = soup.select('[data-testid="product-image"] img') or \
                            soup.select('.css-1u3hop5-ProductCarouselDesktop img')
            if image_elements:
                product_info['images'] = [img.get('src') for img in image_elements if img.get('src')]
            
            # Extract sizes and prices
            size_elements = soup.select('[data-testid="product-size-button"]') or \
                           soup.select('.css-1uym1qd-BaseButton-PrimaryButtonWithSizes')
            
            if size_elements:
                sizes_data = []
                for size_elem in size_elements:
                    size_text = size_elem.get_text().strip()
                    # Some size buttons include price
                    if '$' in size_text:
                        size_parts = size_text.split('$')
                        size = size_parts[0].strip()
                        size_price = extract_price('$' + size_parts[1])
                        sizes_data.append({'size': size, 'price': size_price})
                    else:
                        sizes_data.append({'size': size_text, 'price': product_info.get('price')})
                
                product_info['sizes'] = sizes_data
            
            # Extract last sale info
            last_sale_element = soup.select_one('[data-testid="last-sale"]') or \
                               soup.select_one('.css-5bls5h-LastSaleValue')
            if last_sale_element:
                product_info['last_sale'] = extract_price(last_sale_element.get_text())
            
            # Add market data
            product_info['site'] = 'stockx'
            product_info['url'] = product_url
            product_info['market_price'] = True  # StockX is a market price reference
            
            # Try to determine if item has resale value
            if 'original_price' in product_info and 'last_sale' in product_info:
                if product_info['last_sale'] > product_info['original_price']:
                    product_info['resale_value'] = round(
                        ((product_info['last_sale'] - product_info['original_price']) / product_info['original_price']) * 100, 2
                    )
            
        except Exception as e:
            logger.error(f"Error processing StockX product details: {e}")
        
        return product_info
    
    def extract_brand_from_title(self, title: str) -> str:
        """
        Extract brand from product title
        
        Args:
            title: Product title
            
        Returns:
            Brand name or empty string
        """
        if not title:
            return ""
            
        # Common sneaker brands to check for
        common_brands = [
            "Nike", "Jordan", "Air Jordan", "Adidas", "Yeezy", "New Balance",
            "Converse", "Puma", "Reebok", "Asics", "Vans", "Under Armour",
            "Balenciaga", "Gucci", "Off-White", "Dior", "Louis Vuitton",
            "Bape", "Supreme", "Saucony", "Salomon", "On", "Hoka"
        ]
        
        # Check for each brand in the title
        for brand in common_brands:
            if brand.lower() in title.lower():
                return brand
                
        # If no specific brand found, try to extract the first word as it's often the brand
        first_word = title.split(' ')[0]
        if len(first_word) > 2:  # Avoid single letters or short prefixes
            return first_word
            
        return ""
    
    def __del__(self):
        """
        Clean up resources
        """
        try:
            # Close the Selenium driver if it exists
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
        except Exception:
            pass
