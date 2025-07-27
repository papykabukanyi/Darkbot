"""
Utility functions for managing Selenium webdriver for different browsers and environments
"""
import os
import logging
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def setup_driver(headless=True, proxy=None, retry_attempts=3):
    """Set up a Selenium webdriver with appropriate options
    
    Args:
        headless (bool): Whether to run in headless mode
        proxy (str): Optional proxy to use (format: ip:port)
        retry_attempts (int): Number of times to retry if setup fails
        
    Returns:
        WebDriver: Configured Selenium WebDriver instance
    """
    attempt = 0
    while attempt < retry_attempts:
        try:
            logger.info(f"Setting up Chrome driver (Attempt {attempt+1}/{retry_attempts})")
            return _setup_chrome_driver(headless, proxy)
        except Exception as e:
            attempt += 1
            logger.error(f"Failed to set up Chrome driver (Attempt {attempt}/{retry_attempts}): {e}")
            
            if attempt < retry_attempts:
                # Wait with exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                # Final attempt with undetected_chromedriver as fallback
                logger.info("Trying fallback options...")
                try:
                    return _setup_undetected_chromedriver(headless, proxy)
                except Exception as ue:
                    logger.error(f"Failed to set up undetected Chrome driver: {ue}")
                    raise Exception("Could not set up any webdriver after multiple attempts") from ue

def _setup_chrome_driver(headless=True, proxy=None):
    """Set up a standard Chrome webdriver
    
    Args:
        headless (bool): Whether to run in headless mode
        proxy (str): Optional proxy to use (format: ip:port)
        
    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    
    # Add common options
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
    
    # Add proxy if specified
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    
    # Add anti-detection options
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # Add random behavior for cookie acceptance
    if random.random() > 0.5:
        chrome_options.add_argument("--disable-cookies")
    
    # Set random user agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    # Add experimental options to hide automation
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    try:
        # First try using webdriver-manager for automatic chromedriver management
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute CDP commands to hide automation
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })
        
        logger.info("Successfully set up Chrome driver with webdriver-manager")
        return driver
    except Exception as e:
        logger.warning(f"Failed to set up Chrome driver with webdriver-manager: {e}")
        
        # Fall back to direct path for environments where Chrome is installed in standard location
        try:
            if os.path.exists("/usr/bin/google-chrome"):
                chrome_path = "/usr/bin/google-chrome"
            elif os.path.exists("/usr/bin/google-chrome-stable"):
                chrome_path = "/usr/bin/google-chrome-stable"
            else:
                # For Windows environments
                chrome_path = None
                
            if chrome_path:
                chrome_options.binary_location = chrome_path
                
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Successfully set up Chrome driver with direct path")
            return driver
        except Exception as e2:
            logger.error(f"Failed to set up Chrome driver with direct path: {e2}")
            raise e2

def _setup_undetected_chromedriver(headless=True, proxy=None):
    """Set up an undetected_chromedriver as a fallback option
    
    Args:
        headless (bool): Whether to run in headless mode
        proxy (str): Optional proxy to use (format: ip:port)
        
    Returns:
        WebDriver: Configured undetected_chromedriver instance
    """
    try:
        import undetected_chromedriver as uc
        
        options = uc.ChromeOptions()
        
        if headless:
            options.add_argument("--headless")
        
        if proxy:
            options.add_argument(f"--proxy-server={proxy}")
        
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        
        # Initialize undetected-chromedriver
        driver = uc.Chrome(options=options)
        logger.info("Successfully set up undetected Chrome driver")
        return driver
    except ImportError:
        logger.error("undetected_chromedriver not installed. Install with: pip install undetected-chromedriver")
        raise
    except Exception as e:
        logger.error(f"Failed to set up undetected Chrome driver: {e}")
        raise
