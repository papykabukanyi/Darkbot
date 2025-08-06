"""
StockX Price Checker - Fetches prices from StockX using their API
"""

import logging
import time
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
import traceback

# Import StockX adapter
from utils.stockx_adapter import StockXAdapter

# Load environment variables
load_dotenv()

# Configure logging with more detail
logger = logging.getLogger("SneakerBot")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Check if a file handler already exists, if not add one
file_handler_exists = False
for handler in logger.handlers:
    if isinstance(handler, logging.FileHandler):
        file_handler_exists = True
        break

if not file_handler_exists:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = logging.FileHandler(os.path.join(log_dir, 'stockx_price_checker.log'))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Also add a console handler if none exists
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Set logging level
logger.setLevel(logging.DEBUG)

class StockXPriceChecker:
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
        
        # Verify StockX credentials
        self._verify_stockx_credentials()
    
    def _load_proxies(self):
        """Load proxies from environment variables."""
        proxy_list = os.getenv('PROXY_LIST', '')
        if not proxy_list:
            return []
        
        return [proxy.strip() for proxy in proxy_list.split(',')]
    
    def _verify_stockx_credentials(self):
        """Verify that all required StockX credentials are set."""
        api_key = os.getenv('STOCKX_API_KEY', '')
        client_id = os.getenv('STOCKX_CLIENT_ID', '')
        client_secret = os.getenv('STOCKX_CLIENT_SECRET', '')
        cookie = os.getenv('STOCKX_COOKIE', '')
        
        missing_credentials = []
        
        if not api_key:
            missing_credentials.append('STOCKX_API_KEY')
        if not client_id:
            missing_credentials.append('STOCKX_CLIENT_ID')
        if not client_secret:
            missing_credentials.append('STOCKX_CLIENT_SECRET')
        
        if missing_credentials:
            logger.warning(f"Missing StockX credentials: {', '.join(missing_credentials)}")
            logger.warning("API calls to StockX may fail. Make sure to set these in your .env file.")
        else:
            logger.info("StockX credentials verified")
        
        if not cookie:
            logger.info("STOCKX_COOKIE not set. This may be needed for some authenticated requests.")
    
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
        logger.info(f"======= CHECKING STOCKX API =======")
        logger.info(f"SKU: {sku if sku else 'Not provided'}")
        logger.info(f"Query: {query}")
        
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
            
            logger.info(f"Using search term: {search_term}")
            logger.info(f"Is synthetic SKU: {is_synthetic_sku}")
            
            # Format the search term for URL
            formatted_search = search_term.replace(' ', '%20')
            
            # Try the search
            search_url = f"https://stockx.com/api/browse?_search={formatted_search}"
            logger.info(f"Search URL: {search_url}")
            
            # Get StockX credentials from environment
            api_key = os.getenv('STOCKX_API_KEY', '')
            client_id = os.getenv('STOCKX_CLIENT_ID', '')
            client_secret = os.getenv('STOCKX_CLIENT_SECRET', '')
            cookie = os.getenv('STOCKX_COOKIE', '')
            
            # Log credential status (don't log actual values for security)
            logger.info(f"API Key present: {bool(api_key)}")
            logger.info(f"Client ID present: {bool(client_id)}")
            logger.info(f"Client Secret present: {bool(client_secret)}")
            logger.info(f"Cookie present: {bool(cookie)}")
            
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
                'X-API-Key': api_key,
                'X-Client-ID': client_id,
                'appos': 'web',
                'appversion': '0.1',
                'authorization': f"Bearer {client_secret}",
                'Cookie': cookie
            }
            
            # Log the User-Agent being used
            logger.info(f"Using User-Agent: {headers['User-Agent']}")
            
            # Add delay to avoid rate limiting
            delay = random.uniform(self.rate_limit_delay, self.rate_limit_delay + 2.0)
            logger.info(f"Adding delay of {delay:.2f} seconds to avoid rate limiting")
            time.sleep(delay)
            
            # Set up proxy if available
            proxy = self.get_random_proxy()
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            logger.info(f"Using proxy: {proxy if proxy else 'None'}")
            
            # Make request
            logger.info(f"Sending API request to StockX for: {search_term}")
            
            # Add retry logic with exponential backoff
            max_retries = 3
            retry_delay = 2  # Initial delay in seconds
            response = None
            
            for retry in range(max_retries):
                try:
                    logger.info(f"API request attempt {retry+1}/{max_retries}")
                    response = requests.get(search_url, headers=headers, proxies=proxies, timeout=30)
                    
                    logger.info(f"Response status code: {response.status_code}")
                    
                    # Handle different response codes
                    if response.status_code == 200:
                        # Success, process the response
                        logger.info("Request successful!")
                        break
                    elif response.status_code == 403:
                        logger.error(f"Failed to fetch StockX price for query: {search_term}: Status code 403 (Forbidden)")
                        logger.error("Check your StockX API credentials and permissions")
                        if retry < max_retries - 1:
                            backoff_time = retry_delay * (2 ** retry)
                            logger.info(f"Retrying in {backoff_time} seconds...")
                            time.sleep(backoff_time)  # Exponential backoff
                        continue
                    elif response.status_code == 429:
                        logger.warning(f"Rate limit exceeded (429) for StockX API. Retrying in {retry_delay * (2 ** retry)} seconds...")
                        time.sleep(retry_delay * (2 ** retry))  # Exponential backoff
                        continue
                    else:
                        logger.warning(f"Failed to get response from StockX: {response.status_code}")
                        if retry < max_retries - 1:
                            backoff_time = retry_delay * (2 ** retry)
                            logger.info(f"Retrying in {backoff_time} seconds...")
                            time.sleep(backoff_time)  # Exponential backoff
                        continue
                except Exception as e:
                    logger.error(f"Error making StockX API request (attempt {retry+1}): {str(e)}")
                    logger.error(traceback.format_exc())
                    if retry < max_retries - 1:
                        backoff_time = retry_delay * (2 ** retry)
                        logger.info(f"Retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        logger.error("All retry attempts failed")
                        return result
            
            # Process the response if we got one
            if response and response.status_code == 200:
                logger.info("Processing successful response")
                try:
                    data = response.json()
                    products = data.get('Products', [])
                    
                    logger.info(f"Found {len(products)} products in response")
                    
                    if products:
                        product = products[0]
                        
                        # Log product details
                        logger.info(f"First product title: {product.get('title', 'N/A')}")
                        logger.info(f"First product SKU: {product.get('styleId', 'N/A')}")
                        logger.info(f"First product URL key: {product.get('urlKey', 'N/A')}")
                        
                        market = product.get('market', {})
                        lowest_ask = market.get('lowestAsk')
                        
                        logger.info(f"Market data: {json.dumps(market, indent=2)}")
                        logger.info(f"Lowest ask: {lowest_ask}")
                        
                        if lowest_ask:
                            result['price'] = float(lowest_ask)
                            result['url'] = f"https://stockx.com/{product.get('urlKey')}"
                            result['status'] = 'success'
                            logger.info(f"Success! Found price on StockX API: ${result['price']}")
                            return result
                        else:
                            logger.warning("No lowest ask price found in the market data")
                    else:
                        logger.warning("No products found in the response")
                except Exception as e:
                    logger.error(f"Error processing StockX API response: {str(e)}")
                    logger.error(traceback.format_exc())
                    logger.debug(f"Response content: {response.text[:500]}...")  # Log first 500 chars
            
            # If first search fails and we used SKU, try with the query
            if not is_synthetic_sku and sku and sku != query:
                logger.info("First search failed, trying with the product name instead of SKU")
                # Format the query for URL
                formatted_query = query.replace(' ', '%20')
                search_url = f"https://stockx.com/api/browse?_search={formatted_query}"
                logger.info(f"Alternate search URL: {search_url}")
                
                # Add delay to avoid rate limiting
                delay = random.uniform(self.rate_limit_delay, self.rate_limit_delay + 2.0)
                logger.info(f"Adding delay of {delay:.2f} seconds to avoid rate limiting")
                time.sleep(delay)
                
                # Make request
                logger.info(f"Sending API request to StockX with alternate query: {query}")
                headers['X-API-Key'] = os.getenv('STOCKX_API_KEY', '')
                headers['X-Client-ID'] = os.getenv('STOCKX_CLIENT_ID', '')
                headers['appos'] = 'web'
                headers['appversion'] = '0.1'
                headers['authorization'] = f"Bearer {os.getenv('STOCKX_CLIENT_SECRET', '')}"
                headers['Cookie'] = os.getenv('STOCKX_COOKIE', '')
                
                # Add retry logic with exponential backoff
                for retry in range(max_retries):
                    try:
                        logger.info(f"Alternate API request attempt {retry+1}/{max_retries}")
                        response = requests.get(search_url, headers=headers, proxies=proxies, timeout=30)
                        
                        logger.info(f"Alternate response status code: {response.status_code}")
                        
                        # Handle different response codes
                        if response.status_code == 200:
                            # Success, process the response
                            logger.info("Alternate request successful!")
                            break
                        elif response.status_code == 403:
                            logger.error(f"Failed to fetch StockX price for query: {query}: Status code 403 (Forbidden)")
                            logger.error("Check your StockX API credentials and permissions")
                            if retry < max_retries - 1:
                                backoff_time = retry_delay * (2 ** retry)
                                logger.info(f"Retrying in {backoff_time} seconds...")
                                time.sleep(backoff_time)  # Exponential backoff
                            continue
                        elif response.status_code == 429:
                            logger.warning(f"Rate limit exceeded (429) for StockX API. Retrying in {retry_delay * (2 ** retry)} seconds...")
                            time.sleep(retry_delay * (2 ** retry))  # Exponential backoff
                            continue
                        else:
                            logger.warning(f"Failed to get response from StockX: {response.status_code}")
                            if retry < max_retries - 1:
                                backoff_time = retry_delay * (2 ** retry)
                                logger.info(f"Retrying in {backoff_time} seconds...")
                                time.sleep(backoff_time)  # Exponential backoff
                            continue
                    except Exception as e:
                        logger.error(f"Error making alternate StockX API request (attempt {retry+1}): {str(e)}")
                        logger.error(traceback.format_exc())
                        if retry < max_retries - 1:
                            backoff_time = retry_delay * (2 ** retry)
                            logger.info(f"Retrying in {backoff_time} seconds...")
                            time.sleep(backoff_time)
                            continue
                        else:
                            logger.error("All retry attempts failed for alternate query")
                            return result
            
            # Process the alternate response if we got one
            if response and response.status_code == 200:
                logger.info("Processing alternate response")
                try:
                    data = response.json()
                    products = data.get('Products', [])
                    
                    logger.info(f"Found {len(products)} products in alternate response")
                    
                    if products:
                        product = products[0]
                        
                        # Log product details
                        logger.info(f"First product title: {product.get('title', 'N/A')}")
                        logger.info(f"First product SKU: {product.get('styleId', 'N/A')}")
                        logger.info(f"First product URL key: {product.get('urlKey', 'N/A')}")
                        
                        market = product.get('market', {})
                        lowest_ask = market.get('lowestAsk')
                        
                        logger.info(f"Market data: {json.dumps(market, indent=2)}")
                        logger.info(f"Lowest ask: {lowest_ask}")
                        
                        if lowest_ask:
                            result['price'] = float(lowest_ask)
                            result['url'] = f"https://stockx.com/{product.get('urlKey')}"
                            result['status'] = 'success'
                            logger.info(f"Success! Found price on StockX API with alternate query: ${result['price']}")
                            return result
                        else:
                            logger.warning("No lowest ask price found in the alternate market data")
                    else:
                        logger.warning("No products found in the alternate response")
                except Exception as e:
                    logger.error(f"Error processing alternate StockX API response: {str(e)}")
                    logger.error(traceback.format_exc())
                    logger.debug(f"Alternate response content: {response.text[:500]}...")  # Log first 500 chars
            
            logger.warning(f"Could not find price on StockX API for {sku} / {query}")
            logger.info("======= STOCKX API SEARCH COMPLETE (NO RESULTS) =======")
            return result
            
        except Exception as e:
            logger.error(f"Error checking StockX API: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info("======= STOCKX API SEARCH COMPLETE (ERROR) =======")
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
        logger.info("=" * 80)
        logger.info(f"STARTING PRICE CHECK FOR: {query}")
        logger.info(f"SKU: {sku if sku else 'Not provided'}")
        logger.info(f"Retail Price: {retail_price if retail_price else 'Not provided'}")
        logger.info("=" * 80)
        
        results = []
        
        try:
            # We only have StockX now, so directly check it
            site = self.sites[0]  # StockX is the only site
            logger.info(f"Checking site: {site['name']}")
            result = self.check_site(site, query, retail_price, sku)
            results.append(result)
            
            # Log the result
            if result['status'] == 'success':
                logger.info(f"SUCCESS: Found price on {site['name']}: ${result['price']}")
                if retail_price and result['price']:
                    logger.info(f"Price difference: ${result['price_difference']} ({result['percentage_difference']:.2f}%)")
                    logger.info(f"Potential profit: ${result['profit_potential']}")
            else:
                logger.warning(f"Failed to find price on {site['name']}")
            
            logger.info("=" * 80)
            logger.info(f"PRICE CHECK COMPLETE FOR: {query}")
            logger.info("=" * 80)
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking price on StockX: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info("=" * 80)
            logger.info(f"PRICE CHECK FAILED FOR: {query}")
            logger.info("=" * 80)
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
