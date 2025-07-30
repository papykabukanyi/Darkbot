#!/usr/bin/env python
"""
Test script for HTML unescaping functionality in the base scraper
"""

import sys
import os
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HTMLUnescapeTest")

# Add parent directory to path so we can import from the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseSneakerScraper
import html
from bs4 import BeautifulSoup

def test_html_unescaping():
    """Test the HTML unescaping functionality"""
    print("=" * 50)
    print("Testing HTML unescaping functionality")
    print("=" * 50)
    
    # Sample of escaped HTML that might come from websites
    escaped_html = """
    \u003Cdiv class="grid-product__wrapper">\u003C/div>    
    \u003Cdiv class="grid-product__image-wrapper">
      \u003Ca class="grid-product__image-link" href="/collections/sale/products/undefeated-east-crewneck?variant=39740160344325">
        \u003Cspan class="grid-product__title">UNDEFEATED EAST CREWNECK\u003C/span>
        \u003Cspan class="money">$42.00\u003C/span>
      \u003C/a>
    \u003C/div>
    """
    
    print("\nOriginal escaped HTML:")
    print(escaped_html[:100] + "...")
    
    # Method 1: Using html.unescape
    print("\nMethod 1 - Using html.unescape:")
    unescaped_html1 = html.unescape(escaped_html)
    print(unescaped_html1[:100] + "...")
    
    # Method 2: String replacement
    print("\nMethod 2 - Using string replacement:")
    unescaped_html2 = escaped_html.replace('\\u003C', '<').replace('\\u003E', '>')
    print(unescaped_html2[:100] + "...")
    
    # Method 3: Combined approach (our implementation)
    print("\nMethod 3 - Combined approach:")
    unescaped_html3 = html.unescape(escaped_html).replace('\\u003C', '<').replace('\\u003E', '>')
    print(unescaped_html3[:100] + "...")
    
    # Test parsing with BeautifulSoup
    print("\nParsing with BeautifulSoup:")
    soup1 = BeautifulSoup(unescaped_html1, 'lxml')
    soup2 = BeautifulSoup(unescaped_html2, 'lxml')
    soup3 = BeautifulSoup(unescaped_html3, 'lxml')
    
    # Extract title and price
    print("\nExtracted data from Method 1:")
    title1 = soup1.select_one('.grid-product__title')
    price1 = soup1.select_one('.money')
    print(f"Title: {title1.get_text() if title1 else 'Not found'}")
    print(f"Price: {price1.get_text() if price1 else 'Not found'}")
    
    print("\nExtracted data from Method 2:")
    title2 = soup2.select_one('.grid-product__title')
    price2 = soup2.select_one('.money')
    print(f"Title: {title2.get_text() if title2 else 'Not found'}")
    print(f"Price: {price2.get_text() if price2 else 'Not found'}")
    
    print("\nExtracted data from Method 3:")
    title3 = soup3.select_one('.grid-product__title')
    price3 = soup3.select_one('.money')
    print(f"Title: {title3.get_text() if title3 else 'Not found'}")
    print(f"Price: {price3.get_text() if price3 else 'Not found'}")
    
    print("\nTest completed")
    print("=" * 50)

if __name__ == "__main__":
    test_html_unescaping()
