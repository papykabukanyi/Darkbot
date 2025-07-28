"""
Test script to verify WebDriver initialization is working properly.
"""

import sys
import os
import logging
import colorama
from selenium import webdriver

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WebDriverTest")

# Add parent directory to path so we can import from the main application
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from scrapers.base_scraper import setup_selenium_driver

def test_webdriver_initialization():
    """Test that WebDriver can be properly initialized."""
    print("=" * 50)
    print("Testing WebDriver initialization")
    print("=" * 50)
    print()
    
    # Print system information
    print("System Information:")
    print(f"Operating System: {os.name} / {sys.platform}")
    print(f"Python Version: {sys.version}")
    try:
        import platform
        print(f"Platform: {platform.platform()}")
    except ImportError:
        pass
    
    # Print path information
    print("\nPath Information:")
    print(f"Current Directory: {os.getcwd()}")
    print(f"Script Location: {os.path.abspath(__file__)}")
    
    # Check Chrome binary paths
    print("\nChecking Chrome binary locations:")
    chrome_binary_locations = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/headless-chromium",
        "/chrome/chrome",
        "/usr/bin/google-chrome-stable",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    ]
    
    for location in chrome_binary_locations:
        if os.path.exists(location):
            print(f"✓ Found Chrome binary at: {location}")
        else:
            print(f"✗ No Chrome binary at: {location}")
    
    try:
        print("\nInitializing WebDriver...")
        driver = setup_selenium_driver(headless=True)
        
        if driver:
            print(f"\n✓ SUCCESS: WebDriver initialized successfully!")
            print(f"Browser name: {driver.name}")
            print(f"Browser version: {driver.capabilities.get('browserVersion')}")
            print(f"User Agent: {driver.execute_script('return navigator.userAgent;')}")
            
            # Get driver info
            service = driver.service
            if service:
                print(f"Service URL: {service.service_url}")
                if hasattr(service, 'path'):
                    print(f"ChromeDriver Path: {service.path}")
            
            # Test loading a page
            print("\nTesting page load...")
            driver.get("https://www.example.com")
            print(f"Page title: {driver.title}")
            
            # Clean up
            print("\nClosing driver...")
            driver.quit()
            print("Driver successfully closed!")
        else:
            print("✗ FAIL: WebDriver initialization returned None!")
    
    except Exception as e:
        print(f"✗ ERROR: WebDriver initialization failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webdriver_initialization()
