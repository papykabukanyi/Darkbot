#!/usr/bin/env python
"""
Darkbot Monitoring Script

This script checks the health of the Darkbot application and reports any issues.
It can be run as a cron job to automatically monitor the application.
"""

import os
import sys
import time
import json
import logging
import argparse
import requests
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', f'darkbot_monitor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'))
    ]
)
logger = logging.getLogger("DarkbotMonitor")

def check_process_running():
    """Check if the Darkbot process is running"""
    logger.info("Checking if Darkbot process is running...")
    
    try:
        # Check if process exists using ps
        result = subprocess.run(
            ["ps", "-ef", "|", "grep", "sneakerbot.py", "|", "grep", "-v", "grep"],
            shell=True,
            text=True,
            capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            logger.info("✅ Darkbot process is running")
            return True
        else:
            logger.warning("❌ Darkbot process is not running")
            return False
    except Exception as e:
        logger.error(f"Error checking process: {e}")
        return False

def check_api_health(host="localhost", port=8080):
    """Check if the API endpoint is responding"""
    logger.info(f"Checking API health at http://{host}:{port}/api/status...")
    
    try:
        response = requests.get(f"http://{host}:{port}/api/status", timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ API is responding correctly")
            return True
        else:
            logger.warning(f"❌ API returned status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"❌ Error connecting to API: {e}")
        return False

def check_logs_for_errors(hours_back=1):
    """Check the logs for errors in the last n hours"""
    logger.info(f"Checking logs for errors in the last {hours_back} hours...")
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        logger.error(f"❌ Log directory '{log_dir}' not found")
        return False
    
    error_count = 0
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(hours=hours_back)
    
    # Look for log files in the logs directory
    for filename in os.listdir(log_dir):
        if not filename.endswith(".log"):
            continue
        
        filepath = os.path.join(log_dir, filename)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        
        # Only check recent log files
        if file_mtime >= cutoff_time:
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        if "ERROR" in line or "CRITICAL" in line:
                            error_count += 1
                            if error_count <= 5:  # Limit the number of errors to display
                                logger.warning(f"Found error in {filename}: {line.strip()}")
            except Exception as e:
                logger.error(f"Error reading log file {filepath}: {e}")
    
    if error_count > 0:
        logger.warning(f"❌ Found {error_count} errors in logs")
        return False
    else:
        logger.info("✅ No errors found in recent logs")
        return True

def check_disk_space(min_free_mb=100):
    """Check if there is enough disk space available"""
    logger.info(f"Checking for minimum {min_free_mb}MB of free disk space...")
    
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(os.path.abspath('.')), 
                None, None, 
                ctypes.pointer(free_bytes)
            )
            free_mb = free_bytes.value / (1024 * 1024)
        else:  # Unix/Linux
            stat = os.statvfs(os.path.abspath('.'))
            free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        
        if free_mb < min_free_mb:
            logger.warning(f"❌ Low disk space: {free_mb:.2f}MB free (minimum {min_free_mb}MB)")
            return False
        else:
            logger.info(f"✅ Sufficient disk space: {free_mb:.2f}MB free")
            return True
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        return False

def check_stockx_api(test=False):
    """Check if we can connect to StockX API"""
    logger.info("Checking StockX API connection...")
    
    if test:
        try:
            from utils.stockx_price_checker import StockXPriceChecker
            
            price_checker = StockXPriceChecker()
            test_item = {'name': 'Nike Dunk Low Panda', 'sku': 'DD1391-100'}
            
            # Try to generate a report
            report = price_checker.generate_price_comparison_report(
                test_item['name'],
                sku=test_item['sku']
            )
            
            if report['best_price']['price'] is not None:
                logger.info(f"✅ Successfully connected to StockX API")
                logger.info(f"  Sample price for {test_item['name']}: ${report['best_price']['price']}")
                return True
            else:
                logger.warning("❌ Could not get price from StockX API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing StockX API: {e}")
            return False
    else:
        # Just check if credentials are set
        api_key = os.getenv('STOCKX_API_KEY')
        client_id = os.getenv('STOCKX_CLIENT_ID')
        client_secret = os.getenv('STOCKX_CLIENT_SECRET')
        
        if not api_key or not client_id or not client_secret:
            logger.warning("❌ Missing StockX API credentials")
            return False
        else:
            logger.info("✅ StockX API credentials are set")
            return True

def push_to_uptime_kuma(push_url, status, msg=""):
    """Push status to Uptime Kuma"""
    if not push_url:
        return
        
    try:
        import requests
        status_val = 'up' if status else 'down'
        requests.get(f"{push_url}?status={status_val}&msg={msg}", timeout=10)
        logger.info(f"Pushed status {status_val} to Uptime Kuma")
    except Exception as e:
        logger.error(f"Failed to push to Uptime Kuma: {e}")

def main():
    """Main function to run all checks"""
    parser = argparse.ArgumentParser(description="Monitor the health of Darkbot")
    parser.add_argument('--host', default='localhost', help='API host to check')
    parser.add_argument('--port', type=int, default=8080, help='API port to check')
    parser.add_argument('--email', help='Email to send notifications to')
    parser.add_argument('--test-api', action='store_true', help='Test the StockX API with a real request')
    parser.add_argument('--hours', type=int, default=1, help='Hours to look back for errors in logs')
    parser.add_argument('--push-to-kuma', help='Uptime Kuma push URL')
    parser.add_argument('--check-process-only', action='store_true', 
                    help='Only check if process is running (for Uptime Kuma)')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info(f"Darkbot Monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Special case for process-only check for Uptime Kuma
    if args.check_process_only:
        process_status = check_process_running()
        if args.push_to_kuma:
            push_to_uptime_kuma(args.push_to_kuma, process_status)
        return 0 if process_status else 1
    
    # Run all checks
    checks = [
        ("Process", check_process_running()),
        ("API Health", check_api_health(args.host, args.port)),
        ("Logs", check_logs_for_errors(args.hours)),
        ("Disk Space", check_disk_space()),
        ("StockX API", check_stockx_api(args.test_api))
    ]
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("MONITORING SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for name, result in checks:
        status = "✅ PASSED" if result else "❌ FAILED"
        if not result:
            all_passed = False
        logger.info(f"{name}: {status}")
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("✅ All checks passed! System is healthy.")
    else:
        logger.warning("❌ Some checks failed. System may need attention!")
    
    # Send email notification if configured and there are failures
    if args.email and not all_passed:
        try:
            send_email_notification(args.email, checks)
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    # Push to Uptime Kuma if configured
    if args.push_to_kuma:
        push_to_uptime_kuma(args.push_to_kuma, all_passed)
    
    return 0 if all_passed else 1

def send_email_notification(email_address, checks):
    """Send an email notification about the failed checks"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Get email settings from environment
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_password:
        logger.error("SMTP_USER and SMTP_PASSWORD environment variables must be set for email notifications")
        return
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email_address
    msg['Subject'] = f"⚠️ Darkbot Monitor Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Create the message body
    body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .passed {{ color: green; }}
        .failed {{ color: red; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h2>Darkbot Monitoring Alert</h2>
    <p>The following checks have failed:</p>
    
    <table>
        <tr>
            <th>Check</th>
            <th>Status</th>
        </tr>
"""
    
    for name, result in checks:
        status_class = "passed" if result else "failed"
        status_text = "PASSED" if result else "FAILED"
        body += f"""
        <tr>
            <td>{name}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>"""
    
    body += """
    </table>
    
    <p>Please check the server logs for more details.</p>
    <p>This is an automated message. Please do not reply.</p>
</body>
</html>
"""
    
    msg.attach(MIMEText(body, 'html'))
    
    # Send the message
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"Email notification sent to {email_address}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    sys.exit(main())
