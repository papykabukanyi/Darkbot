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

# Import the fallback proxy system directly to avoid circular imports later
try:
    from utils.fallback_proxy import FallbackProxySystem
except ImportError:
    FallbackProxySystem = None
    logging.getLogger("ProxyManager").warning("FallbackProxySystem couldn't be imported")

# Set up logging
logger = logging.getLogger("ProxyManager")

class ProxyManager:
    """
    Manages a pool of proxies for rotating IPs and avoiding bans.
    Includes fallback mechanisms when no external proxies are available.
    """
    
    def __init__(self, proxy_list_path: str = None, max_fails: int = 3, 
                 ban_time: int = 1800, verify_proxies: bool = True,
                 use_fallback: bool = True):
        """
        Initialize the proxy manager.
        
        Args:
            proxy_list_path: Path to JSON file with proxies
            max_fails: Maximum number of failures before marking a proxy as banned
            ban_time: Time in seconds to ban a proxy (default: 30 minutes)
            verify_proxies: Whether to verify proxies on initialization
            use_fallback: Whether to use the fallback system when no proxies are available
        """
        self.proxy_list_path = proxy_list_path or "proxies.json"
        self.max_fails = max_fails
        self.ban_time = ban_time
        self.use_fallback = use_fallback
        self.fallback_system = None
        
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
            
        # If we have no proxies and fallback is enabled, initialize the fallback system
        if use_fallback and (not self.proxies or self.get_working_proxies_count() == 0):
            try:
                if FallbackProxySystem:
                    self.fallback_system = FallbackProxySystem()
                    logger.info("Initialized fallback proxy system")
                else:
                    logger.error("FallbackProxySystem is not available")
                    self.fallback_system = None
            except Exception as e:
                logger.error(f"Error initializing fallback proxy system: {e}")
                self.fallback_system = None
    
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
            Proxy dictionary for requests or empty dict if this is a direct connection
        """
        # For fallback systems that use direct connections (just user agent rotation)
        if proxy.get("is_fallback") and not proxy.get("port"):
            logger.info("Using direct connection with user agent rotation")
            return {}
            
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
            logger.info("No external proxies available")
            # If fallback system is available, use it
            if self.use_fallback and self.fallback_system:
                # Initialize Tor if not already running
                # Try to use Tor if available
                tor_available = False
                if not self.fallback_system.tor_enabled:
                    if self.fallback_system.setup_tor_proxy():
                        logger.info("Using Tor fallback proxy")
                        tor_available = True
                
                # For direct connection fallback (when Tor isn't available)
                if self.fallback_system.tor_enabled and not self.fallback_system.tor_port:
                    logger.info("Using direct connection with user agent rotation as fallback")
                    return {
                        "id": "fallback_direct",
                        "host": None,
                        "port": None,
                        "protocol": "direct",
                        "is_fallback": True,
                        "last_used": time.time(),
                        "fail_count": 0,
                        "banned_until": None
                    }
                
                # Create a "virtual" proxy entry for the fallback system with Tor
                return {
                    "id": "fallback_proxy",
                    "host": "127.0.0.1",
                    "port": self.fallback_system.tor_port or 9050,
                    "protocol": "http" if not tor_available else "socks5",
                    "is_fallback": True,
                    "last_used": time.time(),
                    "fail_count": 0,
                    "banned_until": None
                }
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
        
        # If fallback system is available, use it as last resort
        if self.use_fallback and self.fallback_system:
            # Initialize Tor if not already running
            if not self.fallback_system.tor_enabled:
                if self.fallback_system.setup_tor_proxy():
                    logger.info("All proxies banned, using Tor fallback proxy")
                    return {
                        "id": "fallback_proxy",
                        "host": "127.0.0.1",
                        "port": self.fallback_system.tor_port or 9050,
                        "protocol": "socks5",
                        "is_fallback": True,
                        "last_used": time.time(),
                        "fail_count": 0,
                        "banned_until": None
                    }
            elif self.fallback_system.tor_enabled:
                # Tor is already enabled, rotate its identity and use it
                self.fallback_system.rotate_tor_identity()
                return {
                    "id": "fallback_proxy",
                    "host": "127.0.0.1",
                    "port": self.fallback_system.tor_port or 9050,
                    "protocol": "socks5",
                    "is_fallback": True,
                    "last_used": time.time(),
                    "fail_count": 0,
                    "banned_until": None
                }
                
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
        Handles fallback system when no external proxies are available.
        
        Args:
            session: Requests session to update
            
        Returns:
            The proxy that was assigned or None
        """
        proxy = self.get_next_proxy()
        if proxy:
            proxy_dict = self.get_proxy_dict(proxy)
            session.proxies.update(proxy_dict)
            
            # If this is a fallback proxy, also update the User-Agent to avoid detection
            if proxy.get("is_fallback") and self.fallback_system:
                random_ua = self.fallback_system.get_random_user_agent()
                session.headers.update({"User-Agent": random_ua})
                logger.info(f"Using fallback proxy with randomized User-Agent")
                
        return proxy


