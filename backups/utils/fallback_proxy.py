"""
Built-in fallback IP rotation system using Tor and local proxies.
This is used when no external proxies are configured.
"""

import logging
import subprocess
import socket
import time
import os
import sys
import random
import requests
import platform
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger("FallbackProxySystem")

class FallbackProxySystem:
    """
    Fallback system that provides basic IP rotation without external services.
    Uses different strategies depending on the operating system and available tools.
    """
    
    def __init__(self):
        """Initialize the fallback proxy system."""
        self.os_type = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
        self.tor_enabled = False
        self.tor_port = None
        self.tor_process = None
        self.vpn_enabled = False
        self.user_agents = []
        self.load_user_agents()
        
    def load_user_agents(self):
        """Load a large set of user agents from file or use defaults."""
        # Try to load from file
        ua_file = os.path.join(os.path.dirname(__file__), 'user_agents.txt')
        
        if os.path.exists(ua_file):
            try:
                with open(ua_file, 'r') as f:
                    self.user_agents = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(self.user_agents)} user agents from file")
            except Exception as e:
                logger.error(f"Error loading user agents from file: {e}")
        
        # If no file or loading failed, use a default set
        if not self.user_agents:
            self.user_agents = [
                # Latest Chrome versions
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                
                # Latest Firefox versions
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0',
                'Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/116.0',
                
                # Latest Edge versions
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
                
                # Latest Safari versions
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.1 Safari/605.1.15',
                
                # Mobile browsers
                'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36',
            ]
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent from the available list."""
        return random.choice(self.user_agents)
        
    def check_tor_installation(self) -> bool:
        """Check if Tor is installed on the system."""
        try:
            if self.os_type == 'Windows':
                # Check for Tor Browser or Tor service
                tor_paths = [
                    r'C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe',
                    r'C:\Program Files (x86)\Tor Browser\Browser\TorBrowser\Tor\tor.exe',
                    r'C:\Tor\tor.exe'
                ]
                
                for path in tor_paths:
                    if os.path.exists(path):
                        return True
                        
                # Check if Tor service is running
                try:
                    result = subprocess.run(['sc', 'query', 'tor'], 
                                          capture_output=True, text=True, check=False)
                    return 'RUNNING' in result.stdout
                except:
                    pass
                    
                return False
                
            elif self.os_type in ['Linux', 'Darwin']:
                # Check if Tor is in PATH
                result = subprocess.run(['which', 'tor'], 
                                       capture_output=True, text=True, check=False)
                return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking Tor installation: {e}")
        
        return False
    
    def setup_tor_proxy(self) -> bool:
        """
        Set up Tor as a SOCKS proxy for IP rotation.
        Returns True if successful, False otherwise.
        """
        if not self.check_tor_installation():
            logger.warning("Tor is not installed on this system")
            # Set a direct connection but with randomized user agent
            self.tor_port = None
            # Mark as "enabled" anyway so we use the fallback system with rotating user agents
            self.tor_enabled = True
            return True
        
        try:
            # Find an available port
            self.tor_port = self._find_available_port(9050, 9150)
            
            if not self.tor_port:
                logger.error("Could not find available port for Tor")
                return False
            
            # Start Tor with the selected port
            if self.os_type == 'Windows':
                # Try to find Tor executable
                tor_paths = [
                    r'C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe',
                    r'C:\Program Files (x86)\Tor Browser\Browser\TorBrowser\Tor\tor.exe',
                    r'C:\Tor\tor.exe'
                ]
                
                tor_exe = None
                for path in tor_paths:
                    if os.path.exists(path):
                        tor_exe = path
                        break
                
                if not tor_exe:
                    logger.error("Tor executable not found")
                    return False
                
                # Start Tor process
                cmd = [tor_exe, '--SocksPort', str(self.tor_port)]
                self.tor_process = subprocess.Popen(cmd, 
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE)
                
            elif self.os_type in ['Linux', 'Darwin']:
                # Start Tor process on Linux/macOS
                cmd = ['tor', '--SocksPort', str(self.tor_port)]
                self.tor_process = subprocess.Popen(cmd,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE)
            
            # Wait for Tor to start up
            time.sleep(5)
            
            # Check if Tor is running
            if self.tor_process.poll() is not None:
                error = self.tor_process.stderr.read().decode('utf-8')
                logger.error(f"Tor failed to start: {error}")
                return False
                
            logger.info(f"Tor started successfully on port {self.tor_port}")
            self.tor_enabled = True
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Tor proxy: {e}")
            return False
    
    def _find_available_port(self, start_port: int, end_port: int) -> Optional[int]:
        """Find an available port in the given range."""
        for port in range(start_port, end_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except:
                continue
        return None
    
    def get_tor_proxy_dict(self) -> Dict[str, str]:
        """Get the proxy dictionary for using with requests."""
        if not self.tor_enabled or not self.tor_port:
            return {}
            
        proxy_url = f'socks5://127.0.0.1:{self.tor_port}'
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def rotate_tor_identity(self) -> bool:
        """
        Request a new Tor identity to change IP.
        Returns True if successful, False otherwise.
        """
        if not self.tor_enabled:
            logger.warning("Tor is not enabled")
            return False
            
        try:
            # Restart Tor process to get a new identity
            if self.tor_process:
                self.tor_process.terminate()
                time.sleep(2)
                
            # Set up Tor proxy again
            return self.setup_tor_proxy()
            
        except Exception as e:
            logger.error(f"Error rotating Tor identity: {e}")
            return False
    
    def create_ip_rotator_session(self) -> requests.Session:
        """
        Create a requests session with IP rotation capabilities.
        """
        session = requests.Session()
        
        # Set a random user agent
        session.headers.update({
            'User-Agent': self.get_random_user_agent(),
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
        
        # Add Tor proxy if enabled
        if self.tor_enabled:
            proxy_dict = self.get_tor_proxy_dict()
            session.proxies.update(proxy_dict)
        
        return session
    
    def check_current_ip(self) -> str:
        """Check the current public IP address."""
        ip_services = [
            'https://api.ipify.org',
            'https://ip.me',
            'https://icanhazip.com',
            'https://ifconfig.co/ip'
        ]
        
        session = self.create_ip_rotator_session()
        
        for url in ip_services:
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text.strip()
            except:
                continue
                
        return "Unknown"
    
    def cleanup(self):
        """Clean up resources."""
        if self.tor_process:
            self.tor_process.terminate()
            self.tor_enabled = False
