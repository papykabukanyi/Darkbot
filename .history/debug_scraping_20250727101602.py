#!/usr/bin/env python3
"""
Simple test script to debug the scraping bot.
"""

import sys
import logging

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DEBUG")

def test_imports():
    """Test that all imports work."""
    try:
        print("Testing imports...")
        
        print("1. Testing config imports...")
        from config import SNEAKER_SITES, DEFAULT_SITES
        print(f"   ✓ Found {len(SNEAKER_SITES)} sites in config")
        print(f"   ✓ Default sites: {DEFAULT_SITES}")
        
        print("2. Testing scraper factory...")
        from scrapers.factory import get_scraper_for_site
        print("   ✓ Factory imported successfully")
        
        print("3. Testing MongoDB storage...")
        from storage.mongodb import MongoDBStorage
        print("   ✓ MongoDB storage imported successfully")
        
        print("4. Testing base scraper...")
        from scrapers.base_scraper import BaseSneakerScraper
        print("   ✓ Base scraper imported successfully")
        
        print("5. Testing sneakers scraper...")
        from scrapers.sneakers import SneakersScraper
        print("   ✓ Sneakers scraper imported successfully")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scraper_creation():
    """Test creating a scraper instance."""
    try:
        print("\nTesting scraper creation...")
        
        from config import SNEAKER_SITES
        from scrapers.factory import get_scraper_for_site
        
        site_name = "sneakers"
        site_config = SNEAKER_SITES[site_name]
        
        print(f"   Site config: {site_config}")
        
        scraper_class = get_scraper_for_site(site_name, site_config)
        print(f"   ✓ Got scraper class: {scraper_class}")
        
        # Test context manager
        print("   Testing context manager...")
        with scraper_class as scraper:
            print(f"   ✓ Context manager works, scraper: {scraper}")
            print(f"   ✓ Scraper name: {scraper.name}")
            print(f"   ✓ Base URL: {scraper.base_url}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Scraper creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_scraping():
    """Test basic scraping functionality."""
    try:
        print("\nTesting basic scraping...")
        
        from config import SNEAKER_SITES
        from scrapers.factory import get_scraper_for_site
        
        site_name = "sneakers"
        site_config = SNEAKER_SITES[site_name]
        
        scraper_class = get_scraper_for_site(site_name, site_config)
        
        with scraper_class as scraper:
            print("   Attempting to scrape...")
            deals = scraper.scrape()
            print(f"   ✓ Scraping completed, found {len(deals)} deals")
            
            if deals:
                print(f"   First deal: {deals[0]}")
            else:
                print("   No deals found (this might be normal)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🔍 DEBUGGING SNEAKER BOT SCRAPING ISSUES")
    print("=" * 50)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Imports failed - cannot continue")
        return False
    
    # Test 2: Scraper creation
    if not test_scraper_creation():
        print("\n❌ Scraper creation failed - cannot continue")
        return False
    
    # Test 3: Basic scraping
    if not test_basic_scraping():
        print("\n❌ Basic scraping failed")
        return False
    
    print("\n✅ All tests passed! Bot should be working.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
