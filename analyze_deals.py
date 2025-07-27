"""
Enhanced deal analyzer script that uses real-time market price data.
"""

import argparse
import json
import logging
import os
import sys
import pandas as pd
from typing import Dict, List, Any, Optional
from tabulate import tabulate

from utils.price_comparison import PriceComparer
from config import BRANDS_OF_INTEREST, MIN_DISCOUNT_PERCENT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DealAnalyzer")

def analyze_deals_file(input_file: str, output_file: Optional[str] = None, 
                      min_profit: float = 15.0, format_type: str = 'table'):
    """
    Analyze deals in a CSV file using real-time market data.
    
    Args:
        input_file: Path to input CSV file with deals
        output_file: Path to output file (optional)
        min_profit: Minimum profit percentage to consider
        format_type: Output format (table, json, or csv)
    """
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found")
        return
    
    # Read deals from CSV
    try:
        df = pd.read_csv(input_file)
        deals = df.to_dict('records')
        logger.info(f"Read {len(deals)} deals from {input_file}")
    except Exception as e:
        logger.error(f"Error reading deals from {input_file}: {e}")
        return
    
    # Initialize price comparer
    price_comparer = PriceComparer()
    
    # Analyze each deal
    analyzed_deals = []
    for deal in deals:
        # Calculate profit metrics
        profit_amount, profit_percentage = price_comparer.calculate_profit(deal)
        
        # Add profit metrics to deal
        deal['profit_amount'] = round(profit_amount, 2)
        deal['profit_percentage'] = round(profit_percentage, 1)
        deal['is_profitable'] = profit_percentage >= min_profit
        
        # Only include profitable deals in results
        if deal['is_profitable']:
            analyzed_deals.append(deal)
    
    logger.info(f"Found {len(analyzed_deals)} profitable deals with {min_profit}%+ profit potential")
    
    # Sort by profit percentage (descending)
    analyzed_deals.sort(key=lambda x: x.get('profit_percentage', 0), reverse=True)
    
    # Output results
    if output_file:
        if format_type == 'json':
            with open(output_file, 'w') as f:
                json.dump(analyzed_deals, f, indent=2)
        elif format_type == 'csv':
            pd.DataFrame(analyzed_deals).to_csv(output_file, index=False)
        else:
            with open(output_file, 'w') as f:
                headers = ['Brand', 'Title', 'Price', 'Market', 'Profit $', 'Profit %', 'Source']
                rows = [
                    [
                        deal.get('brand', 'Unknown'),
                        deal.get('title', 'Unknown')[:50] + ('...' if len(deal.get('title', '')) > 50 else ''),
                        f"${deal.get('price', 0):.2f}",
                        f"${deal.get('market_price', 0):.2f}",
                        f"${deal.get('profit_amount', 0):.2f}",
                        f"{deal.get('profit_percentage', 0):.1f}%",
                        deal.get('site', deal.get('source', 'Unknown')),
                    ]
                    for deal in analyzed_deals
                ]
                f.write(tabulate(rows, headers=headers, tablefmt='grid'))
        
        logger.info(f"Results saved to {output_file}")
    else:
        # Print to console
        if format_type == 'json':
            print(json.dumps(analyzed_deals, indent=2))
        elif format_type == 'csv':
            print(pd.DataFrame(analyzed_deals).to_csv(index=False))
        else:
            headers = ['Brand', 'Title', 'Price', 'Market', 'Profit $', 'Profit %', 'Source']
            rows = [
                [
                    deal.get('brand', 'Unknown'),
                    deal.get('title', 'Unknown')[:50] + ('...' if len(deal.get('title', '')) > 50 else ''),
                    f"${deal.get('price', 0):.2f}",
                    f"${deal.get('market_price', 0):.2f}",
                    f"${deal.get('profit_amount', 0):.2f}",
                    f"{deal.get('profit_percentage', 0):.1f}%",
                    deal.get('site', deal.get('source', 'Unknown')),
                ]
                for deal in analyzed_deals
            ]
            print(tabulate(rows, headers=headers, tablefmt='pretty'))

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Analyze sneaker deals for profit potential')
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='Input CSV file with deals')
    parser.add_argument('--output', '-o', type=str,
                        help='Output file for results (optional)')
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table',
                        help='Output format (default: table)')
    parser.add_argument('--min-profit', type=float, default=15.0,
                        help='Minimum profit percentage (default: 15.0)')
    args = parser.parse_args()
    
    analyze_deals_file(
        input_file=args.input,
        output_file=args.output,
        min_profit=args.min_profit,
        format_type=args.format
    )

if __name__ == "__main__":
    main()
