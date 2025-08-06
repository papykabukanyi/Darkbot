"""
Command-line interface for StockX Price Checker
"""

import os
import sys
import argparse
import logging
import json
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/stockx_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StockXCLI")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import StockX price checker
from utils.stockx_price_checker import StockXPriceChecker

def main():
    """Main function for the CLI"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="StockX Price Checker CLI")
    parser.add_argument("--query", "-q", help="Search query (e.g., 'Nike Dunk Low Panda')")
    parser.add_argument("--sku", "-s", help="Product SKU for more accurate search")
    parser.add_argument("--retail", "-r", type=float, help="Retail price for profit calculation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", "-o", choices=["json", "text"], default="text", 
                       help="Output format (json or text)")
    parser.add_argument("--file", "-f", help="Output file path (if not specified, prints to console)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check for required arguments
    if not args.query and not args.sku:
        parser.error("Either --query or --sku must be provided")
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        # Also set the handler level
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # Initialize StockX price checker
    price_checker = StockXPriceChecker()
    
    # Print header
    print("=" * 80)
    print(f"STOCKX PRICE CHECKER")
    print("=" * 80)
    
    try:
        # Get price information
        results = price_checker.check_prices(
            args.query or args.sku,
            args.retail,
            sku=args.sku
        )
        
        # Generate a report
        report = price_checker.generate_price_comparison_report(
            args.query or args.sku,
            retail_price=args.retail,
            sku=args.sku
        )
        
        # Format output
        if args.output == "json":
            output = json.dumps(report, indent=2)
        else:
            # Text format
            output = format_text_output(report, results)
        
        # Output result
        if args.file:
            with open(args.file, "w") as f:
                f.write(output)
            print(f"Results written to {args.file}")
        else:
            print(output)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)

def format_text_output(report, results):
    """Format report as readable text"""
    output = []
    output.append(f"Product: {report['sneaker_name']}")
    if report['sku']:
        output.append(f"SKU: {report['sku']}")
    
    if report['retail_price']:
        output.append(f"Retail Price: ${report['retail_price']:.2f}")
    
    output.append("\nSTOCKX PRICE INFORMATION:")
    
    if results and results[0]['status'] == 'success':
        result = results[0]
        output.append(f"Price: ${result['price']:.2f}")
        output.append(f"URL: {result['url']}")
        
        if report['retail_price'] and result['price_difference'] is not None:
            diff = result['price_difference']
            pct = result['percentage_difference']
            profit = result['profit_potential']
            
            output.append(f"Price Difference: ${diff:.2f} ({pct:.2f}%)")
            output.append(f"Profit Potential: ${profit:.2f}")
            
            if profit > 0:
                output.append("PROFITABLE ITEM!")
            else:
                output.append("Not profitable at current market price")
    else:
        output.append("No price information found")
    
    output.append("\nTimestamp: " + report['timestamp'])
    
    return "\n".join(output)

if __name__ == "__main__":
    main()
