"""
Price comparison functionality for identifying profitable deals.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import re

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
    
    def calculate_profit(self, deal: Dict[str, Any]) -> Tuple[float, float]:
        """
        Calculate potential profit for a deal.
        
        Args:
            deal: Dictionary with deal information
            
        Returns:
            Tuple of (profit_amount, profit_percentage)
        """
        retail_price = deal.get('current_price', 0)
        if retail_price == 0:
            return 0, 0
            
        # Try to find market price data for this SKU
        sku = deal.get('sku', '')
        if not sku:
            sku = deal.get('model', '')
        
        if not sku:
            return 0, 0
            
        market_sku = self.find_similar_sku(sku)
        if not market_sku:
            return 0, 0
            
        market_data = self.market_data[market_sku]
        market_price = market_data.get('market_price', 0)
        
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
