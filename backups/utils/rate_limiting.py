"""
Rate limiting utilities to respect website limits and avoid detection
"""
import time
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to control request frequency to specific domains"""
    
    def __init__(self):
        self.last_request_time = defaultdict(float)
        
        # Default delay range in seconds (1-3 seconds)
        self.default_min_delay = 1.0
        self.default_max_delay = 3.0
        
        # Site-specific delay configurations (in seconds)
        self.site_delays = {
            'footlocker': (2.0, 4.0),   # Stricter anti-bot measures
            'nike': (3.0, 5.0),         # More aggressive anti-bot measures
            'adidas': (2.0, 4.0),       # Moderate anti-bot measures
            'finishline': (1.5, 3.0),   # Less strict
            'jdsports': (1.5, 3.0),     # Similar to Finish Line
            'stockx': (2.0, 4.0),       # Market data site with limits
            'goat': (2.0, 4.0),         # Market data site with limits
            'flightclub': (1.0, 2.0),   # Less strict
        }
    
    def wait(self, domain):
        """Wait an appropriate amount of time before making a request to the domain
        
        Args:
            domain (str): The domain to request (e.g., 'nike.com')
        """
        # Extract the base domain for matching
        base_domain = self._extract_base_domain(domain)
        
        current_time = time.time()
        last_time = self.last_request_time[base_domain]
        
        # Get delay range for this domain
        min_delay, max_delay = self._get_delay_range(base_domain)
        
        # Calculate a random delay within the range
        delay = random.uniform(min_delay, max_delay)
        
        # Calculate how long to wait
        elapsed = current_time - last_time
        wait_time = max(0, delay - elapsed)
        
        if wait_time > 0:
            logger.debug(f"Rate limiting: Waiting {wait_time:.2f}s before requesting {domain}")
            time.sleep(wait_time)
        
        # Update the last request time
        self.last_request_time[base_domain] = time.time()
    
    def _extract_base_domain(self, domain):
        """Extract the base domain from a URL or domain string
        
        Args:
            domain (str): The domain or URL
            
        Returns:
            str: The base domain
        """
        # Remove protocol and path
        if '//' in domain:
            domain = domain.split('//')[1]
        domain = domain.split('/')[0]
        
        # Handle subdomains by extracting main domain parts
        parts = domain.split('.')
        if len(parts) > 2:
            # For domains like www.nike.com, extract nike
            domain_key = parts[-2]
        else:
            # For domains like nike.com
            domain_key = parts[0]
        
        return domain_key.lower()
    
    def _get_delay_range(self, base_domain):
        """Get the delay range for a domain
        
        Args:
            base_domain (str): The base domain
            
        Returns:
            tuple: (min_delay, max_delay) in seconds
        """
        # Check for specific site configuration
        for site_key, delay_range in self.site_delays.items():
            if site_key in base_domain:
                return delay_range
        
        # Return default delay range
        return self.default_min_delay, self.default_max_delay


# Create a global instance for use across the application
rate_limiter = RateLimiter()
