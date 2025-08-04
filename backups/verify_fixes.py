"""
Fixes for Undefeated scraper and WebDriver issues.
This script contains all fixes for the reported issues.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("darkbot_fixes.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DarkbotFixes")

def verify_webdriver_installation():
    """Verify that WebDriver is properly installed."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("Selenium and WebDriver Manager are installed.")
        
        # Try to get the ChromeDriver path
        driver_path = ChromeDriverManager().install()
        print(f"ChromeDriver installed at: {driver_path}")
        
        # Verify the path
        if os.path.isfile(driver_path):
            print(f"ChromeDriver exists at the path: {driver_path}")
            if "THIRD_PARTY_NOTICES" in driver_path:
                print(f"WARNING: ChromeDriverManager returned a NOTICES file instead of the executable: {driver_path}")
                
                # Look for the actual chromedriver in the parent directory
                parent_dir = os.path.dirname(driver_path)
                for filename in os.listdir(parent_dir):
                    candidate_path = os.path.join(parent_dir, filename)
                    if "chromedriver" in filename.lower() and os.path.isfile(candidate_path) and os.access(candidate_path, os.X_OK):
                        print(f"Found actual ChromeDriver at: {candidate_path}")
                        driver_path = candidate_path
                        break
        else:
            print(f"ERROR: ChromeDriver does not exist at the path: {driver_path}")
            return False
        
        # Try to initialize the WebDriver
        print("Initializing Chrome WebDriver...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("Chrome WebDriver initialized successfully!")
            driver.quit()
            return True
        except Exception as e:
            print(f"Failed to initialize Chrome WebDriver: {e}")
            return False
            
    except ImportError as e:
        print(f"Missing required packages: {e}")
        return False
    except Exception as e:
        print(f"Error verifying WebDriver installation: {e}")
        return False

def verify_undefeated_scraper():
    """Verify that the Undefeated scraper is properly configured."""
    try:
        # Check if the Undefeated scraper module exists
        from scrapers.undefeated import UndefeatedScraper
        print("Undefeated scraper module exists.")
        
        # Check if the site config exists
        from config.sites import SNEAKER_SITES
        if 'undefeated' in SNEAKER_SITES:
            print("Undefeated site config exists.")
            print(f"Site config: {SNEAKER_SITES['undefeated']}")
            return True
        else:
            print("ERROR: Undefeated site config does not exist in SNEAKER_SITES.")
            return False
            
    except ImportError as e:
        print(f"Missing required modules: {e}")
        return False
    except Exception as e:
        print(f"Error verifying Undefeated scraper: {e}")
        return False

def verify_scraper_factory():
    """Verify that the scraper factory is properly configured."""
    try:
        # Check if the scraper factory has the Undefeated scraper
        from scrapers.factory import get_scraper_for_site
        from config.sites import SNEAKER_SITES
        
        if 'undefeated' not in SNEAKER_SITES:
            print("ERROR: Undefeated site config does not exist.")
            return False
            
        # Try to get the Undefeated scraper from the factory
        scraper = get_scraper_for_site('undefeated', SNEAKER_SITES['undefeated'])
        
        if scraper:
            print(f"Scraper factory returned a scraper for Undefeated: {type(scraper).__name__}")
            return True
        else:
            print("ERROR: Scraper factory did not return a scraper for Undefeated.")
            return False
            
    except ImportError as e:
        print(f"Missing required modules: {e}")
        return False
    except Exception as e:
        print(f"Error verifying scraper factory: {e}")
        return False

def verify_site_configuration():
    """Verify that the site configuration is properly set up."""
    try:
        from config.sites import SNEAKER_SITES, DEFAULT_SITES
        
        # Check if Undefeated is in the site configuration
        if 'undefeated' in SNEAKER_SITES:
            print("Undefeated is in SNEAKER_SITES.")
            
            # Check if Undefeated has the required configuration
            site_config = SNEAKER_SITES['undefeated']
            if 'url' in site_config and 'sale_url' in site_config and 'rate_limit' in site_config:
                print("Undefeated site config has all required fields.")
            else:
                print("WARNING: Undefeated site config is missing required fields.")
                
            # Check if Undefeated is in DEFAULT_SITES
            if 'undefeated' in DEFAULT_SITES:
                print("Undefeated is in DEFAULT_SITES.")
            else:
                print("WARNING: Undefeated is not in DEFAULT_SITES.")
            
            return True
        else:
            print("ERROR: Undefeated is not in SNEAKER_SITES.")
            return False
            
    except ImportError as e:
        print(f"Missing required modules: {e}")
        return False
    except Exception as e:
        print(f"Error verifying site configuration: {e}")
        return False

def run_all_verifications():
    """Run all verifications and print a summary."""
    print("=" * 50)
    print(f"Running Darkbot verifications - {datetime.now()}")
    print("=" * 50)
    
    print("\nWebDriver Installation:")
    webdriver_result = verify_webdriver_installation()
    
    print("\nUndefeated Scraper:")
    undefeated_result = verify_undefeated_scraper()
    
    print("\nScraper Factory:")
    factory_result = verify_scraper_factory()
    
    print("\nSite Configuration:")
    config_result = verify_site_configuration()
    
    results = {
        "WebDriver Installation": webdriver_result,
        "Undefeated Scraper": undefeated_result,
        "Scraper Factory": factory_result,
        "Site Configuration": config_result
    }
    
    print("\nVerification Results:")
    all_passed = True
    for name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"  {name}: {status}")
        all_passed = all_passed and result
    
    print("\nOverall Status:")
    if all_passed:
        print("All verifications PASSED!")
        print("The system should be working correctly.")
    else:
        print("Some verifications FAILED!")
        print("Please check the log for details.")
    
    print("=" * 50)
    return all_passed

if __name__ == "__main__":
    run_all_verifications()
