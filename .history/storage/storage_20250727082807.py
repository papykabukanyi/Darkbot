"""
Storage module for sneaker deals.
"""

import csv
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DealStorage:
    """Class for storing and retrieving deals."""
    
    def __init__(self, csv_filename=None, db_enabled=False, db_path=None):
        """
        Initialize the deal storage.
        
        Args:
            csv_filename: Name of the CSV file to save deals to
            db_enabled: Whether to save deals to a database
            db_path: Path to the database file
        """
        self.csv_filename = csv_filename
        self.db_enabled = db_enabled
        self.db_path = db_path
        
        if self.db_enabled:
            self._init_db()
    
    def _init_db(self):
        """
        Initialize the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create the deals table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    url TEXT,
                    price REAL,
                    original_price REAL,
                    discount_percent REAL,
                    brand TEXT,
                    source TEXT,
                    created_at TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def save_deals(self, deals: List[Dict[str, Any]]):
        """
        Save deals to storage.
        
        Args:
            deals: List of deal dictionaries to save
        """
        if not deals:
            logger.info("No deals to save")
            return
            
        if self.csv_filename:
            self._save_to_csv(deals)
            
        if self.db_enabled:
            self._save_to_db(deals)
    
    def _save_to_csv(self, deals: List[Dict[str, Any]]):
        """
        Save deals to a CSV file.
        
        Args:
            deals: List of deal dictionaries to save
        """
        try:
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'title', 'brand', 'price', 'original_price', 
                    'discount_percent', 'source', 'url'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for deal in deals:
                    writer.writerow(deal)
                    
            logger.info(f"Saved {len(deals)} deals to {self.csv_filename}")
        except Exception as e:
            logger.error(f"Error saving deals to CSV: {e}")
    
    def _save_to_db(self, deals: List[Dict[str, Any]]):
        """
        Save deals to the database.
        
        Args:
            deals: List of deal dictionaries to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            for deal in deals:
                cursor.execute("""
                    INSERT INTO deals 
                    (title, url, price, original_price, discount_percent, brand, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    deal.get('title', 'Unknown'),
                    deal.get('url', ''),
                    deal.get('price', 0),
                    deal.get('original_price', 0),
                    deal.get('discount_percent', 0),
                    deal.get('brand', 'Unknown'),
                    deal.get('source', 'Unknown'),
                    timestamp
                ))
                
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(deals)} deals to database")
        except Exception as e:
            logger.error(f"Error saving deals to database: {e}")
    
    def export_to_json(self, filename="deals_export.json"):
        """
        Export deals to a JSON file.
        
        Args:
            filename: Name of the JSON file
        """
        if not self.db_enabled:
            logger.warning("Database not enabled, cannot export to JSON")
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM deals ORDER BY created_at DESC, discount_percent DESC")
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            deals = [{key: row[key] for key in row.keys()} for row in rows]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(deals, f, indent=4)
                
            logger.info(f"Exported {len(deals)} deals to {filename}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error exporting deals to JSON: {e}")
            
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
        new_deal_count = 0
        current_urls = {deal.get('url') for deal in current_deals}
        last_urls = {deal.get('url') for deal in last_iteration_deals}
        
        # Find URLs that are in current but not in last
        new_urls = current_urls - last_urls
        
        logger.info(f"Found {len(new_urls)} new deals in this iteration")
        
        # Continue if we found at least 3 new deals or at least 10% of the total
        if len(new_urls) >= 3 or (len(current_deals) > 0 and len(new_urls) / len(current_deals) >= 0.1):
            return True
            
        return False
