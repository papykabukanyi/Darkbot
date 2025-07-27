"""
MongoDB storage module for the sneaker bot.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class MongoDBStorage:
    """Class for storing and retrieving deals from MongoDB."""
    
    def __init__(self, connection_string, database_name="sneaker_deals", collection_name="deals"):
        """
        Initialize the MongoDB storage.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the MongoDB database
            collection_name: Name of the MongoDB collection for deals
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        
        # Initialize connection
        self.client = self._get_client()
        self.db = None
        self.deals_collection = None
        self.stats_collection = None
        
        if self.client:
            self.db = self.client[database_name]
            self.deals_collection = self.db[collection_name]
            self.stats_collection = self.db["deal_stats"]
            
            # Create indexes for better query performance
            self._create_indexes()
        
    def _get_client(self):
        """
        Get a MongoDB client.
        
        Returns:
            MongoClient: MongoDB client
        """
        try:
            # Set a reasonable timeout for connection attempts
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            
            # Verify connection by sending a ping command
            client.admin.command('ping')
            
            logger.info(f"Successfully connected to MongoDB")
            return client
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            return None
    
    def _create_indexes(self):
        """Create indexes to optimize queries."""
        try:
            # Create indexes for common query patterns
            self.deals_collection.create_index([("brand", pymongo.ASCENDING)])
            self.deals_collection.create_index([("price", pymongo.ASCENDING)])
            self.deals_collection.create_index([("discount_percent", pymongo.DESCENDING)])
            self.deals_collection.create_index([("is_profitable", pymongo.DESCENDING)])
            self.deals_collection.create_index([("created_at", pymongo.DESCENDING)])
            self.deals_collection.create_index([("source", pymongo.ASCENDING)])
            self.deals_collection.create_index([("url", pymongo.ASCENDING)], unique=True)
            
            logger.info(f"Created MongoDB indexes for optimization")
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {e}")
        
    def upload_deals(self, deals: List[Dict[str, Any]]) -> bool:
        """
        Upload deals to MongoDB.
        
        Args:
            deals: List of deal dictionaries to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not deals:
            logger.info("No deals to upload to MongoDB")
            return False
            
        if not self.client or not self.deals_collection:
            logger.error("MongoDB client not initialized")
            return False
        
        # Add timestamp to each deal
        timestamp = datetime.now()
        for deal in deals:
            deal['created_at'] = timestamp
        
        try:
            # Use bulk operations for better performance
            operations = []
            for deal in deals:
                # Use upsert to avoid duplicates based on URL
                operations.append(
                    pymongo.UpdateOne(
                        {"url": deal.get("url")},
                        {"$set": deal},
                        upsert=True
                    )
                )
            
            if operations:
                result = self.deals_collection.bulk_write(operations)
                logger.info(f"MongoDB: Inserted {result.upserted_count} new deals, updated {result.modified_count} existing deals")
                
                # Update statistics
                self._update_stats(deals)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error uploading deals to MongoDB: {e}")
            return False
    
    def _update_stats(self, deals: List[Dict[str, Any]]):
        """Update statistics collection with deal information."""
        try:
            # Get current date for statistics
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Count deals by source
            source_counts = {}
            brand_counts = {}
            profitable_count = 0
            total_discount = 0
            
            for deal in deals:
                # Count by source
                source = deal.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
                
                # Count by brand
                brand = deal.get('brand', 'unknown')
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
                
                # Count profitable deals
                if deal.get('is_profitable', False):
                    profitable_count += 1
                    
                # Sum discounts
                total_discount += deal.get('discount_percent', 0)
            
            # Calculate average discount
            avg_discount = total_discount / len(deals) if deals else 0
            
            # Update stats for today
            self.stats_collection.update_one(
                {"date": today},
                {
                    "$inc": {
                        "total_deals": len(deals),
                        "profitable_deals": profitable_count
                    },
                    "$set": {
                        "last_updated": datetime.now(),
                        "avg_discount": avg_discount
                    },
                    "$push": {
                        "sources": {"$each": [{"name": k, "count": v} for k, v in source_counts.items()]},
                        "brands": {"$each": [{"name": k, "count": v} for k, v in brand_counts.items()]}
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating MongoDB stats: {e}")
    
    def get_deals(self, 
                 limit: int = 100, 
                 min_discount: float = 0, 
                 brand: Optional[str] = None,
                 profitable_only: bool = False,
                 sort_by: str = "discount_percent") -> List[Dict[str, Any]]:
        """
        Get deals from MongoDB with filtering options.
        
        Args:
            limit: Maximum number of deals to return
            min_discount: Minimum discount percentage
            brand: Filter by brand name
            profitable_only: Only return profitable deals
            sort_by: Field to sort by (discount_percent, price, created_at)
            
        Returns:
            List[Dict[str, Any]]: List of deals
        """
        if not self.client or not self.deals_collection:
            logger.error("MongoDB client not initialized")
            return []
            
        try:
            # Build query
            query = {"discount_percent": {"$gte": min_discount}}
            
            if brand:
                query["brand"] = {"$regex": brand, "$options": "i"}  # Case-insensitive search
                
            if profitable_only:
                query["is_profitable"] = True
            
            # Determine sort order
            sort_order = [("created_at", pymongo.DESCENDING)]  # Default secondary sort
            if sort_by == "discount_percent":
                sort_order = [("discount_percent", pymongo.DESCENDING), ("created_at", pymongo.DESCENDING)]
            elif sort_by == "price":
                sort_order = [("price", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)]
            elif sort_by == "profit_amount":
                sort_order = [("profit_amount", pymongo.DESCENDING), ("created_at", pymongo.DESCENDING)]
            
            # Execute query
            deals = list(self.deals_collection.find(query).sort(sort_order).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for deal in deals:
                if '_id' in deal:
                    deal['_id'] = str(deal['_id'])
                if 'created_at' in deal and isinstance(deal['created_at'], datetime):
                    deal['created_at'] = deal['created_at'].isoformat()
            
            return deals
            
        except Exception as e:
            logger.error(f"Error retrieving deals from MongoDB: {e}")
            return []
    
    def export_to_json(self, filename: str = "deals_export.json", limit: int = 1000):
        """
        Export deals to a JSON file.
        
        Args:
            filename: Output JSON filename
            limit: Maximum number of deals to export
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client or not self.deals_collection:
            logger.error("MongoDB client not initialized")
            return False
            
        try:
            # Get the most recent deals
            deals = list(self.deals_collection.find().sort("created_at", pymongo.DESCENDING).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for deal in deals:
                if '_id' in deal:
                    deal['_id'] = str(deal['_id'])
                if 'created_at' in deal and isinstance(deal['created_at'], datetime):
                    deal['created_at'] = deal['created_at'].isoformat()
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(deals, f, indent=4)
                
            logger.info(f"Exported {len(deals)} deals to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting deals to JSON: {e}")
            return False
    
    def get_deal_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics about deals over the specified period.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict[str, Any]: Statistics object
        """
        if not self.client or not self.stats_collection:
            logger.error("MongoDB client not initialized")
            return {}
            
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = start_date.replace(day=start_date.day - days + 1)
            
            # Query stats within date range
            stats = list(self.stats_collection.find({
                "date": {
                    "$gte": start_date.strftime('%Y-%m-%d'),
                    "$lte": end_date.strftime('%Y-%m-%d')
                }
            }).sort("date", pymongo.ASCENDING))
            
            # Prepare summary
            summary = {
                "period": f"{days} days",
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "total_deals": sum(stat.get('total_deals', 0) for stat in stats),
                "profitable_deals": sum(stat.get('profitable_deals', 0) for stat in stats),
                "daily_stats": stats,
                "top_sources": [],
                "top_brands": []
            }
            
            # Calculate profit percentage
            if summary["total_deals"] > 0:
                summary["profit_rate"] = (summary["profitable_deals"] / summary["total_deals"]) * 100
            else:
                summary["profit_rate"] = 0
                
            # Calculate top sources and brands
            sources = {}
            brands = {}
            
            for stat in stats:
                for source_entry in stat.get('sources', []):
                    source_name = source_entry.get('name')
                    source_count = source_entry.get('count', 0)
                    sources[source_name] = sources.get(source_name, 0) + source_count
                    
                for brand_entry in stat.get('brands', []):
                    brand_name = brand_entry.get('name')
                    brand_count = brand_entry.get('count', 0)
                    brands[brand_name] = brands.get(brand_name, 0) + brand_count
            
            # Sort and get top entries
            summary["top_sources"] = sorted(
                [{"name": k, "count": v} for k, v in sources.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
            
            summary["top_brands"] = sorted(
                [{"name": k, "count": v} for k, v in brands.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error retrieving deal stats from MongoDB: {e}")
            return {}
    
    def continue_to_iterate(self, last_iteration_deals, current_deals):
        """
        Determine whether to continue iterating through sites based on new deal discovery.
        
        Args:
            last_iteration_deals: Deals found in the previous iteration
            current_deals: Deals found in the current iteration
            
        Returns:
            bool: True if should continue iterating, False otherwise
        """
        if not last_iteration_deals:
            # First iteration, always continue if we found deals
            return len(current_deals) > 0
            
        # Check if we found new deals that weren't in the last iteration
        current_urls = {deal.get('url') for deal in current_deals}
        last_urls = {deal.get('url') for deal in last_iteration_deals}
        
        # Find URLs that are in current but not in last
        new_urls = current_urls - last_urls
        
        logger.info(f"Found {len(new_urls)} new deals in this iteration")
        
        # Continue if we found profitable new deals
        profitable_new_deals = 0
        for deal in current_deals:
            if deal.get('url') in new_urls and deal.get('is_profitable', False):
                profitable_new_deals += 1
        
        # Continue if we have at least 2 profitable new deals or at least 15% new deals
        if profitable_new_deals >= 2:
            logger.info(f"Found {profitable_new_deals} profitable new deals, continuing iteration")
            return True
            
        # Or if we have a significant percentage of new deals
        if len(current_deals) > 0 and len(new_urls) / len(current_deals) >= 0.15:
            logger.info(f"Found significant percentage of new deals ({len(new_urls) / len(current_deals):.1%}), continuing iteration")
            return True
            
        logger.info("Not enough new or profitable deals found, stopping iteration")
        return False
