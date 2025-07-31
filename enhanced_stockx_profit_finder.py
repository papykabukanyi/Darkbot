#!/usr/bin/env python
"""
Enhanced test script for StockX scraper focused on finding the most profitable sneakers
across all brands, not just Jordans
"""

import sys
import os
import logging
import json
import time
from datetime import datetime
import requests
from typing import Dict, List, Any

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("stockx_profit_finder.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("StockXProfitFinder")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sites import SNEAKER_SITES
from scrapers.stockx import StockXScraper
from utils.price_comparison import PriceComparer

# List of profitable brands to search (expanded beyond just Jordan)
PROFITABLE_BRANDS = [
    "Jordan",
    "Nike",
    "Adidas",
    "Yeezy",
    "New Balance",
    "Travis Scott",
    "Off-White",
    "Sacai",
    "SB",
    "Dunk",
    "Fear of God",
    "Kobe"
]

# Popular models known for resale value
PROFITABLE_MODELS = [
    "Jordan 1",
    "Jordan 4",
    "Jordan 11",
    "Dunk Low",
    "Air Force 1",
    "Yeezy 350",
    "Yeezy 700",
    "New Balance 550",
    "New Balance 990",
    "SB Dunk",
    "Travis Scott",
    "Off-White",
    "Fragment",
    "Air Max 1",
    "Kobe 6"
]

def find_profitable_sneakers():
    """Find the most profitable sneakers from StockX"""
    print("=" * 70)
    print(" STOCKX PROFIT FINDER - Finding the most profitable sneakers across brands ")
    print("=" * 70)
    
    # Get the site config
    site_config = SNEAKER_SITES.get('stockx', {})
    if not site_config:
        logger.error("StockX site config not found")
        return
    
    # Create the scraper and price comparer
    scraper = StockXScraper(site_config)
    price_comparer = PriceComparer()
    
    # Store all found products
    all_products = []
    
    # Get the current date for the report
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # First, search for trending products
    logger.info("Searching for trending products on StockX...")
    with scraper as s:
        trending_products = s.search_trending_products()
        
    if trending_products:
        logger.info(f"Found {len(trending_products)} trending products")
        all_products.extend(trending_products)
    else:
        logger.warning("No trending products found")
    
    # Search for each profitable brand + model combination
    for brand in PROFITABLE_BRANDS:
        for model in PROFITABLE_MODELS:
            search_term = f"{brand} {model}"
            logger.info(f"Searching for: {search_term}")
            
            with scraper as s:
                search_products = s.search_products(keywords=search_term.split())
                
            if search_products:
                logger.info(f"Found {len(search_products)} products for '{search_term}'")
                all_products.extend(search_products)
            else:
                logger.warning(f"No products found for '{search_term}'")
                
            # Delay to avoid rate limiting
            time.sleep(5)
    
    # Remove duplicates (based on URL)
    unique_products = []
    urls_seen = set()
    
    for product in all_products:
        url = product.get('url', '')
        if url and url not in urls_seen:
            urls_seen.add(url)
            unique_products.append(product)
    
    logger.info(f"Found {len(unique_products)} unique products in total")
    
    # Calculate potential profit for each product
    profitable_products = []
    
    logger.info("Analyzing products for profit potential...")
    for product in unique_products:
        # Get detailed information
        with scraper as s:
            try:
                details = s.get_product_details(product.get('url', ''))
                if not details:
                    continue
                
                # Calculate profit potential
                retail_price = details.get('retail_price', 0) or details.get('original_price', 0)
                if not retail_price:
                    continue
                    
                market_price = details.get('market_price', 0) or details.get('last_sale', 0)
                if not market_price:
                    continue
                
                # Calculate profit metrics
                profit_amount = market_price - retail_price
                profit_percentage = (profit_amount / retail_price) * 100 if retail_price > 0 else 0
                
                # Add profit metrics to details
                details['profit_amount'] = profit_amount
                details['profit_percentage'] = profit_percentage
                details['profit_analysis_date'] = current_date
                
                # Consider it profitable if potential profit is at least 15% and $30
                if profit_percentage >= 15 and profit_amount >= 30:
                    profitable_products.append(details)
                    logger.info(f"Profitable: {details.get('title')} - Profit: ${profit_amount:.2f} ({profit_percentage:.1f}%)")
            except Exception as e:
                logger.error(f"Error analyzing product {product.get('title', 'Unknown')}: {e}")
            
            # Delay to avoid rate limiting
            time.sleep(5)
    
    # Sort profitable products by profit percentage (descending)
    profitable_products.sort(key=lambda x: x.get('profit_percentage', 0), reverse=True)
    
    # Make sure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Save results to a file
    results_file = "stockx_profit_analysis.json"
    try:
        with open(results_file, 'w') as f:
            json.dump({
                'analysis_date': current_date,
                'products_analyzed': len(unique_products),
                'profitable_products': profitable_products
            }, f, indent=2)
        logger.info(f"Successfully saved results to {results_file}")
    except Exception as e:
        logger.error(f"Error saving results to {results_file}: {e}")
        print(f"Error saving results: {e}")
    
    # Print results summary
    print("\n" + "=" * 70)
    print(f" PROFIT ANALYSIS RESULTS - {current_date} ")
    print("=" * 70)
    print(f"Total products analyzed: {len(unique_products)}")
    print(f"Profitable products found: {len(profitable_products)}")
    print(f"Results saved to: {results_file}")
    print("\nTOP 10 MOST PROFITABLE SNEAKERS:")
    print("-" * 70)
    
    for i, product in enumerate(profitable_products[:10], 1):
        title = product.get('title', 'Unknown')
        brand = product.get('brand', 'Unknown')
        retail = product.get('retail_price', 0) or product.get('original_price', 0)
        market = product.get('market_price', 0) or product.get('last_sale', 0)
        profit = product.get('profit_amount', 0)
        profit_percent = product.get('profit_percentage', 0)
        
        print(f"{i}. {title} ({brand})")
        print(f"   Retail: ${retail:.2f} | Market: ${market:.2f}")
        print(f"   Profit: ${profit:.2f} ({profit_percent:.1f}%)")
        print(f"   URL: {product.get('url', 'N/A')}")
        print("-" * 70)
    
    # Send results to monitoring server if configured
    try:
        monitoring_url = os.environ.get("PROFIT_MONITOR_WEBHOOK")
        if monitoring_url:
            logger.info("Sending results to monitoring server...")
            monitoring_data = {
                'analysis_date': current_date,
                'total_products': len(unique_products),
                'profitable_count': len(profitable_products),
                'top_profit': profitable_products[0]['profit_amount'] if profitable_products else 0,
                'top_product': profitable_products[0]['title'] if profitable_products else "None",
                'source': 'stockx_profit_finder'
            }
            
            response = requests.post(monitoring_url, json=monitoring_data)
            if response.status_code == 200:
                logger.info("Successfully sent results to monitoring server")
            else:
                logger.warning(f"Failed to send results to monitoring server: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending results to monitoring server: {e}")
    
    print("\nStockX profit finder completed!")
    return profitable_products

if __name__ == "__main__":
    start_time = time.time()
    profitable_sneakers = find_profitable_sneakers()
    elapsed_time = time.time() - start_time
    
    print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
    logger.info(f"Analysis completed in {elapsed_time:.2f} seconds")
