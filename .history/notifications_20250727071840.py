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
    EMAIL_SERVER, EMAIL_PORT, EMAIL_RECIPIENT, EMAIL_INTERVAL_MINUTES
)
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
        self.recipient = EMAIL_RECIPIENT
        self.interval_minutes = EMAIL_INTERVAL_MINUTES
        
        # Store deals to be sent in the next email
        self.pending_deals = []
        self.last_email_time = None
        self.email_thread = None
        self.stop_thread = False
        
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
    
    def add_deals(self, deals: List[Dict[str, Any]]) -> None:
        """
        Add deals to be sent in the next email notification.
        
        Args:
            deals: List of deal dictionaries to include in the notification
        """
        if not self.enabled or not deals:
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
    
    def send_deals_email(self, deals: List[Dict[str, Any]]) -> bool:
        """
        Send an email with the deals information.
        
        Args:
            deals: List of deal dictionaries to include in the email
            
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
            msg['Subject'] = f"🔥 REAL Sneaker Deals Alert - Buy Now! - {get_timestamp()}"
            msg['From'] = self.username
            msg['To'] = self.recipient
            
            # Sort deals by profit potential
            deals.sort(key=lambda x: x.get('profit', 0), reverse=True)
            
            # Create the plain text message
            text_content = f"Sneaker Deals Alert - {get_timestamp()}\n\n"
            text_content += f"Found {len(deals)} potential profitable deals:\n\n"
            
            for i, deal in enumerate(deals):
                text_content += f"{i+1}. {deal.get('title', 'Unknown')}\n"
                text_content += f"   Price: ${deal.get('price', 0):.2f} (was ${deal.get('original_price', 0):.2f})\n"
                text_content += f"   Discount: {deal.get('discount_percent', 0)}%\n"
                text_content += f"   Potential Profit: ${deal.get('profit', 0):.2f}\n"
                text_content += f"   ROI: {deal.get('roi', '0%')}\n"
                text_content += f"   Source: {deal.get('source', 'Unknown')}\n"
                text_content += f"   Link: {deal.get('url', '#')}\n\n"
            
            # Create the HTML message
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
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
                <p>Found {len(deals)} potential profitable deals:</p>
            """
            
            for deal in deals:
                available_sizes = ', '.join([s['size'] for s in deal.get('sizes', []) if s.get('available', False)]) if 'sizes' in deal else 'Unknown'
                
                html_content += f"""
                <div class="deal">
                    <div class="title">{deal.get('title', 'Unknown')}</div>
                    <div class="price">Price: ${deal.get('price', 0):.2f} <strike>${deal.get('original_price', 0):.2f}</strike></div>
                    <div class="discount">Discount: {deal.get('discount_percent', 0)}%</div>
                    <div class="profit">Potential Profit: ${deal.get('profit', 0):.2f} ({deal.get('roi', '0%')})</div>
                    <div>Available Sizes: {available_sizes}</div>
                    <div class="source">Source: {deal.get('source', 'Unknown')}</div>
                    <div style="margin-top: 10px;">
                        <a href="{deal.get('url', '#')}" class="button">BUY NOW</a>
                    </div>
                    <div style="margin-top: 5px; font-size: 12px; color: #cc0000;">
                        <strong>⚠️ LIMITED TIME OFFER - This is a real product with a working purchase link</strong>
                    </div>
                </div>
                """
            
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
                smtp.send_message(msg)
            
            logger.info(f"Email notification sent successfully to {self.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

# Create a global instance
notifier = EmailNotifier()