class CaptchaSolver:
    """
    Detect and handle various CAPTCHA types on sneaker websites.
    This is a passive CAPTCHA avoidance system rather than active solver.
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
        
        # Avoidance strategies
        self.avoidance_strategies = {
            'default': {
                'cooldown': 300,  # 5 minutes cooldown for the IP
                'retry_delay': 30,
                'max_retries': 3
            },
            'recaptcha': {
                'cooldown': 1800,  # 30 minutes cooldown for the IP
                'retry_delay': 120,
                'max_retries': 2
            },
            'cloudflare': {
                'cooldown': 1200,  # 20 minutes cooldown for the IP
                'retry_delay': 60,
                'max_retries': 3
            }
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
        
        # Check for status codes often used for rate limiting
        if response.status_code in [403, 429]:
            return True, 'rate_limited'
            
        return False, ''
    
    def handle_captcha(self, response: requests.Response, session: requests.Session, url: str) -> bool:
        """
        Handle a detected CAPTCHA challenge using avoidance strategies.
        
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
        
        logger.warning(f"CAPTCHA/Rate-limiting detected ({captcha_type}) on {url}")
        
        # Get avoidance strategy for this CAPTCHA type
        strategy = self.avoidance_strategies.get(captcha_type, self.avoidance_strategies['default'])
        
        # Log the detection
        try:
            captcha_dir = "captcha_samples"
            os.makedirs(captcha_dir, exist_ok=True)
            
            # Save minimal info about the CAPTCHA - don't save full HTML which could cause issues
            timestamp = int(time.time())
            filename = f"{captcha_dir}/captcha_{captcha_type}_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Type: {captcha_type}\n")
                f.write(f"Status Code: {response.status_code}\n")
                f.write(f"Headers: {dict(response.headers)}\n")
                f.write(f"Content Length: {len(response.text)}\n")
                # Save a small snippet (first 500 chars) to diagnose
                f.write(f"Content Preview: {response.text[:500]}...\n")
            
            logger.info(f"Saved CAPTCHA detection info to {filename}")
        except Exception as e:
            logger.error(f"Error saving CAPTCHA info: {e}")
        
        # Apply cooldown to this domain
        domain = url.split('//')[-1].split('/')[0]
        logger.info(f"Applying {strategy['cooldown']} second cooldown for domain {domain}")
        
        # Return False to indicate we couldn't handle the CAPTCHA and need to rotate IP
        return False


