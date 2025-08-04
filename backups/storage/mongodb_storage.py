"""
MongoDB storage implementation for sneaker deals.
"""

import logging
import os
from datetime import datetime
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from typing import Dict, List, Any, Optional

from storage.deal_storage import DealStorage

logger = logging.getLogger(__name__)

class MongoDBStorage:
    """
    MongoDB storage implementation for sneaker deals.
    """

    def __init__(self, connection_string: str, database_name: str, collection_name: str):
        """
        Initialize MongoDB storage.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
        # Connect to MongoDB
        self._connect()
    
    def _connect(self) -> None:
        """Connect to MongoDB."""
        try:
            # Connect to MongoDB
            self.client = MongoClient(self.connection_string)
            
            # Create database if it doesn't exist
            self.db = self.client[self.database_name]
            
            # Create collection if it doesn't exist
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better performance
            self._ensure_indexes()
            
            logger.info(f"Connected to MongoDB database: {self.database_name}, collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            self.collection = None
    
    def _ensure_indexes(self) -> None:
        """Ensure indexes exist for better query performance."""
        if self.collection:
            try:
                # Index on SKU field
                self.collection.create_index("sku")
                
                # Index on URL field
                self.collection.create_index("url")
                
                # Index on created_at field for sorting
                self.collection.create_index("created_at")
                
                # Compound index on brand and model
                self.collection.create_index([("brand", 1), ("model", 1)])
                
                # Index on is_profitable flag
                self.collection.create_index("is_profitable")
                
                logger.info("MongoDB indexes created successfully")
            except Exception as e:
                logger.warning(f"Failed to create MongoDB indexes: {e}")
    
    def upload_deals(self, deals: List[Dict[str, Any]]) -> bool:
        """
        Upload deals to MongoDB.
        
        Args:
            deals: List of deal dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not deals:
            logger.info("No deals to upload to MongoDB")
            return True
        
        if not self.collection:
            logger.error("MongoDB collection not initialized")
            return False
        
        try:
            # Add created_at timestamp to each deal
            for deal in deals:
                # Add timestamp if not present
                if 'created_at' not in deal:
                    deal['created_at'] = datetime.utcnow()
            
            # Insert or update deals based on URL or SKU
            processed = 0
            for deal in deals:
                query = {}
                
                # Try to use SKU for matching if available
                if deal.get('sku'):
                    query['sku'] = deal['sku']
                # Otherwise use URL
                elif deal.get('url'):
                    query['url'] = deal['url']
                else:
                    # Skip deals without SKU or URL
                    logger.warning("Skipping deal without SKU or URL")
                    continue
                
                # Check if deal already exists
                existing_deal = self.collection.find_one(query)
                
                if existing_deal:
                    # Update existing deal
                    self.collection.update_one(
                        {"_id": existing_deal["_id"]},
                        {"$set": {
                            "price": deal.get('price', existing_deal.get('price')),
                            "title": deal.get('title', existing_deal.get('title')),
                            "brand": deal.get('brand', existing_deal.get('brand')),
                            "model": deal.get('model', existing_deal.get('model')),
                            "discount_percent": deal.get('discount_percent', existing_deal.get('discount_percent')),
                            "original_price": deal.get('original_price', existing_deal.get('original_price')),
                            "market_price": deal.get('market_price', existing_deal.get('market_price')),
                            "profit_potential": deal.get('profit_potential', existing_deal.get('profit_potential')),
                            "profit_percent": deal.get('profit_percent', existing_deal.get('profit_percent')),
                            "is_profitable": deal.get('is_profitable', existing_deal.get('is_profitable')),
                            "last_updated": datetime.utcnow()
                        }}
                    )
                else:
                    # Insert new deal
                    self.collection.insert_one(deal)
                
                processed += 1
            
            logger.info(f"Uploaded {processed} deals to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to upload deals to MongoDB: {e}")
            return False
    
    def get_deals(self, limit: int = 100, profitable_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get deals from MongoDB.
        
        Args:
            limit: Maximum number of deals to retrieve
            profitable_only: Whether to retrieve only profitable deals
            
        Returns:
            List of deal dictionaries
        """
        if not self.collection:
            logger.error("MongoDB collection not initialized")
            return []
        
        try:
            query = {}
            if profitable_only:
                query['is_profitable'] = True
            
            # Sort by created_at (newest first)
            cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
            
            # Convert cursor to list
            deals = list(cursor)
            
            logger.info(f"Retrieved {len(deals)} deals from MongoDB")
            return deals
        except Exception as e:
            logger.error(f"Failed to retrieve deals from MongoDB: {e}")
            return []
    
    def get_deal_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get a deal by SKU.
        
        Args:
            sku: SKU of the deal
            
        Returns:
            Deal dictionary or None if not found
        """
        if not self.collection:
            logger.error("MongoDB collection not initialized")
            return None
        
        try:
            deal = self.collection.find_one({"sku": sku})
            return deal
        except Exception as e:
            logger.error(f"Failed to retrieve deal by SKU from MongoDB: {e}")
            return None
    
    def get_deal_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get a deal by URL.
        
        Args:
            url: URL of the deal
            
        Returns:
            Deal dictionary or None if not found
        """
        if not self.collection:
            logger.error("MongoDB collection not initialized")
            return None
        
        try:
            deal = self.collection.find_one({"url": url})
            return deal
        except Exception as e:
            logger.error(f"Failed to retrieve deal by URL from MongoDB: {e}")
            return None
    
    def delete_deal(self, deal_id: str) -> bool:
        """
        Delete a deal by ID.
        
        Args:
            deal_id: ID of the deal to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.collection:
            logger.error("MongoDB collection not initialized")
            return False
        
        try:
            result = self.collection.delete_one({"_id": deal_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted deal with ID: {deal_id}")
                return True
            else:
                logger.warning(f"Deal with ID {deal_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to delete deal from MongoDB: {e}")
            return False
    
    def delete_old_deals(self, days: int = 30) -> int:
        """
        Delete deals older than the specified number of days.
        
        Args:
            days: Number of days to keep deals for
            
        Returns:
            Number of deals deleted
        """
        if not self.collection:
            logger.error("MongoDB collection not initialized")
            return 0
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
            
            # Delete deals older than cutoff date
            result = self.collection.delete_many({"created_at": {"$lt": cutoff_date}})
            
            deleted_count = result.deleted_count
            logger.info(f"Deleted {deleted_count} deals older than {days} days")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old deals from MongoDB: {e}")
            return 0
    
    def continue_to_iterate(self, previous_deals: List[Dict[str, Any]], 
                          current_deals: List[Dict[str, Any]]) -> bool:
        """
        Determine if iteration should continue based on new deals found.
        
        Args:
            previous_deals: Deals from previous iteration
            current_deals: Deals from current iteration
            
        Returns:
            bool: True if iteration should continue, False otherwise
        """
        # If no previous deals, continue if we found deals
        if not previous_deals:
            return len(current_deals) > 0
        
        # If we found no deals, stop
        if not current_deals:
            return False
        
        # Get SKUs from previous deals
        previous_skus = set(deal.get('sku') for deal in previous_deals if deal.get('sku'))
        
        # Get SKUs from current deals
        current_skus = set(deal.get('sku') for deal in current_deals if deal.get('sku'))
        
        # Find new SKUs
        new_skus = current_skus - previous_skus
        
        # Continue if we found new deals
        return len(new_skus) > 0
    
    def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")
