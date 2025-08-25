"""
Advanced Sneaker Scalping Bot - Human-like behavior with powerful notifications
"""
import os
import sys
import time
import random
import json
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from dotenv import load_dotenv

# Load environment variables will be done in load_config method

class ScalpingBot:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_browser()
        self.profit_threshold = float(os.getenv('PROFIT_THRESHOLD', 50))
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))
        self.last_email_time = {}
        self.status_email_interval = 2 * 60 * 60  # 2 hours in seconds
        self.last_status_email = 0
        self.session_deals_found = 0
        self.session_checks_completed = 0
        self.bot_start_time = datetime.now()
        
        self.logger.info("🚀 Advanced Scalping Bot initialized successfully!")
        self.logger.info(f"📧 Status emails will be sent every {self.status_email_interval // 3600} hours")
        self.logger.info(f"💰 Profit threshold: ${self.profit_threshold}")
        self.logger.info(f"⏱️ Check interval: {self.check_interval} seconds")
        
    def setup_logging(self):
        """Setup comprehensive logging with file and console output"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Setup logging with detailed format
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            handlers=[
                logging.FileHandler('logs/scalping_bot.log'),
                logging.FileHandler('logs/scalping_bot_detailed.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Also create a separate handler for deal alerts
        deal_handler = logging.FileHandler('logs/deals_found.log')
        deal_handler.setLevel(logging.INFO)
        deal_formatter = logging.Formatter('%(asctime)s - DEAL ALERT - %(message)s')
        deal_handler.setFormatter(deal_formatter)
        
        self.deal_logger = logging.getLogger('deals')
        self.deal_logger.addHandler(deal_handler)
        self.deal_logger.setLevel(logging.INFO)
        
        self.logger.info("=" * 80)
        self.logger.info("🤖 ADVANCED SCALPING BOT STARTING UP")
        self.logger.info("=" * 80)
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.logger.info("Loading configuration from environment variables...")
        
        # For Railway deployment, all variables should be set in Railway dashboard
        # No need to load .env file in production
        
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'email': os.getenv('EMAIL_ADDRESS'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'recipients': os.getenv('EMAIL_RECIPIENTS', '').split(',')
        }
        
        self.stockx_config = {
            'api_key': os.getenv('STOCKX_API_KEY'),
            'client_id': os.getenv('STOCKX_CLIENT_ID'),
            'client_secret': os.getenv('STOCKX_CLIENT_SECRET'),
            'cookie': os.getenv('STOCKX_COOKIE')
        }
        
        # Debug what we found
        self.logger.info(f"EMAIL_ADDRESS: {'SET' if self.email_config['email'] else 'NOT SET'}")
        self.logger.info(f"EMAIL_PASSWORD: {'SET' if self.email_config['password'] else 'NOT SET'}")
        self.logger.info(f"EMAIL_RECIPIENTS: {'SET' if self.email_config['recipients'][0] else 'NOT SET'}")
        
        # Validate email config
        if not self.email_config['email'] or not self.email_config['password']:
            self.logger.error("❌ CRITICAL: EMAIL_ADDRESS and EMAIL_PASSWORD must be set!")
            self.logger.error("📋 TO FIX: Add these variables to Railway dashboard:")
            self.logger.error("   EMAIL_ADDRESS=papykabukanyi@gmail.com")
            self.logger.error("   EMAIL_PASSWORD=cksxfqaymfdkkfis") 
            self.logger.error("   EMAIL_RECIPIENTS=papykabukanyi@gmail.com,hoopstar385@gmail.com")
            self.logger.error("   PROFIT_THRESHOLD=50")
            self.logger.error("   CHECK_INTERVAL=300")
            self.logger.error("   STOCKX_API_KEY=54Ae6PJ6sQ1Bn9dinWl3FaHIsHlNlMqQ4vt1tvB6")
            self.logger.error("   STOCKX_CLIENT_ID=3VYAJs2pNikwozDG9WM1EAis87LkkZY6")
            self.logger.error("   STOCKX_CLIENT_SECRET=TRppZPRMfrTxCZ21baEZ0M3EVg2MufvxELMoENlH5lVGvtDLGUsBZ88ZYF14_HEj")
            self.logger.error("   STOCKX_COOKIE=[your cookie value]")
            sys.exit(1)
            
        self.logger.info("✅ Configuration loaded successfully!")
            
    def setup_browser(self):
        """Setup undetected Chrome browser for human-like behavior"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Anti-detection measures
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = uc.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.logger.info("Browser setup completed successfully")
        except Exception as e:
            self.logger.error(f"Browser setup failed: {e}")
            self.driver = None
            
    def human_delay(self, min_seconds=1, max_seconds=3):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def send_email(self, subject, body, priority="normal"):
        """Send email notification with rate limiting"""
        try:
            # Rate limiting - don't spam emails
            current_time = datetime.now()
            email_key = f"{subject[:20]}_{priority}"
            
            if email_key in self.last_email_time:
                time_diff = current_time - self.last_email_time[email_key]
                if time_diff.total_seconds() < 300:  # 5 minute cooldown
                    self.logger.info(f"Email rate limited for: {subject}")
                    return False
                    
            self.last_email_time[email_key] = current_time
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔥 SCALPING BOT: {subject}"
            msg['From'] = self.email_config['email']
            msg['To'] = ', '.join(self.email_config['recipients'])
            
            # Set priority
            if priority == "high":
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
                
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                             color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                    .content {{ padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 10px 0; }}
                    .profit {{ color: #28a745; font-weight: bold; font-size: 18px; }}
                    .urgent {{ color: #dc3545; font-weight: bold; animation: blink 1s infinite; }}
                    .sneaker {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; background: white; }}
                    .price {{ font-size: 16px; font-weight: bold; }}
                    .btn {{ display: inline-block; padding: 10px 20px; background: #007bff; 
                           color: white; text-decoration: none; border-radius: 5px; margin: 5px; }}
                    @keyframes blink {{ 0%,50% {{ opacity: 1; }} 51%,100% {{ opacity: 0.3; }} }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🚀 ADVANCED SCALPING BOT ALERT</h1>
                    <p>Timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="content">
                    {body}
                </div>
                <div style="text-align: center; padding: 20px; color: #666;">
                    <p>🤖 Powered by Advanced Scalping Bot | Keep this information confidential</p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['email'], self.email_config['password'])
                server.send_message(msg)
                
            self.logger.info(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
            
    def get_stockx_price(self, product_name, sku=None):
        """Get current StockX price with multiple fallback methods"""
        try:
            # Method 1: Direct API if available
            if self.stockx_config.get('api_key'):
                return self._get_stockx_api_price(product_name, sku)
                
            # Method 2: Web scraping with browser
            if self.driver:
                return self._scrape_stockx_price(product_name)
                
            # Method 3: Basic requests fallback
            return self._request_stockx_price(product_name)
            
        except Exception as e:
            self.logger.error(f"Error getting StockX price for {product_name}: {e}")
            return None
            
    def _scrape_stockx_price(self, product_name):
        """Scrape StockX price using browser"""
        try:
            search_url = f"https://stockx.com/search?s={product_name.replace(' ', '%20')}"
            self.driver.get(search_url)
            self.human_delay(2, 4)
            
            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='search-results']"))
            )
            
            # Get first result
            first_result = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='search-results'] > div:first-child a")
            product_url = first_result.get_attribute('href')
            
            if product_url:
                self.driver.get(product_url)
                self.human_delay(2, 4)
                
                # Get current market price
                price_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='current-price']"))
                )
                
                price_text = price_element.text.replace('$', '').replace(',', '')
                return float(price_text)
                
        except Exception as e:
            self.logger.error(f"StockX scraping failed: {e}")
            return None
            
    def scan_kicks_on_fire(self):
        """Scan KicksOnFire for new releases with human-like behavior"""
        self.logger.info("🔍 Initiating KicksOnFire scan...")
        
        try:
            if not self.driver:
                self.logger.warning("⚠️ Browser not available, using requests fallback")
                return self._scan_kicks_fallback()
                
            self.logger.info("🌐 Navigating to KicksOnFire...")
            self.driver.get("https://www.kicksonfire.com")
            self.human_delay(3, 6)
            
            # Simulate human browsing
            self.logger.info("🤖 Simulating human browsing behavior...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            self.human_delay(2, 4)
            
            releases = []
            
            # Find release items
            self.logger.info("🔎 Searching for release elements...")
            release_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.release-item-continer, article.post, .shoe-container")
            
            self.logger.info(f"📦 Found {len(release_elements)} potential releases to process")
            
            for i, element in enumerate(release_elements[:20], 1):  # Limit to 20 for performance
                try:
                    self.logger.info(f"📝 Processing release {i}/{min(20, len(release_elements))}...")
                    # Extract release data
                    title_elem = element.find_element(By.CSS_SELECTOR, "h2 a, .release-item-title, h3 a")
                    title = title_elem.text.strip()
                    url = title_elem.get_attribute('href')
                    
                    # Extract price
                    price = None
                    try:
                        price_elem = element.find_element(By.CSS_SELECTOR, ".release-price-from, .price")
                        price_text = price_elem.text.replace('$', '').replace(',', '')
                        price = float(price_text)
                    except:
                        pass
                        
                    # Extract image
                    image_url = None
                    try:
                        img_elem = element.find_element(By.CSS_SELECTOR, "img")
                        image_url = img_elem.get_attribute('src')
                    except:
                        pass
                        
                    if title and len(title) > 10:  # Valid title
                        release = {
                            'title': title,
                            'url': url,
                            'retail_price': price,
                            'image_url': image_url,
                            'source': 'KicksOnFire',
                            'timestamp': datetime.now().isoformat()
                        }
                        releases.append(release)
                        
                    self.human_delay(0.5, 1.5)  # Small delay between items
                    
                except Exception as e:
                    continue
                    
            self.logger.info(f"✅ Successfully extracted {len(releases)} releases")
            return releases
            
        except Exception as e:
            self.logger.error(f"KicksOnFire scanning failed: {e}")
            return []
            
    def _scan_kicks_fallback(self):
        """Fallback method using requests"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get("https://www.kicksonfire.com", headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            releases = []
            
            # Find articles and release items
            items = soup.find_all(['article', 'div'], class_=['post', 'release-item-continer', 'shoe-container'])
            
            for item in items[:15]:
                try:
                    title_elem = item.find(['h2', 'h3', 'a'], string=True)
                    if title_elem:
                        title = title_elem.get_text().strip()
                        url = None
                        
                        if title_elem.name == 'a':
                            url = title_elem.get('href')
                        else:
                            link = item.find('a')
                            if link:
                                url = link.get('href')
                                
                        if title and len(title) > 10:
                            releases.append({
                                'title': title,
                                'url': url,
                                'source': 'KicksOnFire',
                                'timestamp': datetime.now().isoformat()
                            })
                            
                except Exception:
                    continue
                    
            return releases
            
        except Exception as e:
            self.logger.error(f"Fallback scanning failed: {e}")
            return []
            
    def analyze_profit_potential(self, releases):
        """Analyze profit potential for releases"""
        profitable_releases = []
        
        for release in releases:
            try:
                title = release.get('title', '')
                retail_price = release.get('retail_price')
                
                if not retail_price:
                    continue
                    
                self.logger.info(f"🔍 Analyzing: {title}")
                
                # Get StockX price
                market_price = self.get_stockx_price(title)
                
                if market_price:
                    profit = market_price - retail_price
                    profit_percentage = (profit / retail_price) * 100
                    
                    if profit >= self.profit_threshold:
                        release['market_price'] = market_price
                        release['profit'] = profit
                        release['profit_percentage'] = profit_percentage
                        profitable_releases.append(release)
                        
                        self.logger.info(f"💰 PROFITABLE: {title} - Profit: ${profit:.2f} ({profit_percentage:.1f}%)")
                        
                self.human_delay(1, 3)  # Delay between price checks
                
            except Exception as e:
                self.logger.error(f"Error analyzing {release.get('title', 'Unknown')}: {e}")
                continue
                
        return profitable_releases
        
    def send_profitable_alert(self, profitable_releases):
        """Send detailed alert for profitable releases"""
        if not profitable_releases:
            return
            
        total_profit = sum(r.get('profit', 0) for r in profitable_releases)
        
        subject = f"💎 {len(profitable_releases)} PROFITABLE RELEASES FOUND! Potential: ${total_profit:.2f}"
        
        body = f"""
        <div class="urgent">🚨 URGENT SCALPING OPPORTUNITY 🚨</div>
        <h2>Found {len(profitable_releases)} Highly Profitable Releases!</h2>
        <div class="profit">Total Potential Profit: ${total_profit:.2f}</div>
        """
        
        for release in profitable_releases:
            profit = release.get('profit', 0)
            profit_pct = release.get('profit_percentage', 0)
            retail = release.get('retail_price', 0)
            market = release.get('market_price', 0)
            
            urgency = "🔥 HOT" if profit > 100 else "💰 GOOD" if profit > 50 else "📈 DECENT"
            
            body += f"""
            <div class="sneaker">
                <h3>{urgency} {release.get('title', 'Unknown')}</h3>
                <div class="price">Retail: ${retail:.2f} | Market: ${market:.2f}</div>
                <div class="profit">💵 Profit: ${profit:.2f} ({profit_pct:.1f}%)</div>
                <a href="{release.get('url', '#')}" class="btn">🛒 View Release</a>
            </div>
            """
            
        body += """
        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>⚡ QUICK ACTION REQUIRED:</h3>
            <ul>
                <li>🏃‍♂️ Move fast - these opportunities don't last long</li>
                <li>💳 Prepare multiple payment methods</li>
                <li>📱 Use multiple devices/browsers</li>
                <li>🔄 Set up auto-refresh on release pages</li>
            </ul>
        </div>
        """
        
        self.send_email(subject, body, priority="high")
        
    def send_monitoring_report(self, total_releases, profitable_count):
        """Send periodic monitoring report"""
        subject = f"📊 Monitoring Report - {total_releases} releases scanned"
        
        body = f"""
        <h2>🤖 Bot Status Report</h2>
        <div style="background: #d4edda; padding: 15px; border-radius: 5px;">
            <h3>📈 Statistics:</h3>
            <ul>
                <li>🔍 Total releases scanned: {total_releases}</li>
                <li>💰 Profitable opportunities found: {profitable_count}</li>
                <li>⏰ Last scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li>🎯 Profit threshold: ${self.profit_threshold}</li>
            </ul>
        </div>
        
        <div style="background: #cce5ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3>🔧 Bot Health:</h3>
            <ul>
                <li>✅ Browser: {'Active' if self.driver else 'Fallback mode'}</li>
                <li>✅ Email system: Operational</li>
                <li>✅ StockX integration: {'Active' if self.stockx_config.get('api_key') else 'Scraping mode'}</li>
            </ul>
        </div>
        """
        
        self.send_email(subject, body, priority="normal")
        
    def send_status_email(self):
        """Send 2-hour status update email with bot activity summary"""
        try:
            self.logger.info("📧 Preparing 2-hour status update email...")
            
            current_time = datetime.now()
            uptime = current_time - self.bot_start_time
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            
            subject = f"🤖 Scalping Bot Status Update - {current_time.strftime('%Y-%m-%d %H:%M')}"
            
            # Calculate statistics
            avg_checks_per_hour = self.session_checks_completed / max(uptime.total_seconds() / 3600, 1)
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 20px; border-radius: 10px; text-align: center;">
                    <h1>🤖 Advanced Scalping Bot Status Report</h1>
                    <h2>📊 2-Hour Activity Summary</h2>
                    <p><strong>Status Time:</strong> {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                
                <div style="margin: 20px 0; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>🚀 Bot Performance Metrics</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Bot Uptime</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{uptime_str}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Total Checks Completed</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{self.session_checks_completed}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Deals Found This Session</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{self.session_deals_found}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Average Checks Per Hour</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{avg_checks_per_hour:.1f}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Profit Threshold</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">${self.profit_threshold}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>Check Interval</strong></td>
                            <td style="padding: 10px; border: 1px solid #ddd;">{self.check_interval // 60} minutes</td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin: 20px 0; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>🎯 Bot Status</h3>
                    <p style="font-size: 18px; color: #28a745;"><strong>✅ Bot is running normally</strong></p>
                    <ul>
                        <li>🌐 <strong>Monitoring:</strong> KicksOnFire for new releases</li>
                        <li>💰 <strong>Price Checking:</strong> StockX integration active</li>
                        <li>📧 <strong>Email Alerts:</strong> Configured and working</li>
                        <li>🤖 <strong>Human Behavior:</strong> Anti-detection measures active</li>
                    </ul>
                </div>
                
                <div style="margin: 20px 0; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>📈 Recent Activity</h3>
                    <p>Bot has been continuously monitoring for profitable sneaker releases.</p>
                    <p><strong>Next status update:</strong> {(current_time + timedelta(seconds=self.status_email_interval)).strftime('%Y-%m-%d %H:%M UTC')}</p>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
                    <p>🚀 Advanced Scalping Bot - Automated Status Report</p>
                    <p>Keep scalping profitably! 💰</p>
                </div>
            </body>
            </html>
            """
            
            self.send_email(subject, html_body, priority="📊")
            self.last_status_email = time.time()
            self.logger.info(f"✅ Status email sent successfully! Next update in {self.status_email_interval // 3600} hours")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to send status email: {e}")

    def should_send_status_email(self):
        """Check if it's time to send a status email (every 2 hours)"""
        return time.time() - self.last_status_email >= self.status_email_interval
    
    def run_cycle(self):
        """Run one complete monitoring cycle with comprehensive logging"""
        cycle_start = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 Starting monitoring cycle #{self.session_checks_completed + 1} at {cycle_start.strftime('%H:%M:%S')}")
        self.logger.info("=" * 60)
        
        try:
            # Scan for releases
            self.logger.info("🔍 Scanning KicksOnFire for new releases...")
            releases = self.scan_kicks_on_fire()
            
            if not releases:
                self.logger.warning("⚠️ No releases found in this cycle")
                self.logger.info("📊 Continuing to next cycle...")
                return
                
            self.logger.info(f"📦 Found {len(releases)} releases to analyze")
            
            # Analyze profit potential
            self.logger.info("💰 Analyzing profit potential for each release...")
            profitable_releases = self.analyze_profit_potential(releases)
            
            # Log results
            if profitable_releases:
                self.logger.info(f"🎯 DEALS FOUND! {len(profitable_releases)} profitable releases detected!")
                self.session_deals_found += len(profitable_releases)
                
                # Log each deal
                for deal in profitable_releases:
                    profit = deal.get('profit', 0)
                    self.deal_logger.info(f"💎 DEAL: {deal.get('name', 'Unknown')} - Profit: ${profit:.2f}")
                    self.logger.info(f"💎 PROFITABLE: {deal.get('name', 'Unknown')} - Profit: ${profit:.2f}")
                
                # Send alerts
                self.send_profitable_alert(profitable_releases)
            else:
                self.logger.info("📉 No profitable deals found in this cycle")
                
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(f"✅ Cycle completed in {cycle_duration:.1f}s")
            self.logger.info(f"📊 Session Stats - Cycles: {self.session_checks_completed + 1}, Total Deals: {self.session_deals_found}")
            
        except Exception as e:
            self.logger.error(f"❌ Cycle failed with error: {e}")
            self.logger.exception("Full error traceback:")
            raise
            self.send_email("🚨 Bot Error", f"<div class='urgent'>Bot encountered an error: {str(e)}</div>", priority="high")
            
    def run(self):
        """Main bot loop"""
        self.logger.info("🤖 Advanced Scalping Bot starting...")
        
        # Send startup notification
        self.send_email(
            "🚀 Bot Started", 
            f"""
            <h2>🤖 Advanced Scalping Bot is now ACTIVE!</h2>
            <div style="background: #d1ecf1; padding: 15px; border-radius: 5px;">
                <h3>⚙️ Configuration:</h3>
                <ul>
                    <li>💰 Profit threshold: ${self.profit_threshold}</li>
                    <li>⏱️ Check interval: {self.check_interval} seconds</li>
                    <li>🎯 Target sites: KicksOnFire + StockX</li>
                    <li>🔧 Mode: {'Browser' if self.driver else 'Requests'}</li>
                </ul>
            </div>
            <p>The bot will continuously monitor for profitable sneaker releases and notify you immediately when opportunities are found.</p>
            """,
            priority="normal"
        )
        
        try:
            while True:
                # Check if it's time to send status email
                if self.should_send_status_email():
                    self.send_status_email()
                
                # Run monitoring cycle
                self.run_cycle()
                self.session_checks_completed += 1
                
                # Log cycle completion
                self.logger.info(f"✅ Cycle #{self.session_checks_completed} completed. Total deals found: {self.session_deals_found}")
                
                # Random delay to appear more human
                base_delay = self.check_interval
                jitter = random.randint(-30, 30)
                actual_delay = max(60, base_delay + jitter)
                
                self.logger.info(f"😴 Sleeping for {actual_delay} seconds... Next cycle in {actual_delay // 60}m {actual_delay % 60}s")
                time.sleep(actual_delay)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Bot stopped by user")
            self.logger.info(f"📊 Final Stats - Checks: {self.session_checks_completed}, Deals: {self.session_deals_found}")
        except Exception as e:
            self.logger.error(f"💥 Fatal error: {e}")
            self.send_email("💀 Bot Crashed", f"<div class='urgent'>Bot has crashed: {str(e)}</div>", priority="high")
        finally:
            if self.driver:
                self.driver.quit()
                
if __name__ == "__main__":
    bot = ScalpingBot()
    bot.run()
