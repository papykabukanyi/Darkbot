#!/usr/bin/env python
"""
Darkbot Monitoring Script

This script helps monitor Darkbot's production environment:
- Checks log files for errors and warnings
- Verifies scraper health
- Monitors profit statistics
- Provides a dashboard-like summary
"""

import os
import sys
import re
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
import glob
import subprocess
import platform
import psutil
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DarkbotMonitor")

class DarkbotMonitor:
    """Monitor class for Darkbot production environment"""
    
    def __init__(self, log_dir="logs", config_dir="config", days_back=1):
        """Initialize the monitor"""
        self.log_dir = log_dir
        self.config_dir = config_dir
        self.days_back = days_back
        self.darkbot_root = os.path.dirname(os.path.abspath(__file__))
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def check_system_resources(self):
        """Check system resources and return status"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory.percent,
                'memory_available_gb': memory.available / (1024 ** 3),
                'disk_usage': disk.percent,
                'disk_free_gb': disk.free / (1024 ** 3)
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {
                'cpu_usage': 0,
                'memory_usage': 0,
                'memory_available_gb': 0,
                'disk_usage': 0,
                'disk_free_gb': 0,
                'error': str(e)
            }
    
    def find_recent_logs(self):
        """Find recent log files"""
        cutoff_date = datetime.now() - timedelta(days=self.days_back)
        log_files = []
        
        # Search for log files
        for root, _, files in os.walk(self.log_dir):
            for file in files:
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time >= cutoff_date:
                        log_files.append(file_path)
        
        return log_files
    
    def analyze_log_file(self, log_file):
        """Analyze a log file for errors and warnings"""
        if not os.path.exists(log_file):
            return {'error': f"Log file does not exist: {log_file}"}
            
        errors = []
        warnings = []
        info_count = 0
        
        error_pattern = re.compile(r'ERROR|CRITICAL|Exception|Failed|Traceback')
        warning_pattern = re.compile(r'WARNING')
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if error_pattern.search(line):
                        errors.append(line.strip())
                    elif warning_pattern.search(line):
                        warnings.append(line.strip())
                    else:
                        info_count += 1
            
            return {
                'file': log_file,
                'errors': errors,
                'warnings': warnings,
                'info_count': info_count,
                'error_count': len(errors),
                'warning_count': len(warnings)
            }
        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}")
            return {
                'file': log_file,
                'error': str(e)
            }
    
    def check_scraper_status(self, scraper_name=None):
        """Check status of specific or all scrapers"""
        scrapers_dir = os.path.join(self.darkbot_root, 'scrapers')
        scraper_files = glob.glob(os.path.join(scrapers_dir, '*.py'))
        
        results = []
        
        for scraper_file in scraper_files:
            scraper = os.path.basename(scraper_file).replace('.py', '')
            
            # Skip __init__, base and factory
            if scraper in ('__init__', 'base_scraper', 'factory', 'fallback_scraper'):
                continue
                
            # Skip if we're looking for a specific scraper
            if scraper_name and scraper != scraper_name:
                continue
            
            # Look for recent log entries related to this scraper
            log_files = self.find_recent_logs()
            mentions = 0
            errors = 0
            success = 0
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Count mentions of this scraper
                        scraper_mentions = content.count(scraper)
                        mentions += scraper_mentions
                        
                        # Count errors related to this scraper
                        scraper_errors = len(re.findall(f"ERROR.*{scraper}", content))
                        errors += scraper_errors
                        
                        # Count successful runs
                        scraper_success = len(re.findall(f"Found .* deals .*{scraper}", content))
                        success += scraper_success
                except:
                    continue
            
            results.append({
                'scraper': scraper,
                'file': scraper_file,
                'mentions': mentions,
                'errors': errors,
                'success': success,
                'health': 'Good' if errors == 0 and mentions > 0 else 'Warning' if errors > 0 else 'Unknown'
            })
        
        return results
    
    def analyze_profit_stats(self):
        """Analyze profit statistics from recent runs"""
        # Look for profit analysis files
        profit_files = glob.glob(os.path.join(self.darkbot_root, '*profit*.json'))
        
        if not profit_files:
            return {'error': 'No profit analysis files found'}
        
        # Sort by modification time (newest first)
        profit_files.sort(key=os.path.getmtime, reverse=True)
        
        # Analyze the most recent file
        latest_file = profit_files[0]
        
        try:
            with open(latest_file, 'r') as f:
                profit_data = json.load(f)
                
            # Extract statistics
            analysis_date = profit_data.get('analysis_date', 'Unknown')
            products_analyzed = profit_data.get('products_analyzed', 0)
            profitable_products = profit_data.get('profitable_products', [])
            
            # Calculate stats
            avg_profit = 0
            max_profit = 0
            max_profit_product = None
            
            if profitable_products:
                profits = [p.get('profit_amount', 0) for p in profitable_products]
                avg_profit = sum(profits) / len(profits) if profits else 0
                max_profit = max(profits) if profits else 0
                max_profit_product = next(
                    (p for p in profitable_products if p.get('profit_amount', 0) == max_profit),
                    None
                )
            
            return {
                'analysis_date': analysis_date,
                'products_analyzed': products_analyzed,
                'profitable_count': len(profitable_products),
                'average_profit': avg_profit,
                'max_profit': max_profit,
                'max_profit_product': max_profit_product.get('title', 'Unknown') if max_profit_product else 'Unknown',
                'file': latest_file
            }
            
        except Exception as e:
            logger.error(f"Error analyzing profit stats from {latest_file}: {e}")
            return {'error': f"Error analyzing profit stats: {e}"}
    
    def check_database_status(self):
        """Check database status"""
        config_file = os.path.join(self.darkbot_root, 'config', '__init__.py')
        
        try:
            with open(config_file, 'r') as f:
                config_content = f.read()
                
            # Check if MongoDB is enabled
            mongodb_enabled = 'MONGODB_ENABLED' in config_content and 'True' in config_content
            
            if mongodb_enabled:
                # Try to connect to MongoDB
                try:
                    from pymongo import MongoClient
                    import re
                    
                    # Extract connection string
                    conn_match = re.search(r'MONGODB_CONNECTION_STRING\s*=\s*["\']([^"\']+)["\']', config_content)
                    conn_str = conn_match.group(1) if conn_match else ''
                    
                    if conn_str:
                        client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
                        client.server_info()  # Will raise exception if cannot connect
                        
                        # Get database name
                        db_match = re.search(r'MONGODB_DATABASE\s*=\s*["\']([^"\']+)["\']', config_content)
                        db_name = db_match.group(1) if db_match else 'darkbot'
                        
                        # Get collection name
                        coll_match = re.search(r'MONGODB_COLLECTION\s*=\s*["\']([^"\']+)["\']', config_content)
                        coll_name = coll_match.group(1) if coll_match else 'deals'
                        
                        # Get stats
                        db = client[db_name]
                        coll = db[coll_name]
                        doc_count = coll.count_documents({})
                        
                        return {
                            'status': 'Connected',
                            'database': db_name,
                            'collection': coll_name,
                            'document_count': doc_count
                        }
                    else:
                        return {'status': 'No connection string found'}
                        
                except Exception as e:
                    return {'status': 'Error', 'error': str(e)}
            else:
                return {'status': 'Disabled'}
                
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            return {'status': 'Error', 'error': str(e)}
    
    def get_dashboard_summary(self):
        """Generate a complete dashboard summary"""
        # System resources
        system = self.check_system_resources()
        
        # Log analysis
        logs = self.find_recent_logs()
        log_analysis = [self.analyze_log_file(log) for log in logs]
        total_errors = sum(analysis.get('error_count', 0) for analysis in log_analysis)
        total_warnings = sum(analysis.get('warning_count', 0) for analysis in log_analysis)
        
        # Scraper status
        scrapers = self.check_scraper_status()
        healthy_scrapers = sum(1 for s in scrapers if s['health'] == 'Good')
        warning_scrapers = sum(1 for s in scrapers if s['health'] == 'Warning')
        
        # Profit stats
        profit_stats = self.analyze_profit_stats()
        
        # Database status
        db_status = self.check_database_status()
        
        # Format the results in a dashboard-style summary
        summary = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system': system,
            'scrapers': {
                'total': len(scrapers),
                'healthy': healthy_scrapers,
                'warning': warning_scrapers,
                'details': scrapers
            },
            'logs': {
                'total': len(logs),
                'errors': total_errors,
                'warnings': total_warnings,
                'details': log_analysis
            },
            'profit': profit_stats,
            'database': db_status
        }
        
        return summary
    
    def display_dashboard(self):
        """Display the dashboard in a user-friendly format"""
        summary = self.get_dashboard_summary()
        
        # Clear screen
        os.system('cls' if platform.system() == 'Windows' else 'clear')
        
        # Print header
        print("=" * 80)
        print(f" DARKBOT MONITORING DASHBOARD - {summary['timestamp']} ".center(80, '='))
        print("=" * 80)
        
        # System resources
        print("\n[System Resources]")
        print(f"CPU Usage: {summary['system']['cpu_usage']}%")
        print(f"Memory Usage: {summary['system']['memory_usage']}% ({summary['system']['memory_available_gb']:.1f} GB free)")
        print(f"Disk Usage: {summary['system']['disk_usage']}% ({summary['system']['disk_free_gb']:.1f} GB free)")
        
        # Scraper status
        print("\n[Scraper Status]")
        print(f"Total Scrapers: {summary['scrapers']['total']}")
        print(f"Healthy Scrapers: {summary['scrapers']['healthy']}")
        print(f"Warning Scrapers: {summary['scrapers']['warning']}")
        
        scraper_table = []
        for scraper in summary['scrapers']['details']:
            scraper_table.append([
                scraper['scraper'],
                scraper['health'],
                scraper['success'],
                scraper['errors']
            ])
        
        if scraper_table:
            print("\nScraper Details:")
            print(tabulate(scraper_table, headers=['Scraper', 'Health', 'Success', 'Errors'], tablefmt='pretty'))
        
        # Log analysis
        print("\n[Log Analysis]")
        print(f"Total Logs: {summary['logs']['total']}")
        print(f"Total Errors: {summary['logs']['errors']}")
        print(f"Total Warnings: {summary['logs']['warnings']}")
        
        # Show most recent errors if any
        if summary['logs']['errors'] > 0:
            print("\nRecent Errors:")
            shown_errors = 0
            for log in summary['logs']['details']:
                if 'errors' in log and log['errors']:
                    for error in log['errors'][-3:]:  # Show last 3 errors per log
                        print(f"- {error[:100]}..." if len(error) > 100 else f"- {error}")
                        shown_errors += 1
                        if shown_errors >= 5:  # Show at most 5 errors total
                            break
                if shown_errors >= 5:
                    break
        
        # Profit stats
        print("\n[Profit Analysis]")
        if 'error' in summary['profit']:
            print(f"Error: {summary['profit']['error']}")
        else:
            print(f"Analysis Date: {summary['profit']['analysis_date']}")
            print(f"Products Analyzed: {summary['profit']['products_analyzed']}")
            print(f"Profitable Products: {summary['profit']['profitable_count']}")
            print(f"Average Profit: ${summary['profit']['average_profit']:.2f}")
            print(f"Maximum Profit: ${summary['profit']['max_profit']:.2f} ({summary['profit']['max_profit_product']})")
        
        # Database status
        print("\n[Database Status]")
        print(f"Status: {summary['database']['status']}")
        
        if summary['database']['status'] == 'Connected':
            print(f"Database: {summary['database']['database']}")
            print(f"Collection: {summary['database']['collection']}")
            print(f"Documents: {summary['database']['document_count']}")
        elif 'error' in summary['database']:
            print(f"Error: {summary['database']['error']}")
        
        print("\n" + "=" * 80)
        
        # Save the summary to a JSON file
        with open('darkbot_monitor_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Full summary saved to darkbot_monitor_summary.json")
    
def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Darkbot Production Monitoring Tool')
    parser.add_argument('--log-dir', default='logs', help='Log directory to analyze')
    parser.add_argument('--days', type=int, default=1, help='Number of days back to analyze logs')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--scraper', help='Check status of specific scraper')
    parser.add_argument('--watch', action='store_true', help='Watch mode - update every 60 seconds')
    args = parser.parse_args()
    
    monitor = DarkbotMonitor(args.log_dir, days_back=args.days)
    
    if args.scraper:
        results = monitor.check_scraper_status(args.scraper)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for result in results:
                print(f"Scraper: {result['scraper']}")
                print(f"Health: {result['health']}")
                print(f"Mentions: {result['mentions']}")
                print(f"Errors: {result['errors']}")
                print(f"Successful runs: {result['success']}")
    elif args.watch:
        try:
            while True:
                monitor.display_dashboard()
                print("\nUpdating in 60 seconds... (Press Ctrl+C to exit)")
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nExiting watch mode")
    else:
        if args.json:
            summary = monitor.get_dashboard_summary()
            print(json.dumps(summary, indent=2))
        else:
            monitor.display_dashboard()

if __name__ == "__main__":
    main()
