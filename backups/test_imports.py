"""
Quick test script to verify imports.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Try importing from both config modules
try:
    print("Trying to import from config package...")
    from config import USE_PROXY, PROXY_CONFIG
    print(f"SUCCESS: USE_PROXY = {USE_PROXY}")
    print(f"PROXY_CONFIG available: {bool(PROXY_CONFIG)}")
except ImportError as e:
    print(f"ERROR importing from config package: {e}")

try:
    print("\nTrying to import from scrapers.base_scraper...")
    from scrapers.base_scraper import USE_PROXY, PROXY_CONFIG
    print(f"SUCCESS: USE_PROXY = {USE_PROXY}")
    print(f"PROXY_CONFIG available: {bool(PROXY_CONFIG)}")
except ImportError as e:
    print(f"ERROR importing from base_scraper: {e}")

try:
    print("\nTrying to instantiate BaseSneakerScraper...")
    from scrapers.base_scraper import BaseSneakerScraper
    proxy_manager = BaseSneakerScraper.get_proxy_manager()
    print(f"SUCCESS: proxy_manager is {'available' if proxy_manager else 'None'}")
except Exception as e:
    print(f"ERROR instantiating BaseSneakerScraper: {e}")

print("\nTest completed!")
