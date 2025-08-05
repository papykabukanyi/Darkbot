"""
Test script for the dynamic sneaker detail system
"""

import os
import sys
import logging
import json
import time

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Import configuration
from config_fixed import setup_logging

# Import custom modules
from utils.database import SneakerDatabase
from utils.detail_handler import SneakerDetailHandler
import webbrowser

# Set up logging
logger = setup_logging('test_detail_system')

def test_detail_system():
    """Test the dynamic sneaker detail system."""
    logger.info("Testing the dynamic sneaker detail system...")
    
    # Initialize database
    db_path = os.path.join(BASE_DIR, "data", "sneaker_releases.db")
    db = SneakerDatabase(db_path)
    
    # Initialize detail handler
    detail_handler = SneakerDetailHandler(base_dir=BASE_DIR, db=db)
    
    # Start the detail server
    if not detail_handler.is_server_running:
        detail_handler.start_detail_server()
        logger.info(f"Detail server started on port {detail_handler.port}")
    
    # Get all SKUs in the database
    all_skus = db.get_all_skus()
    logger.info(f"Found {len(all_skus)} SKUs in the database")
    
    if all_skus:
        # Take the first SKU for testing
        test_sku = all_skus[0]
        logger.info(f"Testing with SKU: {test_sku}")
        
        # Get the sneaker data
        sneaker_data = db.get_release_by_sku(test_sku)
        
        if sneaker_data:
            logger.info(f"Found sneaker: {sneaker_data.get('title')}")
            
            # Get the detail URL
            detail_url = detail_handler.get_detail_url(test_sku)
            logger.info(f"Detail URL: {detail_url}")
            
            # Open the detail page in browser
            webbrowser.open(detail_url)
            logger.info("Opened detail page in browser")
            
            # Keep the server running for a while
            logger.info("Server will keep running for 60 seconds for testing...")
            time.sleep(60)
            
        else:
            logger.error(f"Sneaker with SKU '{test_sku}' not found in database")
    else:
        logger.error("No SKUs found in database. Add some sneakers first.")
    
    # Stop the server when done
    detail_handler.stop_detail_server()
    logger.info("Detail server stopped")

if __name__ == "__main__":
    test_detail_system()
