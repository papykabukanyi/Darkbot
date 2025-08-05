"""
StockX Price Checker - Fetches prices from StockX using their API
"""

import logging
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import concurrent.futures
import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

# Import adapters
from utils.stockx_adapter import StockXAdapter

# Load environment variables
load_dotenv()

logger = logging.getLogger("SneakerBot")

class MultiSitePriceChecker:
    """Checks sneaker prices on StockX"""
    
    def __init__(self):
        """Initialize the StockX price checker."""
        # Initialize adapters
        self.stockx_adapter = StockXAdapter()
        
        self.sites = [
            {
                'name': 'StockX',
                'search_url': 'https://stockx.com/search?s={query}',
                'sku_search_url': 'https://stockx.com/api/browse?_search={sku}',
                'product_url': 'https://stockx.com/{slug}',
                'price_selector': '.css-1dyz9qy, .chakra-text.css-13jjnd7',
                'base_url': 'https://stockx.com',
                'api_enabled': True,
                'adapter': self.stockx_adapter
            }
        ]
        
        # Extended list of user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 OPR/94.0.0.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 13; Mobile; rv:68.0) Gecko/68.0 Firefox/108.0'
        ]
        
        # Proxy configuration
        self.use_proxies = os.getenv('USE_PROXIES', 'False').lower() == 'true'
        self.proxies = self._load_proxies()
        
        # Rate limiting
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', '5'))
        
        # Cache for search results
        self.cache_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'cache')
        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)
        
        # Maximum retries
        self.max_retries = 3
    
    def _load_proxies(self):
        """Load proxies from environment variables."""
        proxy_list = os.getenv('PROXY_LIST', '')
        if not proxy_list:
            return []
        
        return [proxy.strip() for proxy in proxy_list.split(',')]
    
    def get_random_user_agent(self):
        """Get a random user agent."""
        return random.choice(self.user_agents)
    
    def get_random_proxy(self):
        """Get a random proxy if available."""
        if not self.use_proxies or not self.proxies:
            return None
        
        return random.choice(self.proxies)
    
    def extract_price(self, price_text):
        """Extract price from text."""
        if not price_text:
            return None
            
        try:
            # Look for price pattern (e.g., $190, $160.50)
            price_match = re.search(r'\$(\d+(?:\.\d+)?)', price_text)
            if price_match:
                return float(price_match.group(1))
                
            # Try with just digits (in case $ is missing)
            digit_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
            if digit_match:
                return float(digit_match.group(1))
                
            # If all else fails, try to extract any numbers
            clean_price = re.sub(r'[^0-9.]', '', price_text)
            if clean_price:
                return float(clean_price)
                
        except Exception as e:
            logger.error(f"Error extracting price from '{price_text}': {e}")
        
        return None
    
    def _get_cached_result(self, site_name, query):
        """Get cached result if available."""
        # Pre-compute the regex substitution outside the f-string
        safe_query = re.sub(r'[^\w]', '_', query)
        cache_file = os.path.join(self.cache_directory, f"{site_name}_{safe_query}.json")
        
        if os.path.exists(cache_file):
            try:
                # Check if cache is recent (less than 12 hours old)
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < 43200:  # 12 hours in seconds
                    with open(cache_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache file: {e}")
        
        return None
    
    def _save_to_cache(self, site_name, query, result):
        """Save result to cache."""
        try:
            # Pre-compute the regex substitution outside the f-string
            safe_query = re.sub(r'[^\w]', '_', query)
            cache_file = os.path.join(self.cache_directory, f"{site_name}_{safe_query}.json")
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    def check_stockx_api(self, sku, query):
        """
        Check StockX price using their API.
        
        Args:
            sku: Product SKU (may be None or synthetic)
            query: Search query (sneaker name)
            
        Returns:
            Dictionary with price information
        """
        result = {
            'site_name': 'StockX',
            'price': None,
            'url': None,
            'price_difference': None,
            'percentage_difference': None,
            'profit_potential': None,
            'status': 'error'
        }
        
        try:
            # Determine if we have a valid SKU
            is_synthetic_sku = sku and (sku.startswith('KI') or len(sku) < 6 or sku == 'KICKSONFIR')
            search_term = query if is_synthetic_sku else sku if sku else query
            
            # Format the search term for URL
            formatted_search = search_term.replace(' ', '%20')
            
            # Try the search
            search_url = f"https://stockx.com/api/browse?_search={formatted_search}"
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://stockx.com/',
                'x-requested-with': 'XMLHttpRequest',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-API-Key': os.getenv('STOCKX_API_KEY'),
                'X-Client-ID': os.getenv('STOCKX_CLIENT_ID'),
                'Authorization': f"Bearer {os.getenv('STOCKX_CLIENT_SECRET')}"
            }
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(self.rate_limit_delay, self.rate_limit_delay + 2.0))
            
            # Set up proxy if available
            proxy = self.get_random_proxy()
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            
            # Make request
            logger.info(f"Checking StockX API for: {search_term}")
            response = requests.get(search_url, headers=headers, proxies=proxies, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('Products', [])
                
                if products:
                    product = products[0]
                    market = product.get('market', {})
                    lowest_ask = market.get('lowestAsk')
                    
                    if lowest_ask:
                        result['price'] = float(lowest_ask)
                        result['url'] = f"https://stockx.com/{product.get('urlKey')}"
                        result['status'] = 'success'
                        logger.info(f"Found price on StockX API: ${result['price']}")
                        return result
            
            # If first search fails and we used SKU, try with the query
            if not is_synthetic_sku and sku and sku != query:
                # Format the query for URL
                formatted_query = query.replace(' ', '%20')
                search_url = f"https://stockx.com/api/browse?_search={formatted_query}"
                
                # Add delay to avoid rate limiting
                time.sleep(random.uniform(self.rate_limit_delay, self.rate_limit_delay + 2.0))
                
                # Make request
                logger.info(f"Checking StockX API with alternate query: {query}")
                headers['X-API-Key'] = os.getenv('STOCKX_API_KEY')
                headers['X-Client-ID'] = os.getenv('STOCKX_CLIENT_ID')
                headers['Authorization'] = f"Bearer {os.getenv('STOCKX_CLIENT_SECRET')}"
                response = requests.get(search_url, headers=headers, proxies=proxies, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('Products', [])
                
                if products:
                    product = products[0]
                    market = product.get('market', {})
                    lowest_ask = market.get('lowestAsk')
                    
                    if lowest_ask:
                        result['price'] = float(lowest_ask)
                        result['url'] = f"https://stockx.com/{product.get('urlKey')}"
                        result['status'] = 'success'
                        logger.info(f"Found price on StockX API: ${result['price']}")
                        return result
            
            logger.warning(f"Could not find price on StockX API for {sku} / {query}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking StockX API: {e}")
            return result
    
    def check_site(self, site, query, retail_price=None, sku=None):
        """
        Check a single site for price information.
        
        Args:
            site: Site configuration dictionary
            query: Search query
            retail_price: Optional retail price for comparison
            sku: Product SKU
            
        Returns:
            Dictionary with site name, price, URL, and comparison info
        """
        # Initialize result dictionary
        result = {
            'site_name': site['name'],
            'price': None,
            'url': None,
            'price_difference': None,
            'percentage_difference': None,
            'profit_potential': None,
            'status': 'error'
        }
        
        # Check if this is a synthetic SKU (e.g., KICKSONFIR)
        is_synthetic_sku = sku and (sku.startswith('KI') or len(sku) < 6 or sku == 'KICKSONFIR')
        
        # Use sneaker name for search if SKU appears to be synthetic
        search_term = query if is_synthetic_sku else sku if sku else query
        
        # Check cache first
        cached_result = self._get_cached_result(site['name'], search_term)
        if cached_result:
            logger.info(f"Using cached result for {site['name']}: {search_term}")
            
            # If we have retail price, update comparison data
            if retail_price and cached_result['status'] == 'success' and cached_result['price']:
                price = cached_result['price']
                cached_result['price_difference'] = price - retail_price
                cached_result['percentage_difference'] = (price - retail_price) / retail_price * 100 if retail_price > 0 else 0
                
                # Calculate potential profit (assuming 12% platform fee and $15 shipping)
                platform_fee = price * 0.12
                shipping_cost = 15
                profit = price - retail_price - platform_fee - shipping_cost
                cached_result['profit_potential'] = profit
            
            return cached_result
        
        # For StockX, try the API approach first if enabled
        if site['name'] == 'StockX' and site.get('api_enabled', False):
            # Check if we're dealing with a synthetic SKU (e.g., KICKSONFIR)
            is_synthetic_sku = sku and (sku.startswith('KI') or len(sku) < 6 or sku == 'KICKSONFIR')
            api_result = self.check_stockx_api(sku if not is_synthetic_sku else None, query)
            
            if api_result['status'] == 'success':
                # Calculate comparison if retail price is provided
                if retail_price and api_result['price']:
                    price = api_result['price']
                    api_result['price_difference'] = price - retail_price
                    api_result['percentage_difference'] = (price - retail_price) / retail_price * 100 if retail_price > 0 else 0
                    
                    # Calculate potential profit
                    platform_fee = price * 0.12
                    shipping_cost = 15
                    profit = price - retail_price - platform_fee - shipping_cost
                    api_result['profit_potential'] = profit
                
                # Cache the result
                self._save_to_cache(site['name'], search_term, api_result)
                return api_result
        
        # Use adapter if available
        if 'adapter' in site and site['adapter'] is not None:
            try:
                logger.info(f"Using adapter for {site['name']} to check price for: {search_term}")
                adapter = site['adapter']
                price = adapter.get_price(search_term)
                
                if price:
                    result['price'] = price
                    result['url'] = site['search_url'].format(query=search_term.replace(' ', '+'))
                    result['status'] = 'success'
                    
                    # Calculate comparison if retail price is provided
                    if retail_price:
                        result['price_difference'] = price - retail_price
                        result['percentage_difference'] = (price - retail_price) / retail_price * 100 if retail_price > 0 else 0
                        
                        # Calculate potential profit (assuming 12% platform fee and $15 shipping)
                        platform_fee = price * 0.12
                        shipping_cost = 15
                        profit = price - retail_price - platform_fee - shipping_cost
                        result['profit_potential'] = profit
                    
                    logger.info(f"Found price on {site['name']} using adapter: ${price}")
                    
                    # Cache the result
                    self._save_to_cache(site['name'], search_term, result)
                    return result
            except Exception as e:
                logger.error(f"Error using adapter for {site['name']}: {e}")
                # Fall through to web scraping approach
        
        try:
            # Prepare URL and headers
            search_url = site['search_url'].format(query=search_term.replace(' ', '+'))
            headers = {
                'User-Agent': self.get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': site['base_url'],
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 3.0))
            
            # Make request
            logger.info(f"Checking {site['name']} for: {search_term}")
            response = requests.get(search_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get response from {site['name']}: {response.status_code}")
                return result
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract price using selector
            price_elem = soup.select_one(site['price_selector'])
            if not price_elem:
                logger.warning(f"No price element found on {site['name']} using selector: {site['price_selector']}")
                return result
            
            # Extract price text
            price_text = price_elem.get_text().strip()
            price = self.extract_price(price_text)
            
            if not price:
                logger.warning(f"Could not extract price from text: {price_text} on {site['name']}")
                return result
            
            # Update result
            result['price'] = price
            result['url'] = search_url
            result['status'] = 'success'
            
            # Calculate comparison if retail price is provided
            if retail_price:
                result['price_difference'] = price - retail_price
                result['percentage_difference'] = (price - retail_price) / retail_price * 100 if retail_price > 0 else 0
                
                # Calculate potential profit (assuming 12% platform fee and $15 shipping)
                platform_fee = price * 0.12
                shipping_cost = 15
                profit = price - retail_price - platform_fee - shipping_cost
                result['profit_potential'] = profit
            
            logger.info(f"Found price on {site['name']}: ${price}")
            
            # Cache the result
            self._save_to_cache(site['name'], search_term, result)
            return result
            
        except Exception as e:
            logger.error(f"Error checking {site['name']}: {e}")
            return result
    
    def check_prices(self, query, retail_price=None, max_workers=1, sku=None):
        """
        Check price on StockX.
        
        Args:
            query: Search query (e.g., "Nike Dunk Low Panda")
            retail_price: Optional retail price for comparison
            max_workers: Not used, kept for compatibility
            sku: Optional SKU for more accurate searching
            
        Returns:
            List with one dictionary containing StockX price information
        """
        results = []
        
        try:
            # We only have StockX now, so directly check it
            site = self.sites[0]  # StockX is the only site
            result = self.check_site(site, query, retail_price, sku)
            results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking price on StockX: {e}")
            return results
    
    def generate_price_comparison_report(self, sneaker_name, retail_price=None, sku=None):
        """
        Generate a price report for a sneaker from StockX.
        
        Args:
            sneaker_name: Name of the sneaker
            retail_price: Optional retail price
            sku: Optional SKU for more accurate searching
            
        Returns:
            Dictionary with StockX price report
        """
        logger.info(f"Generating StockX price report for: {sneaker_name}")
        
        # Determine if we have a synthetic SKU
        is_synthetic_sku = sku and (sku.startswith('KI') or len(sku) < 6 or sku == 'KICKSONFIR')
        
        # Use sneaker name if SKU is synthetic or not provided
        if is_synthetic_sku or not sku:
            logger.info(f"Using sneaker name for search: {sneaker_name}")
            query = sneaker_name
        else:
            logger.info(f"Using SKU for search: {sku}")
            query = sku
        
        # Check price on StockX
        price_results = self.check_prices(query, retail_price, sku=sku if not is_synthetic_sku else None)
        
        # Get StockX price information
        stockx_result = None
        for result in price_results:
            if result['status'] == 'success' and result['price'] is not None:
                stockx_result = result
                break
        
        # Prepare report
        report = {
            'sneaker_name': sneaker_name,
            'sku': sku,
            'retail_price': retail_price,
            'best_price': {
                'price': stockx_result['price'] if stockx_result else None,
                'site': 'StockX'
            },
            'highest_price': {
                'price': stockx_result['price'] if stockx_result else None,
                'site': 'StockX'
            },
            'price_range': 0,  # Only one site, so range is 0
            'best_profit': {
                'amount': stockx_result['profit_potential'] if stockx_result else None,
                'site': 'StockX'
            },
            'price_results': price_results,
            'timestamp': datetime.now().isoformat()
        }
        
        return report
