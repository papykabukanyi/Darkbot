"""
Test script to verify WebDriver initialization and save output to a file.
"""

import sys
import os
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WebDriverTest")

# Add parent directory to path so we can import from the main application
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def write_to_file(text):
    """Write text to the output file."""
    with open("webdriver_test_output.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def test_webdriver_initialization():
    """Test that WebDriver can be properly initialized."""
    write_to_file("=" * 50)
    write_to_file(f"WebDriver Test - {datetime.now()}")
    write_to_file("=" * 50)
    write_to_file("")
    
    # System information
    write_to_file("System Information:")
    write_to_file(f"Operating System: {os.name} / {sys.platform}")
    write_to_file(f"Python Version: {sys.version}")
    try:
        import platform
        write_to_file(f"Platform: {platform.platform()}")
    except ImportError:
        pass
    
    # Path information
    write_to_file("\nPath Information:")
    write_to_file(f"Current Directory: {os.getcwd()}")
    write_to_file(f"Script Location: {os.path.abspath(__file__)}")
    
    # Check for required packages
    write_to_file("\nChecking required packages:")
    required_packages = ["selenium", "webdriver_manager"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            write_to_file(f"[OK] {package} is installed")
        except ImportError:
            write_to_file(f"[FAIL] {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        write_to_file("\n⚠ Missing required packages. Please install them first:")
        write_to_file(f"pip install {' '.join(missing_packages)}")
        write_to_file("Test aborted.")
        return
    
    # Try to import the base_scraper module
    try:
        write_to_file("\nTrying to import setup_selenium_driver...")
        from scrapers.base_scraper import setup_selenium_driver
        write_to_file("[OK] Successfully imported setup_selenium_driver")
    except Exception as e:
        write_to_file(f"[FAIL] Failed to import setup_selenium_driver: {str(e)}")
        write_to_file(traceback.format_exc())
        write_to_file("Test aborted.")
        return
        
    try:
        write_to_file("\nInitializing WebDriver...")
        driver = setup_selenium_driver(headless=True)
        
        if driver:
            write_to_file("\n[SUCCESS] WebDriver initialized successfully!")
            write_to_file(f"Browser name: {driver.name}")
            write_to_file(f"Browser version: {driver.capabilities.get('browserVersion')}")
            
            # Test loading a page
            write_to_file("\nTesting page load...")
            driver.get("https://www.example.com")
            write_to_file(f"Page title: {driver.title}")
            
            # Clean up
            write_to_file("\nClosing driver...")
            driver.quit()
            write_to_file("Driver successfully closed!")
        else:
            write_to_file("[FAIL] WebDriver initialization returned None!")
    
    except Exception as e:
        write_to_file(f"\n[ERROR] WebDriver initialization failed with error: {str(e)}")
        write_to_file(traceback.format_exc())
    
    write_to_file("\nTest completed!")

if __name__ == "__main__":
    # Clear the output file before starting
    with open("webdriver_test_output.txt", "w") as f:
        f.write("")
    
    test_webdriver_initialization()
    print(f"Test completed! Check webdriver_test_output.txt for results.")
