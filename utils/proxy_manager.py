"""
Proxy management system for IP rotation and avoiding bans.
"""

import logging
import random
import time
import requests
from typing import Dict, List, Optional, Tuple, Union
import json
import os
from concurrent.futures import ThreadPoolExecutor
import re
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger("ProxyManager")

class ProxyManager:
    """
    Manages a pool of proxies for rotating IPs and avoiding bans.
    """
    
    def __init__(self, proxy_list_path: str = None, max_fails: int = 3, 
                 ban_time: int = 1800, verify_proxies: bool = True):
        """
        Initialize the proxy manager.
        
        Args:
            proxy_list_path: Path to JSON file with proxies
            max_fails: Maximum number of failures before marking a proxy as banned
            ban_time: Time in seconds to ban a proxy (default: 30 minutes)
            verify_proxies: Whether to verify proxies on initialization
        """
        self.proxy_list_path = proxy_list_path or "proxies.json"
        self.max_fails = max_fails
        self.ban_time = ban_time
        
        # Proxy structure:
        # {
        #     "id": "proxy1",
        #     "host": "123.45.67.89",
        #     "port": 8080,
        #     "username": "user123", # optional
        #     "password": "pass456", # optional
        #     "protocol": "http", # or https, socks5, etc.
        #     "country": "US", # optional
        #     "last_used": 1627408123, # timestamp
        #     "fail_count": 0,
        #     "banned_until": null, # timestamp or null
        #     "avg_response_time": 1.2, # in seconds
        # }
        
        self.proxies = self._load_proxies()
        self.current_proxy_index = 0
        
        # Test proxies if requested
        if verify_proxies and self.proxies:
            self._verify_all_proxies()
    
    def _load_proxies(self) -> List[Dict]:
        """
        Load proxies from file or create an empty list.
        
        Returns:
            List of proxy configurations
        """
        if os.path.exists(self.proxy_list_path):
            try:
                with open(self.proxy_list_path, 'r') as f:
                    proxies = json.load(f)
                logger.info(f"Loaded {len(proxies)} proxies from {self.proxy_list_path}")
                return proxies
            except Exception as e:
                logger.error(f"Error loading proxies from {self.proxy_list_path}: {e}")
        
        logger.warning(f"Proxy file {self.proxy_list_path} not found. Starting with empty proxy list.")
        return []
    
    def _save_proxies(self) -> None:
        """Save the current proxy list to file."""
        try:
            with open(self.proxy_list_path, 'w') as f:
                json.dump(self.proxies, f, indent=2)
            logger.info(f"Saved {len(self.proxies)} proxies to {self.proxy_list_path}")
        except Exception as e:
            logger.error(f"Error saving proxies to {self.proxy_list_path}: {e}")
    
    def add_proxy(self, host: str, port: int, protocol: str = "http", 
                 username: str = None, password: str = None, 
                 country: str = None) -> Dict:
        """
        Add a new proxy to the pool.
        
        Args:
            host: Proxy host/IP
            port: Proxy port
            protocol: Proxy protocol (http, https, socks5)
            username: Authentication username (if needed)
            password: Authentication password (if needed)
            country: Proxy country code (if known)
            
        Returns:
            The added proxy configuration
        """
        proxy_id = f"{protocol}-{host}-{port}"
        
        # Check if proxy already exists
        for proxy in self.proxies:
            if proxy.get("id") == proxy_id:
                logger.warning(f"Proxy {proxy_id} already exists")
                return proxy
        
        # Create new proxy entry
        proxy = {
            "id": proxy_id,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "protocol": protocol,
            "country": country,
            "last_used": 0,
            "fail_count": 0,
            "banned_until": None,
            "avg_response_time": None
        }
        
        self.proxies.append(proxy)
        logger.info(f"Added proxy {proxy_id}")
        self._save_proxies()
        return proxy
    
    def add_proxies_from_list(self, proxy_list: List[Dict]) -> None:
        """
        Add multiple proxies from a list.
        
        Args:
            proxy_list: List of proxy dictionaries with host, port, etc.
        """
        for proxy_data in proxy_list:
            self.add_proxy(
                host=proxy_data.get("host"),
                port=proxy_data.get("port"),
                protocol=proxy_data.get("protocol", "http"),
                username=proxy_data.get("username"),
                password=proxy_data.get("password"),
                country=proxy_data.get("country")
            )
    
    def get_proxy_url(self, proxy: Dict) -> str:
        """
        Get the formatted proxy URL for the requests library.
        
        Args:
            proxy: Proxy configuration dictionary
            
        Returns:
            Proxy URL string
        """
        protocol = proxy.get("protocol", "http")
        host = proxy.get("host")
        port = proxy.get("port")
        username = proxy.get("username")
        password = proxy.get("password")
        
        if username and password:
            return f"{protocol}://{username}:{password}@{host}:{port}"
        else:
            return f"{protocol}://{host}:{port}"
    
    def get_proxy_dict(self, proxy: Dict) -> Dict[str, str]:
        """
        Get the proxy dictionary for the requests library.
        
        Args:
            proxy: Proxy configuration dictionary
            
        Returns:
            Proxy dictionary for requests
        """
        proxy_url = self.get_proxy_url(proxy)
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def get_next_proxy(self, for_url: str = None) -> Optional[Dict]:
        """
        Get the next available proxy from the pool using rotation.
        
        Args:
            for_url: Target URL (for domain-specific proxy selection)
            
        Returns:
            Next available proxy or None if no valid proxies
        """
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        # Try to find a non-banned proxy
        for _ in range(len(self.proxies)):
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            proxy = self.proxies[self.current_proxy_index]
            
            # Check if proxy is banned
            banned_until = proxy.get("banned_until")
            if banned_until and banned_until > time.time():
                # Still banned, skip
                continue
            
            # Reset ban if it's expired
            if banned_until and banned_until <= time.time():
                proxy["banned_until"] = None
                proxy["fail_count"] = 0
                logger.info(f"Proxy {proxy['id']} ban expired, now available")
            
            # Update last used time
            proxy["last_used"] = time.time()
            return proxy
        
        logger.warning("All proxies are currently banned")
        return None
    
    def mark_proxy_success(self, proxy: Dict, response_time: float = None) -> None:
        """
        Mark a proxy as successful and update its stats.
        
        Args:
            proxy: Proxy configuration
            response_time: Response time in seconds
        """
        if not proxy:
            return
            
        proxy_id = proxy.get("id")
        if not proxy_id:
            return
            
        # Find the proxy in our list
        for p in self.proxies:
            if p.get("id") == proxy_id:
                p["fail_count"] = 0
                p["banned_until"] = None
                
                # Update average response time
                if response_time is not None:
                    if p.get("avg_response_time") is None:
                        p["avg_response_time"] = response_time
                    else:
                        # Moving average
                        p["avg_response_time"] = 0.8 * p["avg_response_time"] + 0.2 * response_time
                
                self._save_proxies()
                return
    
    def mark_proxy_failure(self, proxy: Dict, ban: bool = False) -> None:
        """
        Mark a proxy as failed and update its stats.
        
        Args:
            proxy: Proxy configuration
            ban: Force ban the proxy immediately
        """
        if not proxy:
            return
            
        proxy_id = proxy.get("id")
        if not proxy_id:
            return
        
        # Find the proxy in our list
        for p in self.proxies:
            if p.get("id") == proxy_id:
                if ban:
                    p["fail_count"] = self.max_fails
                else:
                    p["fail_count"] = p.get("fail_count", 0) + 1
                
                # Ban if too many failures
                if p["fail_count"] >= self.max_fails:
                    p["banned_until"] = time.time() + self.ban_time
                    logger.warning(f"Proxy {proxy_id} banned for {self.ban_time} seconds")
                
                self._save_proxies()
                return
    
    def verify_proxy(self, proxy: Dict) -> bool:
        """
        Test if a proxy is working.
        
        Args:
            proxy: Proxy configuration to test
            
        Returns:
            True if the proxy is working, False otherwise
        """
        test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org"
        ]
        
        proxy_dict = self.get_proxy_dict(proxy)
        
        for url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(
                    url, 
                    proxies=proxy_dict, 
                    timeout=10
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    logger.info(f"Proxy {proxy['id']} verified working (response time: {elapsed:.2f}s)")
                    self.mark_proxy_success(proxy, elapsed)
                    return True
            except Exception as e:
                logger.warning(f"Proxy {proxy['id']} verification failed: {e}")
        
        self.mark_proxy_failure(proxy)
        return False
    
    def _verify_all_proxies(self) -> None:
        """Verify all proxies in parallel."""
        logger.info(f"Verifying {len(self.proxies)} proxies...")
        
        with ThreadPoolExecutor(max_workers=min(10, len(self.proxies))) as executor:
            results = list(executor.map(self.verify_proxy, self.proxies))
        
        working = sum(1 for result in results if result)
        logger.info(f"Proxy verification complete: {working}/{len(self.proxies)} working")
    
    def get_working_proxies_count(self) -> int:
        """
        Get the number of currently working (not banned) proxies.
        
        Returns:
            Count of available proxies
        """
        current_time = time.time()
        return sum(1 for p in self.proxies if not p.get("banned_until") or p.get("banned_until") <= current_time)
    
    def rotate_proxy_for_session(self, session: requests.Session) -> Optional[Dict]:
        """
        Assign a proxy to an existing requests session.
        
        Args:
            session: Requests session to update
            
        Returns:
            The proxy that was assigned or None
        """
        proxy = self.get_next_proxy()
        if proxy:
            proxy_dict = self.get_proxy_dict(proxy)
            session.proxies.update(proxy_dict)
        return proxy


class CaptchaSolver:
    """
    Detect and handle various CAPTCHA types on sneaker websites.
    """
    
    def __init__(self):
        """Initialize the CAPTCHA solver."""
        self.captcha_patterns = {
            'recaptcha': [
                'google.com/recaptcha',
                'class="g-recaptcha"',
                'data-sitekey'
            ],
            'cloudflare': [
                'cf-challenge',
                'cf_chl_captcha',
                'hcaptcha'
            ],
            'akamai': [
                'id="ak_js"',
                'bot-detection'
            ],
            'generic': [
                'captcha',
                'robot check',
                'verify you are human',
                'please verify',
                'security check'
            ]
        }
    
    def detect_captcha(self, response: requests.Response) -> Tuple[bool, str]:
        """
        Detect if a response contains a CAPTCHA.
        
        Args:
            response: Response object to check
            
        Returns:
            Tuple of (is_captcha, captcha_type)
        """
        if not response or not response.text:
            return False, ''
        
        content = response.text.lower()
        
        for captcha_type, patterns in self.captcha_patterns.items():
            for pattern in patterns:
                if pattern.lower() in content:
                    return True, captcha_type
        
        # Check for unusual response size (often indicates bot detection)
        if len(content) < 1000 and any(keyword in content for keyword in ['security', 'bot', 'automated']):
            return True, 'size_anomaly'
        
        return False, ''
    
    def handle_captcha(self, response: requests.Response, session: requests.Session, url: str) -> bool:
        """
        Handle a detected CAPTCHA challenge.
        
        Args:
            response: Response containing CAPTCHA
            session: Current requests session
            url: URL that triggered the CAPTCHA
            
        Returns:
            True if handled successfully, False otherwise
        """
        is_captcha, captcha_type = self.detect_captcha(response)
        if not is_captcha:
            return True
        
        logger.warning(f"CAPTCHA detected ({captcha_type}) on {url}")
        
        # For now, we just detect and report the CAPTCHA
        # In a full implementation, this could:
        # 1. Use a CAPTCHA solving service API
        # 2. Implement browser automation to solve simple CAPTCHAs
        # 3. Use delay and retry strategies
        
        # Log the CAPTCHA for analysis
        try:
            captcha_dir = "captcha_samples"
            os.makedirs(captcha_dir, exist_ok=True)
            
            # Save the CAPTCHA response
            timestamp = int(time.time())
            filename = f"{captcha_dir}/captcha_{captcha_type}_{timestamp}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Saved CAPTCHA sample to {filename}")
        except Exception as e:
            logger.error(f"Error saving CAPTCHA sample: {e}")
        
        return False


