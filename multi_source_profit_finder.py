#!/usr/bin/env python
"""
Multi-Source Profit Finder for Sneakers and Other E-commerce Items
This tool finds profitable items from multiple sources, not just StockX
"""

import sys
import os
import logging
import json
import time
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("logs/profit_finder.log", mode="w"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MultiSourceProfitFinder")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sites import SNEAKER_SITES
from scrapers.factory import get_scraper_for_site
from utils.price_comparison import PriceComparer

# Key sources to check for deals and price comparisons
SOURCES = [
    "stockx",
    "adidas",
    "nike",
    "footlocker",
    "champssports",
    "jdsports",
    "finishline",
    "undefeated",
]

# List of profitable brands to search across all sources
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
    "Kobe",
    "Puma",
    "Reebok",
    "Converse",
    "Vans"
]

# Popular models known for resale value
PROFITABLE_MODELS = [
    "Jordan 1",
    "Jordan 3",
    "Jordan 4",
    "Jordan 11",
    "Dunk Low",
    "Dunk High",
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
    "Kobe 6",
    "Foam Runner",
    "Ultra Boost",
    "NMD"
]

# Additional categories to search (beyond just sneakers)
OTHER_CATEGORIES = [
    "apparel",
    "accessories",
    "streetwear",
    "collabs",
    "limited",
    "exclusive"
]

def get_scraper_for_source(source):
    """Get a scraper instance for a specific source"""
    site_config = SNEAKER_SITES.get(source, {})
    if not site_config:
        logger.warning(f"Config not found for source: {source}")
        return None
        
    try:
        scraper_class = get_scraper_for_site(source, site_config)
        return scraper_class
    except Exception as e:
        logger.error(f"Error creating scraper for {source}: {e}")
        return None

def search_source(source, search_term, max_products=10):
    """Search a specific source for products matching the search term"""
    logger.info(f"Searching {source} for: {search_term}")
    scraper_class = get_scraper_for_source(source)
    
    if not scraper_class:
        return []
    
    try:
        with scraper_class as scraper:
            products = scraper.search_products(keywords=search_term.split())
            logger.info(f"Found {len(products)} products from {source} for '{search_term}'")
            
            # Limit results to avoid overwhelming
            return products[:max_products]
    except Exception as e:
        logger.error(f"Error searching {source} for {search_term}: {e}")
        return []

def get_market_prices(products, price_comparer):
    """Get market prices for products from multiple sources"""
    enriched_products = []
    
    for product in products:
        try:
            # Get detailed market data
            market_price = price_comparer.fetch_market_price(product)
            
            # Add market price information
            if market_price > 0:
                product['market_price'] = market_price
                
                # Calculate profit metrics if retail price is available
                retail_price = product.get('price', 0) or product.get('current_price', 0)
                if retail_price > 0:
                    profit_amount = market_price - retail_price
                    profit_percentage = (profit_amount / retail_price) * 100
                    
                    product['profit_amount'] = profit_amount
                    product['profit_percentage'] = profit_percentage
                    product['is_profitable'] = profit_percentage >= 15 and profit_amount >= 30
            
            enriched_products.append(product)
        except Exception as e:
            logger.error(f"Error getting market price for {product.get('title', 'Unknown')}: {e}")
    
    return enriched_products

