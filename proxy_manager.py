"""
Proxy initialization and management script.
"""

import argparse
import logging
import json
import os
import sys
import time

from utils.proxy_manager import ProxyManager, ProxiedRequester, ProxySourceManager, CaptchaSolver
from config import PROXY_CONFIG, USE_PROXY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ProxyManager")

def initialize_proxy_system():
    """Initialize the proxy system using configuration."""
    if not USE_PROXY:
        logger.warning("Proxy system is disabled in config. Enable USE_PROXY to use proxies.")
        return None, None
        
    proxy_file = PROXY_CONFIG.get('proxy_file', 'proxies.json')
    max_fails = PROXY_CONFIG.get('max_fails', 3)
    ban_time = PROXY_CONFIG.get('ban_time', 1800)
    verify_on_startup = PROXY_CONFIG.get('verify_on_startup', True)
    
    # Initialize proxy manager
    proxy_manager = ProxyManager(
        proxy_list_path=proxy_file,
        max_fails=max_fails,
        ban_time=ban_time,
        verify_proxies=verify_on_startup
    )
    
    # Check if we have any proxies
    working_proxies = proxy_manager.get_working_proxies_count()
    logger.info(f"Found {working_proxies} working proxies")
    
    # If auto-fetch is enabled and we don't have working proxies, try to fetch some
    if working_proxies == 0 and PROXY_CONFIG.get('auto_fetch_free', True):
        logger.info("No working proxies found, fetching free proxies...")
        source_manager = ProxySourceManager(proxy_manager)
        new_proxies = source_manager.refresh_all_proxies()
        logger.info(f"Added {new_proxies} new proxies from free sources")
        
        # Verify the new proxies
        if verify_on_startup and new_proxies > 0:
            proxy_manager._verify_all_proxies()
            working_proxies = proxy_manager.get_working_proxies_count()
            logger.info(f"After verification: {working_proxies} working proxies")
    
    # Create a requester with the proxy manager
    requester = ProxiedRequester(
        proxy_manager=proxy_manager,
        rotate_user_agents=True,
        captcha_detection=PROXY_CONFIG.get('captcha_detection', True)
    )
    
    return proxy_manager, requester

def add_proxies_from_file(file_path):
    """Add proxies from a text file (one proxy per line)."""
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} not found")
        return 0
        
    proxy_manager = ProxyManager(proxy_list_path=PROXY_CONFIG.get('proxy_file', 'proxies.json'))
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        added = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                # Parse proxy format: [protocol://][username:password@]host:port
                protocol = 'http'
                username = None
                password = None
                host = None
                port = None
                
                if '://' in line:
                    protocol, line = line.split('://', 1)
                
                if '@' in line:
                    auth, line = line.split('@', 1)
                    username, password = auth.split(':', 1) if ':' in auth else (auth, '')
                
                if ':' in line:
                    host, port = line.split(':', 1)
                    port = int(port)
                else:
                    host = line
                    port = 80 if protocol == 'http' else 443
                
                proxy_manager.add_proxy(
                    host=host,
                    port=port,
                    protocol=protocol,
                    username=username,
                    password=password
                )
                added += 1
            except Exception as e:
                logger.error(f"Error parsing proxy {line}: {e}")
        
        logger.info(f"Added {added} proxies from {file_path}")
        return added
    except Exception as e:
        logger.error(f"Error reading proxies from {file_path}: {e}")
        return 0

def test_proxies():
    """Test all proxies and print statistics."""
    proxy_manager = ProxyManager(proxy_list_path=PROXY_CONFIG.get('proxy_file', 'proxies.json'))
    
    total = len(proxy_manager.proxies)
    if total == 0:
        logger.warning("No proxies found")
        return
    
    logger.info(f"Testing {total} proxies...")
    proxy_manager._verify_all_proxies()
    
    # Count working proxies
    working = proxy_manager.get_working_proxies_count()
    banned = sum(1 for p in proxy_manager.proxies if p.get('banned_until') and p.get('banned_until') > time.time())
    
    logger.info(f"Proxy statistics:")
    logger.info(f"  Total proxies: {total}")
    logger.info(f"  Working proxies: {working}")
    logger.info(f"  Banned proxies: {banned}")
    logger.info(f"  Success rate: {working / total * 100:.1f}%")
    
    # Display the fastest proxies
    working_proxies = [p for p in proxy_manager.proxies 
                      if p.get('avg_response_time') is not None and 
                         (not p.get('banned_until') or p.get('banned_until') <= time.time())]
    
    if working_proxies:
        fastest = sorted(working_proxies, key=lambda p: p.get('avg_response_time', 9999))[:5]
        logger.info("Fastest proxies:")
        for i, proxy in enumerate(fastest, 1):
            logger.info(f"  {i}. {proxy['protocol']}://{proxy['host']}:{proxy['port']} - "
                        f"{proxy.get('avg_response_time', 0):.2f}s")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Proxy System Management")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize the proxy system')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add proxies from a file')
    add_parser.add_argument('file', help='File containing proxies (one per line)')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch free proxies')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test all proxies')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        proxy_manager, requester = initialize_proxy_system()
        if proxy_manager:
            logger.info(f"Proxy system initialized with {proxy_manager.get_working_proxies_count()} working proxies")
        else:
            logger.warning("Proxy system initialization failed or is disabled")
    
    elif args.command == 'add':
        count = add_proxies_from_file(args.file)
        logger.info(f"Added {count} proxies")
    
    elif args.command == 'fetch':
        proxy_manager = ProxyManager(proxy_list_path=PROXY_CONFIG.get('proxy_file', 'proxies.json'))
        source_manager = ProxySourceManager(proxy_manager)
        count = source_manager.refresh_all_proxies()
        logger.info(f"Fetched {count} new proxies")
    
    elif args.command == 'test':
        test_proxies()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
