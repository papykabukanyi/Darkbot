"""
Multi-Site Price Checker (StockX-focused)

This module provides a unified interface for checking sneaker prices across different platforms,
with StockX as the primary source.
"""

import logging
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import platform-specific adapters
from utils.stockx_adapter import StockXAdapter

logger = logging.getLogger("SneakerBot")

class MultiSitePriceChecker:
    """Checks prices across multiple platforms with StockX as the primary source."""
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize the price checker.
        
        Args:
            cache_dir: Directory to store cached data
        """
        self.stockx_adapter = StockXAdapter()
        
        # Set up cache directory
        if not cache_dir:
            cache_dir = os.path.join("data", "cache")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info("MultiSitePriceChecker initialized (StockX-focused)")
    
    def get_price(self, sku: str, name: str = None, retry_count: int = 3) -> Dict[str, Any]:
        """
        Get the price for a sneaker from StockX.
        
        Args:
            sku: The SKU of the sneaker
            name: The name of the sneaker (optional, for better search results)
            retry_count: Number of retries if the request fails
            
        Returns:
            Dictionary with price information
        """
        logger.info(f"Getting price for {name or sku} from StockX")
        
        # Check cache first
        cached_data = self._get_from_cache(sku)
        if cached_data:
            logger.info(f"Using cached price data for {sku}")
            return cached_data
        
        # Try to get price from StockX
        for attempt in range(retry_count):
            try:
                result = self.stockx_adapter.get_product_details(sku, name)
                
                if result and "price" in result:
                    # Cache the result
                    self._save_to_cache(sku, result)
                    return result
                
                logger.warning(f"Failed to get price for {sku} from StockX (attempt {attempt+1}/{retry_count})")
                time.sleep(2)  # Wait before retrying
            
            except Exception as e:
                logger.error(f"Error getting price for {sku} from StockX: {e}")
                time.sleep(2)  # Wait before retrying
        
        logger.error(f"Failed to get price for {sku} after {retry_count} attempts")
        return {"price": None, "source": "stockx", "error": "Failed to retrieve price"}
    
    def get_multiple_prices(self, sneakers: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Get prices for multiple sneakers.
        
        Args:
            sneakers: List of dictionaries with 'sku' and optionally 'name' keys
            
        Returns:
            List of dictionaries with price information
        """
        results = []
        
        for sneaker in sneakers:
            sku = sneaker.get("sku")
            name = sneaker.get("name")
            
            if not sku:
                logger.warning("Skipping sneaker without SKU")
                continue
            
            result = self.get_price(sku, name)
            result["sku"] = sku
            if name:
                result["name"] = name
            
            results.append(result)
            
            # Wait between requests to avoid rate limiting
            time.sleep(2)
        
        return results
    
    def _get_from_cache(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get price data from cache if available and not expired."""
        cache_file = os.path.join(self.cache_dir, f"{sku}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            
            # Check if cache is expired (24 hours)
            timestamp = data.get("timestamp", 0)
            if timestamp < time.time() - 86400:  # 24 hours in seconds
                logger.info(f"Cache expired for {sku}")
                return None
            
            return data
        except Exception as e:
            logger.error(f"Error reading cache for {sku}: {e}")
            return None
    
    def _save_to_cache(self, sku: str, data: Dict[str, Any]):
        """Save price data to cache."""
        cache_file = os.path.join(self.cache_dir, f"{sku}.json")
        
        try:
            # Add timestamp
            data["timestamp"] = time.time()
            
            with open(cache_file, "w") as f:
                json.dump(data, f)
            
            logger.info(f"Saved price data to cache for {sku}")
        except Exception as e:
            logger.error(f"Error saving cache for {sku}: {e}")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    checker = MultiSitePriceChecker()
    
    # Example sneakers
    sneakers = [
        {"sku": "DD1391-100", "name": "Nike Dunk Low Panda"},
        {"sku": "555088-101", "name": "Jordan 1 Retro High OG Chicago"}
    ]
    
    results = checker.get_multiple_prices(sneakers)
    
    for result in results:
        print(f"{result.get('name', result.get('sku'))}: ${result.get('price')}")
