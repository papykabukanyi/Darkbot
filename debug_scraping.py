"""
Debug Scraping Utility

This script provides debugging tools for the web scraping components of Darkbot.
It allows you to test individual scrapers, check proxy configurations,
and verify that the StockX API integration is working correctly.
"""

import os
import sys
import logging
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"debug_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DebugScraping")

# Import configuration if available
try:
    from config_fixed import (
        STOCKX_CONFIG, PROFIT_CHECKER_CONFIG
    )
    config_loaded = True
except ImportError:
    logger.warning("Could not import configuration. Will use default settings.")
    config_loaded = False
    STOCKX_CONFIG = {}
    PROFIT_CHECKER_CONFIG = {}

# Import custom modules
try:
    from utils.stockx_price_checker import StockXPriceChecker
    from utils.stockx_adapter import StockXAdapter
    from utils.proxy_manager import ProxyManager
    from utils.user_agents import get_random_user_agent
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def test_stockx_connection():
    """Test the connection to StockX API"""
    logger.info("Testing StockX API connection...")
    
    try:
        adapter = StockXAdapter()
        test_result = adapter.test_connection()
        
        if test_result['success']:
            logger.info("✅ Successfully connected to StockX API")
            return True
        else:
            logger.error(f"❌ Failed to connect to StockX API: {test_result['error']}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing StockX API connection: {e}")
        return False

def test_stockx_search(query="nike dunk"):
    """Test the StockX search functionality"""
    logger.info(f"Testing StockX search with query: '{query}'...")
    
    try:
        price_checker = StockXPriceChecker()
        results = price_checker.search_products(query)
        
        if results and len(results) > 0:
            logger.info(f"✅ Found {len(results)} results for '{query}'")
            for i, result in enumerate(results[:5]):  # Show top 5 results
                logger.info(f"  {i+1}. {result['name']} - ${result['price']}")
            return True
        else:
            logger.warning(f"❌ No results found for '{query}'")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing StockX search: {e}")
        return False

def test_stockx_product_details(sku="DD1391-100"):  # Nike Dunk Low Panda
    """Test retrieving detailed product information from StockX"""
    logger.info(f"Testing StockX product details for SKU: '{sku}'...")
    
    try:
        price_checker = StockXPriceChecker()
        product = price_checker.get_product_by_sku(sku)
        
        if product:
            logger.info(f"✅ Successfully retrieved details for {product['name']}")
            logger.info(f"  Brand: {product.get('brand', 'Unknown')}")
            logger.info(f"  SKU: {product.get('sku', 'Unknown')}")
            logger.info(f"  Retail Price: ${product.get('retailPrice', 'Unknown')}")
            logger.info(f"  Current Price: ${product.get('price', 'Unknown')}")
            logger.info(f"  Release Date: {product.get('releaseDate', 'Unknown')}")
            return True
        else:
            logger.warning(f"❌ No product found with SKU '{sku}'")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing StockX product details: {e}")
        return False

def test_proxy_configuration():
    """Test the proxy configuration"""
    logger.info("Testing proxy configuration...")
    
    try:
        # Check if proxy configuration file exists
        proxy_file = os.path.join(BASE_DIR, "proxies.json")
        if not os.path.exists(proxy_file):
            logger.warning(f"❌ Proxy file not found at {proxy_file}")
            return False
        
        # Load and check proxy configuration
        with open(proxy_file, 'r') as f:
            proxy_config = json.load(f)
        
        if not proxy_config or len(proxy_config) == 0:
            logger.warning("❌ No proxies defined in configuration file")
            return False
        
        # Initialize proxy manager
        proxy_manager = ProxyManager()
        proxies = proxy_manager.get_proxy()
        
        if not proxies:
            logger.warning("❌ No working proxies available")
            return False
        
        logger.info(f"✅ Successfully loaded proxy configuration")
        logger.info(f"  Active proxy: {proxies}")
        
        # Test proxy with a simple request
        try:
            import requests
            response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=10)
            if response.status_code == 200:
                ip_data = response.json()
                logger.info(f"✅ Proxy connection successful. IP: {ip_data.get('origin', 'unknown')}")
                return True
            else:
                logger.warning(f"❌ Proxy test request failed with status code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error testing proxy connection: {e}")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error testing proxy configuration: {e}")
        return False

def test_user_agent_rotation():
    """Test user agent rotation"""
    logger.info("Testing user agent rotation...")
    
    try:
        user_agents = set()
        for _ in range(5):
            ua = get_random_user_agent()
            user_agents.add(ua)
            logger.info(f"  User Agent: {ua}")
        
        if len(user_agents) > 1:
            logger.info(f"✅ Successfully rotated user agents")
            return True
        else:
            logger.warning("❌ User agent rotation not working properly")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing user agent rotation: {e}")
        return False

def main():
    """Main function to run debugging tests"""
    parser = argparse.ArgumentParser(description="Debug scraping components")
    parser.add_argument('--stockx', action='store_true', help='Test StockX API connection')
    parser.add_argument('--search', type=str, help='Test StockX search with a specific query')
    parser.add_argument('--sku', type=str, help='Test StockX product details with a specific SKU')
    parser.add_argument('--proxy', action='store_true', help='Test proxy configuration')
    parser.add_argument('--user-agent', action='store_true', help='Test user agent rotation')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info(f"Darkbot Scraping Debugger - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Determine which tests to run
    run_stockx = args.stockx or args.all
    run_search = args.search is not None or args.all
    run_sku = args.sku is not None or args.all
    run_proxy = args.proxy or args.all
    run_ua = args.user_agent or args.all
    
    # If no specific tests are selected, run all
    if not any([run_stockx, run_search, run_sku, run_proxy, run_ua]):
        run_stockx = run_proxy = run_ua = True
        run_search = run_sku = args.all  # Only run these if --all is specified
    
    # Run the selected tests
    results = []
    
    if run_stockx:
        logger.info("\n" + "=" * 40)
        logger.info("Testing StockX API Connection")
        logger.info("=" * 40)
        results.append(("StockX API", test_stockx_connection()))
    
    if run_search:
        logger.info("\n" + "=" * 40)
        logger.info("Testing StockX Search")
        logger.info("=" * 40)
        query = args.search if args.search else "nike dunk"
        results.append(("StockX Search", test_stockx_search(query)))
    
    if run_sku:
        logger.info("\n" + "=" * 40)
        logger.info("Testing StockX Product Details")
        logger.info("=" * 40)
        sku = args.sku if args.sku else "DD1391-100"  # Default to Nike Dunk Low Panda
        results.append(("StockX Product Details", test_stockx_product_details(sku)))
    
    if run_proxy:
        logger.info("\n" + "=" * 40)
        logger.info("Testing Proxy Configuration")
        logger.info("=" * 40)
        results.append(("Proxy Configuration", test_proxy_configuration()))
    
    if run_ua:
        logger.info("\n" + "=" * 40)
        logger.info("Testing User Agent Rotation")
        logger.info("=" * 40)
        results.append(("User Agent Rotation", test_user_agent_rotation()))
    
    # Print summary
    logger.info("\n\n" + "=" * 60)
    logger.info("DEBUG SUMMARY")
    logger.info("=" * 60)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{name}: {status}")
    
    # Overall result
    success_count = sum(1 for _, success in results if success)
    logger.info(f"\nOverall: {success_count}/{len(results)} tests passed")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