class ProxiedRequester:
    """
    HTTP client that uses proxy rotation and handles CAPTCHAs.
    """
    
    def __init__(self, proxy_manager: ProxyManager = None, 
                 rotate_user_agents: bool = True,
                 captcha_detection: bool = True):
        """
        Initialize the proxied requester.
        
        Args:
            proxy_manager: ProxyManager instance
            rotate_user_agents: Whether to rotate user agents
            captcha_detection: Whether to detect and handle CAPTCHAs
        """
        self.proxy_manager = proxy_manager or ProxyManager()
        self.rotate_user_agents = rotate_user_agents
        self.captcha_detection = captcha_detection
        self.captcha_solver = CaptchaSolver() if captcha_detection else None
        
        # List of user agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        # Default session
        self.session = self._create_session()
        self.current_proxy = None
    
    def _create_session(self) -> requests.Session:
        """
        Create a new requests session with rotated user agent.
        
        Returns:
            New requests.Session instance
        """
        session = requests.Session()
        
        # Set a random user agent
        if self.rotate_user_agents:
            user_agent = random.choice(self.user_agents)
            session.headers.update({
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
        
        return session
    
    def _rotate_session(self) -> None:
        """Create a new session with a different user agent and proxy."""
        self.session = self._create_session()
        self.current_proxy = self.proxy_manager.rotate_proxy_for_session(self.session)
    
    def request(self, method: str, url: str, max_retries: int = 3, **kwargs) -> Optional[requests.Response]:
        """
        Make an HTTP request with proxy rotation and CAPTCHA handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            max_retries: Maximum number of retries
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object or None if failed
        """
        retries = 0
        backoff = 1
        
        while retries <= max_retries:
            # If we don't have a proxy, get one
            if not self.current_proxy:
                self._rotate_session()
                if not self.current_proxy and self.proxy_manager.get_working_proxies_count() == 0:
                    logger.error("No working proxies available")
                    time.sleep(5)  # Wait before retry without proxy
            
            try:
                start_time = time.time()
                response = self.session.request(method, url, timeout=30, **kwargs)
                elapsed = time.time() - start_time
                
                # Check for CAPTCHA if enabled
                if self.captcha_detection and self.captcha_solver:
                    is_captcha, _ = self.captcha_solver.detect_captcha(response)
                    if is_captcha:
                        logger.warning(f"CAPTCHA detected on {url}")
                        
                        # Mark this proxy as problematic
                        if self.current_proxy:
                            self.proxy_manager.mark_proxy_failure(self.current_proxy)
                            
                        # Rotate session for next try
                        self._rotate_session()
                        
                        retries += 1
                        time.sleep(backoff)
                        backoff *= 2  # Exponential backoff
                        continue
                
                # Success, mark the proxy as good
                if self.current_proxy:
                    self.proxy_manager.mark_proxy_success(self.current_proxy, elapsed)
                
                return response
                
            except requests.RequestException as e:
                logger.warning(f"Request to {url} failed: {e}")
                
                # Mark the proxy as failed
                if self.current_proxy:
                    self.proxy_manager.mark_proxy_failure(self.current_proxy)
                    
                # Rotate session for next try
                self._rotate_session()
            
            retries += 1
            if retries <= max_retries:
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
        
        logger.error(f"Failed to request {url} after {max_retries} retries")
        return None
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Perform a GET request."""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Perform a POST request."""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Perform a PUT request."""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Perform a DELETE request."""
        return self.request('DELETE', url, **kwargs)
    

# Proxy list sources manager
class ProxySourceManager:
    """
    Fetches and manages free and paid proxy lists from various sources.
    """
    
    def __init__(self, proxy_manager: ProxyManager):
        """
        Initialize the proxy source manager.
        
        Args:
            proxy_manager: ProxyManager instance to update with new proxies
        """
        self.proxy_manager = proxy_manager
        self.proxy_sources = {
            'free': [
                'https://www.proxy-list.download/api/v1/get?type=http',
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            ],
            'free_https': [
                'https://www.proxy-list.download/api/v1/get?type=https',
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=https&timeout=10000',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt',
            ],
            'free_socks': [
                'https://www.proxy-list.download/api/v1/get?type=socks5',
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
            ]
        }
    
    def fetch_from_sources(self, source_type: str = 'free') -> int:
        """
        Fetch proxies from the specified source type.
        
        Args:
            source_type: Type of sources to use ('free', 'free_https', 'free_socks')
            
        Returns:
            Number of new proxies added
        """
        sources = self.proxy_sources.get(source_type, [])
        if not sources:
            logger.warning(f"No sources defined for type {source_type}")
            return 0
        
        new_proxies = 0
        
        for source in sources:
            try:
                logger.info(f"Fetching proxies from {source}")
                protocol = 'socks5' if 'socks5' in source else ('https' if 'https' in source else 'http')
                
                response = requests.get(source, timeout=10)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch from {source}: Status {response.status_code}")
                    continue
                
                proxy_text = response.text
                
                # Process the proxy list - formats vary by source
                proxy_list = []
                
                # Simple IP:PORT format
                for line in proxy_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try IP:PORT format
                    if ':' in line:
                        try:
                            host, port = line.split(':', 1)
                            port = int(port)
                            proxy_list.append({
                                "host": host,
                                "port": port,
                                "protocol": protocol
                            })
                        except ValueError:
                            pass
                
                # Add the proxies
                if proxy_list:
                    start_count = len(self.proxy_manager.proxies)
                    self.proxy_manager.add_proxies_from_list(proxy_list)
                    new_count = len(self.proxy_manager.proxies) - start_count
                    new_proxies += new_count
                    logger.info(f"Added {new_count} new proxies from {source}")
                else:
                    logger.warning(f"No proxies found in {source}")
                
            except Exception as e:
                logger.error(f"Error fetching from {source}: {e}")
        
        return new_proxies
    
    def refresh_all_proxies(self) -> int:
        """
        Refresh proxies from all sources.
        
        Returns:
            Total number of new proxies added
        """
        total_new = 0
        for source_type in self.proxy_sources.keys():
            new_count = self.fetch_from_sources(source_type)
            total_new += new_count
            
        logger.info(f"Added {total_new} new proxies from all sources")
        return total_new
