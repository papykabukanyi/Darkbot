"""
StockX Price Adapter - Gets price data from StockX
"""

import logging
import time
import random
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup

# Import config
from config import get_random_user_agent, get_random_delay

logger = logging.getLogger("SneakerBot")

class StockXAdapter:
    """Adapter for retrieving price data from StockX."""
    
    def __init__(self, config):
        """Initialize the adapter with configuration."""
        self.name = "StockX"
        self.config = config
        self.base_url = config.get('url', 'https://stockx.com')
        self.search_url = config.get('search_url', 'https://stockx.com/api/browse')
        self.product_url = config.get('product_url', 'https://stockx.com/api/products')
        self.use_proxy = config.get('use_proxy', False)
        self.session = requests.Session()
        self.headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://stockx.com/',
            'Origin': 'https://stockx.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
    
    def search_product(self, query, retries=3):
        """
        Search for a product on StockX.
        
        Args:
            query: Search query
            retries: Number of retries
            
        Returns:
            List of search results
        """
        params = {
            '_search': query,
            'dataType': 'product',
            'limit': 10
        }
        
        for attempt in range(retries):
            try:
                logger.info(f"Searching StockX for: {query}")
                
                # Random delay to avoid rate limiting
                get_random_delay()
                
                # Update User-Agent for each request
                self.headers['User-Agent'] = get_random_user_agent()
                
                response = self.session.get(
                    self.search_url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        products = data.get('Products', [])
                        logger.info(f"Found {len(products)} products on StockX")
                        return products
                    except json.JSONDecodeError:
                        logger.error("Failed to parse StockX search response as JSON")
                else:
                    logger.warning(f"StockX search failed with status {response.status_code}")
            except Exception as e:
                logger.error(f"Error searching StockX: {str(e)}")
            
            # Wait before retry
            wait_time = (attempt + 1) * 2
            logger.debug(f"Retrying StockX search in {wait_time} seconds...")
            time.sleep(wait_time)
        
        logger.error(f"Failed to search StockX after {retries} attempts")
        return []
    
    def get_product_details(self, sku=None, name=None, retries=3):
        """
        Get detailed information for a product by SKU or name.
        
        Args:
            sku: Product SKU
            name: Product name (used if SKU is not provided)
            retries: Number of retries
            
        Returns:
            Product details as dictionary
        """
        # First search for the product
        search_query = sku if sku else name
        if not search_query:
            logger.error("No SKU or name provided for StockX product lookup")
            return None
        
        products = self.search_product(search_query, retries)
        
        if not products:
            logger.warning(f"No products found on StockX for {search_query}")
            return None
        
        # Find the best match
        product = None
        if sku:
            # Try to find by SKU exact match first
            for p in products:
                if p.get('styleId', '').lower() == sku.lower():
                    product = p
                    break
        
        # If no match by SKU or no SKU provided, use the first result
        if not product and products:
            product = products[0]
        
        if not product:
            return None
        
        # Extract necessary information
        return {
            'name': product.get('name', 'Unknown'),
            'sku': product.get('styleId'),
            'brand': product.get('brand', 'Unknown'),
            'colorway': product.get('colorway'),
            'release_date': product.get('releaseDate'),
            'retail_price': product.get('retailPrice'),
            'market_price': self._get_market_price(product),
            'image_url': product.get('media', {}).get('imageUrl'),
            'url': f"{self.base_url}/{product.get('urlKey')}",
            'source': 'StockX'
        }
    
    def _get_market_price(self, product):
        """Extract the market price from a product."""
        try:
            market_data = product.get('market', {})
            return market_data.get('lastSale') or market_data.get('lowestAsk')
        except Exception:
            return None
    
    def get_product_by_name(self, name, retries=3):
        """Get product details by name."""
        return self.get_product_details(name=name, retries=retries)
    
    def get_product_by_sku(self, sku, retries=3):
        """Get product details by SKU."""
        return self.get_product_details(sku=sku, retries=retries)
