"""
Darkbot System Verification

This script checks that all essential components of Darkbot are working correctly.
It runs a series of tests to verify:
1. StockX API integration
2. Configuration loading
3. File structure
4. Required dependencies
"""

import os
import sys
import logging
import importlib
import traceback
from datetime import datetime

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"verify_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemVerification")

def check_dependencies():
    """Verify that all required dependencies are installed"""
    logger.info("Checking required dependencies...")
    
    required_packages = [
        "requests", "beautifulsoup4", "flask", "werkzeug", 
        "python-dotenv", "schedule", "selenium", "lxml", "gunicorn"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        return False
    else:
        logger.info("✅ All required dependencies are installed")
        return True

def check_file_structure():
    """Verify that the required file structure exists"""
    logger.info("Checking file structure...")
    
    required_dirs = ["utils", "scrapers", "logs", "data", "data/cache"]
    required_files = ["sneakerbot.py", "app.py", "config_fixed.py", "utils/stockx_adapter.py", "utils/stockx_price_checker.py"]
    
    missing_dirs = []
    missing_files = []
    
    for directory in required_dirs:
        if not os.path.isdir(directory):
            missing_dirs.append(directory)
    
    for file in required_files:
        if not os.path.isfile(file):
            missing_files.append(file)
    
    if missing_dirs or missing_files:
        if missing_dirs:
            logger.error(f"Missing required directories: {', '.join(missing_dirs)}")
        if missing_files:
            logger.error(f"Missing required files: {', '.join(missing_files)}")
        return False
    else:
        logger.info("✅ All required files and directories exist")
        return True

def check_config():
    """Verify that the configuration can be loaded"""
    logger.info("Checking configuration...")
    
    try:
        from config_fixed import (
            setup_logging, STOCKX_CONFIG, PROFIT_CHECKER_CONFIG
        )
        logger.info("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.error(traceback.format_exc())
        return False

def check_stockx_api():
    """Verify that the StockX API integration works"""
    logger.info("Checking StockX API integration...")
    
    try:
        from utils.stockx_adapter import StockXAdapter
        
        adapter = StockXAdapter()
        test_result = True
        
        # Check if credentials are set
        missing_credentials = []
        if not adapter.api_key:
            missing_credentials.append("STOCKX_API_KEY")
        if not adapter.client_id:
            missing_credentials.append("STOCKX_CLIENT_ID")
        if not adapter.client_secret:
            missing_credentials.append("STOCKX_CLIENT_SECRET")
        
        if missing_credentials:
            logger.warning(f"Missing StockX credentials: {', '.join(missing_credentials)}")
            logger.warning("Some functionality may not work without these credentials.")
            test_result = False
        
        logger.info("✅ StockX adapter initialized successfully")
        return test_result
    except Exception as e:
        logger.error(f"Error checking StockX API: {e}")
        logger.error(traceback.format_exc())
        return False

def check_flask_app():
    """Verify that the Flask application can be initialized"""
    logger.info("Checking Flask application...")
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import app
        
        logger.info("✅ Flask application imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing Flask application: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all verification checks"""
    logger.info("=" * 60)
    logger.info(f"Darkbot System Verification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    tests = [
        ("Dependencies", check_dependencies()),
        ("File Structure", check_file_structure()),
        ("Configuration", check_config()),
        ("StockX API", check_stockx_api()),
        ("Flask Application", check_flask_app())
    ]
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    for name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
    
    all_passed = all(result for _, result in tests)
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("✅ All verification checks passed! System is ready.")
        return 0
    else:
        logger.warning("❌ Some verification checks failed. Please fix the issues before using the system.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
