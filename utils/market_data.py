"""
Market data fetchers for real-time sneaker price comparison.
"""

import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional, Tuple
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """Base class for fetching market data from different sources."""
    
    def __init__(self, rate_limit=15):
        """
        Initialize the market data fetcher.
        
        Args:
            rate_limit: Seconds to wait between requests
        """
        self.rate_limit = rate_limit
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with a random user agent."""
        import random
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/'
        }
    
    def _make_request(self, url: str, method: str = 'GET', params: Dict = None, 
                    data: Dict = None, json_data: Dict = None) -> Optional[requests.Response]:
        """
        Make an HTTP request with rate limiting and retries.
        
        Args:
            url: URL to request
            method: HTTP method
            params: URL parameters
            data: Form data
            json_data: JSON data
            
        Returns:
            Response object if successful, None otherwise
        """
        # Wait for rate limit
        time.sleep(self.rate_limit)
        
        # Set up headers
        headers = self._get_headers()
        
        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too many requests
                    logger.warning(f"Rate limited by {url}. Waiting longer before retry.")
                    time.sleep(self.rate_limit * 2)
                else:
                    logger.error(f"Request to {url} failed with status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error making request to {url}: {e}")
                
            # Exponential backoff for retries
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                
        return None
    
    def search_by_name(self, product_name: str) -> List[Dict[str, Any]]:
        """
        Search for a product by name.
        
        Args:
            product_name: Name of the product to search for
            
        Returns:
            List of matching products with market data
        """
        # Implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")
        
    def search_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Search for a product by SKU.
        
        Args:
            sku: SKU of the product to search for
            
        Returns:
            Market data for the product if found
        """
        # Implemented by subclasses
        raise NotImplementedError("Subclasses must implement this method")


class StockXFetcher(MarketDataFetcher):
    """Fetcher for StockX market data."""
    
    def __init__(self, rate_limit=20):
        super().__init__(rate_limit=rate_limit)
        self.base_url = "https://stockx.com"
        self.search_url = "https://stockx.com/api/browse"
        self.product_url = "https://stockx.com/api/products"
        
    def search_by_name(self, product_name: str) -> List[Dict[str, Any]]:
        """Search StockX by product name."""
        params = {
            'query': product_name,
            '_search': product_name,
            'page': 1,
            'resultsPerPage': 10,
            'dataType': 'product',
            'facetsToRetrieve': 'browseVerticals,brand'
        }
        
        response = self._make_request(self.search_url, params=params)
        if not response:
            return []
            
        try:
            data = response.json()
            products = data.get('Products', [])
            
            results = []
            for product in products:
                # Extract key information
                market_data = {
                    'name': product.get('title', 'Unknown'),
                    'sku': product.get('styleId', ''),
                    'brand': product.get('brand', 'Unknown'),
                    'url': f"{self.base_url}/{product.get('urlKey', '')}",
                    'image_url': product.get('media', {}).get('imageUrl', ''),
                    'market_price': product.get('market', {}).get('lowestAsk', 0),
                    'retail_price': product.get('retailPrice', 0),
                    'release_date': product.get('releaseDate', ''),
                    'source': 'StockX',
                    'last_sale': product.get('market', {}).get('lastSale', 0),
                    'highest_bid': product.get('market', {}).get('highestBid', 0)
                }
                results.append(market_data)
                
            return results
            
        except Exception as e:
            logger.error(f"Error parsing StockX search results: {e}")
            return []
            
    def search_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Search StockX by product SKU."""
        # StockX doesn't have a direct SKU search API, so use name search first
        results = self.search_by_name(sku)
        
        # Filter for exact SKU match
        for result in results:
            if result.get('sku', '').upper() == sku.upper():
                return result
                
        # If no exact match, try to fetch more details for the first result
        if results:
            return results[0]
            
        return None


class GoatFetcher(MarketDataFetcher):
    """Fetcher for GOAT market data."""
    
    def __init__(self, rate_limit=20):
        super().__init__(rate_limit=rate_limit)
        self.base_url = "https://www.goat.com"
        self.search_url = "https://ac.cnstrc.com/search/sneakers"
        self.product_url = "https://www.goat.com/sneakers/"
        
    def search_by_name(self, product_name: str) -> List[Dict[str, Any]]:
        """Search GOAT by product name."""
        params = {
            'c': 'ciojs-client-2.29.12',
            'key': 'key_XT7bjdbvjgECO5d8',
            'i': '7cd2b8e6-0380-4162-8cd8-167bcf172b41',
            's': product_name,
            'num_results_per_page': 10,
            '_dt': int(time.time() * 1000)
        }
        
        response = self._make_request(self.search_url, params=params)
        if not response:
            return []
            
        try:
            data = response.json()
            products = data.get('response', {}).get('results', [])
            
            results = []
            for product in products:
                item_data = product.get('data', {})
                # Extract key information
                market_data = {
                    'name': item_data.get('name', 'Unknown'),
                    'sku': item_data.get('sku', ''),
                    'brand': item_data.get('brand_name', 'Unknown'),
                    'url': f"{self.base_url}/sneakers/{item_data.get('slug', '')}",
                    'image_url': item_data.get('image_url', ''),
                    'market_price': float(item_data.get('lowest_price_cents', 0)) / 100,
                    'retail_price': float(item_data.get('retail_price_cents', 0)) / 100,
                    'release_date': item_data.get('release_date', ''),
                    'source': 'GOAT',
                    'last_sale': float(item_data.get('last_sale_price_cents', 0)) / 100
                }
                results.append(market_data)
                
            return results
            
        except Exception as e:
            logger.error(f"Error parsing GOAT search results: {e}")
            return []
            
    def search_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Search GOAT by product SKU."""
        # Search by SKU
        results = self.search_by_name(sku)
        
        # Filter for exact SKU match
        for result in results:
            if result.get('sku', '').upper() == sku.upper():
                return result
                
        # If no exact match, try to fetch more details for the first result
        if results:
            return results[0]
            
        return None


