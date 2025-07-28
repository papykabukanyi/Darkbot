"""
Script to run the bot focusing on Undefeated.com
"""

import sys
import os
import colorama
from datetime import datetime, timedelta
import argparse
import time
import random
import schedule

# Add necessary directories to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import from config
from config import (
    EMAIL_NOTIFICATIONS, MONGODB_ENABLED, MONGODB_CONNECTION_STRING, 
    MONGODB_DATABASE, MONGODB_COLLECTION
)
from config.sites import MARKET_PRICE_SITES

# Import from main module
from main import run_scraper_job, get_timestamp
from notifications import EmailNotifier
from storage import MongoDBStorage
from utils.price_comparison import PriceComparer

if __name__ == "__main__":
    # Initialize colorama for colored output
    colorama.init()
    
    print(f"{colorama.Fore.CYAN}=== Running Darkbot with Undefeated.com Focus ==={colorama.Style.RESET_ALL}")
    print(f"Started at: {get_timestamp()}")
    print()
    
    # Create custom argument parser
    parser = argparse.ArgumentParser(description='Darkbot - Undefeated.com Focus')
    parser.add_argument('--interval', type=int, default=30, 
                      help='Minutes between scans in continuous mode')
    parser.add_argument('--no-continuous', action='store_true',
                      help='Run once and exit instead of continuous mode')
    args = parser.parse_args()
    
    # Set custom settings
    args.sites = ["nike", "adidas", "undefeated", "footlocker", "jdsports", "finishline"]
    args.continuous = not args.no_continuous
    args.test_mode = False
    args.quiet = False
    args.scheduled_run = False
    args.market_sites = MARKET_PRICE_SITES
    args.list_sites = False
    
    # Start main functionality based on main.py but focused on Undefeated
    print("=" * 80)
    print("DARKBOT - Undefeated Edition")
    print(f"Focused on sneaker deals from Undefeated.com and other top sites")
    print(f"Started at: {get_timestamp()}")
    print("=" * 80)
    
    # Initialize email notifier
    notifier = EmailNotifier()
    notifier.start_notification_thread()
    
    # Set up MongoDB storage
    mongodb_storage = None
    if MONGODB_ENABLED:
        mongodb_storage = MongoDBStorage(
            connection_string=MONGODB_CONNECTION_STRING,
            database_name=MONGODB_DATABASE,
            collection_name=MONGODB_COLLECTION
        )
        print(f"MongoDB storage: Enabled")
    
    # Print configuration
    print(f"Scraping {len(args.sites)} sites: {', '.join(args.sites)}")
    print("-" * 80)
    
    # Run in continuous or one-time mode
    if args.continuous:
        print(f"Running in continuous mode every {args.interval} minutes")
        print("-" * 80)
        
        # Run once immediately
        print("Running initial scan...")
        run_scraper_job(args)
        
        # Set up global collection for all deals
        all_found_deals = []
        
        # Schedule email reports every 30 minutes
        def email_report_job():
            global all_found_deals
            print(f"\n{colorama.Fore.GREEN}Sending email report - {get_timestamp()}{colorama.Style.RESET_ALL}")
            
            if all_found_deals and len(all_found_deals) > 0:
                print(f"Sending email with {len(all_found_deals)} collected deals")
                try:
                    notifier.send_deals_email(all_found_deals, "Darkbot - Undefeated & Top Sites Deal Summary")
                    print(f"{colorama.Fore.GREEN}Email sent successfully with {len(all_found_deals)} deals{colorama.Style.RESET_ALL}")
                    all_found_deals = []  # Reset after sending
                except Exception as e:
                    print(f"{colorama.Fore.RED}Error sending email report: {str(e)}{colorama.Style.RESET_ALL}")
            else:
                print("No new deals found in the last 30 minutes, skipping email")
        
        # Schedule scraper job
        def scraper_job():
            print(f"\n{colorama.Fore.CYAN}Running scraper scan - {get_timestamp()}{colorama.Style.RESET_ALL}")
            deals = run_scraper_job(args, scheduled_run=True)
            
            if deals and len(deals) > 0:
                global all_found_deals
                all_found_deals.extend([d for d in deals if d not in all_found_deals])
                print(f"{colorama.Fore.GREEN}Found {len(deals)} new deals in this scan! Total unique deals: {len(all_found_deals)}{colorama.Style.RESET_ALL}")
            
            # Randomize next run time between 2-3 minutes
            next_interval = random.randint(120, 180)
            next_run = datetime.now() + timedelta(seconds=next_interval)
            print(f"Next scan: {next_run.strftime('%H:%M:%S')} ({next_interval} seconds)")
        
        # Schedule jobs
        schedule.every(30).minutes.do(email_report_job)
        schedule.every(2).minutes.do(scraper_job)
        
        print(f"Bot will run every 2-3 minutes and send email reports every 30 minutes. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{colorama.Fore.YELLOW}Bot stopped by user.{colorama.Style.RESET_ALL}")
    else:
        print("Running in one-time mode")
        print("-" * 80)
        run_scraper_job(args)
    
    # Stop email notification thread
    notifier.stop_notification_thread()
