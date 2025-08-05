"""
Sneaker Detail Handler - Handles requests for detailed sneaker information pages
with advanced dynamic functionality
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import http.server
import socketserver
import urllib.parse
import jinja2
import threading
import webbrowser
import time
import re
import socket
from http import HTTPStatus

logger = logging.getLogger("SneakerBot")

class SneakerDetailServer(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for sneaker detail pages"""
    
    def __init__(self, *args, **kwargs):
        self.detail_handler = kwargs.pop('detail_handler')
        self.db = kwargs.pop('db', None)
        self.directory = kwargs.pop('directory', None)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for detail pages"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Check if this is a request for a detail page
        if path.startswith('/detail/'):
            # Extract SKU from path
            sku = path[8:]  # Remove '/detail/' prefix
            
            # Handle query parameters
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # Check if SKU is valid
            if not sku:
                self.send_error(HTTPStatus.NOT_FOUND, "SKU not specified")
                return
            
            # Try to fetch sneaker data from database or cache
            sneaker_data = self.get_sneaker_data(sku)
            
            if sneaker_data:
                # Generate HTML content
                html_content, _ = self.detail_handler.generate_detail_page(sneaker_data)
                
                if html_content:
                    # Send response
                    self.send_response(HTTPStatus.OK)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Content-Length', str(len(html_content)))
                    self.end_headers()
                    self.wfile.write(html_content.encode('utf-8'))
                    return
            
            # If we get here, we couldn't generate the detail page
            self.send_error(HTTPStatus.NOT_FOUND, f"Sneaker with SKU '{sku}' not found")
            return
            
        # For all other requests, use the default handler
        return super().do_GET()
    
    def get_sneaker_data(self, sku):
        """Get sneaker data by SKU"""
        # Try to fetch from database if available
        if self.db:
            sneaker = self.db.get_release_by_sku(sku)
            if sneaker:
                return sneaker
        
        # Try to load from cache
        cache_dir = os.path.join(self.detail_handler.data_dir, "cache")
        cache_file = os.path.join(cache_dir, f"sneaker_{sku}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading cache file for SKU {sku}: {e}")
        
        # If all else fails, return None
        return None

