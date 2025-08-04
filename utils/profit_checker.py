"""
Profit Checker - Compares sneaker prices across multiple sources to find profitable opportunities
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import concurrent.futures
from enum import Enum

logger = logging.getLogger("SneakerBot")

class ProfitStatus(Enum):
    """Enum to represent the profit status of a sneaker."""
    PROFITABLE = "profitable"
    BREAK_EVEN = "break_even"
    LOSS = "loss"
    UNKNOWN = "unknown"

class ProfitChecker:
    """Class to check sneaker prices across multiple sources and identify profitable opportunities."""
    
    def __init__(self, config):
        """Initialize the profit checker with configuration."""
        self.config = config
        self.data_sources = config.get('data_sources', [])
        self.price_threshold = config.get('price_threshold', 20)  # Minimum profit percentage
        self.fee_percentage = config.get('fee_percentage', 12)    # Platform fees (e.g., StockX)
        self.shipping_cost = config.get('shipping_cost', 15)      # Average shipping cost
        self.profit_margin_required = config.get('profit_margin_required', 20)  # Min profit in dollars
    
    def calculate_profit(self, retail_price: float, market_price: float) -> Dict[str, Any]:
        """
        Calculate the profit for a sneaker.
        
        Args:
            retail_price: The retail price of the sneaker
            market_price: The market price (what you can sell for)
            
        Returns:
            Dictionary with profit details
        """
        if not retail_price or not market_price:
            return {
                'profit_amount': 0,
                'profit_percentage': 0,
                'profit_status': ProfitStatus.UNKNOWN.value,
                'fees': 0,
                'shipping': 0,
                'net_profit': 0,
                'is_profitable': False
            }
        
        # Calculate fees
        fees = (market_price * self.fee_percentage) / 100
        
        # Calculate net profit
        net_profit = market_price - retail_price - fees - self.shipping_cost
        
        # Calculate profit percentage
        profit_percentage = (net_profit / retail_price) * 100 if retail_price > 0 else 0
        
        # Determine profit status
        if net_profit >= self.profit_margin_required:
            profit_status = ProfitStatus.PROFITABLE.value
            is_profitable = True
        elif net_profit > 0:
            profit_status = ProfitStatus.BREAK_EVEN.value
            is_profitable = False
        else:
            profit_status = ProfitStatus.LOSS.value
            is_profitable = False
        
        return {
            'profit_amount': round(net_profit, 2),
            'profit_percentage': round(profit_percentage, 2),
            'profit_status': profit_status,
            'fees': round(fees, 2),
            'shipping': self.shipping_cost,
            'net_profit': round(net_profit, 2),
            'is_profitable': is_profitable
        }
    
    def check_price(self, release: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check the profit potential for a single release.
        
        Args:
            release: Release information with at least 'sku' and 'price'
            
        Returns:
            Updated release with profit information
        """
        if not release.get('sku'):
            logger.warning(f"Cannot check price for release without SKU: {release.get('title', 'Unknown')}")
            return release
        
        retail_price = self._extract_price(release.get('price', '0'))
        if not retail_price:
            logger.warning(f"No retail price found for {release.get('title', 'Unknown')}")
            release['price_check_results'] = {
                'status': 'error',
                'message': 'No retail price found'
            }
            return release
        
        # Get prices from all configured data sources
        prices = []
        for source in self.data_sources:
            try:
                source_prices = self._get_price_from_source(source, release)
                if source_prices:
                    prices.extend(source_prices)
            except Exception as e:
                logger.error(f"Error getting prices from {source.get('name', 'Unknown')}: {e}")
        
        # Find the best price (highest market price)
        if prices:
            best_price = max(prices, key=lambda x: x.get('price', 0))
            market_price = best_price.get('price', 0)
            
            # Calculate profit
            profit_info = self.calculate_profit(retail_price, market_price)
            
            # Add price check results to release
            release['price_check_results'] = {
                'status': 'success',
                'retail_price': retail_price,
                'market_price': market_price,
                'best_price_source': best_price.get('source'),
                'profit': profit_info,
                'all_prices': prices,
                'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            release['price_check_results'] = {
                'status': 'error',
                'message': 'No market prices found'
            }
        
        return release
    
    def check_prices_batch(self, releases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check prices for multiple releases in parallel.
        
        Args:
            releases: List of release dictionaries
            
        Returns:
            Updated releases with profit information
        """
        logger.info(f"Checking prices for {len(releases)} releases")
        
        # Use a thread pool to check prices in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit tasks
            future_to_release = {executor.submit(self.check_price, release): release for release in releases}
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(future_to_release):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error checking price: {e}")
        
        # Sort results by profitability
        results.sort(
            key=lambda x: x.get('price_check_results', {}).get('profit', {}).get('profit_amount', 0),
            reverse=True
        )
        
        return results
    
    def _extract_price(self, price_str: Any) -> float:
        """
        Extract a price value from a string or number.
        
        Args:
            price_str: Price string (e.g., '$150', '150.00', 150)
            
        Returns:
            Float price value
        """
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        if not price_str:
            return 0.0
        
        # Remove currency symbols and other non-numeric characters
        import re
        price_numeric = re.sub(r'[^\d.]', '', str(price_str))
        
        try:
            return float(price_numeric)
        except (ValueError, TypeError):
            return 0.0
    
    def _get_price_from_source(self, source, release) -> List[Dict[str, Any]]:
        """
        Get prices from a specific data source.
        
        Args:
            source: Data source configuration
            release: Release information
            
        Returns:
            List of price dictionaries
        """
        source_name = source.get('name', 'Unknown')
        sku = release.get('sku')
        if not sku:
            logger.warning(f"Cannot get price from {source_name} without SKU")
            return []
        
        try:
            # Get the appropriate adapter for this source
            adapter_class = self._get_adapter_class(source.get('type', 'none'))
            if not adapter_class:
                logger.error(f"No adapter found for source type: {source.get('type')}")
                return []
            
            # Initialize the adapter with the source config
            adapter = adapter_class(source)
            
            # Get prices
            prices = adapter.get_prices(sku, release)
            
            # Add source information to each price
            for price in prices:
                price['source'] = source_name
                price['source_type'] = source.get('type')
                price['source_url'] = price.get('url') or source.get('url')
            
            return prices
            
        except Exception as e:
            logger.error(f"Error getting price from {source_name}: {e}")
            return []
    
    def _get_adapter_class(self, adapter_type):
        """
        Get the adapter class for a specific type.
        
        Args:
            adapter_type: Type of adapter to get
            
        Returns:
            Adapter class
        """
        # Import adapters only when needed
        if adapter_type == 'stockx':
            from price_sources.stockx import StockXAdapter
            return StockXAdapter
        elif adapter_type == 'goat':
            from price_sources.goat import GoatAdapter
            return GoatAdapter
        elif adapter_type == 'ebay':
            from price_sources.ebay import EbayAdapter
            return EbayAdapter
        elif adapter_type == 'flight_club':
            from price_sources.flight_club import FlightClubAdapter
            return FlightClubAdapter
        elif adapter_type == 'stadium_goods':
            from price_sources.stadium_goods import StadiumGoodsAdapter
            return StadiumGoodsAdapter
        elif adapter_type == 'api':
            from price_sources.api import ApiAdapter
            return ApiAdapter
        else:
            logger.warning(f"Unknown adapter type: {adapter_type}")
            return None
