"""
Simple database module for storing sneaker releases.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import os

logger = logging.getLogger("SneakerBot")

class SneakerDatabase:
    """Simple SQLite database for storing sneaker releases."""
    
    def __init__(self, db_path: str = "sneaker_releases.db"):
        """Initialize the database."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create releases table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS releases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        brand TEXT,
                        url TEXT,
                        image_url TEXT,
                        release_date TEXT,
                        retail_price INTEGER,
                        market_price INTEGER,
                        profit_potential INTEGER,
                        source TEXT NOT NULL,
                        status TEXT DEFAULT 'new',
                        scraped_at TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(title, source)
                    )
                ''')
                
                # Create index for faster searches
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_brand ON releases(brand)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON releases(source)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON releases(status)')
                
                conn.commit()
                logger.info(f"Database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def save_releases(self, releases: List[Dict[str, Any]]) -> int:
        """
        Save releases to the database.
        
        Args:
            releases: List of release dictionaries
            
        Returns:
            Number of new releases saved
        """
        if not releases:
            return 0
            
        saved_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for release in releases:
                    try:
                        # Extract values with defaults
                        title = release.get('title', 'Unknown')
                        brand = release.get('brand', 'Unknown')
                        url = release.get('url', '')
                        image_url = release.get('image_url', '')
                        release_date = release.get('release_date', '')
                        retail_price = release.get('retail_price')
                        market_price = release.get('market_price')
                        profit_potential = release.get('profit_potential')
                        source = release.get('source', 'Unknown')
                        status = release.get('status', 'new')
                        scraped_at = release.get('timestamp', datetime.now().isoformat())
                        
                        # Insert or ignore (duplicate check by title and source)
                        cursor.execute('''
                            INSERT OR IGNORE INTO releases 
                            (title, brand, url, image_url, release_date, retail_price, 
                             market_price, profit_potential, source, status, scraped_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (title, brand, url, image_url, release_date, retail_price,
                              market_price, profit_potential, source, status, scraped_at))
                        
                        if cursor.rowcount > 0:
                            saved_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error saving release {release.get('title', 'Unknown')}: {e}")
                        continue
                
                conn.commit()
                logger.info(f"Saved {saved_count} new releases to database")
                
        except Exception as e:
            logger.error(f"Error saving releases to database: {e}")
            
        return saved_count
    
    def get_recent_releases(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent releases from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM releases 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving releases from database: {e}")
            return []
    
    def get_profitable_releases(self, min_profit: int = 50) -> List[Dict[str, Any]]:
        """Get releases with profit potential above the threshold."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM releases 
                    WHERE profit_potential >= ? 
                    ORDER BY profit_potential DESC
                ''', (min_profit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error retrieving profitable releases: {e}")
            return []
    
    def update_market_data(self, title: str, source: str, market_price: int, profit_potential: int):
        """Update market price and profit data for a release."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE releases 
                    SET market_price = ?, profit_potential = ?
                    WHERE title = ? AND source = ?
                ''', (market_price, profit_potential, title, source))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating market data for {title}: {e}")
