"""
Price comparison functionality for identifying profitable deals.
"""

import logging
import time
from typing import Dict, List, Any, Tuple, Optional
import re

from utils.market_data import MarketDataService

logger = logging.getLogger(__name__)

class PriceComparer:
    """
    Compares retail and market prices to identify profitable deals.
    """
    
    def __init__(self, market_data: Dict[str, Dict[str, Any]] = None):
        """
        Initialize the price comparer with market price data.
        
        Args:
            market_data: Dictionary of market price data keyed by SKU/model
        """
        self.market_data = market_data or {}
        self.profit_threshold = 20  # Minimum profit percentage to consider a good deal
        self.market_service = MarketDataService()
        self.cache_ttl = 3600  # Cache market data for 1 hour (in seconds)
        
    def add_market_data(self, sku: str, data: Dict[str, Any]) -> None:
        """
        Add market price data for a SKU.
        
        Args:
            sku: SKU or model number
            data: Dictionary with market price data
        """
        self.market_data[sku] = data
        
    def add_market_price(self, deal: Dict[str, Any]) -> None:
        """
        Add market price data from a deal dictionary.
        
        Args:
            deal: Dictionary with deal information including sku/model and market price
        """
        sku = deal.get('sku', '') or deal.get('model', '')
        if not sku:
            logger.warning("Cannot add market price: No SKU or model in deal")
            return
            
        self.market_data[sku] = {
            'market_price': deal.get('market_price', 0),
            'source': deal.get('site', 'unknown'),
            'url': deal.get('url', ''),
            'timestamp': deal.get('timestamp', None)
        }
        
    def get_market_data_count(self) -> int:
        """
        Get the count of market price data entries.
        
        Returns:
            Number of market price data entries
        """
        return len(self.market_data)
    
    def normalize_sku(self, sku: str) -> str:
        """
        Normalize SKU for consistent comparison.
        
        Args:
            sku: SKU or model number
            
        Returns:
            Normalized SKU
        """
        # Remove non-alphanumeric characters and convert to uppercase
        return re.sub(r'[^A-Z0-9]', '', sku.upper())
    
    def find_similar_sku(self, sku: str) -> Optional[str]:
        """
        Find a similar SKU in the market data.
        
        Args:
            sku: SKU or model number to find
            
        Returns:
            Similar SKU if found, None otherwise
        """
        normalized_sku = self.normalize_sku(sku)
        
        # Exact match
        if normalized_sku in self.market_data:
            return normalized_sku
            
        # Partial match (if SKU contains the other)
        for market_sku in self.market_data:
            norm_market_sku = self.normalize_sku(market_sku)
            if normalized_sku in norm_market_sku or norm_market_sku in normalized_sku:
                return market_sku
                
        return None
    
    def fetch_market_price(self, deal: Dict[str, Any]) -> float:
        """
        Fetch the current market price for a deal from real market data sources.
        
        Args:
            deal: Dictionary with deal information
            
        Returns:
            Current market price for the deal
        """
        # First check if we have cached data
        sku = deal.get('sku', '') or deal.get('model', '')
        title = deal.get('title', '')
        brand = deal.get('brand', '')
        
        # Try to get market data by SKU
        market_price = 0
        if sku:
            # First check cache
            matching_sku = self.find_similar_sku(sku)
            if matching_sku and self._is_cache_valid(matching_sku):
                logger.info(f"Using cached market data for SKU {sku}")
                return self.market_data[matching_sku].get('market_price', 0)
                
            # If not in cache or expired, fetch from service
            logger.info(f"Fetching market data for SKU {sku}")
            market_data = self.market_service.get_market_data(sku=sku)
            
            if market_data and market_data.get('market_price', 0) > 0:
                # Cache the data
                self.market_data[sku] = market_data
                return market_data.get('market_price', 0)
        
        # If no SKU or no result by SKU, try by product name
        if title and not market_price:
            search_query = f"{brand} {title}" if brand else title
            logger.info(f"Fetching market data for product {search_query}")
            market_data = self.market_service.get_market_data(product_name=search_query)
            
            if market_data and market_data.get('market_price', 0) > 0:
                # If we now have a SKU, cache by that
                if market_data.get('sku'):
                    self.market_data[market_data['sku']] = market_data
                # Also cache by the original title as a fallback
                self.market_data[f"title:{title}"] = market_data
                return market_data.get('market_price', 0)
        
        # If we still don't have market data, use 90% of original price as estimate
        logger.warning(f"No market data found for {title} (SKU: {sku}). Using estimate.")
        return deal.get('original_price', 0) * 0.9
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached market data is still valid."""
        if key not in self.market_data:
            return False
            
        last_updated = self.market_data[key].get('last_updated', 0)
        return (time.time() - last_updated) < self.cache_ttl
    
    def calculate_profit(self, deal: Dict[str, Any]) -> Tuple[float, float]:
        """
        Calculate potential profit for a deal.
        
        Args:
            deal: Dictionary with deal information
            
        Returns:
            Tuple of (profit_amount, profit_percentage)
        """
        retail_price = deal.get('price', 0) or deal.get('current_price', 0)
        if retail_price == 0:
            return 0, 0
        
        # Get market price using our new fetcher
        market_price = self.fetch_market_price(deal)
        
        if market_price == 0:
            return 0, 0
            
        # Calculate profit
        profit_amount = market_price - retail_price
        profit_percentage = (profit_amount / retail_price) * 100
        
        return profit_amount, profit_percentage
    
    def is_profitable(self, deal: Dict[str, Any]) -> bool:
        """
        Determine if a deal is profitable based on profit threshold.
        
        Args:
            deal: Dictionary with deal information
            
        Returns:
            True if deal meets profit threshold, False otherwise
        """
        _, profit_percentage = self.calculate_profit(deal)
        return profit_percentage >= self.profit_threshold
    
    def analyze_deals(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze deals to add profit information.
        
        Args:
            deals: List of deal dictionaries
            
        Returns:
            List of deals with profit information added
        """
        enriched_deals = []
        
        for deal in deals:
            profit_amount, profit_percentage = self.calculate_profit(deal)
            
            # Add profit information to the deal
            deal['profit_amount'] = profit_amount
            deal['profit_percentage'] = profit_percentage
            deal['is_profitable'] = profit_percentage >= self.profit_threshold
            
            enriched_deals.append(deal)
        
        # Sort by profitability (highest percentage first)
        return sorted(enriched_deals, key=lambda x: x.get('profit_percentage', 0), reverse=True)
        
    def get_most_profitable_deals(self, deals: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most profitable deals.
        
        Args:
            deals: List of deal dictionaries
            limit: Maximum number of deals to return
            
        Returns:
            List of the most profitable deals
        """
        analyzed_deals = self.analyze_deals(deals)
        profitable_deals = [deal for deal in analyzed_deals if deal.get('is_profitable', False)]
        
        return profitable_deals[:limit]
