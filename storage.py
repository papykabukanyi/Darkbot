"""
Data storage and analysis functions for sneaker deals.
"""

import os
import csv
import json
import sqlite3
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional

import pandas as pd

from config import CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH

logger = logging.getLogger("SneakerBot")

class DealStorage:
    """Class for storing and analyzing sneaker deals."""
    
    def __init__(self, csv_filename: str = CSV_FILENAME, db_enabled: bool = DATABASE_ENABLED, 
                 db_path: str = DATABASE_PATH):
        """
        Initialize the storage system.
        
        Args:
            csv_filename: Name of the CSV file to save data to
            db_enabled: Whether to use SQLite database storage
            db_path: Path to the SQLite database file
        """
        self.csv_filename = csv_filename
        self.db_enabled = db_enabled
        self.db_path = db_path
        
        # Create database if enabled
        if self.db_enabled:
            self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Create the database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                original_price REAL NOT NULL,
                url TEXT NOT NULL UNIQUE,
                description TEXT,
                brand TEXT,
                source TEXT NOT NULL,
                on_sale BOOLEAN NOT NULL,
                discount_percent INTEGER,
                timestamp DATETIME NOT NULL,
                image_url TEXT
            )
            ''')
            
            # Create sizes table with foreign key to products
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sizes (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                size TEXT NOT NULL,
                available BOOLEAN NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.db_enabled = False
    
    def save_deals(self, deals: List[Dict[str, Any]]) -> None:
        """
        Save the deals to storage.
        
        Args:
            deals: List of product dictionaries to save
        """
        if not deals:
            logger.warning("No deals to save")
            return
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for deal in deals:
            deal["timestamp"] = timestamp
        
        # Save to CSV
        self._save_to_csv(deals)
        
        # Save to database if enabled
        if self.db_enabled:
            self._save_to_db(deals)
    
    def _save_to_csv(self, deals: List[Dict[str, Any]]) -> None:
        """Save deals to CSV file."""
        try:
            # Flatten the dictionary for CSV storage
            flattened_deals = []
            for deal in deals:
                flat_deal = {k: v for k, v in deal.items() if not isinstance(v, (list, dict))}
                
                # Handle sizes separately
                if "sizes" in deal:
                    available_sizes = [size["size"] for size in deal["sizes"] if size["available"]]
                    flat_deal["available_sizes"] = ", ".join(available_sizes)
                
                # Handle images separately
                if "images" in deal and deal["images"]:
                    flat_deal["image_url"] = deal["images"][0]
                
                flattened_deals.append(flat_deal)
            
            # Get all possible fields
            all_fields = set()
            for deal in flattened_deals:
                all_fields.update(deal.keys())
            
            # Write to CSV
            file_exists = os.path.isfile(self.csv_filename)
            
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted(all_fields))
                
                # Write header only if file is new
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(flattened_deals)
            
            logger.info(f"Saved {len(deals)} deals to {self.csv_filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def _save_to_db(self, deals: List[Dict[str, Any]]) -> None:
        """Save deals to SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for deal in deals:
                try:
                    # Extract the basic product info
                    product_data = {
                        "title": deal.get("title", "Unknown"),
                        "price": deal.get("price", 0.0),
                        "original_price": deal.get("original_price", 0.0),
                        "url": deal.get("url", ""),
                        "description": deal.get("description", ""),
                        "brand": deal.get("brand", "Unknown"),
                        "source": deal.get("source", "Unknown"),
                        "on_sale": deal.get("on_sale", False),
                        "discount_percent": deal.get("discount_percent", 0),
                        "timestamp": deal.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        "image_url": deal.get("images", [""])[0] if "images" in deal and deal["images"] else ""
                    }
                    
                    # Insert product, ignore if URL already exists
                    cursor.execute('''
                    INSERT OR IGNORE INTO products 
                    (title, price, original_price, url, description, brand, source, on_sale, discount_percent, timestamp, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_data["title"],
                        product_data["price"],
                        product_data["original_price"],
                        product_data["url"],
                        product_data["description"],
                        product_data["brand"],
                        product_data["source"],
                        product_data["on_sale"],
                        product_data["discount_percent"],
                        product_data["timestamp"],
                        product_data["image_url"]
                    ))
                    
                    # Get the product ID
                    product_id = cursor.lastrowid
                    if not product_id:
                        # If the product already existed, get its ID
                        cursor.execute("SELECT id FROM products WHERE url = ?", (product_data["url"],))
                        product_id = cursor.fetchone()[0]
                    
                    # Insert sizes if available
                    if "sizes" in deal and product_id:
                        for size_info in deal["sizes"]:
                            cursor.execute('''
                            INSERT INTO sizes (product_id, size, available)
                            VALUES (?, ?, ?)
                            ''', (
                                product_id,
                                size_info["size"],
                                size_info["available"]
                            ))
                
                except Exception as e:
                    logger.error(f"Error saving product to database: {e}")
                    continue
            
            conn.commit()
            conn.close()
            logger.info(f"Saved {len(deals)} deals to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def get_best_deals(self, min_discount: int = 30, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get the best deals based on discount percentage.
        
        Args:
            min_discount: Minimum discount percentage
            max_results: Maximum number of results to return
            
        Returns:
            List of the best deals
        """
        try:
            if os.path.exists(self.csv_filename):
                df = pd.read_csv(self.csv_filename)
                
                # Filter for products on sale with minimum discount
                if "discount_percent" in df.columns:
                    df = df[df["discount_percent"] >= min_discount]
                elif "price" in df.columns and "original_price" in df.columns:
                    df["discount_percent"] = ((df["original_price"] - df["price"]) / df["original_price"]) * 100
                    df = df[df["discount_percent"] >= min_discount]
                
                # Sort by discount percentage (descending)
                if "discount_percent" in df.columns:
                    df = df.sort_values("discount_percent", ascending=False)
                
                # Return top results as dictionaries
                return df.head(max_results).to_dict("records")
            else:
                logger.warning(f"CSV file {self.csv_filename} not found")
                return []
        except Exception as e:
            logger.error(f"Error getting best deals: {e}")
            return []
    
    def get_deals_by_brand(self, brand: str) -> List[Dict[str, Any]]:
        """
        Get deals for a specific brand.
        
        Args:
            brand: The brand name to filter by
            
        Returns:
            List of deals for the specified brand
        """
        try:
            if os.path.exists(self.csv_filename):
                df = pd.read_csv(self.csv_filename)
                
                # Filter for the specified brand (case-insensitive)
                if "brand" in df.columns:
                    df = df[df["brand"].str.lower() == brand.lower()]
                    return df.to_dict("records")
                else:
                    logger.warning("Brand column not found in CSV file")
                    return []
            else:
                logger.warning(f"CSV file {self.csv_filename} not found")
                return []
        except Exception as e:
            logger.error(f"Error getting deals by brand: {e}")
            return []
    
    def export_to_json(self, filename: str = "deals_export.json") -> bool:
        """
        Export all deals to a JSON file.
        
        Args:
            filename: Name of the JSON file to export to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.csv_filename):
                df = pd.read_csv(self.csv_filename)
                deals = df.to_dict("records")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(deals, f, indent=2)
                
                logger.info(f"Exported {len(deals)} deals to {filename}")
                return True
            else:
                logger.warning(f"CSV file {self.csv_filename} not found")
                return False
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return False
