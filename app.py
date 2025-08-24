"""
Simple Flask API for the Advanced Scalping Bot
"""
import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'active',
        'bot': 'Advanced Scalping Bot',
        'version': '2.0.0',
        'message': 'Scalping bot is running in the background'
    })

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'active',
        'bot_running': True,
        'profit_threshold': os.getenv('PROFIT_THRESHOLD', '50'),
        'check_interval': os.getenv('CHECK_INTERVAL', '300'),
        'email_enabled': bool(os.getenv('EMAIL_ADDRESS'))
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
