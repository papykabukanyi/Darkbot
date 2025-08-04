"""
Test script for proxy rotation and fallback system.
"""

import sys
import os
import logging
import requests
import time
import json
import traceback

# Set up logging with console output
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This ensures logs are output to the console
    ]
)
logger = logging.getLogger("ProxyTester")

# Set all loggers to DEBUG
logging.getLogger("ProxyManager").setLevel(logging.DEBUG)
logging.getLogger("FallbackProxySystem").setLevel(logging.DEBUG)

# Print out some debug information
print("Starting proxy test script")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the proxy manager
from utils.proxy_manager import ProxyManager
from utils.fallback_proxy import FallbackProxySystem

def test_proxy_rotation():
    """Test the proxy rotation system."""
    logger.info("Testing proxy rotation...")
    
    # Initialize the proxy manager with fallback enabled
    proxy_manager = ProxyManager(verify_proxies=True, use_fallback=True)
    
    # Check how many proxies were loaded
    working_count = proxy_manager.get_working_proxies_count()
    logger.info(f"Working proxies available: {working_count}")
    
    # Create a session and rotate proxy
    session = requests.Session()
    proxy = proxy_manager.rotate_proxy_for_session(session)
    
    if proxy:
        logger.info(f"Using proxy: {proxy.get('id')}")
        logger.info(f"Is fallback: {proxy.get('is_fallback', False)}")
        logger.info(f"Session proxies: {session.proxies}")
        logger.info(f"Session headers: {session.headers}")
    else:
        logger.error("No proxy was assigned!")
        return False
    
    # Test the connection
    test_urls = [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
    ]
    
    for url in test_urls:
        try:
            logger.info(f"Testing connection to {url}...")
            start_time = time.time()
            response = session.get(url, timeout=15)
            elapsed = time.time() - start_time
            
            logger.info(f"Response time: {elapsed:.2f} seconds")
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                ip_data = response.json()
                logger.info(f"IP information: {json.dumps(ip_data, indent=2)}")
                return True
            else:
                logger.warning(f"Request failed with status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
    
    return False

def test_fallback_system():
    """Test the fallback proxy system directly."""
    logger.info("Testing fallback proxy system...")
    
    fallback = FallbackProxySystem()
    
    # Test Tor setup
    if fallback.check_tor_installation():
        logger.info("Tor is installed!")
        
        tor_started = fallback.setup_tor_proxy()
        if tor_started:
            logger.info(f"Tor started successfully on port {fallback.tor_port}")
            
            # Test the connection
            proxy_dict = {
                "http": f"socks5://127.0.0.1:{fallback.tor_port}",
                "https": f"socks5://127.0.0.1:{fallback.tor_port}"
            }
            
            session = requests.Session()
            session.proxies = proxy_dict
            
            try:
                response = session.get("https://httpbin.org/ip", timeout=30)
                logger.info(f"Tor IP: {response.json()}")
                return True
            except Exception as e:
                logger.error(f"Tor connection test failed: {str(e)}")
        else:
            logger.error("Failed to start Tor")
    else:
        logger.info("Tor is not installed, testing random user agent")
        
    # Test user agent rotation
    for _ in range(3):
        ua = fallback.get_random_user_agent()
        logger.info(f"Random User-Agent: {ua}")
    
    return False

if __name__ == "__main__":
    try:
        print("Starting main test execution...")
        logger.info("Starting proxy system tests...")
        
        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"Added project root to path: {project_root}")
        
        # Test fallback system first
        print("Testing fallback system...")
        fallback_result = test_fallback_system()
        logger.info(f"Fallback system test {'succeeded' if fallback_result else 'failed'}")
        
        # Test proxy rotation
        print("Testing proxy rotation...")
        proxy_result = test_proxy_rotation()
        logger.info(f"Proxy rotation test {'succeeded' if proxy_result else 'failed'}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
