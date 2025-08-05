import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the StockXPriceChecker
from utils.stockx_price_checker import StockXPriceChecker

print("StockXPriceChecker imported successfully!")
print(f"Python version: {sys.version}")
