"""
Display recent deals from storage.
"""

import argparse
import logging
import pandas as pd
import sys
import os
from typing import Dict, List, Any
import json
from tabulate import tabulate

from config import CSV_FILENAME, MONGODB_ENABLED, MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_COLLECTION
from storage import DealStorage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DealViewer")

def print_deals(deals: List[Dict[str, Any]], format_type: str = 'table') -> None:
    """
    Print deals in the specified format.
    
    Args:
        deals: List of deal dictionaries
        format_type: Format to print ('table', 'json', or 'csv')
    """
    if not deals:
        print("No deals found.")
        return
    
    # Select columns to display
    columns = ['brand', 'title', 'price', 'original_price', 'discount_percent', 'profit_percentage', 'site']
    
    if format_type == 'json':
        print(json.dumps(deals, indent=2))
    elif format_type == 'csv':
        df = pd.DataFrame(deals)
        print(df.to_csv(index=False))
    else:  # Default to table
        # Create a list of lists with selected columns
        headers = ['Brand', 'Title', 'Price', 'MSRP', 'Discount %', 'Profit %', 'Source']
        
        # Prepare rows
        rows = []
        for deal in deals:
            row = [
                deal.get('brand', 'Unknown'),
                deal.get('title', 'Unknown')[:50] + ('...' if len(deal.get('title', '')) > 50 else ''),
                f"${deal.get('price', 0):.2f}",
                f"${deal.get('original_price', 0):.2f}",
                f"{deal.get('discount_percent', 0):.1f}%",
                f"{deal.get('profit_percentage', 0):.1f}%" if 'profit_percentage' in deal else 'N/A',
                deal.get('site', deal.get('source', 'Unknown')),
            ]
            rows.append(row)
        
        print(tabulate(rows, headers=headers, tablefmt='pretty'))
        print(f"\nTotal deals: {len(deals)}")

def get_deals_from_mongodb() -> List[Dict[str, Any]]:
    """
    Get deals from MongoDB storage.
    
    Returns:
        List of deal dictionaries
    """
    try:
        # Try importing directly first
        try:
            from storage.mongodb import MongoDBStorage
        except ImportError:
            # Fall back to top-level storage module
            from storage import MongoDBStorage
            
        mongo_storage = MongoDBStorage(
            connection_string=MONGODB_CONNECTION_STRING,
            database_name=MONGODB_DATABASE,
            collection_name=MONGODB_COLLECTION
        )
        
        # Get most recent deals (limit to 50)
        return mongo_storage.get_recent_deals(limit=50)
    except ImportError:
        logger.error("MongoDB module not found")
        return []
    except Exception as e:
        logger.error(f"Error accessing MongoDB: {e}")
        return []

def get_deals_from_csv(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get deals from CSV storage.
    
    Args:
        limit: Maximum number of deals to return
    
    Returns:
        List of deal dictionaries
    """
    try:
        if not os.path.exists(CSV_FILENAME):
            logger.error(f"CSV file {CSV_FILENAME} not found")
            return []
        
        df = pd.read_csv(CSV_FILENAME)
        if df.empty:
            return []
        
        # Sort by timestamp if available, otherwise use the file's order
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)
        
        # Return most recent deals
        return df.head(limit).to_dict('records')
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return []

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='View recent sneaker deals')
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                        help='Output format (default: table)')
    parser.add_argument('--source', choices=['csv', 'mongodb'], default='csv',
                        help='Data source (default: csv)')
    parser.add_argument('--limit', type=int, default=20,
                        help='Maximum number of deals to show (default: 20)')
    parser.add_argument('--min-discount', type=float, default=0,
                        help='Minimum discount percentage (default: 0)')
    parser.add_argument('--brand', type=str, help='Filter by brand')
    args = parser.parse_args()
    
    # Get deals from the specified source
    if args.source == 'mongodb' and MONGODB_ENABLED:
        deals = get_deals_from_mongodb()
    else:
        deals = get_deals_from_csv(args.limit)
    
    # Apply filters
    if args.min_discount > 0:
        deals = [d for d in deals if d.get('discount_percent', 0) >= args.min_discount]
    
    if args.brand:
        deals = [d for d in deals if args.brand.lower() in d.get('brand', '').lower()]
    
    # Limit results
    deals = deals[:args.limit]
    
    # Print deals
    print_deals(deals, args.format)

if __name__ == "__main__":
    main()
