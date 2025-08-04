import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List, Dict, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class EmailNotification:
    """Class for sending email notifications about new sneaker releases"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the email notification system.
        
        Args:
            config: Configuration for the email system
        """
        self.config = config or {}
        self.smtp_server = self.config.get('smtp_server', os.getenv('SMTP_SERVER', 'smtp.gmail.com'))
        self.smtp_port = self.config.get('smtp_port', int(os.getenv('SMTP_PORT', 587)))
        self.smtp_username = self.config.get('smtp_username', os.getenv('SMTP_USERNAME', ''))
        self.smtp_password = self.config.get('smtp_password', os.getenv('SMTP_PASSWORD', ''))
        self.sender_email = self.config.get('sender_email', os.getenv('SENDER_EMAIL', self.smtp_username))
        self.recipient_emails = self.config.get('recipient_emails', os.getenv('RECIPIENT_EMAILS', '').split(','))
        
        # Ensure recipient_emails is a list
        if isinstance(self.recipient_emails, str):
            self.recipient_emails = [self.recipient_emails]
    
    def send_notification(self, releases: List[Dict[str, Any]]) -> bool:
        """
        Send an email notification about new releases.
        
        Args:
            releases: List of release information
            
        Returns:
            True if the email was sent, False otherwise
        """
        if not releases:
            logger.info("No releases to notify about")
            return False
        
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        if not self.recipient_emails:
            logger.error("No recipient emails configured")
            return False
        
        # Create the email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New Sneaker Releases - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(self.recipient_emails)
        
        # Create HTML content
        html_content = self._create_email_html(releases)
        msg.attach(MIMEText(html_content, 'html'))
        
        try:
            # Connect to the SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # Send the email
            server.sendmail(self.sender_email, self.recipient_emails, msg.as_string())
            server.quit()
            
            logger.info(f"Email notification sent to {', '.join(self.recipient_emails)}")
            return True
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _create_email_html(self, releases: List[Dict[str, Any]]) -> str:
        """
        Create HTML content for the email notification.
        
        Args:
            releases: List of release information
            
        Returns:
            HTML content for the email
        """
        # Style for the HTML email
        style = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }
            h1 { color: #c9302c; }
            h2 { color: #c9302c; border-bottom: 1px solid #eee; padding-bottom: 5px; }
            .release { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
            .release-header { margin-bottom: 10px; }
            .release-title { font-size: 20px; font-weight: bold; margin: 0; }
            .release-date { color: #666; }
            .release-image { max-width: 300px; max-height: 300px; margin: 10px 0; }
            .release-details { margin: 10px 0; }
            .release-detail { margin: 5px 0; }
            .profit-potential { margin-top: 15px; padding: 10px; border-radius: 4px; }
            .profit-good { background-color: #dff0d8; color: #3c763d; }
            .profit-bad { background-color: #f2dede; color: #a94442; }
            .profit-neutral { background-color: #fcf8e3; color: #8a6d3b; }
            .comparison-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            .comparison-table th { background-color: #f5f5f5; text-align: left; padding: 8px; border: 1px solid #ddd; }
            .comparison-table td { padding: 8px; border: 1px solid #ddd; }
            .price-source { font-weight: bold; }
            .no-data { color: #999; font-style: italic; }
        </style>
        """
        
        # HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>New Sneaker Releases</title>
            {style}
        </head>
        <body>
            <h1>New Sneaker Releases</h1>
            <p>Found {len(releases)} new releases:</p>
        """
        
        # Add each release to the HTML
        for release in releases:
            title = release.get('title', 'Unknown Sneaker')
            date_str = release.get('release_date', 'Unknown date')
            image_url = release.get('image_url', '')
            url = release.get('url', '')
            sku = release.get('sku', 'Unknown')
            retail_price = release.get('retail_price', 'Unknown')
            
            # Get price check results if available
            price_check_results = release.get('price_check_results', {})
            price_check_status = price_check_results.get('status', 'error')
            
            # Determine CSS class for profit section
            profit_class = 'profit-neutral'
            profit_message = 'Unknown profit potential'
            
            if price_check_status == 'success':
                retail_price = price_check_results.get('retail_price', retail_price)
                market_price = price_check_results.get('market_price', 'Unknown')
                best_price_source = price_check_results.get('best_price_source', 'Unknown')
                profit_info = price_check_results.get('profit', {})
                profit_amount = profit_info.get('amount', 0)
                profit_percentage = profit_info.get('percentage', 0)
                
                if profit_amount > 0:
                    profit_class = 'profit-good'
                    profit_message = f'Potential profit: ${profit_amount:.2f} ({profit_percentage:.1f}%)'
                else:
                    profit_class = 'profit-bad'
                    profit_message = f'No profit potential: ${profit_amount:.2f} ({profit_percentage:.1f}%)'
            
            # Create HTML for this release
            release_html = f"""
            <div class="release">
                <div class="release-header">
                    <h2 class="release-title">{title}</h2>
                    <div class="release-date">{date_str}</div>
                </div>
            """
            
            # Add image if available
            if image_url:
                release_html += f'<img class="release-image" src="{image_url}" alt="{title}" />'
            
            # Add details
            release_html += f"""
                <div class="release-details">
                    <div class="release-detail">SKU: {sku}</div>
                    <div class="release-detail">Retail Price: ${retail_price}</div>
            """
            
            # Add URL if available
            if url:
                release_html += f'<div class="release-detail">Link: <a href="{url}">{url}</a></div>'
            
            # Add profit section
            release_html += f"""
                <div class="profit-potential {profit_class}">
                    <strong>{profit_message}</strong>
            """
            
            # Add price comparison data if available
            comparison_data = price_check_results.get('price_comparison', {})
            if comparison_data and comparison_data.get('price_results'):
                price_results = comparison_data.get('price_results', [])
                if price_results:
                    release_html += """
                    <table class="comparison-table">
                        <tr>
                            <th>Marketplace</th>
                            <th>Price</th>
                            <th>Profit</th>
                            <th>ROI %</th>
                        </tr>
                    """
                    
                    for result in price_results:
                        site_name = result.get('site_name', 'Unknown')
                        price = result.get('price')
                        status = result.get('status')
                        
                        if status == 'success' and price is not None:
                            site_profit = price - float(retail_price)
                            roi_percent = (site_profit / float(retail_price)) * 100 if float(retail_price) > 0 else 0
                            
                            release_html += f"""
                            <tr>
                                <td class="price-source">{site_name}</td>
                                <td>${price:.2f}</td>
                                <td>${site_profit:.2f}</td>
                                <td>{roi_percent:.1f}%</td>
                            </tr>
                            """
                        else:
                            error_msg = result.get('error', 'No data available')
                            release_html += f"""
                            <tr>
                                <td class="price-source">{site_name}</td>
                                <td colspan="3" class="no-data">{error_msg}</td>
                            </tr>
                            """
                    
                    release_html += "</table>"
            
            # Close divs
            release_html += """
                </div>
                </div>
            </div>
            """
            
            # Add this release to the main HTML
            html += release_html
        
        # Close HTML
        html += """
        </body>
        </html>
        """
        
        return html
