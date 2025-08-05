"""
Simple Flask application for Darkbot with OAuth support
"""

import os
from flask import Flask, redirect, request, session, url_for, jsonify
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
