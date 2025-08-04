import logging
import re
import random
import time
import requests
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

class StockXAdapter:
    """Adapter for fetching prices from StockX"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the StockX adapter.
        
        Args:
            config: Configuration for the adapter
        """
        self.config = config or {}
        self.headers = self._get_headers()
        self.base_url = "https://stockx.com/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36 Edg/91.0.864.53",
        ]
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers.
        
        Returns:
            Request headers
        """
        user_agent = random.choice(self.user_agents) if hasattr(self, 'user_agents') else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        return {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
    
    def get_price(self, query: str) -> Optional[float]:
        """
        Get the market price for a sneaker from StockX.
        
        Args:
            query: SKU or name of the sneaker
            
        Returns:
            Market price as a float, or None if not found
        """
        if not query:
            logger.warning("Cannot get price without query")
            return None
        
        # Replace spaces with + for URL formatting
        formatted_query = query.replace(" ", "+")
        url = f"{self.base_url}?s={formatted_query}"
        logger.info(f"Fetching StockX price for query: {query} from {url}")
        
        try:
            # Add random delay to appear more human-like
            time.sleep(random.uniform(1.0, 3.0))
            
            # Rotate user agent
            self.headers = self._get_headers()
            
            # Make the request
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch StockX price for query: {query}: Status code {response.status_code}")
                return None
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the price element
            price_element = soup.select_one('div.product-tile a div.product-price')
            if price_element:
                price_text = price_element.text.strip()
                return self._extract_price(price_text)
            
            # If we can't find the price element, we may need to try a different selector
            alternate_price_element = soup.select_one('div.css-1ny2kle div.chakra-text')
            if alternate_price_element:
                price_text = alternate_price_element.text.strip()
                return self._extract_price(price_text)
            
            logger.warning(f"Could not find price element on StockX for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Error fetching StockX price for query: {query}: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """
        Extract price from a string.
        
        Args:
            price_text: String containing a price
            
        Returns:
            Price as a float, or None if no price found
        """
        if not price_text:
            return None
        
        # Extract price using regex
        # This will match formats like $120, $1,200, etc.
        match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', price_text)
        if match:
            # Remove commas and convert to float
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert price string to float: {price_str}")
                return None
        
        logger.warning(f"Could not extract price from string: {price_text}")
        return None
