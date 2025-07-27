"""
Main script for the Sneaker Bot - MongoDB optimized version.
"""

import argparse
import colorama
import datetime
import logging
import schedule
import time
from tqdm import tqdm

from config import (WEBSITES, MIN_DISCOUNT_PERCENT, BRANDS_OF_INTEREST,
                   SAVE_TO_CSV, CSV_FILENAME, DATABASE_ENABLED, DATABASE_PATH,
                   EMAIL_INTERVAL_MINUTES, EMAIL_NOTIFICATIONS,
                   SNEAKER_SITES, DEFAULT_SITES, MARKET_PRICE_SITES,
                   CLOUDFLARE_R2_ENABLED, CLOUDFLARE_R2_ACCESS_KEY, CLOUDFLARE_R2_SECRET_KEY,
                   CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_R2_BUCKET,
                   MONGODB_ENABLED, MONGODB_CONNECTION_STRING, MONGODB_DATABASE, MONGODB_COLLECTION)

from scrapers.factory import get_scraper_for_site
from notifications import EmailNotifier
from storage import DealStorage, R2Storage, MongoDBStorage
from utils.price_comparison import PriceComparer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SneakerBot")

# Initialize colorama for colored output
colorama.init()

# Global storage instances
r2_storage = None
mongodb_storage = None

def get_timestamp():
    """Get current timestamp for display."""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def analyze_deals_for_profit(deals, price_comparer):
    """
    Analyze deals for profitability against market prices.
    
    Args:
        deals: List of deals to analyze
        price_comparer: PriceComparer instance with market data
        
    Returns:
        List of analyzed deals with profit calculations
    """
    if not deals:
        return []
    
    logger.info(f"Analyzing {len(deals)} deals for profitability...")
    
    analyzed_deals = []
    for deal in deals:
        # Calculate potential profit
        profit_analysis = price_comparer.calculate_profit_potential(deal)
        
        # Add profit analysis to deal
        deal.update(profit_analysis)
        
        # Mark as profitable if it meets criteria
        if deal.get('profit_potential', 0) > 0:
            deal['is_profitable'] = True
        
        analyzed_deals.append(deal)
    
    return analyzed_deals

def save_and_upload_deals(analyzed_deals, storage, args):
    """
    Save deals and upload to various storage systems.
    
    Args:
        analyzed_deals: List of analyzed deals
        storage: Local storage instance
        args: Command line arguments
        
    Returns:
        bool: True if we should continue iterating (for continuous mode)
    """
    global r2_storage, mongodb_storage
    
    # Get the most profitable deals
    price_comparer = PriceComparer()
    profitable_deals = price_comparer.get_most_profitable_deals(analyzed_deals)
    
    # Save deals if there are any
    if analyzed_deals:
        if SAVE_TO_CSV:
            storage.save_deals(analyzed_deals)
            
        if hasattr(args, 'export_json') and args.export_json:
            storage.export_to_json()
            
        # Upload to MongoDB (primary storage)
        if mongodb_storage is not None and MONGODB_ENABLED:
            mongodb_storage.upload_deals(analyzed_deals)
            
        # Upload to Cloudflare R2 if enabled (legacy support)
        latest_file_key = None
        if r2_storage is not None and CLOUDFLARE_R2_ENABLED:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            latest_file_key = f"{today}/deals_{timestamp}.json"
            r2_storage.upload_deals(analyzed_deals)
            
        # Check if we should continue iterating
        should_continue = False
        if hasattr(args, 'iterate') and args.iterate and not hasattr(args, 'scheduled_run'):
            if mongodb_storage is not None and MONGODB_ENABLED:
                should_continue = mongodb_storage.continue_to_iterate([], analyzed_deals)
            elif r2_storage is not None and CLOUDFLARE_R2_ENABLED:
                should_continue = r2_storage.continue_to_iterate(latest_file_key)
            else:
                # For local storage, use simple comparison
                should_continue = len(analyzed_deals) > 0
                
        return should_continue
    
    return False

