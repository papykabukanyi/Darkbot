"""
Fallback scraper implementation for sites without a dedicated scraper.
"""

import logging
import datetime
from typing import Dict, List, Optional, Any
from importlib import import_module
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
        Enhanced implementation of search_products for unknown sites.
        Attempts to find some products by making generic searches.
        
        Args:
            keywords: Search keywords (optional)
            category: Product category (optional)
            
        Returns:
            List of product dictionaries if found, otherwise empty list
        """
        logger.info(f"Attempting to search for products on {self.name} using generic approach")
        
        try:
            # Use the base URL and add some common search paths
            search_url = self.base_url
            
            if category == "sale":
                search_paths = [
                    "/sale", 
                    "/clearance", 
                    "/discount",
                    "/promotions",
                    "/special-offers",
                    "/deals"
                ]
            else:
                # Try to find sneakers section
                search_paths = [
                    "/sneakers",
                    "/shoes/sneakers",
                    "/footwear/sneakers",
                    "/shoes"
                ]
            
            # Try each search path
            for path in search_paths:
                try:
                    url = f"{self.base_url.rstrip('/')}{path}"
                    logger.info(f"Trying URL: {url}")
                    
                    soup = self.get_page(url)
                    if not soup:
                        continue
                    
                    # Look for product elements - common patterns
                    product_elements = []
                    
                    # Method 1: Look for items with price
                    product_elements.extend(soup.select(".product-item, .product, .item, [class*='product']"))
                    
                    # Method 2: Look for price elements and find their parent containers
                    price_elements = soup.select("[class*='price'], .price, span[class*='price'], div[class*='price']")
                    for price_el in price_elements:
                        for parent in price_el.parents:
                            if parent.name in ['div', 'li', 'article']:
                                if parent not in product_elements:
                                    product_elements.append(parent)
                                break
                                
                    # Extract basic product info
                    products = []
                    for element in product_elements[:15]:  # Limit to 15 products
                        # Extract product URL
                        link = element.select_one("a[href]")
                        if not link:
                            continue
                            
                        product_url = link.get("href")
                        if product_url and not product_url.startswith("http"):
                            product_url = f"{self.base_url.rstrip('/')}{product_url}"
                            
                        # Try to extract title
                        title_el = element.select_one("h1, h2, h3, h4, h5, .title, .product-title, [class*='title']")
                        title = title_el.get_text().strip() if title_el else "Unknown Product"
                        
                        # Try to extract price
                        price_el = element.select_one(".price, [class*='price'], .current-price")
                        price_text = price_el.get_text().strip() if price_el else ""
                        price = 0.0
                        if price_text:
                            import re
                            price_match = re.search(r'\d+(\.\d+)?', price_text)
                            if price_match:
                                try:
                                    price = float(price_match.group())
                                except ValueError:
                                    price = 0.0
                                    
                        # Create product object
                        product = {
                            "title": title,
                            "url": product_url,
                            "price": price,
                            "site": self.name
                        }
                        products.append(product)
                        
                    if products:
                        logger.info(f"Found {len(products)} products on {self.name} using generic scraper")
                        return products
                        
                except Exception as e:
                    logger.error(f"Error searching path {path} on {self.name}: {e}")
                    continue
                    
            logger.warning(f"No products found on {self.name} after trying all search paths")
            return []
            
        except Exception as e:
            logger.error(f"Error in fallback search_products for {self.name}: {e}")
            return []
    
    def get_product_details(self, product_url):
        """
        Enhanced implementation of get_product_details for unknown sites.
        Attempts to extract product details using common patterns.
        
        Args:
            product_url: URL of the product
            
        Returns:
            Dictionary of product details if found, otherwise None
        """
        logger.info(f"Attempting to get product details from {product_url}")
        
        try:
            # Get the product page
            soup = self.get_page(product_url)
            if not soup:
                logger.error(f"Failed to load page: {product_url}")
                return None
                
            # Extract product details
            # 1. Title
            title_element = soup.select_one("h1, .product-title, .title, [class*='product-name'], [class*='product-title']")
            title = title_element.get_text().strip() if title_element else "Unknown Product"
            
            # 2. Current price
            price_element = soup.select_one(".price, .current-price, [class*='current-price'], [class*='sale-price']")
            price_text = price_element.get_text().strip() if price_element else ""
            price = 0.0
            if price_text:
                import re
                price_match = re.search(r'\d+(\.\d+)?', price_text)
                if price_match:
                    try:
                        price = float(price_match.group())
                    except ValueError:
                        price = 0.0
            
            # 3. Original price / MSRP
            original_price_element = soup.select_one(".original-price, .msrp, .regular-price, .compare-at, [class*='original-price'], [class*='msrp']")
            original_price_text = original_price_element.get_text().strip() if original_price_element else ""
            original_price = price  # Default to current price if no original price found
            if original_price_text:
                import re
                original_match = re.search(r'\d+(\.\d+)?', original_price_text)
                if original_match:
                    try:
                        original_price = float(original_match.group())
                    except ValueError:
                        original_price = price
            
            # 4. Brand
            brand_element = soup.select_one("[class*='brand'], .brand, [itemprop='brand']")
            brand = brand_element.get_text().strip() if brand_element else "Unknown"
            
            # 5. Image URL
            image_element = soup.select_one("img.product-image, img[class*='product'], .product-image img")
            image_url = ""
            if image_element:
                image_url = image_element.get("src", "")
                if image_url and not image_url.startswith("http"):
                    image_url = f"{self.base_url.rstrip('/')}{image_url}"
            
            # 6. Discount calculation
            discount_percent = 0
            if original_price > price and original_price > 0:
                discount_percent = ((original_price - price) / original_price) * 100
            
            # 7. Product details / description
            description_element = soup.select_one(".product-description, .description, [class*='description']")
            description = description_element.get_text().strip() if description_element else ""
            
            # Create product details object
            product_details = {
                "title": title,
                "brand": brand,
                "price": price,
                "original_price": original_price,
                "discount_percent": discount_percent,
                "site": self.name,
                "url": product_url,
                "image_url": image_url,
                "description": description,
                "available": True,  # Assume it's available
                "created_at": datetime.datetime.now().isoformat()
            }
            
            logger.info(f"Successfully extracted details for {title} from {self.name}")
            return product_details
            
        except Exception as e:
            logger.error(f"Error in fallback get_product_details for {product_url}: {e}")
            return None
