"""
Site verification script to test which sites are currently working
"""
import os
import sys
import logging
import argparse
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('site_verification.log')
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from config import load_config
from utils.site_verifier import verify_sites_parallel
from utils.user_agents import get_headers

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Darkbot Site Verification Tool')
    parser.add_argument('--sites', nargs='+',
                      help='Specific sites to verify (default: all configured sites)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose output')
    parser.add_argument('--output', type=str, default='site_status.txt',
                      help='Output file for verification results')
    parser.add_argument('--max-workers', type=int, default=5,
                      help='Maximum number of parallel workers')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_config()
    site_configs = config.get('sites', {})
    
    # If specific sites were provided, filter the site_configs
    if args.sites:
        site_configs = {name: cfg for name, cfg in site_configs.items() if name in args.sites}
    
    if not site_configs:
        logger.error("No sites found in configuration. Please check config.py")
        return
    
    logger.info(f"Starting verification of {len(site_configs)} sites")
    
    # Create a dictionary of site names and URLs
    sites_to_verify = {name: cfg['url'] for name, cfg in site_configs.items()}
    
    start_time = time.time()
    # Verify sites in parallel
    results = verify_sites_parallel(sites_to_verify, max_workers=args.max_workers)
    end_time = time.time()
    
    # Process and display results
    working_sites = []
    failing_sites = []
    
    for name, info in results.items():
        if info['available']:
            working_sites.append(name)
            status = "✅ AVAILABLE"
        else:
            failing_sites.append(name)
            status = "❌ UNAVAILABLE"
        
        logger.info(f"{status} - {name} ({info['url']}) - "
                   f"Status: {info['status_code']} - "
                   f"Response time: {info['response_time']}s")
    
    # Summary
    logger.info("\nSUMMARY:")
    logger.info(f"Total sites checked: {len(results)}")
    logger.info(f"Working sites: {len(working_sites)}")
    logger.info(f"Failing sites: {len(failing_sites)}")
    logger.info(f"Total verification time: {end_time - start_time:.2f} seconds")
    
    # Write results to file
    with open(args.output, 'w') as f:
        f.write(f"# Darkbot Site Verification Results\n")
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Working Sites\n\n")
        for site in sorted(working_sites):
            f.write(f"- {site} ({results[site]['url']})\n")
        
        f.write("\n## Unavailable Sites\n\n")
        for site in sorted(failing_sites):
            f.write(f"- {site} ({results[site]['url']})\n")
        
        f.write("\n## Raw Results\n\n")
        f.write("| Site | URL | Status | Response Code | Response Time |\n")
        f.write("|------|-----|--------|---------------|---------------|\n")
        for name, info in sorted(results.items()):
            status = "Available" if info['available'] else "Unavailable"
            f.write(f"| {name} | {info['url']} | {status} | {info['status_code']} | {info['response_time']}s |\n")
    
    logger.info(f"Results written to {args.output}")
    
    # Return codes for potential scripting
    if failing_sites:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