def find_profitable_items():
    """Find the most profitable items from multiple sources"""
    print("=" * 70)
    print(" MULTI-SOURCE PROFIT FINDER - Finding profitable items across platforms ")
    print("=" * 70)
    
    # Initialize price comparer
    price_comparer = PriceComparer()
    
    # Store all found products
    all_products = []
    
    # Get the current date for the report
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Make sure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # First, get trending/popular items from each source
    logger.info("Searching for trending products across multiple sources...")
    
    for source in SOURCES:
        try:
            scraper_class = get_scraper_for_source(source)
            if scraper_class:
                with scraper_class as scraper:
                    if hasattr(scraper, 'search_trending_products'):
                        trending_products = scraper.search_trending_products()
                        if trending_products:
                            logger.info(f"Found {len(trending_products)} trending products from {source}")
                            for product in trending_products:
                                product['source'] = source
                            all_products.extend(trending_products)
                    else:
                        # If no specific trending method, just search popular products
                        popular_products = scraper.search_products()
                        if popular_products:
                            logger.info(f"Found {len(popular_products)} popular products from {source}")
                            for product in popular_products:
                                product['source'] = source
                            all_products.extend(popular_products)
        except Exception as e:
            logger.error(f"Error getting trending products from {source}: {e}")
        
        # Delay to avoid rate limiting
        time.sleep(2)
    
    # Now search for specific profitable combinations across sources using ThreadPoolExecutor
    search_combinations = []
    
    # Create search combinations
    for brand in PROFITABLE_BRANDS:
        for model in PROFITABLE_MODELS:
            search_combinations.append(f"{brand} {model}")
    
    # Add some category searches
    for brand in PROFITABLE_BRANDS[:5]:  # Use just top brands for category searches
        for category in OTHER_CATEGORIES:
            search_combinations.append(f"{brand} {category}")
    
    logger.info(f"Generated {len(search_combinations)} search combinations")
    logger.info(f"Searching across {len(SOURCES)} different sources")
    
    # Use ThreadPoolExecutor to speed up the process
    with ThreadPoolExecutor(max_workers=3) as executor:
        # For each source, submit search tasks
        future_to_search = {}
        
        for source in SOURCES:
            for search_term in search_combinations:
                future = executor.submit(search_source, source, search_term, max_products=5)
                future_to_search[future] = (source, search_term)
        
        # Process results as they complete
        for future in future_to_search:
            source, search_term = future_to_search[future]
            try:
                products = future.result()
                if products:
                    # Add source information to each product
                    for product in products:
                        product['source'] = source
                    all_products.extend(products)
                    logger.info(f"Added {len(products)} products from {source} for '{search_term}'")
                    
            except Exception as e:
                logger.error(f"Error processing search results for {source}, {search_term}: {e}")
    
    # Remove duplicates (based on URL)
    unique_products = []
    urls_seen = set()
    
    for product in all_products:
        url = product.get('url', '')
        if url and url not in urls_seen:
            urls_seen.add(url)
            unique_products.append(product)
    
    logger.info(f"Found {len(unique_products)} unique products in total")
    
    # Get market prices and calculate profit for all products
    logger.info("Getting market prices and calculating profit potential...")
    enriched_products = get_market_prices(unique_products, price_comparer)
    
    # Filter profitable products
    profitable_products = [p for p in enriched_products if p.get('is_profitable', False)]
    
    # Sort profitable products by profit percentage (descending)
    profitable_products.sort(key=lambda x: x.get('profit_percentage', 0), reverse=True)
    
    # Make sure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Save results to a file
    results_file = "profit_analysis.json"
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
    print("\nTOP PROFITABLE ITEMS BY SOURCE:")
    
    # Group profitable items by source
    source_products = {}
    for product in profitable_products:
        source = product.get('source', 'unknown')
        if source not in source_products:
            source_products[source] = []
        source_products[source].append(product)
    
    # Display top products by source
    for source, products in source_products.items():
        if not products:
            continue
            
        print(f"\n{source.upper()} - Top 3 Most Profitable:")
        print("-" * 70)
        
        for i, product in enumerate(products[:3], 1):
            title = product.get('title', 'Unknown')
            brand = product.get('brand', 'Unknown')
            retail = product.get('price', 0) or product.get('current_price', 0)
            market = product.get('market_price', 0)
            profit = product.get('profit_amount', 0)
            profit_percent = product.get('profit_percentage', 0)
            
            print(f"{i}. {title} ({brand})")
            print(f"   Retail: ${retail:.2f} | Market: ${market:.2f}")
            print(f"   Profit: ${profit:.2f} ({profit_percent:.1f}%)")
            print(f"   URL: {product.get('url', 'N/A')}")
    
    print("-" * 70)
    print("\nProfit finder completed!")
    return profitable_products

if __name__ == "__main__":
    start_time = time.time()
    profitable_items = find_profitable_items()
    elapsed_time = time.time() - start_time
    
    print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
    logger.info(f"Analysis completed in {elapsed_time:.2f} seconds")
