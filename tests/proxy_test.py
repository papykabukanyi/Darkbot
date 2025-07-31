"""
Proxy testing script to verify the proxy rotation and CAPTCHA detection.
"""

import argparse
import logging
import json
import os
from utils.proxy_manager import ProxyManager, ProxiedRequester, ProxySourceManager, CaptchaSolver

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ProxyTest")

def test_proxy_rotation():
    """Test proxy rotation functionality."""
    print("Testing proxy rotation...")
    
    # Initialize the proxy manager
    proxy_manager = ProxyManager(proxy_list_path="test_proxies.json")
    
    # Check if we have proxies already
    if len(proxy_manager.proxies) == 0:
        print("No proxies found. Let's fetch some free ones...")
        proxy_source_manager = ProxySourceManager(proxy_manager)
        new_count = proxy_source_manager.refresh_all_proxies()
        print(f"Added {new_count} new proxies")
    
    # If we still don't have proxies, add a few test ones
    if len(proxy_manager.proxies) == 0:
        test_proxies = [
            {
                "host": "199.19.224.3",
                "port": 80,
                "protocol": "http"
            },
            {
                "host": "104.129.202.128",
                "port": 8800,
                "protocol": "http"
            },
            {
                "host": "149.5.152.34",
                "port": 3128,
                "protocol": "http"
            }
        ]
        proxy_manager.add_proxies_from_list(test_proxies)
        print(f"Added {len(test_proxies)} test proxies")
    
    print(f"Current proxies: {len(proxy_manager.proxies)}")
    
    # Create the requester
    requester = ProxiedRequester(proxy_manager=proxy_manager)
    
    # Test multiple requests to verify rotation
    test_urls = [
        "https://httpbin.org/ip",
        "https://api.ipify.org",
        "https://ip.me"
    ]
    
    print("\nSending test requests...")
    for i, url in enumerate(test_urls):
        print(f"\nRequest {i+1} to {url}:")
        response = requester.get(url)
        
        if response:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:100]}...")
            
            # Verify the proxy is working by showing the IP
            print(f"Proxy used: {requester.current_proxy['id'] if requester.current_proxy else 'None'}")
            
            # Force rotation for testing
            requester._rotate_session()
        else:
            print(f"Request failed")

def test_captcha_detection():
    """Test CAPTCHA detection functionality."""
    print("\nTesting CAPTCHA detection...")
    
    captcha_solver = CaptchaSolver()
    
    # Create a test HTML with a CAPTCHA
    captcha_html = """
    <html>
    <head><title>Security Check</title></head>
    <body>
        <h1>Please verify you are human</h1>
        <div class="g-recaptcha" data-sitekey="6LdkF9UeAAAAAMBl_xq"></div>
        <script src="https://www.google.com/recaptcha/api.js"></script>
    </body>
    </html>
    """
    
    # Create a mock response
    class MockResponse:
        def __init__(self, text):
            self.text = text
    
    mock_response = MockResponse(captcha_html)
    
    # Test CAPTCHA detection
    is_captcha, captcha_type = captcha_solver.detect_captcha(mock_response)
    
    print(f"CAPTCHA detected: {is_captcha}")
    print(f"CAPTCHA type: {captcha_type}")

def save_proxies_from_arguments(args):
    """Save proxies from command line arguments."""
    proxy_list = []
    
    for proxy_str in args.proxies:
        try:
            # Parse proxy string (format: protocol://host:port or host:port)
            if '://' in proxy_str:
                protocol, rest = proxy_str.split('://', 1)
                host, port = rest.split(':', 1)
            else:
                host, port = proxy_str.split(':', 1)
                protocol = 'http'
            
            port = int(port)
            
            proxy_list.append({
                "host": host,
                "port": port,
                "protocol": protocol
            })
        except Exception as e:
            logger.error(f"Invalid proxy format: {proxy_str} - {e}")
    
    if proxy_list:
        # Save proxies
        proxy_manager = ProxyManager(proxy_list_path=args.output)
        proxy_manager.add_proxies_from_list(proxy_list)
        logger.info(f"Saved {len(proxy_list)} proxies to {args.output}")
    else:
        logger.warning("No valid proxies provided")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Proxy Manager Testing and Configuration')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test proxy rotation')
    test_parser.add_argument('--captcha', action='store_true', help='Test CAPTCHA detection')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch proxies from free sources')
    fetch_parser.add_argument('--output', '-o', type=str, default='proxies.json',
                             help='Output JSON file for proxies')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add proxies from command line')
    add_parser.add_argument('--proxies', '-p', type=str, nargs='+', required=True,
                           help='List of proxies (format: protocol://host:port or host:port)')
    add_parser.add_argument('--output', '-o', type=str, default='proxies.json',
                           help='Output JSON file for proxies')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        test_proxy_rotation()
        if args.captcha:
            test_captcha_detection()
    
    elif args.command == 'fetch':
        proxy_manager = ProxyManager(proxy_list_path=args.output)
        source_manager = ProxySourceManager(proxy_manager)
        total = source_manager.refresh_all_proxies()
        print(f"Added {total} new proxies to {args.output}")
    
    elif args.command == 'add':
        save_proxies_from_arguments(args)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