class FlightClubFetcher(MarketDataFetcher):
    """Fetcher for Flight Club market data."""
    
    def __init__(self, rate_limit=15):
        super().__init__(rate_limit=rate_limit)
        self.base_url = "https://www.flightclub.com"
        self.search_url = "https://www.flightclub.com/catalogsearch/result"
        
    def search_by_name(self, product_name: str) -> List[Dict[str, Any]]:
        """Search Flight Club by product name."""
        params = {
            'q': product_name
        }
        
        response = self._make_request(self.search_url, params=params)
        if not response:
            return []
            
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            product_elements = soup.select('.product-grid-item')
            
            results = []
            for element in product_elements:
                # Extract product name and URL
                name_elem = element.select_one('.product-tile-title')
                link_elem = element.select_one('a.product-tile-link')
                price_elem = element.select_one('.product-tile-pricing-current')
                
                if not name_elem or not link_elem or not price_elem:
                    continue
                
                # Extract product URL
                url = link_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                # Extract image
                img_elem = element.select_one('.product-tile-img img')
                img_url = img_elem.get('src', '') if img_elem else ''
                
                # Extract price (remove currency symbols and commas)
                price_text = price_elem.text.strip()
                price = self._extract_price(price_text)
                
                # Create market data object
                market_data = {
                    'name': name_elem.text.strip(),
                    'url': url,
                    'image_url': img_url,
                    'market_price': price,
                    'source': 'Flight Club'
                }
                
                # Extract SKU if available (usually in the URL)
                sku_match = re.search(r'/([A-Za-z0-9-]+)$', url)
                if sku_match:
                    market_data['sku'] = sku_match.group(1)
                
                results.append(market_data)
                
            return results
            
        except Exception as e:
            logger.error(f"Error parsing Flight Club search results: {e}")
            return []
    
    def _extract_price(self, price_text: str) -> float:
        """Extract price from text."""
        # Remove currency symbols and commas
        cleaned = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
            
    def search_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Search Flight Club by product SKU."""
        # Flight Club doesn't have a direct SKU search, so use the name search
        return self.search_by_name(sku)


class MarketDataService:
    """Service to fetch and aggregate market data from multiple sources."""
    
    def __init__(self):
        """Initialize the market data service."""
        self.fetchers = {
            'stockx': StockXFetcher(),
            'goat': GoatFetcher(),
            'flightclub': FlightClubFetcher(),
        }
        
    def search_product(self, query: str, sources: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for a product across multiple sources.
        
        Args:
            query: Search query (name or SKU)
            sources: List of sources to search (default: all)
            
        Returns:
            Dictionary of search results by source
        """
        if sources is None:
            sources = list(self.fetchers.keys())
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(sources)) as executor:
            # Create search tasks
            future_to_source = {
                executor.submit(self.fetchers[source].search_by_name, query): source
                for source in sources if source in self.fetchers
            }
            
            # Process results as they complete
            for future in future_to_source:
                source = future_to_source[future]
                try:
                    results[source] = future.result()
                except Exception as e:
                    logger.error(f"Error searching {source}: {e}")
                    results[source] = []
                    
        return results
        
    def get_market_data(self, sku: str = None, product_name: str = None) -> Dict[str, Any]:
        """
        Get comprehensive market data for a product.
        
        Args:
            sku: Product SKU (preferred)
            product_name: Product name (used if SKU is not provided)
            
        Returns:
            Dictionary with consolidated market data
        """
        if not sku and not product_name:
            return {}
            
        query = sku if sku else product_name
        search_method = 'search_by_sku' if sku else 'search_by_name'
        
        all_results = {}
        
        # Try each source sequentially to avoid rate limiting
        for source, fetcher in self.fetchers.items():
            try:
                if search_method == 'search_by_sku':
                    result = fetcher.search_by_sku(query)
                    if result:
                        all_results[source] = result
                else:
                    results = fetcher.search_by_name(query)
                    if results:
                        all_results[source] = results[0]  # Take first result
            except Exception as e:
                logger.error(f"Error getting market data from {source}: {e}")
                
        # If we don't have any results, return empty dict
        if not all_results:
            return {}
            
        # Calculate average market price
        prices = [data.get('market_price', 0) for data in all_results.values() 
                  if data.get('market_price', 0) > 0]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        # Get the result with the most information
        best_result = max(all_results.values(), key=lambda x: len([v for v in x.values() if v]))
        
        # Create consolidated result
        consolidated = {
            'name': best_result.get('name', 'Unknown'),
            'sku': best_result.get('sku', sku or ''),
            'brand': best_result.get('brand', 'Unknown'),
            'market_price': avg_price,
            'retail_price': best_result.get('retail_price', 0),
            'price_sources': len(prices),
            'sources': list(all_results.keys()),
            'image_url': best_result.get('image_url', ''),
            'url': best_result.get('url', ''),
            'last_updated': time.time()
        }
        
        return consolidated
