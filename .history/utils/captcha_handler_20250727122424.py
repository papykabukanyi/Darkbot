"""
CAPTCHA detection and handling utilities
"""
import logging
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

logger = logging.getLogger(__name__)

# Common CAPTCHA detection strings
CAPTCHA_INDICATORS = [
    "captcha",
    "robot",
    "human verification",
    "security check",
    "prove you're not a robot",
    "are you a human",
    "please verify",
    "bot detection",
    "challenge"
]

# Common CAPTCHA service providers' domains
CAPTCHA_SERVICES = [
    "recaptcha",
    "hcaptcha",
    "arkoselabs",
    "funcaptcha",
    "cloudflare",
    "datadome",
    "perimeterx",
    "akamai"
]

def is_captcha_present(driver):
    """Check if a CAPTCHA challenge is present on the page
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if CAPTCHA detected, False otherwise
    """
    # Check page source for CAPTCHA indicators
    page_source = driver.page_source.lower()
    
    # Check for CAPTCHA indicators in the page source
    for indicator in CAPTCHA_INDICATORS:
        if indicator.lower() in page_source:
            logger.warning(f"CAPTCHA detected: Found '{indicator}' in page source")
            return True
    
    # Check for CAPTCHA service domains in the page source
    for service in CAPTCHA_SERVICES:
        if service.lower() in page_source:
            logger.warning(f"CAPTCHA service detected: Found '{service}' in page source")
            return True
    
    # Check for common CAPTCHA iframe elements
    try:
        captcha_iframes = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'captcha') or contains(@title, 'captcha')]")
        if captcha_iframes:
            logger.warning("CAPTCHA detected: Found CAPTCHA iframe")
            return True
    except Exception as e:
        logger.debug(f"Error while checking for CAPTCHA iframes: {e}")
    
    return False

def handle_captcha(driver, site_name):
    """Handle CAPTCHA challenges with appropriate strategies
    
    Args:
        driver: Selenium WebDriver instance
        site_name: Name of the site being scraped
        
    Returns:
        bool: True if handled successfully, False otherwise
    """
    logger.warning(f"Attempting to handle CAPTCHA for {site_name}")
    
    # 1. Try waiting strategy - sometimes this helps with temporary blocks
    logger.info("Trying waiting strategy")
    wait_time = random.randint(30, 60)
    logger.info(f"Waiting for {wait_time} seconds")
    time.sleep(wait_time)
    
    # 2. Check if waiting helped
    if not is_captcha_present(driver):
        logger.info("CAPTCHA appears to be gone after waiting")
        return True
    
    # 3. Try refreshing the page
    logger.info("Trying page refresh")
    driver.refresh()
    time.sleep(5)
    
    if not is_captcha_present(driver):
        logger.info("CAPTCHA appears to be gone after refresh")
        return True
    
    # 4. If still not resolved, report failure
    logger.warning(f"Failed to handle CAPTCHA for {site_name}")
    return False

def avoid_captcha_triggers(driver):
    """Simulate human behavior to avoid triggering CAPTCHAs
    
    Args:
        driver: Selenium WebDriver instance
    """
    # Add random pauses between actions
    time.sleep(random.uniform(1, 3))
    
    # Simulate human-like scrolling
    scroll_amount = random.randint(300, 700)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(0.5, 1.5))
    
    # Occasionally scroll back up a bit
    if random.random() > 0.7:
        scroll_back = random.randint(100, 300)
        driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
        time.sleep(random.uniform(0.5, 1.0))
    
    # Add more random pauses
    time.sleep(random.uniform(0.5, 2))
