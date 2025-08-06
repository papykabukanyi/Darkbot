"""
Test script for StockX price checker
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_stockx_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import StockX price checker
from utils.stockx_price_checker import StockXPriceChecker

def main():
    """Main function to test StockX price checker"""
    logger.info("=" * 80)
    logger.info("TESTING STOCKX PRICE CHECKER")
    logger.info("=" * 80)
    
    # Check if StockX credentials are set
    api_key = os.getenv('STOCKX_API_KEY', '')
    client_id = os.getenv('STOCKX_CLIENT_ID', '')
    client_secret = os.getenv('STOCKX_CLIENT_SECRET', '')
    cookie = os.getenv('STOCKX_COOKIE', '')
    
    logger.info(f"API Key present: {bool(api_key)}")
    logger.info(f"Client ID present: {bool(client_id)}")
    logger.info(f"Client Secret present: {bool(client_secret)}")
    logger.info(f"Cookie present: {bool(cookie)}")
    
    if not all([api_key, client_id, client_secret]):
        logger.warning("Not all StockX credentials are set. API calls may fail.")
    
    # Initialize StockX price checker
    logger.info("Initializing StockX price checker...")
    price_checker = StockXPriceChecker()
    
    # Test search queries
    test_queries = [
        {
            "name": "Nike Dunk Low Panda",
            "sku": "DD1391-100",
            "retail_price": 110.0
        },
        {
            "name": "Air Jordan 1 Chicago",
            "sku": "DZ5485-612",
            "retail_price": 180.0
        },
        {
            "name": "Yeezy Boost 350 V2 Zebra",
            "sku": "CP9654",
            "retail_price": 220.0
        }
    ]
    
    # Test each query
    for query in test_queries:
        logger.info("-" * 80)
        logger.info(f"Testing query: {query['name']}")
        logger.info(f"SKU: {query['sku']}")
        logger.info(f"Retail price: ${query['retail_price']}")
        
        try:
            # Get price information
            results = price_checker.check_prices(
                query['name'],
                query['retail_price'],
                sku=query['sku']
            )
            
            # Generate a report
            report = price_checker.generate_price_comparison_report(
                query['name'],
                retail_price=query['retail_price'],
                sku=query['sku']
            )
            
            # Print results
            logger.info(f"Results: {json.dumps(results, indent=2)}")
            logger.info(f"Report: {json.dumps(report, indent=2)}")
            
            # Check if price was found
            if results and results[0]['status'] == 'success':
                logger.info(f"SUCCESS! Found price on StockX: ${results[0]['price']}")
                if results[0]['profit_potential'] is not None:
                    logger.info(f"Profit potential: ${results[0]['profit_potential']:.2f}")
            else:
                logger.warning("Failed to find price on StockX")
                
        except Exception as e:
            logger.error(f"Error testing query {query['name']}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("=" * 80)
    logger.info("STOCKX PRICE CHECKER TEST COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
