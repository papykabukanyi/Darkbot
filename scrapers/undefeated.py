"""
Scraper for undefeated.com
"""

import logging
import json
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scrapers.base_scraper import BaseSneakerScraper, format_price, extract_price

logger = logging.getLogger("SneakerBot")

class UndefeatedScraper(BaseSneakerScraper):
    """Scraper for undefeated.com"""
    
    def __init__(self, site_config):
        super().__init__(site_config)
        self.name = "Undefeated"
        self.site_config = site_config  # Store the site config for later use
    
    def search_products(self, keywords: List[str] = None, category: str = None) -> List[Dict]:
        """
        Search for products on undefeated.com
        
        Args:
            keywords: List of keywords to search for
            category: Category to browse (e.g., 'sale')
            
        Returns:
            List of product dictionaries with basic info
        """
        products = []
        
        # Determine the URL to scrape
        if category and category.lower() == 'sale':
            # Check if there's a specific sale URL in the site config
            url = self.site_config.get('sale_url', f"{self.base_url}/collections/sale")
        elif keywords:
            search_term = '+'.join(keywords)
            # Check if there's a specific search URL format in the site config
            search_url_template = self.site_config.get('search_url_template', f"{self.base_url}/search?type=product&q={{keywords}}")
            url = search_url_template.format(keywords=search_term)
        else:
            # Check if there's a specific product URL in the site config
            url = self.site_config.get('product_url', f"{self.base_url}/collections/footwear")
        
        # Get the page
        logger.info(f"Scraping Undefeated URL: {url}")
        try:
            soup = self.get_page(url)
            if not soup:
                logger.warning(f"Failed to get page content from {url}")
                return products
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return products
        
        # Find product listings
        # Primary selector targeting product cards
        product_elements = soup.select('.product-card') or soup.select('.product-grid-item') or soup.select('.grid__item')
        
        logger.info(f"Found {len(product_elements)} product elements on Undefeated")
        
        for product_element in product_elements:
            try:
                # Find the product link
                link_element = product_element.select_one('a[href*="/products/"]')
                if not link_element:
                    continue
                
                product_url = urljoin(self.base_url, link_element.get('href', ''))
                
                # Find the title
                title_element = product_element.select_one('.product-card__title') or product_element.select_one('.grid-product__title')
                if not title_element:
                    title_element = link_element  # Use link text as fallback
                
                title = title_element.get_text().strip()
                
                # Find the price - look for sale price first, then regular price
                price = None
                sale_price_element = product_element.select_one('.product-card__price--sale') or product_element.select_one('.sale-price')
                regular_price_element = product_element.select_one('.product-card__price') or product_element.select_one('.regular-price')
                
                if sale_price_element:
                    price = extract_price(sale_price_element.get_text())
                elif regular_price_element:
                    price = extract_price(regular_price_element.get_text())
                
                # Skip if no price found
                if not price:
                    continue
                
                # Find original price for discount calculation
                original_price = None
                original_price_element = product_element.select_one('.product-card__price--regular') or product_element.select_one('.compare-price')
                
                if original_price_element:
                    original_price = extract_price(original_price_element.get_text())
                else:
                    original_price = price  # If no original price, assume it's the same as current
                
                # Find image URL
                image_url = None
                image_element = product_element.select_one('img')
                if image_element:
                    # Try data-src first (for lazy loading), then regular src
                    image_url = image_element.get('data-src') or image_element.get('src')
                    
                    # Undefeated may use srcset - get the first URL
                    if not image_url and image_element.has_attr('srcset'):
                        srcset = image_element['srcset'].split(',')[0]
                        image_url = srcset.split(' ')[0]
                        
                    # Ensure absolute URL
                    if image_url and not image_url.startswith(('http://', 'https://')):
                        image_url = urljoin(self.base_url, image_url)
                
                # Calculate discount percentage
                discount_percent = 0
                if original_price and price and original_price > price:
                    discount_percent = round(((original_price - price) / original_price) * 100)
                
                # Extract brand from title
                brand = self.extract_brand_from_title(title)
                
                # Create product dictionary
                product = {
                    'title': title,
                    'url': product_url,
                    'price': price,
                    'original_price': original_price,
                    'discount_percent': discount_percent,
                    'image_url': image_url,
                    'site': 'undefeated',
                    'brand': brand,
                    'in_stock': True  # Assume in stock if listed
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Undefeated product: {e}")
                continue
        
        logger.info(f"Found {len(products)} products on Undefeated")
        return products
    
    def get_product_details(self, product_url: str) -> Dict:
        """
        Get detailed information about a product
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with product details
        """
        logger.info(f"Getting Undefeated product details from: {product_url}")
        product_info = {}
        
        soup = self.get_page(product_url)
        if not soup:
            return product_info
            
        try:
            # Extract title
            title_element = soup.select_one('h1.product__title') or soup.select_one('.product-single__title')
            if title_element:
                product_info['title'] = title_element.get_text().strip()
            
            # Extract price
            price_element = soup.select_one('.product__price--sale') or soup.select_one('.product__price') or soup.select_one('.product-single__price')
            if price_element:
                product_info['price'] = extract_price(price_element.get_text())
            
            # Extract original price
            original_price_element = soup.select_one('.product__price--regular') or soup.select_one('.product-single__price--compare')
            if original_price_element:
                product_info['original_price'] = extract_price(original_price_element.get_text())
                
                # Calculate discount percentage
                if 'price' in product_info and 'original_price' in product_info and product_info['original_price'] > product_info['price']:
                    product_info['discount_percent'] = round(((product_info['original_price'] - product_info['price']) / product_info['original_price']) * 100)
            
            # Extract images
            images = []
            image_elements = soup.select('.product__image-wrapper img') or soup.select('.product-single__photo img')
            for img in image_elements:
                image_url = img.get('data-src') or img.get('src')
                if image_url:
                    # Remove any URL parameters or sizes
                    if '?' in image_url:
                        image_url = image_url.split('?')[0]
                    
                    # Ensure absolute URL
                    if not image_url.startswith(('http://', 'https://')):
                        image_url = urljoin(self.base_url, image_url)
                        
                    images.append(image_url)
            
            if images:
                product_info['images'] = images
                product_info['image_url'] = images[0]
            
            # Extract description
            description_element = soup.select_one('.product__description') or soup.select_one('.product-single__description')
            if description_element:
                product_info['description'] = description_element.get_text().strip()
            
            # Extract SKU/style code
            sku_element = soup.select_one('[itemprop="sku"]') or soup.select_one('.product-single__sku')
            if sku_element:
                product_info['sku'] = sku_element.get_text().strip()
            else:
                # Try to find it in the description or elsewhere
                for element in soup.select('p, div, span'):
                    text = element.get_text()
                    if 'SKU:' in text or 'Style:' in text or 'Style Code:' in text:
                        sku_match = re.search(r'(?:SKU|Style|Style Code):\s*([A-Za-z0-9\-]+)', text)
                        if sku_match:
                            product_info['sku'] = sku_match.group(1).strip()
                            break
            
            # Extract availability
            product_info['in_stock'] = True  # Assume in stock by default
            sold_out_elements = soup.select('.sold-out-text, .product--sold-out, [data-sold-out="true"]')
            if sold_out_elements:
                product_info['in_stock'] = False
            
            # Look for product JSON data which might contain additional info
            for script in soup.find_all('script', type='application/json'):
                if 'ProductJson' in script.get('id', ''):
                    try:
                        data = json.loads(script.string)
                        if 'title' in data and not product_info.get('title'):
                            product_info['title'] = data['title']
                        if 'vendor' in data and data['vendor']:
                            product_info['brand'] = data['vendor']
                        if 'price' in data and not product_info.get('price'):
                            product_info['price'] = float(data['price']) / 100  # Shopify stores price in cents
                        if 'compare_at_price' in data and data['compare_at_price']:
                            product_info['original_price'] = float(data['compare_at_price']) / 100
                        if 'available' in data:
                            product_info['in_stock'] = data['available']
                    except:
                        pass
            
            # If brand not found yet, try to extract from title
            if 'brand' not in product_info and 'title' in product_info:
                product_info['brand'] = self.extract_brand_from_title(product_info['title'])
            
            # Add site name
            product_info['site'] = 'undefeated'
            
            # Add URL
            product_info['url'] = product_url
            
        except Exception as e:
            logger.error(f"Error getting Undefeated product details: {e}")
        
        return product_info
    
    def extract_brand_from_title(self, title):
        """Extract brand name from product title."""
        common_brands = ['Nike', 'Adidas', 'Jordan', 'New Balance', 'Asics', 
                         'Puma', 'Reebok', 'Yeezy', 'Converse', 'Vans', 
                         'Under Armour', 'Saucony', 'Diadora', 'Fila']
        
        for brand in common_brands:
            if brand.lower() in title.lower():
                return brand
        
        # Check for "Air Jordan" which is commonly listed as just "Air"
        if 'air' in title.lower() and 'jordan' in title.lower():
            return 'Jordan'
            
        # Default to unknown if no brand found
        return 'Unknown'
