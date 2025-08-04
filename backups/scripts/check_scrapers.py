#!/usr/bin/env python
"""
Scraper health check utility for Darkbot
"""

import sys
import os
import logging
import time
from typing import Dict, List
import argparse
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ScraperHealthCheck")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.sites import SNEAKER_SITES
from scrapers.factory import get_scraper_for_site

class ScraperHealthCheck:
    """Utility to check the health of scrapers"""
    
    def __init__(self, sites: List[str] = None):
        """
        Initialize the health check utility
        
        Args:
            sites: List of site names to check, or None for all sites
        """
        self.sites = sites or list(SNEAKER_SITES.keys())
        self.results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_status': 'pass',
            'sites': {}
        }
        
    def run_checks(self):
        """Run health checks on all specified sites"""
        for site_name in self.sites:
            if site_name not in SNEAKER_SITES:
                logger.warning(f"Site {site_name} not found in configuration")
                continue
                
            site_config = SNEAKER_SITES[site_name]
            logger.info(f"Running health check for {site_name}...")
            
            site_result = {
                'name': site_name,
                'url': site_config.get('url', 'N/A'),
                'status': 'pass',
                'products_found': 0,
                'response_time': 0,
                'errors': []
            }
            
            try:
                # Get the scraper for this site
                start_time = time.time()
                scraper = get_scraper_for_site(site_name, site_config)
                
                with scraper as s:
                    # Try to get products from the sale page
                    products = s.search_products(category='sale')
                    
                end_time = time.time()
                response_time = round(end_time - start_time, 2)
                
                # Record results
                site_result['response_time'] = response_time
                site_result['products_found'] = len(products)
                
                # Check if we found any products
                if len(products) == 0:
                    site_result['status'] = 'warn'
                    site_result['errors'].append('No products found')
                
                # Check response time thresholds
                if response_time > 30:
                    site_result['status'] = 'warn'
                    site_result['errors'].append(f'Slow response time: {response_time}s')
                
                logger.info(f"{site_name}: Found {len(products)} products in {response_time}s")
                
            except Exception as e:
                logger.error(f"Error checking {site_name}: {e}")
                site_result['status'] = 'fail'
                site_result['errors'].append(str(e))
                self.results['overall_status'] = 'fail'
            
            self.results['sites'][site_name] = site_result
            
            # Add a small delay between sites to be nice
            time.sleep(2)
    
    def print_report(self):
        """Print a formatted report of the health check results"""
        print("\n" + "=" * 80)
        print(f"SCRAPER HEALTH CHECK REPORT - {self.results['timestamp']}")
        print("=" * 80)
        
        # Overall status
        status_color = '\033[92m' if self.results['overall_status'] == 'pass' else '\033[91m'
        print(f"Overall Status: {status_color}{self.results['overall_status'].upper()}\033[0m\n")
        
        # Site details
        print(f"{'SITE':<15} {'STATUS':<10} {'PRODUCTS':<10} {'RESPONSE TIME':<15} {'ERRORS'}")
        print("-" * 80)
        
        for site_name, site_data in self.results['sites'].items():
            status = site_data['status']
            status_display = status.upper()
            
            if status == 'pass':
                status_color = '\033[92m'  # Green
            elif status == 'warn':
                status_color = '\033[93m'  # Yellow
            else:
                status_color = '\033[91m'  # Red
                
            errors = '; '.join(site_data['errors']) if site_data['errors'] else 'None'
            
            print(f"{site_name:<15} {status_color}{status_display:<10}\033[0m {site_data['products_found']:<10} {site_data['response_time']}s{' '*11} {errors}")
        
        print("=" * 80)
    
    def save_report(self, filename: str = 'scraper_health_check.json'):
        """Save the report to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Report saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Check the health of sneaker scrapers')
    parser.add_argument('--sites', nargs='+', help='List of sites to check (default: all)')
    parser.add_argument('--output', help='Output file for JSON report')
    
    args = parser.parse_args()
    
    health_check = ScraperHealthCheck(sites=args.sites)
    health_check.run_checks()
    health_check.print_report()
    
    if args.output:
        health_check.save_report(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        health_check.save_report(f'scraper_health_check_{timestamp}.json')

if __name__ == '__main__':
    main()
