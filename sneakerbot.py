"""
Streamlined SneakerBot - Focuses on KicksOnFire and price checking across multiple sources
"""

import os
import sys
import logging
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Import configuration
from config import (
    setup_logging, send_email, ENABLE_NOTIFICATIONS,
    KICKSONFIRE_CONFIG, STOCKX_CONFIG, PROFIT_CHECKER_CONFIG
)

# Import custom scrapers
from scrapers.kicksonfire import KicksOnFireScraper
from utils.profit_checker import ProfitChecker
from price_sources.stockx import StockXAdapter

# Set up logging
logger = setup_logging('sneakerbot')

# Import custom scrapers
from scrapers.kicksonfire import KicksOnFireScraper
from utils.profit_checker import ProfitChecker
from price_sources.stockx import StockXAdapter

# Set up logging
logger = setup_logging('sneakerbot')

def setup_directories():
    """Create necessary directories if they don't exist."""
    dirs = [
        os.path.join(BASE_DIR, "data"),
        os.path.join(BASE_DIR, "logs"),
        os.path.join(BASE_DIR, "data", "cache")
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")

def send_notification_email(profitable_releases):
    """Send email notification about profitable releases."""
    if not profitable_releases:
        logger.info("No profitable releases to notify about")
        return False
    
    logger.info(f"Sending email notification about {len(profitable_releases)} profitable releases")
    
    # Create email subject
    subject = f"SneakerBot: Found {len(profitable_releases)} Profitable Releases!"
    
    # Create email body with HTML formatting
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .release {{ margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; }}
            .title {{ font-size: 18px; font-weight: bold; color: #333; }}
            .info {{ margin: 5px 0; }}
            .profit {{ font-weight: bold; color: green; }}
            .details {{ color: #666; }}
            img {{ max-width: 150px; height: auto; float: right; margin: 0 0 10px 10px; }}
        </style>
    </head>
    <body>
        <h1>SneakerBot Found Profitable Releases!</h1>
        <p>The following releases have good profit potential:</p>
        
    """
    
    # Add each release to the email
    for release in profitable_releases:
        title = release.get('title', 'Unknown Release')
        price = release.get('price', 'Unknown Price')
        sku = release.get('sku', 'Unknown SKU')
        brand = release.get('brand', 'Unknown Brand')
        release_date = release.get('release_date', 'Unknown Date')
        image_url = release.get('image_url', '')
        url = release.get('url', '')
        
        # Get profit info
        profit_info = release.get('price_check_results', {}).get('profit', {})
        profit_amount = profit_info.get('profit_amount', 0)
        profit_percentage = profit_info.get('profit_percentage', 0)
        retail_price = release.get('price_check_results', {}).get('retail_price', 0)
        market_price = release.get('price_check_results', {}).get('market_price', 0)
        
        body += f"""
        <div class="release">
            {'<img src="' + image_url + '" alt="' + title + '">' if image_url else ''}
            <div class="title">{'<a href="' + url + '">' if url else ''}{title}{('</a>' if url else '')}</div>
            <div class="info"><strong>Brand:</strong> {brand}</div>
            <div class="info"><strong>SKU:</strong> {sku}</div>
            <div class="info"><strong>Release Date:</strong> {release_date}</div>
            <div class="info"><strong>Retail Price:</strong> ${retail_price}</div>
            <div class="info"><strong>Market Price:</strong> ${market_price}</div>
            <div class="profit"><strong>Profit:</strong> ${profit_amount:.2f} ({profit_percentage:.2f}%)</div>
            <div class="details">This release has good profit potential based on current market prices.</div>
        </div>
        """
    
    body += """
        <p>Happy Hunting!</p>
        <p>- SneakerBot</p>
    </body>
    </html>
    """
    
    # Send the email
    return send_email(subject, body)

def get_kicksonfire_releases():
    """Get new releases from KicksOnFire."""
    logger.info("Getting releases from KicksOnFire")
    
    # Create and use the scraper
    with KicksOnFireScraper(KICKSONFIRE_CONFIG) as scraper:
        # Get new releases
        new_releases = scraper.get_new_releases(limit=20)
        logger.info(f"Found {len(new_releases)} new releases")
        
        # Get upcoming releases
        upcoming_releases = scraper.get_upcoming_releases(limit=20)
        logger.info(f"Found {len(upcoming_releases)} upcoming releases")
        
        # Combine all releases
        all_releases = new_releases + upcoming_releases
        
    return all_releases

def check_profit_potential(releases):
    """Check profit potential for releases using StockX."""
    if not releases:
        logger.warning("No releases to check for profit")
        return []
    
    logger.info(f"Checking profit potential for {len(releases)} releases")
    
    # Create profit checker
    profit_checker = ProfitChecker(PROFIT_CHECKER_CONFIG)
    
    # Check profit for all releases
    releases_with_profit = profit_checker.check_prices_batch(releases)
    
    # Filter profitable releases
    profitable_releases = [
        release for release in releases_with_profit
        if release.get('price_check_results', {}).get('profit', {}).get('is_profitable', False)
    ]
    
    logger.info(f"Found {len(profitable_releases)} profitable releases")
    return profitable_releases

def save_results(releases, filename=None):
    """Save releases to a JSON file."""
    if not releases:
        logger.warning("No releases to save")
        return
    
    # Create data directory if it doesn't exist
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(data_dir, f"releases_{timestamp}.json")
    
    try:
        with open(filename, 'w') as f:
            json.dump(releases, f, indent=2)
        logger.info(f"Saved {len(releases)} releases to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving releases: {e}")
        return None

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Streamlined SneakerBot for finding profitable opportunities")
    parser.add_argument("--save", dest="save_file", help="Save results to specified file")
    parser.add_argument("--check-profit", dest="check_profit", action="store_true", help="Check profit potential")
    parser.add_argument("--notify", dest="notify", action="store_true", help="Send notifications for profitable releases")
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    logger.info("Starting Streamlined SneakerBot")
    
    try:
        # Get releases from KicksOnFire
        releases = get_kicksonfire_releases()
        
        if not releases:
            logger.error("No releases found. Exiting.")
            return 1
        
        # Save all releases
        all_releases_file = os.path.join(BASE_DIR, "data", f"all_releases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        save_results(releases, all_releases_file)
        
        # Check profit potential if requested
        if args.check_profit:
            profitable_releases = check_profit_potential(releases)
            
            # Save profitable releases
            if profitable_releases:
                profitable_file = args.save_file or os.path.join(BASE_DIR, "data", f"profitable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                save_results(profitable_releases, profitable_file)
                
                # Send notifications if requested
                if args.notify and ENABLE_NOTIFICATIONS:
                    logger.info("Sending email notifications about profitable releases...")
                    if send_notification_email(profitable_releases):
                        logger.info("Email notification sent successfully")
                    else:
                        logger.warning("Failed to send email notification")
        
        logger.info("SneakerBot run completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Error running SneakerBot: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
