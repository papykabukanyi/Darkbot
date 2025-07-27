"""
Simple test mode for the scraper to check if it's working properly.
"""

import sys
import logging
from utils import make_request, format_price, get_timestamp

def test_websites():
    """Test connections to all configured websites."""
    from config import WEBSITES
    
    print(f"Sneaker Bot Test Mode - {get_timestamp()}")
    print("Testing connections to configured websites:")
    print("-" * 60)
    
    results = {}
    
    for site_name, site_config in WEBSITES.items():
        url = site_config['url']
        print(f"Testing {site_name} - {url}...")
        
        try:
            response = make_request(url)
            
            if response and response.status_code == 200:
                content_length = len(response.text)
                results[site_name] = {
                    'status': 'Success',
                    'status_code': response.status_code,
                    'content_length': content_length
                }
                print(f"  ✅ Success: Status {response.status_code}, Content Length: {content_length}")
            else:
                status_code = response.status_code if response else 'N/A'
                results[site_name] = {
                    'status': 'Failed',
                    'status_code': status_code,
                }
                print(f"  ❌ Failed: Status {status_code}")
        
        except Exception as e:
            results[site_name] = {
                'status': 'Error',
                'error': str(e)
            }
            print(f"  ❌ Error: {e}")
    
    print("\nSummary:")
    success_count = sum(1 for r in results.values() if r['status'] == 'Success')
    print(f"Total sites: {len(results)}")
    print(f"Successful connections: {success_count}")
    print(f"Failed connections: {len(results) - success_count}")
    
    if success_count == 0:
        print("\n⚠️ No connections successful. Please check your internet connection and website URLs.")
        print("   Also verify that you're not being blocked or rate-limited.")
    
    return results

if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the tests
    results = test_websites()
    
    # Exit with appropriate status code
    success_count = sum(1 for r in results.values() if r['status'] == 'Success')
    sys.exit(0 if success_count > 0 else 1)