class SneakerDetailHandler:
    """Handler for sneaker detail pages"""
    
    def __init__(self, base_dir=None, db=None, port=8000):
        """Initialize the handler with the base directory"""
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.templates_dir = os.path.join(self.base_dir, "templates")
        self.cache_dir = os.path.join(self.data_dir, "cache")
        self.detail_pages_dir = os.path.join(self.data_dir, "detail_pages")
        self.db = db
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_server_running = False
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.templates_dir, self.cache_dir, self.detail_pages_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Initialize Jinja2 template environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.template_env.filters['floatformat'] = self._float_format_filter
    
    def start_detail_server(self):
        """Start the HTTP server for serving detail pages"""
        if self.is_server_running:
            logger.info("Detail server is already running")
            return True
        
        # Find an available port if the default is taken
        if not self._is_port_available(self.port):
            for port in range(8001, 8100):
                if self._is_port_available(port):
                    self.port = port
                    break
            else:
                logger.error("No available ports found for detail server")
                return False
        
        try:
            # Create a handler class with access to our detail handler
            handler = lambda *args, **kwargs: SneakerDetailServer(*args, 
                                                             detail_handler=self,
                                                             db=self.db,
                                                             directory=self.detail_pages_dir,
                                                             **kwargs)
            
            # Create server
            self.server = socketserver.ThreadingTCPServer(("", self.port), handler)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.is_server_running = True
            logger.info(f"Detail server started on port {self.port}")
            
            # Store server info in a file for external access
            self._save_server_info()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting detail server: {e}")
            return False
    
    def stop_detail_server(self):
        """Stop the HTTP server"""
        if not self.is_server_running:
            return
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                self.is_server_running = False
                logger.info("Detail server stopped")
        except Exception as e:
            logger.error(f"Error stopping detail server: {e}")
    
    def _is_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return True
        except:
            return False
    
    def _save_server_info(self):
        """Save server information to a file"""
        info = {
            "port": self.port,
            "base_url": f"http://localhost:{self.port}",
            "started_at": datetime.now().isoformat(),
            "directory": self.detail_pages_dir
        }
        
        info_file = os.path.join(self.data_dir, "detail_server_info.json")
        try:
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving server info: {e}")
    
    def get_detail_url(self, sku):
        """Get the URL for a sneaker detail page"""
        if not self.is_server_running:
            # Try to start the server
            if not self.start_detail_server():
                return None
        
        return f"http://localhost:{self.port}/detail/{sku}"
    
    def cache_sneaker_data(self, sneaker_data):
        """Cache sneaker data for faster access"""
        if not sneaker_data or not sneaker_data.get('sku'):
            return False
        
        sku = sneaker_data.get('sku')
        cache_file = os.path.join(self.cache_dir, f"sneaker_{sku}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(sneaker_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error caching sneaker data: {e}")
            return False
    
    def _float_format_filter(self, value, decimal_places=2):
        """Format float to specified decimal places"""
        if value is None:
            return "0.00"
        try:
            return f"{float(value):.{decimal_places}f}"
        except (ValueError, TypeError):
            return "0.00"
    
    def generate_detail_page(self, sneaker_data, output_path=None, refresh_price_data=False):
        """
        Generate a detailed HTML page for a sneaker.
        
        Args:
            sneaker_data: Dictionary containing sneaker information
            output_path: Path where to save the HTML file (optional)
            refresh_price_data: Whether to refresh price data (default: False)
            
        Returns:
            HTML content as string and saved file path (if output_path is provided)
        """
        try:
            title = sneaker_data.get('title', 'Unknown Sneaker')
            logger.info(f"Generating detail page for {title}")
            
            # Cache the sneaker data for future access
            self.cache_sneaker_data(sneaker_data)
            
            # If we need to refresh price data and have the necessary info
            if refresh_price_data and sneaker_data.get('sku') and sneaker_data.get('retail_price'):
                from utils.stockx_price_checker import StockXPriceChecker
                
                checker = StockXPriceChecker()
                comparison_report = checker.generate_price_comparison_report(
                    sneaker_data.get('title'),
                    sneaker_data.get('retail_price'),
                    sneaker_data.get('sku')
                )
                
                # Update price comparison data
                if 'price_check_results' not in sneaker_data:
                    sneaker_data['price_check_results'] = {}
                
                sneaker_data['price_check_results']['price_comparison'] = comparison_report
                
                # Update cached data
                self.cache_sneaker_data(sneaker_data)
            
            # Load the template
            template = self.template_env.get_template('sneaker_detail.html')
            
            # Clean up and prepare data for the template
            template_data = {
                'title': sneaker_data.get('title', 'Unknown Sneaker'),
                'brand': sneaker_data.get('brand', 'Unknown'),
                'sku': sneaker_data.get('sku', 'N/A'),
                'release_date': sneaker_data.get('release_date', 'TBA'),
                'retail_price': sneaker_data.get('retail_price', 0),
                'image_url': sneaker_data.get('image_url', ''),
                'source': sneaker_data.get('source', 'Unknown'),
                'source_url': sneaker_data.get('source_url', '#'),
                'colorway': sneaker_data.get('colorway', ''),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add price comparison data if available
            price_check_results = sneaker_data.get('price_check_results', {})
            price_comparison = price_check_results.get('price_comparison', {})
            
            if price_comparison:
                template_data.update({
                    'best_price': price_comparison.get('best_price', {}),
                    'highest_price': price_comparison.get('highest_price', {}),
                    'price_range': price_comparison.get('price_range', 0),
                    'best_profit': price_comparison.get('best_profit', {}),
                    'price_results': price_comparison.get('price_results', [])
                })
            
            # Add purchase links if available
            purchase_links = sneaker_data.get('purchase_links', [])
            if purchase_links:
                template_data['purchase_links'] = purchase_links
                
            # Add server info for refresh functionality
            template_data['server_port'] = self.port
            template_data['server_running'] = self.is_server_running
            template_data['refresh_url'] = f"/detail/{sneaker_data.get('sku', '')}?refresh=true"
            
            # Render the template
            html_content = template.render(**template_data)
            
            # Save to file if output path is provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"Detail page saved to {output_path}")
                return html_content, output_path
            
            return html_content, None
            
        except Exception as e:
            logger.error(f"Error generating detail page: {e}")
            return None, None
    
    def serve_detail_page(self, sneaker_data, port=8000):
        """
        Generate and serve a detail page for a sneaker.
        
        Args:
            sneaker_data: Dictionary containing sneaker information
            port: Port to serve the page on
            
        Returns:
            URL of the served page
        """
        try:
            # Create a temporary directory for serving files
            temp_dir = os.path.join(self.cache_dir, "temp_serve")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # Generate a safe filename from the sneaker title
            safe_title = "".join(c if c.isalnum() else "_" for c in sneaker_data.get('title', 'sneaker'))
            html_path = os.path.join(temp_dir, f"{safe_title}.html")
            
            # Generate the HTML file
            html_content, _ = self.generate_detail_page(sneaker_data, html_path)
            if not html_content:
                logger.error("Failed to generate HTML content")
                return None
            
            # Start a simple HTTP server in a separate thread
            handler = http.server.SimpleHTTPRequestHandler
            
            class CustomHandler(handler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=temp_dir, **kwargs)
            
            httpd = socketserver.TCPServer(("", port), CustomHandler)
            
            # Start the server in a thread
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Construct the URL
            url = f"http://localhost:{port}/{safe_title}.html"
            logger.info(f"Serving detail page at {url}")
            
            # Open the URL in the default browser
            webbrowser.open(url)
            
            return url
            
        except Exception as e:
            logger.error(f"Error serving detail page: {e}")
            return None
    
    def generate_detail_pages_batch(self, sneakers_data, output_dir=None):
        """
        Generate detail pages for multiple sneakers.
        
        Args:
            sneakers_data: List of dictionaries containing sneaker information
            output_dir: Directory to save the HTML files (optional)
            
        Returns:
            Dictionary mapping sneaker titles to file paths
        """
        if not output_dir:
            output_dir = os.path.join(self.data_dir, "detail_pages")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        results = {}
        for sneaker in sneakers_data:
            # Cache the sneaker data for future dynamic access
            self.cache_sneaker_data(sneaker)
            
            title = sneaker.get('title', 'Unknown')
            sku = sneaker.get('sku', 'unknown')
            safe_title = "".join(c if c.isalnum() else "_" for c in title)
            output_path = os.path.join(output_dir, f"{safe_title}_{sku}.html")
            
            _, saved_path = self.generate_detail_page(sneaker, output_path)
            if saved_path:
                results[title] = saved_path
                
                # If the server is running, update the URL to point to the dynamic version
                if self.is_server_running:
                    results[title + "_url"] = self.get_detail_url(sku)
        
        # Make sure the server is running for dynamic access
        if not self.is_server_running:
            self.start_detail_server()
        
        return results
    
    def update_sneaker_data(self, sku, new_data):
        """
        Update cached sneaker data with new information.
        
        Args:
            sku: The SKU of the sneaker to update
            new_data: New data to merge with existing data
            
        Returns:
            Boolean indicating success
        """
        cache_file = os.path.join(self.cache_dir, f"sneaker_{sku}.json")
        
        try:
            # Load existing data if available
            existing_data = {}
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Update with new data
            existing_data.update(new_data)
            
            # Save updated data
            with open(cache_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error updating sneaker data: {e}")
            return False
