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
from config_fixed import (
    setup_logging, send_email, ENABLE_NOTIFICATIONS,
    KICKSONFIRE_CONFIG, STOCKX_CONFIG, PROFIT_CHECKER_CONFIG
)

# Import custom modules
from scrapers.kicksonfire import KicksOnFireScraper
from utils.profit_checker import ProfitChecker 
from utils.database import SneakerDatabase
from utils.stockx_price_checker import StockXPriceChecker
from utils.stockx_adapter import StockXAdapter
from utils.detail_handler import SneakerDetailHandler

# Set up logging
logger = setup_logging('sneakerbot')

def setup_directories():
    """Create necessary directories if they don't exist."""
    dirs = [
        os.path.join(BASE_DIR, "data"),
        os.path.join(BASE_DIR, "logs"),
        os.path.join(BASE_DIR, "data", "cache"),
        os.path.join(BASE_DIR, "templates")
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
            .comparison-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            .comparison-table th {{ background-color: #f5f5f5; text-align: left; padding: 8px; border: 1px solid #ddd; }}
            .comparison-table td {{ padding: 8px; border: 1px solid #ddd; }}
            .price-source {{ font-weight: bold; }}
            .no-data {{ color: #999; font-style: italic; }}
            .btn {{ display: inline-block; padding: 6px 12px; background-color: #0275d8; color: white; text-decoration: none; border-radius: 4px; }}
            .btn:hover {{ background-color: #0262b7; }}
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
        profit_amount = profit_info.get('amount', 0)
        profit_percentage = profit_info.get('percentage', 0)
        retail_price = release.get('price_check_results', {}).get('retail_price', 0)
        market_price = release.get('price_check_results', {}).get('market_price', 0)
        
        # Get detail URL for dynamic access
        detail_url = f"http://localhost:8000/detail/{sku}"
        
        body += f"""
        <div class="release">
            {'<img src="' + image_url + '" alt="' + title + '">' if image_url else ''}
            <div class="title">{'<a href="' + url + '">' if url else ''}{title}{('</a>' if url else '')}</div>
            <div class="info"><strong>Brand:</strong> {brand}</div>
            <div class="info"><strong>SKU:</strong> {sku}</div>
            <div class="info"><strong>Release Date:</strong> {release_date}</div>
            <div class="info"><strong>Retail Price:</strong> ${retail_price:.2f}</div>
            <div class="info"><strong>Market Price:</strong> ${market_price:.2f}</div>
            <div class="profit"><strong>Profit:</strong> ${profit_amount:.2f} ({profit_percentage:.2f}%)</div>
            <div class="details">This release has good profit potential based on current market prices.</div>
            <p><a href="{url}" class="btn" target="_blank">View Original</a> <a href="{detail_url}" class="btn" target="_blank">View Detailed Analysis</a></p>
        """
        
        # Add price comparison table if available
        comparison_data = release.get('price_check_results', {}).get('price_comparison', {})
        if comparison_data and comparison_data.get('price_results'):
            price_results = comparison_data.get('price_results', [])
            if price_results:
                body += """
                <h3>Price Comparison Across Sites</h3>
                <table class="comparison-table">
                    <tr>
                        <th>Marketplace</th>
                        <th>Price</th>
                        <th>Profit</th>
                        <th>ROI %</th>
                        <th>Link</th>
                    </tr>
                """
                
                for result in price_results:
                    site_name = result.get('site_name', 'Unknown')
                    price = result.get('price')
                    status = result.get('status')
                    site_url = result.get('url', '#')
                    
                    if status == 'success' and price is not None:
                        site_profit = price - float(retail_price)
                        roi_percent = (site_profit / float(retail_price)) * 100 if float(retail_price) > 0 else 0
                        
                        body += f"""
                        <tr>
                            <td class="price-source">{site_name}</td>
                            <td>${price:.2f}</td>
                            <td>${site_profit:.2f}</td>
                            <td>{roi_percent:.1f}%</td>
                            <td><a href="{site_url}" target="_blank" class="btn">Visit</a></td>
                        </tr>
                        """
                    else:
                        error_msg = result.get('error', 'No data available')
                        body += f"""
                        <tr>
                            <td class="price-source">{site_name}</td>
                            <td colspan="4" class="no-data">{error_msg}</td>
                        </tr>
                        """
                
                body += "</table>"
        
        body += "</div>"
    
    body += """
        <p>Happy Hunting!</p>
        <p>- SneakerBot</p>
    </body>
    </html>
    """
    
    # Send the email
    return send_email(subject, body)

def send_new_releases_email(releases):
    """Send email notification about new releases found."""
    if not releases:
        return False
        
    subject = f"🔥 {len(releases)} New Sneaker Releases Found on KicksOnFire!"
    
    body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .release {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .brand {{ font-weight: bold; color: #333; }}
        .title {{ font-size: 16px; margin: 5px 0; }}
        .price {{ color: green; font-weight: bold; }}
        .date {{ color: #666; }}
        .btn {{ display: inline-block; padding: 6px 12px; background-color: #0275d8; color: white; text-decoration: none; border-radius: 4px; margin-right: 5px; }}
        .btn:hover {{ background-color: #0262b7; }}
    </style>
</head>
<body>
    <h2>🔥 New Sneaker Releases Detected!</h2>
    <p>Found {len(releases)} new releases on KicksOnFire:</p>
    
    <div class="releases">
"""
    
    for release in releases:
        brand = release.get('brand', 'Unknown')
        title = release.get('title', 'Unknown Title')
        price = release.get('retail_price')
        sku = release.get('sku', '')
        release_date = release.get('release_date', 'TBA')
        url = release.get('url', '#')
        
        price_text = f"${price:.2f}" if price else "Price TBA"
        
        # Get detail URL for dynamic access
        detail_url = f"http://localhost:8000/detail/{sku}"
        
        body += f"""
        <div class="release">
            <div class="brand">{brand}</div>
            <div class="title">{title}</div>
            <div class="price">Retail Price: {price_text}</div>
            <div class="date">Release Date: {release_date}</div>
            <p>
                <a href="{url}" class="btn" target="_blank">View Original</a>
                <a href="{detail_url}" class="btn" target="_blank">View Detailed Analysis</a>
            </p>
        </div>
"""
    
    body += """
    </div>
    
    <p><strong>💡 Tip:</strong> Check these releases for profit potential on StockX and other resale platforms!</p>
    
    <p>Happy hunting! 🚀</p>
</body>
</html>
"""
    
    logger.info(f"Sending email notification about {len(releases)} new releases")
    return send_email(subject, body)

def get_kicksonfire_releases():
    """Get new releases from KicksOnFire."""
    logger.info("Getting releases from KicksOnFire")
    
    # Create and use the scraper
    with KicksOnFireScraper(KICKSONFIRE_CONFIG) as scraper:
        # Use the enhanced scrape_site method that handles pagination
        all_releases = scraper.scrape_site()
        logger.info(f"Found {len(all_releases)} total releases")
        
    return all_releases

def check_profit_potential(releases):
    """Check profit potential for releases using multiple sources."""
    if not releases:
        logger.warning("No releases to check for profit")
        return []
    
    logger.info(f"Checking profit potential for {len(releases)} releases")
    
    # Create profit checker
    profit_checker = ProfitChecker(PROFIT_CHECKER_CONFIG)
    
    # Use multi-site price checker for enhanced reporting
    logger.info("Using multi-site price checker for enhanced price comparison")
    
    # Process each release to add multi-site price data
    for release in releases:
        if not release.get('sku'):
            logger.warning(f"Skipping release without SKU: {release.get('title', 'Unknown')}")
            continue
        
        if not release.get('retail_price'):
            logger.warning(f"Skipping release without retail price: {release.get('title', 'Unknown')}")
            continue
        
        try:
            stockx_checker = StockXPriceChecker()
            comparison_report = stockx_checker.generate_price_comparison_report(
                release.get('title'), 
                release.get('retail_price'), 
                release.get('sku')
            )
            
            # Add comparison data to release
            if 'price_check_results' not in release:
                release['price_check_results'] = {}
            
            release['price_check_results']['price_comparison'] = comparison_report
            
            # Update market price and profit based on highest price found
            price_results = comparison_report.get('price_results', [])
            valid_results = [r for r in price_results if r.get('status') == 'success' and r.get('price') is not None]
            
            if valid_results:
                # Find the highest price
                highest_price_result = max(valid_results, key=lambda x: x.get('price', 0))
                market_price = highest_price_result.get('price', 0)
                site_name = highest_price_result.get('site_name', 'Unknown')
                
                # Update the price check results
                release['price_check_results']['market_price'] = market_price
                release['price_check_results']['best_price_source'] = site_name
                
                # Calculate profit
                retail_price = float(release.get('retail_price', 0))
                profit_amount = market_price - retail_price
                profit_percentage = (profit_amount / retail_price * 100) if retail_price > 0 else 0
                
                # Update profit information
                release['price_check_results']['profit'] = {
                    'amount': profit_amount,
                    'percentage': profit_percentage,
                    'is_profitable': profit_amount > 0
                }
                
                release['price_check_results']['status'] = 'success'
                logger.info(f"Multi-site price check completed for {release.get('title')}")
        except Exception as e:
            logger.error(f"Error using multi-site price checker for {release.get('title')}: {e}")
    
    # Check profit for all releases (this will fill in any missing data)
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

def generate_detail_pages(releases):
    """Generate detailed HTML pages for releases."""
    if not releases:
        logger.warning("No releases to generate detail pages for")
        return {}
    
    logger.info(f"Generating detail pages for {len(releases)} releases")
    
    # Create detail handler and start the server
    detail_handler = SneakerDetailHandler(db=SneakerDatabase())
    
    # Start the server if it's not already running
    if not detail_handler.is_server_running:
        detail_handler.start_detail_server()
        logger.info(f"Detail server started on port {detail_handler.port}")
    
    # Generate detail pages
    output_dir = os.path.join(BASE_DIR, "data", "detail_pages")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    result = detail_handler.generate_detail_pages_batch(releases, output_dir)
    logger.info(f"Generated {len(result)} detail pages")
    
    # Return the server information along with the pages
    result['server_info'] = {
        'port': detail_handler.port,
        'base_url': f"http://localhost:{detail_handler.port}",
        'is_running': detail_handler.is_server_running
    }
    
    return result

def main():
    """Main function that runs continuously until manually stopped."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Streamlined SneakerBot for finding profitable opportunities")
    parser.add_argument("--save", dest="save_file", help="Save results to specified file")
    parser.add_argument("--check-profit", dest="check_profit", action="store_true", help="Check profit potential")
    parser.add_argument("--notify", dest="notify", action="store_true", help="Send notifications for profitable releases")
    parser.add_argument("--interval", dest="interval", type=int, default=30, help="Check interval in minutes (default: 30)")
    parser.add_argument("--run-once", dest="run_once", action="store_true", help="Run once and exit")
    parser.add_argument("--details", dest="generate_details", action="store_true", help="Generate detailed HTML pages for sneakers")
    args = parser.parse_args()
    
    # Setup directories
    setup_directories()
    
    logger.info("Starting Streamlined SneakerBot in continuous mode")
    
    # Initialize database
    db = SneakerDatabase()
    
    # Initialize detail handler and start server
    detail_handler = SneakerDetailHandler(db=db)
    detail_handler.start_detail_server()
    logger.info(f"Detail server started on port {detail_handler.port}")
    
    # Convert interval to seconds
    check_interval = args.interval * 60
    
    # Set default flags for continuous mode
    if not args.run_once:
        args.check_profit = True  # Always check profit in continuous mode
        args.notify = True  # Always send notifications in continuous mode
    
    # Run continuously until stopped
    run_count = 0
    while True:
        run_count += 1
        logger.info(f"Starting run #{run_count}")
        
        try:
            # Get releases from KicksOnFire's main page
            releases = get_kicksonfire_releases()
            
            if not releases:
                logger.error("No releases found. Check network connection and URL validity.")
                logger.info("Retrying with identical URL...")
                
                # The main URL is already set in config_fixed.py
                # Just retry the request with additional delay
                time.sleep(3)  # Add a short delay before retrying
                releases = get_kicksonfire_releases()
                
                if not releases:
                    logger.error("All attempts to fetch releases failed. Waiting for next run.")
                    if args.run_once:
                        return 1
                    time.sleep(check_interval)
                    continue
            
            # Save all releases to database
            new_releases_count = db.save_releases(releases)
            logger.info(f"Saved {new_releases_count} new releases to database")
            
            # Send email notification about new releases found
            if new_releases_count > 0 and ENABLE_NOTIFICATIONS and args.notify:
                send_new_releases_email(releases[:10])  # Send info about first 10 releases
            
            # Save all releases
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            all_releases_file = os.path.join(BASE_DIR, "data", f"all_releases_{timestamp}.json")
            save_results(releases, all_releases_file)
            
            # Check profit potential
            if args.check_profit:
                profitable_releases = check_profit_potential(releases)
                
                # Update database with market prices
                for release in profitable_releases:
                    market_price = release.get('price_check_results', {}).get('market_price')
                    profit_info = release.get('price_check_results', {}).get('profit', {})
                    profit_potential = profit_info.get('amount')
                    
                    if market_price and profit_potential:
                        db.update_market_data(
                            release['title'], 
                            release['source'], 
                            market_price, 
                            profit_potential
                        )
                
                # Generate detail pages if requested
                if args.generate_details:
                    detail_pages = generate_detail_pages(profitable_releases)
                    logger.info(f"Generated {len(detail_pages)} detail pages")
                
                # Save profitable releases
                if profitable_releases:
                    profitable_file = args.save_file or os.path.join(BASE_DIR, "data", f"profitable_{timestamp}.json")
                    save_results(profitable_releases, profitable_file)
                    
                    # Send notifications about profitable releases
                    if args.notify and ENABLE_NOTIFICATIONS:
                        logger.info("Sending email notifications about profitable releases...")
                        retry_count = 3
                        email_sent = False
                        
                        for attempt in range(retry_count):
                            if send_notification_email(profitable_releases):
                                logger.info("Email notification sent successfully")
                                email_sent = True
                                break
                            else:
                                logger.warning(f"Failed to send email notification (attempt {attempt+1}/{retry_count})")
                                time.sleep(5)  # Wait before retrying
                        
                        if not email_sent:
                            logger.error("All attempts to send email notification failed")
                            
                    logger.info(f"Found {len(profitable_releases)} profitable releases!")
                else:
                    logger.info("No profitable releases found at this time.")
            else:
                logger.info("Skipping profit check. Use --check-profit to analyze profit potential.")
            
            logger.info(f"SneakerBot run #{run_count} completed successfully")
            
            # Exit if we're only supposed to run once
            if args.run_once:
                return 0
                
            # Otherwise wait for the next interval
            logger.info(f"Waiting {args.interval} minutes until next check...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("SneakerBot manually stopped")
            return 0
        except Exception as e:
            logger.error(f"Error running SneakerBot: {e}")
            if args.run_once:
                return 1
            logger.info(f"Waiting {args.interval} minutes until next attempt...")
            time.sleep(check_interval)

if __name__ == "__main__":
    sys.exit(main())
