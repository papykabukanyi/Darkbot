#!/usr/bin/env python3
"""
Railway Environment Variables Setup
Copy your .env variables to Railway dashboard
"""
import os
from dotenv import load_dotenv

def print_railway_vars():
    """Print all environment variables in Railway format"""
    load_dotenv()
    
    print("🚀 RAILWAY ENVIRONMENT VARIABLES SETUP")
    print("="*50)
    print("Copy these to your Railway dashboard (Variables tab):")
    print("="*50)
    
    vars_to_copy = [
        'EMAIL_ADDRESS',
        'EMAIL_PASSWORD', 
        'EMAIL_RECIPIENTS',
        'SMTP_SERVER',
        'SMTP_PORT',
        'PROFIT_THRESHOLD',
        'CHECK_INTERVAL',
        'STOCKX_API_KEY',
        'STOCKX_CLIENT_ID',
        'STOCKX_CLIENT_SECRET',
        'STOCKX_COOKIE'
    ]
    
    for var in vars_to_copy:
        value = os.getenv(var)
        if value:
            print(f"{var}={value}")
        else:
            print(f"{var}=NOT_SET")
    
    print("="*50)
    print("📋 TO FIX THE DEPLOYMENT:")
    print("1. Go to railway.app")
    print("2. Select your Darkbot project")
    print("3. Go to Variables tab")
    print("4. Add each variable above")
    print("5. Redeploy the service")
    print("="*50)

if __name__ == "__main__":
    print_railway_vars()
