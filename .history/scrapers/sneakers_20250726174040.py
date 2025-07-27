"""
Scraper for sneakers.com
"""

import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils import format_price, random_delay

logger = logging.getLogger("SneakerBot")

class SneakersScraper(BaseScraper):
    """Scraper for sneakers.com"""
    
    def __init__(self, site_config):
        super().__init__(site_config)
        self.name = "Sneakers.com"
    
    def search_products(self, keywords: List[str] = None, category: str = None) -> List[Dict]:
        """
        Search for products on sneakers.com
        
        Args:
            keywords: List of keywords to search for
            category: Category to browse (e.g., 'sale')
            
        Returns:
            List of product dictionaries with basic info
        """
        products = []
        
        # Determine the URL to scrape
        if category and category.lower() == 'sale':
            url = f"{self.base_url}/collections/sale"
        elif keywords:
            search_term = '+'.join(keywords)
            url = f"{self.base_url}/search?q={search_term}"
        else:
            url = f"{self.base_url}/collections/sneakers"
        
        # Get the page
        soup = self.get_page(url)
        if not soup:
            return products
        
        # Find product listings
        # Note: This is a generic approach, will need to be adjusted for the actual site structure
        product_elements = soup.select('.product-item') or soup.select('.product-card')
        
        for product in product_elements:
            try:
                # Extract product information
                title_element = product.select_one('.product-title') or product.select_one('.product-name')
                price_element = product.select_one('.product-price') or product.select_one('.price')
                link_element = product.select_one('a')
                image_element = product.select_one('img')
                
                # Get the data
                title = title_element.text.strip() if title_element else "Unknown"
                
                # Handle different price formats
                price_text = price_element.text.strip() if price_element else ""
                price = format_price(price_text)
                
                # Check if there's a sale price
                original_price_element = product.select_one('.original-price') or product.select_one('.compare-at-price')
                original_price = format_price(original_price_element.text) if original_price_element else price
                
                # Get the product URL
                product_url = link_element['href'] if link_element and 'href' in link_element.attrs else ""
                if product_url and not product_url.startswith('http'):
                    product_url = self.base_url + product_url if not product_url.startswith('/') else self.base_url + product_url
                
                # Get the image URL
                image_url = image_element['src'] if image_element and 'src' in image_element.attrs else ""
                if image_url and not image_url.startswith('http'):
                    image_url = "https:" + image_url if image_url.startswith('//') else self.base_url + image_url
                
                # Create the product dictionary
                product_data = {
                    "title": title,
                    "price": price,
                    "original_price": original_price,
                    "url": product_url,
                    "image_url": image_url,
                    "source": self.name,
                    "on_sale": original_price > price
                }
                
                # Only add products that have all required information
                if product_data["title"] != "Unknown" and product_data["price"] > 0 and product_data["url"]:
                    products.append(product_data)
            
            except Exception as e:
                logger.error(f"Error extracting product data: {e}")
                continue
        
        logger.info(f"Found {len(products)} products on {url}")
        return products
    
    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Extract detailed information from a product page
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dictionary with product details
        """
        soup = self.get_page(product_url)
        if not soup:
            return None
        
        try:
            # Extract product details
            title = soup.select_one('h1.product-title').text.strip() if soup.select_one('h1.product-title') else "Unknown"
            
            # Get price information
            price_element = soup.select_one('.product-price') or soup.select_one('.price')
            price = format_price(price_element.text) if price_element else 0
            
            # Get original price if on sale
            original_price_element = soup.select_one('.original-price') or soup.select_one('.compare-at-price')
            original_price = format_price(original_price_element.text) if original_price_element else price
            
            # Get product description
            description = ""
            desc_element = soup.select_one('.product-description') or soup.select_one('.description')
            if desc_element:
                description = desc_element.text.strip()
            
            # Get available sizes
            sizes = []
            size_elements = soup.select('.size-option') or soup.select('.variant-option')
            for size_elem in size_elements:
                size_text = size_elem.text.strip()
                availability = not ('unavailable' in size_elem.get('class', []) or 'sold-out' in size_elem.get('class', []))
                sizes.append({
                    "size": size_text,
                    "available": availability
                })
            
            # Get brand information
            brand = "Unknown"
            brand_element = soup.select_one('.product-brand') or soup.select_one('.vendor')
            if brand_element:
                brand = brand_element.text.strip()
            elif "nike" in title.lower():
                brand = "Nike"
            elif "adidas" in title.lower():
                brand = "Adidas"
            elif "jordan" in title.lower():
                brand = "Jordan"
            
            # Get product images
            images = []
            image_elements = soup.select('.product-image img') or soup.select('.product-gallery img')
            for img in image_elements:
                if 'src' in img.attrs:
                    img_url = img['src']
                    if not img_url.startswith('http'):
                        img_url = "https:" + img_url if img_url.startswith('//') else self.base_url + img_url
                    images.append(img_url)
            
            # Compile the product data
            product_data = {
                "title": title,
                "price": price,
                "original_price": original_price,
                "url": product_url,
                "description": description,
                "brand": brand,
                "sizes": sizes,
                "images": images,
                "source": self.name,
                "on_sale": original_price > price,
                "discount_percent": round(((original_price - price) / original_price) * 100) if original_price > price else 0
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product details from {product_url}: {e}")
            return None
