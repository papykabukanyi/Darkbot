"""
Site verification utility to test and validate site scrapers
"""
import logging
import time
import requests
from urllib.parse import urlparse
import concurrent.futures

from utils.user_agents import get_headers
from utils.rate_limiting import rate_limiter

logger = logging.getLogger(__name__)

def check_site_availability(url, timeout=10):
    """Check if a site is available via simple HTTP request
    
    Args:
        url (str): The URL to check
        timeout (int): Request timeout in seconds
        
    Returns:
        tuple: (success, status_code, response_time)
    """
    domain = urlparse(url).netloc
    rate_limiter.wait(domain)
    
    start_time = time.time()
    try:
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=timeout)
        response_time = time.time() - start_time
        
        return (
            response.status_code == 200,
            response.status_code,
            round(response_time, 2)
        )
    except requests.exceptions.RequestException as e:
        response_time = time.time() - start_time
        logger.error(f"Failed to check {url}: {e}")
        return False, None, round(response_time, 2)

def verify_sites(sites):
    """Verify a list of sites and return status information
    
    Args:
        sites (dict): Dictionary of site names and URLs
        
    Returns:
        dict: Status information for each site
    """
    results = {}
    
    for name, url in sites.items():
        logger.info(f"Checking site: {name} ({url})")
        success, status_code, response_time = check_site_availability(url)
        
        results[name] = {
            'url': url,
            'available': success,
            'status_code': status_code,
            'response_time': response_time
        }
        
        logger.info(f"Site {name}: {'Available' if success else 'Unavailable'} "
                   f"(Status: {status_code}, Time: {response_time}s)")
    
    return results

def verify_sites_parallel(sites, max_workers=4):
    """Verify multiple sites in parallel
    
    Args:
        sites (dict): Dictionary of site names and URLs
        max_workers (int): Maximum number of parallel workers
        
    Returns:
        dict: Status information for each site
    """
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all site checks
        future_to_site = {
            executor.submit(check_site_availability, url): (name, url)
            for name, url in sites.items()
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_site):
            name, url = future_to_site[future]
            try:
                success, status_code, response_time = future.result()
                
                results[name] = {
                    'url': url,
                    'available': success,
                    'status_code': status_code,
                    'response_time': response_time
                }
                
                logger.info(f"Site {name}: {'Available' if success else 'Unavailable'} "
                           f"(Status: {status_code}, Time: {response_time}s)")
            except Exception as e:
                logger.error(f"Error checking {name} ({url}): {e}")
                results[name] = {
                    'url': url,
                    'available': False,
                    'status_code': None,
                    'response_time': None,
                    'error': str(e)
                }
    
    return results

def get_working_sites(sites, parallel=True):
    """Get a list of working sites from the provided sites dictionary
    
    Args:
        sites (dict): Dictionary of site names and URLs
        parallel (bool): Whether to check sites in parallel
        
    Returns:
        list: List of names of working sites
    """
    if parallel:
        results = verify_sites_parallel(sites)
    else:
        results = verify_sites(sites)
    
    # Return the names of sites that are available
    return [name for name, info in results.items() if info['available']]
