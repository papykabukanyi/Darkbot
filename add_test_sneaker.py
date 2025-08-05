"""
Add a test sneaker to the database
"""

import os
import sys
import logging

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Import configuration
from config_fixed import setup_logging

# Import custom modules
from utils.database import SneakerDatabase

# Set up logging
logger = setup_logging('add_test_sneaker')

def add_test_sneaker():
    """Add a test sneaker to the database."""
    logger.info("Adding test sneaker to the database...")
    
    # Initialize database
    db_path = os.path.join(BASE_DIR, "data", "sneaker_releases.db")
    db = SneakerDatabase(db_path)
    
    # Create test sneaker data
    test_sneaker = {
        'title': 'Air Jordan 1 Retro High OG "Chicago Lost and Found"',
        'brand': 'Nike',
        'sku': 'DZ5485-612',
        'url': 'https://www.nike.com/t/air-jordan-1-retro-high-og-shoes-789X6Z/DZ5485-612',
        'image_url': 'https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/e125b578-4173-401a-ab13-f066979c8848/air-jordan-1-retro-high-og-shoes-789X6Z.png',
        'release_date': '2022-11-19',
        'retail_price': 180,
        'market_price': 350,
        'profit_potential': 170,
        'source': 'test',
        'status': 'available',
        'scraped_at': '2023-01-01T00:00:00',
        'price_check_results': {
            'retail_price': 180,
            'market_price': 350,
            'profit': {
                'amount': 170,
                'percentage': 94.44
            },
            'price_comparison': {
                'best_price': {
                    'site': 'StockX',
                    'price': 350
                },
                'highest_price': {
                    'site': 'GOAT',
                    'price': 375
                },
                'price_range': 25,
                'best_profit': {
                    'site': 'GOAT',
                    'profit': 195,
                    'roi': 108.33
                },
                'price_results': [
                    {
                        'site_name': 'StockX',
                        'price': 350,
                        'status': 'success',
                        'url': 'https://stockx.com/air-jordan-1-retro-high-og-chicago-lost-and-found'
                    },
                    {
                        'site_name': 'GOAT',
                        'price': 375,
                        'status': 'success',
                        'url': 'https://www.goat.com/sneakers/air-jordan-1-retro-high-og-chicago-lost-and-found-dz5485-612'
                    },
                    {
                        'site_name': 'Flight Club',
                        'price': 360,
                        'status': 'success',
                        'url': 'https://www.flightclub.com/air-jordan-1-retro-high-og-chicago-lost-and-found-dz5485-612'
                    },
                    {
                        'site_name': 'Stadium Goods',
                        'price': 365,
                        'status': 'success',
                        'url': 'https://www.stadiumgoods.com/en-us/shopping/air-jordan-1-retro-high-og-chicago-lost-and-found-18817556'
                    }
                ]
            }
        },
        'purchase_links': [
            {
                'retailer': 'Nike',
                'status': 'sold_out',
                'price': 180,
                'discount': None,
                'url': 'https://www.nike.com/t/air-jordan-1-retro-high-og-shoes-789X6Z/DZ5485-612'
            },
            {
                'retailer': 'Foot Locker',
                'status': 'sold_out',
                'price': 180,
                'discount': None,
                'url': 'https://www.footlocker.com/product/jordan-aj-1-high-og-mens/DZ5485612.html'
            },
            {
                'retailer': 'StockX',
                'status': 'available',
                'price': 350,
                'discount': None,
                'url': 'https://stockx.com/air-jordan-1-retro-high-og-chicago-lost-and-found'
            },
            {
                'retailer': 'GOAT',
                'status': 'available',
                'price': 375,
                'discount': None,
                'url': 'https://www.goat.com/sneakers/air-jordan-1-retro-high-og-chicago-lost-and-found-dz5485-612'
            }
        ]
    }
    
    # Save to database
    result = db.save_releases([test_sneaker])
    
    if result > 0:
        logger.info("Test sneaker added successfully!")
    else:
        logger.warning("Test sneaker already exists in database. No changes made.")
    
    # Verify that we can retrieve it by SKU
    sneaker = db.get_release_by_sku(test_sneaker['sku'])
    if sneaker:
        logger.info(f"Successfully retrieved test sneaker by SKU: {sneaker.get('title')}")
    else:
        logger.error(f"Failed to retrieve test sneaker by SKU: {test_sneaker['sku']}")

if __name__ == "__main__":
    add_test_sneaker()
