"""
Email notification module for the sneaker bot.
"""

import smtplib
import logging
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import (
    EMAIL_NOTIFICATIONS, EMAIL_ADDRESS, EMAIL_PASSWORD,
    EMAIL_SERVER, EMAIL_PORT, EMAIL_RECIPIENT, EMAIL_INTERVAL_MINUTES,
    WEBSITES
)
from config.sites import SNEAKER_SITES, DEFAULT_SITES
from utils import get_timestamp

logger = logging.getLogger("SneakerBot")

class EmailNotifier:
    """Class for handling email notifications."""
    
    def __init__(self):
        """Initialize the email notifier."""
        self.enabled = EMAIL_NOTIFICATIONS
        self.server = EMAIL_SERVER
        self.port = EMAIL_PORT
        self.username = EMAIL_ADDRESS
        self.password = EMAIL_PASSWORD
        
        # Handle multiple recipients (comma-separated string)
        self.recipients = [email.strip() for email in EMAIL_RECIPIENT.split(',') if email.strip()]
        self.interval_minutes = EMAIL_INTERVAL_MINUTES
        
        # Store deals to be sent in the next email
        self.pending_deals = []
        self.last_email_time = None
        self.email_thread = None
        self.stop_thread = False
        
        # Log recipients
        if self.enabled:
            logger.info(f"Email notifications enabled for {', '.join(self.recipients)}")
            logger.info(f"Will send emails every {self.interval_minutes} minutes")
        
    def start_notification_thread(self):
        """Start a background thread to send periodic email notifications."""
        if not self.enabled:
            logger.info("Email notifications are disabled in config.")
            return
        
        logger.info(f"Starting email notification thread (every {self.interval_minutes} minutes)...")
        
        self.email_thread = threading.Thread(
            target=self._notification_loop,
            daemon=True  # Make thread terminate when main program exits
        )
        self.email_thread.start()
    
    def stop_notification_thread(self):
        """Stop the notification thread."""
        if self.email_thread and self.email_thread.is_alive():
            logger.info("Stopping email notification thread...")
            self.stop_thread = True
            self.email_thread.join(timeout=5)
            logger.info("Email notification thread stopped.")
    
    def _notification_loop(self):
        """Background loop to send emails periodically."""
        while not self.stop_thread:
            # Check if we have pending deals and it's time to send an email
            current_time = datetime.now()
            
            if (self.pending_deals and 
                (not self.last_email_time or 
                 (current_time - self.last_email_time).total_seconds() / 60 >= self.interval_minutes)):
                
                try:
                    deals_to_send = self.pending_deals.copy()
                    self.pending_deals = []  # Clear the pending deals
                    
                    self.send_deals_email(deals_to_send)
                    self.last_email_time = current_time
                    
                    logger.info(f"Email notification sent with {len(deals_to_send)} deals.")
                except Exception as e:
                    logger.error(f"Failed to send email notification: {e}")
                    # Put the deals back in the pending list
                    self.pending_deals = deals_to_send + self.pending_deals
            
            # Sleep for a minute before checking again
            time.sleep(60)
    
    def verify_product_url(self, url: str) -> bool:
        """
        Verify that a product URL is valid and working.
        
        Args:
            url: The URL to verify
            
        Returns:
            True if the URL is valid and accessible, False otherwise
        """
        try:
            if not url or not url.startswith('http'):
                logger.warning(f"Invalid URL format: {url}")
                return False
                
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            
            response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code < 400:
                logger.info(f"Verified working product URL: {url}")
                return True
            else:
                logger.warning(f"Product URL returned status {response.status_code}: {url}")
                return False
        except Exception as e:
            logger.error(f"Error verifying product URL {url}: {e}")
            return False
    
    def send_no_deals_notification(self):
        """Send an email notification when no deals are found."""
        if not self.enabled:
            return
            
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Sneaker Bot Update - No Deals Found - {get_timestamp()}"
            msg['From'] = self.username
            # Don't set To header here, we'll set it individually for each recipient
            
            # Create the plain text message
            # Generate list of sites being monitored based on configuration
            site_list = ""
            for site in DEFAULT_SITES:
                site_config = SNEAKER_SITES.get(site, {})
                site_url = site_config.get('url', f"unknown-{site}")
                if site_url.startswith('http'):
                    site_url = site_url.replace('https://', '').replace('http://', '')
                site_list += f"- {site_url}\n"
            
            # Always ensure Undefeated is included
            if 'undefeated' not in DEFAULT_SITES:
                site_list += "- www.undefeated.com\n"
            
            text_content = f"Darkbot Sneaker Scraper Update - {get_timestamp()}\n\n"
            text_content += "No profitable deals were found in the latest scan.\n\n"
            text_content += "The bot is currently monitoring these sites for deals:\n"
            text_content += site_list + "\n"
            text_content += "Next scan is scheduled in the coming minutes.\n\n"
            text_content += "The bot will continue running and notify you when good deals become available.\n\n"
            
            # Create the HTML message
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 20px auto; }}
                    .header {{ background-color: #222; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .message {{ 
                        padding: 20px;
                        border: 1px solid #ddd;
                        border-radius: 0 0 5px 5px;
                        background-color: #fff;
                    }}
                    .title {{ font-weight: bold; font-size: 22px; color: #333; margin-bottom: 15px; }}
                    .content {{ font-size: 16px; line-height: 1.5; color: #444; }}
                    .sites {{ margin: 15px 0; }}
                    .sites ul {{ padding-left: 20px; }}
                    .sites li {{ margin-bottom: 8px; }}
                    .highlight {{ color: #0066cc; font-weight: bold; }}
                    .footer {{ font-size: 12px; color: #777; margin-top: 20px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin: 0;">Darkbot Sneaker Scraper</h1>
                    </div>
                    <div class="message">
                        <div class="title">No Profitable Deals Found Yet</div>
                        <div class="content">
                            <p>The bot has completed its latest scan but didn't find any deals meeting your profit criteria.</p>
                            
                            <div class="sites">
                                <p>Currently monitoring these sites:</p>
                                <ul>
"""

            # Generate HTML list of sites
            for site in DEFAULT_SITES:
                site_config = SNEAKER_SITES.get(site, {})
                site_url = site_config.get('url', f"unknown-{site}")
                if site_url.startswith('http'):
                    site_url = site_url.replace('https://', '').replace('http://', '')
                html_content += f"                                    <li>{site_url}</li>\n"
            
            # Always ensure Undefeated is included
            if 'undefeated' not in DEFAULT_SITES:
                html_content += "                                    <li>www.undefeated.com</li>\n"
            
            html_content += """                                </ul>
                            </div>
                            
                            <p>The next scan is scheduled in the coming minutes.</p>
                            <p>We'll <span class="highlight">notify you immediately</span> when we find deals worth your attention!</p>
                        </div>
                        
                        <div class="footer">
                            <p>Generated at {get_timestamp()}</p>
                            <p>Darkbot Sneaker Scraper | Automatic Notification</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send the email
            with smtplib.SMTP(self.server, self.port) as smtp:
                smtp.starttls()
                smtp.login(self.username, self.password)
                
                # Send to each recipient individually
                for recipient in self.recipients:
                    # Create a fresh message for each recipient instead of copying
                    msg['To'] = recipient
                    smtp.send_message(msg)
                    logger.info(f"'No deals found' notification sent to {recipient}")
                    # Remove the To header for the next recipient
                    del msg['To']
            
            logger.info(f"'No deals found' notifications sent successfully to {len(self.recipients)} recipients")
            self.last_email_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to send 'no deals found' notification: {e}")
    
    def add_deals(self, deals: List[Dict[str, Any]], send_no_deals_notification: bool = False) -> None:
        """
        Add deals to be sent in the next email notification.
        
        Args:
            deals: List of deal dictionaries to include in the notification
            send_no_deals_notification: Whether to send notification when no deals are found
                                        (Default: False - don't send, wait for scheduled report)
        """
        if not self.enabled:
            return
            
        if not deals:
            logger.info("No deals found in this scan - will be included in next scheduled report")
            # Only send immediate "no deals" email if explicitly requested (not during scheduled runs)
            if send_no_deals_notification:
                self.send_no_deals_notification()
            return
        
        # Only add worth_buying deals with verified URLs
        worthy_deals = []
        for deal in deals:
            if deal.get('worth_buying', False):
                # Verify the product URL is working
                if 'url' in deal and self.verify_product_url(deal['url']):
                    worthy_deals.append(deal)
                    logger.info(f"Added verified deal: {deal.get('title', 'Unknown')}")
                else:
                    logger.warning(f"Skipping deal with invalid URL: {deal.get('title', 'Unknown')}")
        
        if worthy_deals:
            self.pending_deals.extend(worthy_deals)
            logger.info(f"Added {len(worthy_deals)} verified deals to pending email notification.")
            
            # If this is the first batch of deals, start the notification thread
            if not self.email_thread or not self.email_thread.is_alive():
                self.start_notification_thread()
    
    def send_deals_email(self, deals: List[Dict[str, Any]], custom_subject: str = None) -> bool:
        """
        Send an email with the deals information.
        
        Args:
            deals: List of deal dictionaries to include in the email
            custom_subject: Optional custom subject line for the email
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Email notifications are disabled.")
            return False
        
        if not deals:
            logger.info("No deals to send in email.")
            return False
        
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            if custom_subject:
                msg['Subject'] = f"{custom_subject} - {get_timestamp()}"
            else:
                msg['Subject'] = f"🔥 REAL Sneaker Deals Alert - Buy Now! - {get_timestamp()}"
            msg['From'] = self.username
            # Don't set To header here, we'll set it individually for each recipient
            
            # Sort deals by profit potential
            deals.sort(key=lambda x: x.get('profit_percentage', 0), reverse=True)
            
            # Separate profitable deals from regular deals
            profitable_deals = [d for d in deals if d.get('is_profitable', False)]
            other_deals = [d for d in deals if not d.get('is_profitable', False)]
            
            # Create the plain text message
            text_content = f"Sneaker Deals Alert - {get_timestamp()}\n\n"
            
            if profitable_deals:
                text_content += f"Found {len(profitable_deals)} HIGHLY PROFITABLE deals:\n\n"
                
                for i, deal in enumerate(profitable_deals):
                    text_content += f"{i+1}. {deal.get('title', 'Unknown')}\n"
                    text_content += f"   Price: ${deal.get('current_price', deal.get('price', 0)):.2f} (was ${deal.get('original_price', 0):.2f})\n"
                    text_content += f"   Discount: {deal.get('discount_percent', 0)}%\n"
                    text_content += f"   Market Value: ${deal.get('profit_amount', 0) + deal.get('current_price', 0):.2f}\n"
                    text_content += f"   Potential Profit: ${deal.get('profit_amount', 0):.2f}\n"
                    text_content += f"   ROI: {deal.get('profit_percentage', 0):.1f}%\n"
                    text_content += f"   SKU: {deal.get('sku', 'Unknown')}\n"
                    text_content += f"   URL: {deal.get('url', '')}\n\n"
            
            if other_deals:
                text_content += f"\nOther potential deals ({len(other_deals)}):\n\n"
                for i, deal in enumerate(other_deals[:5]):  # Show only top 5 other deals
                    text_content += f"{i+1}. {deal.get('title', 'Unknown')}\n"
                    text_content += f"   Price: ${deal.get('current_price', deal.get('price', 0)):.2f} (was ${deal.get('original_price', 0):.2f})\n"
                    text_content += f"   Discount: {deal.get('discount_percent', 0)}%\n"
                    text_content += f"   URL: {deal.get('url', '')}\n\n"
                
                if len(other_deals) > 5:
                    text_content += f"...and {len(other_deals) - 5} more deals\n"
            
            # Create the HTML message
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .profitable-deal {{
                        margin: 20px;
                        padding: 20px;
                        border: 2px solid #28a745;
                        border-radius: 5px;
                        background-color: #f2fff5;
                    }}
                    .deal {{ 
                        margin-bottom: 20px;
                        padding: 15px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                    }}
                    .deal:nth-child(odd) {{ background-color: #f9f9f9; }}
                    .title {{ font-weight: bold; font-size: 18px; color: #333; }}
                    .price {{ font-size: 16px; }}
                    .discount {{ color: green; font-weight: bold; }}
                    .profit {{ color: #cc0000; font-weight: bold; }}
                    .source {{ color: #666; }}
                    .button {{ 
                        background-color: #4CAF50; 
                        border: none;
                        color: white;
                        padding: 10px 20px;
                        text-align: center;
                        text-decoration: none;
                        display: inline-block;
                        font-size: 16px;
                        margin: 4px 2px;
                        cursor: pointer;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <h1>Sneaker Deals Alert - {get_timestamp()}</h1>
            """
            
            if profitable_deals:
                html_content += f"""
                <h2 style="color: #28a745;">🔥 {len(profitable_deals)} HIGHLY PROFITABLE DEALS FOUND!</h2>
                <p>These deals show the highest profit potential based on current market prices:</p>
                """
                
                for deal in profitable_deals:
                    available_sizes = ', '.join([s['size'] for s in deal.get('sizes', []) if s.get('available', False)]) if 'sizes' in deal else 'Unknown'
                    market_value = deal.get('profit_amount', 0) + deal.get('current_price', deal.get('price', 0))
                    
                    html_content += f"""
                    <div class="profitable-deal">
                        <div class="title">{deal.get('title', 'Unknown')}</div>
                        <div class="price">Price: <span style="color: green; font-weight: bold;">${deal.get('current_price', deal.get('price', 0)):.2f}</span> <strike>${deal.get('original_price', 0):.2f}</strike></div>
                        <div class="discount">Discount: {deal.get('discount_percent', 0)}%</div>
                        <div><strong>Market Value: ${market_value:.2f}</strong></div>
                        <div class="profit" style="color: #28a745; font-size: 18px;">Potential Profit: ${deal.get('profit_amount', 0):.2f} ({deal.get('profit_percentage', 0):.1f}%)</div>
                        <div>Available Sizes: {available_sizes}</div>
                        <div>SKU: {deal.get('sku', 'Unknown')}</div>
                        <div class="source">Source: {deal.get('source', 'Unknown')}</div>
                        <div style="margin-top: 10px;">
                            <a href="{deal.get('url', '#')}" class="button">BUY NOW</a>
                        </div>
                        <div style="margin-top: 5px; font-size: 12px; color: #cc0000;">
                            <strong>⚠️ LIMITED TIME OFFER - This is a real product with a working purchase link</strong>
                        </div>
                    </div>
                    """
            
            if other_deals:
                html_content += f"""
                <h3>Other Potential Deals ({len(other_deals)} more)</h3>
                <p>These deals meet your discount criteria but may not have the same profit potential:</p>
                """
                
                for deal in other_deals[:5]:  # Only show top 5
                    available_sizes = ', '.join([s['size'] for s in deal.get('sizes', []) if s.get('available', False)]) if 'sizes' in deal else 'Unknown'
                    
                    html_content += f"""
                    <div class="deal">
                        <div class="title">{deal.get('title', 'Unknown')}</div>
                        <div class="price">Price: ${deal.get('current_price', deal.get('price', 0)):.2f} <strike>${deal.get('original_price', 0):.2f}</strike></div>
                        <div class="discount">Discount: {deal.get('discount_percent', 0)}%</div>
                        <div class="source">Source: {deal.get('source', 'Unknown')}</div>
                        <div style="margin-top: 10px;">
                            <a href="{deal.get('url', '#')}" class="button">BUY NOW</a>
                        </div>
                    </div>
                    """
                
                if len(other_deals) > 5:
                    html_content += f"<p>...and {len(other_deals) - 5} more deals</p>"
            
            html_content += """
            </body>
            </html>
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send the email
            with smtplib.SMTP(self.server, self.port) as smtp:
                smtp.starttls()
                smtp.login(self.username, self.password)
                
                # Send to each recipient individually
                for recipient in self.recipients:
                    # Create a fresh message for each recipient instead of copying
                    msg['To'] = recipient
                    smtp.send_message(msg)
                    logger.info(f"Email notification sent to {recipient}")
                    # Remove the To header for the next recipient
                    del msg['To']
            
            logger.info(f"Email notifications sent successfully to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

# Create a global instance
notifier = EmailNotifier()