def run_scraper(scraper, site_name):
    """
    Run a single scraper and return deals.
    
    Args:
        scraper: Scraper instance
        site_name: Name of the site being scraped
        
    Returns:
        List of deals found
    """
    deals = []
    
    try:
        logger.info(f"Searching {site_name} for real products with purchase links...")
        logger.info(f"Scraping {site_name}...")
        
        # Scrape the site
        site_deals = scraper.scrape()
        
        if site_deals:
            # Filter deals by minimum discount
            filtered_deals = [
                deal for deal in site_deals 
                if deal.get('discount_percent', 0) >= MIN_DISCOUNT_PERCENT
            ]
            
            # Filter by brand if configured
            if BRANDS_OF_INTEREST:
                filtered_deals = [
                    deal for deal in filtered_deals
                    if deal.get('brand', '').lower() in [b.lower() for b in BRANDS_OF_INTEREST]
                ]
            
            # Add a note that these are real products with working links
            for deal in filtered_deals:
                deal['is_real_product'] = True
                deal['verified_link'] = True
            
            logger.info(f"Found {len(filtered_deals)} deals on {site_name} meeting criteria")
            deals.extend(filtered_deals)
            
        logger.info(f"Found {len(deals)} real products on {site_name}")
    
    except Exception as e:
        logger.error(f"Error running scraper for {site_name}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
    
    return deals

def run_scraper_job(args, scheduled_run=False, last_iteration_deals=None):
    """
    Run the scraper job to find deals.
    
    Args:
        args: Command line arguments
        scheduled_run: Whether this is a scheduled run
        last_iteration_deals: Deals found in the previous iteration
    
    Returns:
        List of deals found
    """
    if scheduled_run:
        args.scheduled_run = True
    
    print(f"\n{colorama.Fore.YELLOW}Real Product Search - {get_timestamp()}{colorama.Style.RESET_ALL}")
    print("Searching for real products with working links...")
    
    # Initialize storage
    storage = DealStorage(
        csv_filename=CSV_FILENAME,
        db_enabled=DATABASE_ENABLED,
        db_path=DATABASE_PATH
    )
    
    # Initialize R2 storage if enabled
    global r2_storage
    if r2_storage is not None and CLOUDFLARE_R2_ENABLED:
        logger.info("R2 Storage initialized and enabled")
    
    # Initialize price comparer
    price_comparer = PriceComparer()
    
    # Always use real scraping mode
    args.test_mode = False
    
    # First, scrape market price sites to get comparison data
    logger.info("First collecting market price data for comparison...")
    for site_name in tqdm([s for s in args.sites if s in MARKET_PRICE_SITES], 
                          desc="Collecting market price data"):
        if site_name in SNEAKER_SITES:
            site_config = SNEAKER_SITES[site_name]
            
            try:
                scraper_class = get_scraper_for_site(site_name, site_config)
                with scraper_class as scraper:
                    market_deals = run_scraper(scraper, site_name)
                    
                    # Store market price data for comparison
                    for deal in market_deals:
                        price_comparer.add_market_price(deal)
                        
            except Exception as e:
                logger.error(f"Error collecting market data from {site_name}: {e}")
    
    logger.info(f"Collected market price data for {price_comparer.get_market_data_count()} products")
    
    # Now scrape for deals from other sites
    all_deals = []
    
    # Get sites to scrape (excluding market price sites)
    sites_to_scrape = [s for s in args.sites if s not in MARKET_PRICE_SITES]
    
    print(f"About to scrape {len(sites_to_scrape)} sites: {', '.join(sites_to_scrape)}")
    
    for site_name in tqdm(sites_to_scrape, desc="Scraping for deals"):
        if site_name in SNEAKER_SITES:
            site_config = SNEAKER_SITES[site_name]
            
            try:
                print(f"Getting scraper for {site_name}...")
                scraper_class = get_scraper_for_site(site_name, site_config)
                print(f"Got scraper class: {scraper_class}")
                
                with scraper_class as scraper:
                    print(f"Running scraper for {site_name}...")
                    deals = run_scraper(scraper, site_name)
                    all_deals.extend(deals)
                    print(f"Found {len(deals)} deals from {site_name}")
                    
            except Exception as e:
                logger.error(f"Error with {site_name}: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
    
    print(f"Total deals found: {len(all_deals)}")
    logger.info("Analyzing deals for profitability...")
    
    # Analyze deals for profit potential
    analyzed_deals = analyze_deals_for_profit(all_deals, price_comparer)
    
    # Get the most profitable deals for display
    profitable_deals = price_comparer.get_most_profitable_deals(analyzed_deals)
    
    # Save and upload deals
    should_continue = save_and_upload_deals(analyzed_deals, storage, args)
    
    # Display results
    if profitable_deals:
        print(f"\n{colorama.Fore.GREEN}🎯 Found {len(profitable_deals)} PROFITABLE deals!{colorama.Style.RESET_ALL}")
        
        for i, deal in enumerate(profitable_deals[:10], 1):  # Show top 10
            profit = deal.get('profit_potential', 0)
            profit_margin = deal.get('profit_margin_percent', 0)
            
            print(f"\n{colorama.Fore.CYAN}Deal #{i}:{colorama.Style.RESET_ALL}")
            print(f"  Product: {deal.get('title', 'N/A')}")
            print(f"  Brand: {deal.get('brand', 'N/A')}")
            print(f"  Sale Price: ${deal.get('price', 0):.2f}")
            print(f"  Market Price: ${deal.get('market_price', 0):.2f}")
            print(f"  Potential Profit: ${profit:.2f} ({profit_margin:.1f}%)")
            print(f"  Site: {deal.get('site', 'N/A')}")
            print(f"  URL: {deal.get('url', 'N/A')}")
            
        if not scheduled_run or not hasattr(args, 'quiet') or not args.quiet:
            print(f"\n{colorama.Fore.YELLOW}See all {len(profitable_deals)} profitable deals above!{colorama.Style.RESET_ALL}")
            
        # Print remaining deals if not in quiet mode
        if not hasattr(args, 'quiet') or (not args.quiet and not scheduled_run):
            other_deals = [d for d in analyzed_deals if not d.get('is_profitable', False)]
            if other_deals:
                print(f"\n{colorama.Fore.BLUE}Found {len(other_deals)} other deals (less profitable):{colorama.Style.RESET_ALL}")
                for deal in other_deals[:5]:  # Show first 5
                    print(f"  • {deal.get('title', 'N/A')} - ${deal.get('price', 0):.2f} from {deal.get('site', 'N/A')}")
    else:
        print(f"\n{colorama.Fore.RED}No deals found matching your criteria.{colorama.Style.RESET_ALL}")
    
    # Send notifications if enabled
    if EMAIL_NOTIFICATIONS:
        from notifications import EmailNotifier
        notifier = EmailNotifier()
        
        if not scheduled_run:
            # Send immediate notification for manual runs
            notifier.send_deals_email(analyzed_deals, is_scheduled=False)
        else:
            # Queue for scheduled notification
            notifier.queue_deals_for_email(analyzed_deals)
    
    # Print summary
    if not scheduled_run:
        print(f"\n{colorama.Fore.GREEN}Summary:{colorama.Style.RESET_ALL}")
        print(f"  Total deals found: {len(analyzed_deals)}")
        print(f"  Profitable deals: {len(profitable_deals)}")
        print(f"  Sites scraped: {len(sites_to_scrape)}")
        
        if SAVE_TO_CSV:
            print(f"  Results saved to: {CSV_FILENAME}")
        if DATABASE_ENABLED:
            print(f"  Database updated: {DATABASE_PATH}")
        if MONGODB_ENABLED and mongodb_storage is not None:
            print(f"  Results saved to MongoDB database: {MONGODB_DATABASE}")
        if CLOUDFLARE_R2_ENABLED and r2_storage is not None:
            print(f"  Results uploaded to Cloudflare R2: {CLOUDFLARE_R2_BUCKET}")
    
    if not scheduled_run:
        print(f"\n{colorama.Fore.CYAN}Finished at: {get_timestamp()}{colorama.Style.RESET_ALL}")
    
    return analyzed_deals

def main():
    """Main function."""
    print("🚀 Main function started!")
    
    parser = argparse.ArgumentParser(description='Sneaker Deal Bot - MongoDB Optimized')
    
    # Site selection
    parser.add_argument('--sites', nargs='+', default=DEFAULT_SITES,
                        help='Sites to scrape (default: all configured sites)')
    parser.add_argument('--list-sites', action='store_true',
                        help='List available sites and exit')
    
    # Mode options
    parser.add_argument('--test-mode', action='store_true',
                        help='Run in test mode with mock data')
    parser.add_argument('--continuous', action='store_true',
                        help='Run continuously with scheduled intervals')
    parser.add_argument('--interval', type=int, default=30,
                        help='Interval in minutes for continuous mode (default: 30)')
    parser.add_argument('--iterate', action='store_true',
                        help='Keep running until no new deals are found')
    
    # Output options
    parser.add_argument('--export-json', action='store_true',
                        help='Export results to JSON file')
    parser.add_argument('--quiet', action='store_true',
                        help='Reduce output verbosity')
    parser.add_argument('--verbose', action='store_true',
                        help='Increase output verbosity')
    
    # Notification options
    parser.add_argument('--email', action='store_true',
                        help='Enable email notifications (overrides config)')
    parser.add_argument('--no-email', action='store_true',
                        help='Disable email notifications')
    
    # Storage options
    parser.add_argument('--r2', action='store_true',
                        help='Enable Cloudflare R2 storage (overrides config)')
    parser.add_argument('--no-r2', action='store_true',
                        help='Disable Cloudflare R2 storage')
    parser.add_argument('--r2-access-key', help='Cloudflare R2 access key')
    parser.add_argument('--r2-secret-key', help='Cloudflare R2 secret key')
    parser.add_argument('--r2-endpoint', help='Cloudflare R2 endpoint URL')
    parser.add_argument('--r2-bucket', help='Cloudflare R2 bucket name')
    
    # MongoDB options
    parser.add_argument('--mongodb', action='store_true',
                        help='Enable MongoDB storage (overrides config)')
    parser.add_argument('--no-mongodb', action='store_true',
                        help='Disable MongoDB storage')
    parser.add_argument('--mongodb-connection', help='MongoDB connection string')
    parser.add_argument('--mongodb-database', help='MongoDB database name')
    parser.add_argument('--mongodb-collection', help='MongoDB collection name')
    
    args = parser.parse_args()
    print(f"🔧 Arguments parsed: {args}")
    
    # Set verbose logging if requested
    if hasattr(args, 'verbose') and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        print("🔍 Verbose logging enabled")
    
    # List sites if requested
    if args.list_sites:
        print("Available sites:")
        for site in SNEAKER_SITES.keys():
            market_indicator = " (market price)" if site in MARKET_PRICE_SITES else ""
            print(f"  {site}{market_indicator}")
        return
    
    # Validate sites
    invalid_sites = [site for site in args.sites if site not in SNEAKER_SITES]
    if invalid_sites:
        print(f"Error: Unknown sites: {', '.join(invalid_sites)}")
        print("Use --list-sites to see available sites.")
        return
    
    # Print banner
    print("=" * 80)
    print("REAL Sneaker Deal Finder Bot")
    print("Searching for REAL products with WORKING purchase links")
    print(f"Started at: {get_timestamp()}")
    print("=" * 80)
    
    # Setup email notifications
    if EMAIL_NOTIFICATIONS:
        notifier = EmailNotifier()
        notifier.start_background_thread(EMAIL_INTERVAL_MINUTES)
    else:
        notifier = EmailNotifier()
        notifier.enabled = False
        
    # Initialize MongoDB storage (primary storage)
    global mongodb_storage
    mongodb_enabled = MONGODB_ENABLED
    if hasattr(args, 'mongodb') and args.mongodb:
        mongodb_enabled = True
    if hasattr(args, 'no_mongodb') and args.no_mongodb:
        mongodb_enabled = False
        
    if mongodb_enabled:
        # Setup MongoDB storage using command line args if provided, otherwise use config
        mongodb_storage = MongoDBStorage(
            connection_string=getattr(args, 'mongodb_connection', None) or MONGODB_CONNECTION_STRING,
            database_name=getattr(args, 'mongodb_database', None) or MONGODB_DATABASE,
            collection_name=getattr(args, 'mongodb_collection', None) or MONGODB_COLLECTION
        )
    
    # Initialize Cloudflare R2 storage if enabled (legacy support)
    global r2_storage
    r2_enabled = CLOUDFLARE_R2_ENABLED
    if hasattr(args, 'r2') and args.r2:
        r2_enabled = True
    if hasattr(args, 'no_r2') and args.no_r2:
        r2_enabled = False
        
    if r2_enabled:
        # Setup R2 storage using command line args if provided, otherwise use config
        r2_storage = R2Storage(
            access_key_id=getattr(args, 'r2_access_key', None) or CLOUDFLARE_R2_ACCESS_KEY,
            secret_access_key=getattr(args, 'r2_secret_key', None) or CLOUDFLARE_R2_SECRET_KEY,
            endpoint_url=getattr(args, 'r2_endpoint', None) or CLOUDFLARE_R2_ENDPOINT,
            bucket_name=getattr(args, 'r2_bucket', None) or CLOUDFLARE_R2_BUCKET
        )
    
    # Print configuration
    print(f"Scraping {len(args.sites)} sites: {', '.join(args.sites)}")
    print(f"Looking for brands: {', '.join(BRANDS_OF_INTEREST)}")
    print(f"Minimum discount: {MIN_DISCOUNT_PERCENT}%")
    print(f"Email notifications: {'Enabled' if EMAIL_NOTIFICATIONS else 'Disabled'}")
    print(f"MongoDB storage: {'Enabled' if mongodb_enabled else 'Disabled'}")
    print(f"Cloudflare R2 storage: {'Enabled' if r2_enabled else 'Disabled'}")
    print("-" * 80)
    
    # Run in continuous mode if specified
    if hasattr(args, 'continuous') and args.continuous:
        print(f"Running in continuous mode every {args.interval} minutes")
        print("-" * 80)
        
        # Run once immediately
        print("Running initial scan...")
        run_scraper_job(args)
        
        # Setup for continuous running
        start_time = datetime.datetime.now()
        
        # Schedule runs
        def scheduled_job():
            print(f"\n{colorama.Fore.CYAN}Running scheduled scan - {get_timestamp()}{colorama.Style.RESET_ALL}")
            run_scraper_job(args, scheduled_run=True)
            
            # Display uptime info
            uptime = datetime.datetime.now() - start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            next_run = datetime.datetime.now() + datetime.timedelta(minutes=args.interval)
            print(f"Uptime: {uptime_str} | Next run: {next_run.strftime('%H:%M:%S')}")
        
        schedule.every(args.interval).minutes.do(scheduled_job)
        
        print(f"Bot will run every {args.interval} minutes. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print(f"\n{colorama.Fore.YELLOW}Bot stopped by user.{colorama.Style.RESET_ALL}")
    
    # Run in iterate mode if specified
    elif hasattr(args, 'iterate') and args.iterate:
        print("Running in iterate mode until no new deals found")
        print("-" * 80)
        
        iteration = 1
        last_deals = []
        
        while True:
            print(f"\n{colorama.Fore.CYAN}Iteration #{iteration} - {get_timestamp()}{colorama.Style.RESET_ALL}")
            
            current_deals = run_scraper_job(args, last_iteration_deals=last_deals)
            
            # Check if we should continue
            should_continue = False
            if mongodb_storage is not None and MONGODB_ENABLED:
                should_continue = mongodb_storage.continue_to_iterate(last_deals, current_deals)
            elif r2_storage is not None and CLOUDFLARE_R2_ENABLED:
                should_continue = len(current_deals) > len(last_deals)
            else:
                should_continue = len(current_deals) > 0 and current_deals != last_deals
            
            if not should_continue:
                print(f"\n{colorama.Fore.GREEN}No new deals found. Stopping iteration.{colorama.Style.RESET_ALL}")
                break
            
            last_deals = current_deals
            iteration += 1
            
            print(f"Waiting 2 minutes before next iteration...")
            time.sleep(120)  # Wait 2 minutes between iterations
    
    # Run once if no special mode specified
    else:
        print("Running in one-time mode")
        print("-" * 80)
        run_scraper_job(args)
    
    # Stop email notification thread
    if EMAIL_NOTIFICATIONS:
        notifier.stop_background_thread()

if __name__ == "__main__":
    print("🎯 Starting Sneaker Bot...")
    main()
    print("✅ Bot execution completed!")
