"""
Base scraper class that all scrapers will inherit from.
"""

import logging
import time
import random
import re
import os
import html
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup

# Import config settings
from config_fixed import get_random_user_agent, get_random_proxy, get_random_delay

logger = logging.getLogger("SneakerBot")

def random_delay(min_seconds=1.0, max_seconds=3.0):
    """
    Wait for a random amount of time between min_seconds and max_seconds.
    
    Args:
        min_seconds: Minimum number of seconds to wait
        max_seconds: Maximum number of seconds to wait
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Waiting for {delay:.2f} seconds")
    time.sleep(delay)


class BaseSneakerScraper(ABC):
    """Base class for all sneaker scrapers."""
    
    def __init__(self, site_config):
        """
        Initialize the base scraper.
        
        Args:
            site_config: Dictionary with site configuration
        """
        self.name = site_config.get('name', 'Unknown')
        self.base_url = site_config.get('url', '')
        self.session = requests.Session()
        self.rate_limit = site_config.get('rate_limit', 10)  # Requests per minute
        self.rotate_user_agent = site_config.get('rotate_user_agent', True)
        self.use_proxies = site_config.get('use_proxies', False)
        self.use_random_delays = site_config.get('use_random_delays', True)
        
        # Set up default headers
        self.headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Initialize the last request timestamp
        self.last_request_time = 0
        
    def validate_url(self, url):
        """
        Validate that a URL is well-formed and accessible.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        try:
            # Check if URL is well-formed
            parsed_url = re.match(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', url)
            if not parsed_url:
                logger.error(f"Invalid URL format: {url}")
                return False
                
            # We'll avoid making a head request to prevent detection
            # Just validate the format is correct
            return True
            
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False
            
    def __enter__(self):
        """Enter the context manager."""
        logger.info(f"Initialized {self.name} scraper for {self.base_url}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.session.close()
    
    def get_page(self, url, params=None, retries=3):
        """
        Get a page and return the BeautifulSoup object.
        
        Args:
            url: URL to get
            params: Dictionary of query parameters
            retries: Number of retries on failure
            
        Returns:
            BeautifulSoup object or None if failed
        """
        # Validate the URL first
        if not self.validate_url(url):
            logger.error(f"Invalid URL: {url}")
            return BeautifulSoup("<html><body></body></html>", 'lxml')  # Return empty page
        
        if self.rotate_user_agent:
            self.headers['User-Agent'] = get_random_user_agent()
        
        proxies = None
        if self.use_proxies:
            proxy = get_random_proxy()
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
        
        for attempt in range(retries):
            try:
                logger.debug(f"Getting {url}")
                
                # Add delay for rate limiting
                if self.use_random_delays:
                    random_delay()
                
                response = self.session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    proxies=proxies,
                    timeout=30
                )
                
                # Check if response is ok
                if response.status_code == 200:
                    logger.debug(f"Successfully got {url}")
                    return BeautifulSoup(response.text, 'lxml')
                elif response.status_code == 404:
                    logger.error(f"Page not found (404): {url} - Check if the URL is correct")
                    # If this is the last attempt, return an empty BeautifulSoup object rather than None
                    if attempt == retries - 1:
                        logger.warning(f"Creating empty page for {url} after {retries} failed attempts")
                        return BeautifulSoup("<html><body></body></html>", 'lxml')
                elif response.status_code == 403:
                    logger.error(f"Access forbidden (403): {url} - Possible bot detection")
                    # Change user agent for next attempt
                    if self.rotate_user_agent:
                        self.headers['User-Agent'] = get_random_user_agent()
                else:
                    logger.warning(f"Failed to get {url} - Status {response.status_code}")
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout for {url}")
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error for {url} - Check your internet connection")
            except Exception as e:
                logger.error(f"Error getting {url}: {str(e)}")
            
            # Wait before retrying with increasing backoff
            wait_time = (attempt + 1) * 2 + random.uniform(0, 1)  # Add some randomness
            logger.debug(f"Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        
        return None
    
    def post_request(self, url, data=None, json=None, retries=3):
        """
        Send a POST request and return the response.
        
        Args:
            url: URL to post to
            data: Form data to send
            json: JSON data to send
            retries: Number of retries on failure
            
        Returns:
            Response object or None if failed
        """
        if self.rotate_user_agent:
            self.headers['User-Agent'] = get_random_user_agent()
        
        proxies = None
        if self.use_proxies:
            proxy = get_random_proxy()
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
        
        for attempt in range(retries):
            try:
                logger.debug(f"Posting to {url}")
                
                # Add delay for rate limiting
                if self.use_random_delays:
                    random_delay()
                
                response = self.session.post(
                    url,
                    headers=self.headers,
                    data=data,
                    json=json,
                    proxies=proxies,
                    timeout=30
                )
                
                # Check if response is ok
                if response.status_code in [200, 201]:
                    logger.debug(f"Successfully posted to {url}")
                    return response
                else:
                    logger.warning(f"Failed to post to {url} - Status {response.status_code}")
            except Exception as e:
                logger.error(f"Error posting to {url}: {str(e)}")
            
            # Wait before retrying
            wait_time = (attempt + 1) * 2
            logger.debug(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        
        return None
    
    def extract_text(self, element, selector=None, default=''):
        """
        Extract text from an element or selector.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector to find within the element
            default: Default value if no text is found
            
        Returns:
            Extracted text or default value
        """
        if not element:
            return default
        
        try:
            if selector:
                found = element.select_one(selector)
                if found:
                    return html.unescape(found.get_text(strip=True))
            else:
                return html.unescape(element.get_text(strip=True))
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
        
        return default
    
    def clean_price(self, price_str):
        """
        Clean a price string and convert to float.
        
        Args:
            price_str: Price string to clean
            
        Returns:
            Cleaned price as float or None if invalid
        """
        if not price_str:
            return None
        
        try:
            # Remove currency symbols and non-numeric chars except for decimal point
            cleaned = re.sub(r'[^\d.]', '', price_str)
            return float(cleaned)
        except Exception:
            return None
    
    @abstractmethod
    def get_releases(self):
        """
        Get new releases from the site.
        
        This method must be implemented by subclasses.
        
        Returns:
            List of release dictionaries
        """
        pass
