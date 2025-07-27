"""
Utility functions for the sneaker bot.
"""

import random
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from fake_useragent import UserAgent
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import DEFAULT_HEADERS, USE_PROXY, PROXIES, REQUEST_TIMEOUT, RETRY_ATTEMPTS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SneakerBot")

def get_random_user_agent() -> str:
    """Generate a random user agent string."""
    try:
        ua = UserAgent()
        return ua.random
    except Exception as e:
        logger.error(f"Error generating random user agent: {e}")
        return DEFAULT_HEADERS['User-Agent']

def random_delay(min_seconds: float = 1.0, max_seconds: float = 5.0) -> None:
    """Add a random delay to mimic human behavior."""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def setup_selenium_driver(headless: bool = True) -> webdriver.Chrome:
    """Set up and return a Selenium Chrome webdriver."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    # Add common options to make the browser more stealthy
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Set a random user agent
    options.add_argument(f"user-agent={get_random_user_agent()}")
    
    # Create the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Change the navigator property to prevent detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def make_request(url: str, method: str = "GET", headers: Optional[Dict] = None, 
                data: Any = None, params: Any = None) -> Optional[requests.Response]:
    """
    Make an HTTP request with retry logic and proxy support.
    """
    if not headers:
        headers = DEFAULT_HEADERS.copy()
        headers["User-Agent"] = get_random_user_agent()
    
    proxies = PROXIES if USE_PROXY else None
    
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                params=params,
                proxies=proxies,
                timeout=REQUEST_TIMEOUT
            )
            
            # Check if we got blocked or hit a captcha
            if "captcha" in response.text.lower() or "access denied" in response.text.lower():
                logger.warning(f"Possible CAPTCHA or blocking detected on {url}")
                random_delay(5.0, 10.0)
                continue
                
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed (attempt {attempt+1}/{RETRY_ATTEMPTS}): {str(e)}")
            if attempt < RETRY_ATTEMPTS - 1:
                random_delay(attempt * 2, attempt * 5)  # Exponential backoff
            else:
                logger.error(f"Failed to retrieve {url} after {RETRY_ATTEMPTS} attempts")
                return None
    
    return None

def format_price(price_str: str) -> float:
    """
    Convert price string to float.
    
    Examples:
    - "$120.00" -> 120.0
    - "$1,299.99" -> 1299.99
    - "120 USD" -> 120.0
    """
    if not price_str:
        return 0.0
    
    # Remove currency symbols and non-numeric chars except decimal point
    price_str = ''.join(c for c in price_str if c.isdigit() or c == '.')
    
    try:
        return float(price_str)
    except ValueError:
        logger.error(f"Failed to convert price: {price_str}")
        return 0.0

def calculate_profit_potential(retail: float, market_value: float) -> Dict[str, Union[float, str]]:
    """
    Calculate potential profit and ROI for a product.
    
    Args:
        retail: Current retail price
        market_value: Estimated market value/resale price
    
    Returns:
        Dictionary with profit amount and percentage
    """
    if retail <= 0 or market_value <= 0:
        return {"profit": 0, "roi": "0%", "worth_buying": False}
    
    # Estimate fees and shipping costs
    estimated_fees = market_value * 0.10  # Assume 10% marketplace fees
    shipping_cost = 15  # Estimated shipping cost
    
    # Calculate net profit
    profit = market_value - retail - estimated_fees - shipping_cost
    
    # Calculate ROI
    roi_percentage = (profit / retail) * 100 if retail > 0 else 0
    roi = f"{roi_percentage:.1f}%"
    
    # Determine if it's worth buying
    worth_buying = profit > 20 and roi_percentage > 15
    
    return {
        "profit": round(profit, 2),
        "roi": roi,
        "worth_buying": worth_buying
    }

def get_timestamp() -> str:
    """Get current timestamp in a readable format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