class ProxiedRequester:
    """
    HTTP client that uses proxy rotation and handles CAPTCHAs.
    This class implements various strategies to avoid detection.
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
        
        # Try to get user agents from fallback system if available
        if self.proxy_manager and self.proxy_manager.fallback_system:
            self.user_agents = self.proxy_manager.fallback_system.user_agents
        else:
            # More realistic and recent user agents
            self.user_agents = [
                # Windows Chrome
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                # Windows Firefox
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
                # Windows Edge
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.58',
                # Mac Safari
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.1 Safari/605.1.15',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
                # Mac Chrome
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                # Mac Firefox
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0',
                # iPhone/iPad
                'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
            ]
        
        # Track visited domains to implement per-domain delays
        self.domain_last_visited = {}
        self.domain_visit_count = {}
        self.domain_jitter = {}  # Random jitter to add to each domain
        
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
                'Upgrade-Insecure-Requests': '1',
                # Common browser headers to appear more legitimate
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1',  # Do Not Track
                'Cache-Control': 'max-age=0'
            })
        
        return session
    
    def _rotate_session(self) -> None:
        """Create a new session with a different user agent and proxy."""
        self.session = self._create_session()
        self.current_proxy = self.proxy_manager.rotate_proxy_for_session(self.session)
    
    def _get_domain(self, url: str) -> str:
        """Extract the domain from a URL."""
        try:
            domain = url.split('//')[-1].split('/')[0]
            return domain
        except:
            return url
    
    def _apply_domain_specific_delay(self, domain: str) -> None:
        """
        Apply domain-specific delays to mimic human behavior and avoid rate limiting.
        Different websites have different rate limits and detection systems.
        """
        current_time = time.time()
        
        # Initialize domain stats if not seen before
        if domain not in self.domain_last_visited:
            self.domain_last_visited[domain] = 0
            self.domain_visit_count[domain] = 0
            # Random jitter between 1-3 seconds unique to each domain
            self.domain_jitter[domain] = random.uniform(1, 3)
        
        # Calculate how long since we last visited this domain
        time_since_last_visit = current_time - self.domain_last_visited[domain]
        
        # Determine appropriate delay for this domain
        # Base delay increases with visit count to simulate natural browsing
        visit_count = self.domain_visit_count[domain]
        base_delay = 5.0  # Start with 5 second baseline
        
        if visit_count > 30:
            # After 30 requests to the same domain, increase delay significantly
            base_delay = 15.0
        elif visit_count > 15:
            # After 15 requests, increase delay moderately
            base_delay = 10.0
        elif visit_count > 5:
            # After 5 requests, increase delay slightly
            base_delay = 7.5
            
        # Add domain-specific jitter for less predictable timing
        total_delay = base_delay + self.domain_jitter[domain]
        
        # Only wait if we haven't waited long enough already
        if time_since_last_visit < total_delay:
            sleep_time = total_delay - time_since_last_visit
            logger.debug(f"Applying {sleep_time:.2f}s delay for domain {domain} (visit #{visit_count+1})")
            time.sleep(sleep_time)
        
        # Update domain stats
        self.domain_last_visited[domain] = time.time()
        self.domain_visit_count[domain] += 1
        
        # Slightly modify the jitter for next time (human behavior is not consistent)
        self.domain_jitter[domain] = min(5.0, max(1.0, self.domain_jitter[domain] + random.uniform(-0.5, 0.5)))
    
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
        domain = self._get_domain(url)
        retries = 0
        backoff = 2  # Start with a 2-second backoff
        
        # Apply domain-specific delay before first attempt
        self._apply_domain_specific_delay(domain)
        
        while retries <= max_retries:
            # If we don't have a proxy, get one
            if not self.current_proxy:
                self._rotate_session()
                if not self.current_proxy:
                    # If no proxy is available and no fallback is used,
                    # we might want to wait a bit before trying again
                    if self.proxy_manager.fallback_system is None:
                        logger.error("No working proxies available and no fallback system configured")
                        time.sleep(5)  # Wait before retry without proxy
                    else:
                        # If we're using fallback but still didn't get a proxy, log the issue
                        logger.warning("Using fallback proxy system, but no proxy was assigned")
            
            # Add random query parameter to bypass caching
            if '?' in url:
                request_url = f"{url}&_nocache={int(time.time() * 1000)}"
            else:
                request_url = f"{url}?_nocache={int(time.time() * 1000)}"
            
            try:
                # Add a random delay to simulate human behavior (0.1-1.5 seconds)
                time.sleep(random.uniform(0.1, 1.5))
                
                # Randomize the timeout slightly for less predictable behavior
                timeout = random.uniform(25, 35)
                
                # Add a referer if not provided to look more legitimate
                if 'headers' not in kwargs:
                    kwargs['headers'] = {}
                
                if 'Referer' not in kwargs['headers']:
                    # Use a common referer like Google
                    kwargs['headers']['Referer'] = 'https://www.google.com/search?q=' + domain
                
                start_time = time.time()
                response = self.session.request(method, request_url, timeout=timeout, **kwargs)
                elapsed = time.time() - start_time
                
                # Check for CAPTCHA if enabled
                if self.captcha_detection and self.captcha_solver:
                    is_captcha, captcha_type = self.captcha_solver.detect_captcha(response)
                    if is_captcha:
                        logger.warning(f"CAPTCHA detected ({captcha_type}) on {url}")
                        
                        # Mark this proxy as problematic
                        if self.current_proxy:
                            self.proxy_manager.mark_proxy_failure(self.current_proxy)
                            
                        # Rotate session for next try
                        self._rotate_session()
                        
                        # Get the avoidance strategy
                        strategy = self.captcha_solver.avoidance_strategies.get(
                            captcha_type, 
                            self.captcha_solver.avoidance_strategies['default']
                        )
                        
                        retries += 1
                        retry_delay = strategy['retry_delay']
                        if retries <= max_retries:
                            logger.info(f"Waiting {retry_delay}s before retry {retries}/{max_retries}")
                            time.sleep(retry_delay)
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
                # Use exponential backoff with some randomness
                jitter = random.uniform(0.5, 1.5)
                wait_time = backoff * jitter
                logger.info(f"Retrying in {wait_time:.2f}s (attempt {retries}/{max_retries})")
                time.sleep(wait_time)
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
