"""
Simple Flask application for Darkbot with OAuth support
"""

import os
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/flask_app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Apply Flask compatibility fixes
try:
    import flask_compat
    flask_compat.patch_flask()
    logger.info("Flask compatibility patches applied")
except Exception as e:
    logger.error(f"Error applying Flask compatibility patches: {e}")
    logger.error(traceback.format_exc())

# Import Flask
try:
    from flask import Flask, redirect, request, session, url_for, jsonify
    logger.info("Flask successfully imported")
except ImportError as e:
    logger.error(f"Error importing Flask: {e}")
    logger.error("Please run fix_flask_deps.bat to install compatible versions")
    sys.exit(1)

from dotenv import load_dotenv
import requests
from utils.stockx_price_checker import StockXPriceChecker

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Log app creation success
logger.info("Flask app created successfully")

# OAuth configuration
CLIENT_ID = os.getenv('OAUTH_CLIENT_ID')
CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')
REDIRECT_URI = os.getenv('RAILWAY_CALLBACK_URL', 'https://darkbot-production.up.railway.app/auth/callback')

@app.route('/')
def index():
    """Home page"""
    if 'access_token' in session:
        return f"""
        <h1>Darkbot API</h1>
        <p>Authentication Status: <strong>Authenticated</strong></p>
        <p><a href="/api/status">Check API Status</a></p>
        <p><a href="/logout">Logout</a></p>
        """
    else:
        return f"""
        <h1>Darkbot API</h1>
        <p>Authentication Status: <strong>Not Authenticated</strong></p>
        <p><a href="/login">Login</a></p>
        """

@app.route('/login')
def login():
    """Redirect to OAuth provider login page"""
    auth_url = f"https://your-oauth-provider.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    return redirect(auth_url)

@app.route('/auth/callback')
def callback():
    """Handle OAuth callback"""
    code = request.args.get('code')
    if not code:
        return "No authorization code provided", 400
    
    # Exchange code for access token
    token_url = "https://your-oauth-provider.com/oauth/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        return "Failed to get access token", 400
    
    token_data = response.json()
    session['access_token'] = token_data.get('access_token')
    
    return redirect('/')

@app.route('/logout')
def logout():
    """Log out the user"""
    session.pop('access_token', None)
    return redirect('/')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    if 'access_token' not in session:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    return jsonify({
        'status': 'active',
        'version': '1.0.0',
        'message': 'Darkbot API is running'
    })

@app.route('/api/stockx/price', methods=['GET'])
def stockx_price():
    """Get price information from StockX"""
    try:
        # Get query parameters
        query = request.args.get('query')
        sku = request.args.get('sku')
        retail_price = request.args.get('retail_price')
        
        # Validate parameters
        if not query and not sku:
            logger.error("No query or SKU provided")
            return jsonify({
                'status': 'error',
                'message': 'Either query or SKU is required'
            }), 400
        
        # Convert retail price to float if provided
        if retail_price:
            try:
                retail_price = float(retail_price)
            except ValueError:
                logger.error(f"Invalid retail price format: {retail_price}")
                return jsonify({
                    'status': 'error',
                    'message': 'Retail price must be a number'
                }), 400
        
        # Initialize StockX price checker
        logger.info(f"Initializing StockX price checker for query: {query}, SKU: {sku}")
        price_checker = StockXPriceChecker()
        
        # Get price information
        if sku:
            logger.info(f"Checking price with SKU: {sku}")
            result = price_checker.check_prices(query or sku, retail_price, sku=sku)
        else:
            logger.info(f"Checking price with query only: {query}")
            result = price_checker.check_prices(query, retail_price)
        
        # Generate a report
        logger.info("Generating price report")
        report = price_checker.generate_price_comparison_report(
            query or sku,
            retail_price=retail_price,
            sku=sku
        )
        
        return jsonify({
            'status': 'success',
            'data': report
        })
        
    except Exception as e:
        logger.error(f"Error getting StockX price: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    try:
        # Check for werkzeug compatibility issue
        try:
            # Attempt to import url_quote - this will be handled by flask_compat
            # if there's an issue, but we want to check it directly here too
            try:
                from werkzeug.urls import url_quote
                logger.info("werkzeug.urls.url_quote imported successfully")
            except ImportError:
                logger.warning("Could not import werkzeug.urls.url_quote directly")
                logger.info("Checking if flask_compat patched it correctly...")
                
                # Check if our patch worked
                import werkzeug
                if hasattr(werkzeug, 'urls') and hasattr(werkzeug.urls, 'url_quote'):
                    logger.info("Successfully using patched url_quote from flask_compat")
                else:
                    logger.error("url_quote patch failed!")
                    logger.error("Please run fix_flask_deps.bat (Windows) or fix_flask_deps.sh (Linux/Mac)")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Error checking werkzeug compatibility: {str(e)}")
            logger.error(traceback.format_exc())
            logger.error("Please run fix_flask_deps.bat (Windows) or fix_flask_deps.sh (Linux/Mac)")
            sys.exit(1)
            
        port = int(os.getenv('PORT', 5000))
        logger.info(f"Starting Flask app on port {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Error starting Flask app: {str(e)}")
        logger.error(traceback.format_exc())
