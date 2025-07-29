# StockX Scraper Documentation

## Overview

This document provides technical details on the StockX scraper implementation for Darkbot. The scraper is designed to mimic human browsing behavior to avoid detection while gathering price data and market insights from StockX.com.

## Features

1. **Advanced Anti-Detection Mechanisms**
   - Dynamic user agent rotation
   - JavaScript property spoofing to hide automation
   - Human-like mouse movements and scrolling patterns
   - Random timing between actions
   - Session cookie management

2. **Data Collection Capabilities**
   - Product title and brand extraction
   - Current market prices (lowest ask)
   - Retail prices for discount calculation
   - Last sale prices for market trend analysis
   - SKU/style code extraction
   - Release date information
   - Available sizes with price variations
   - Product images
   - Resale value calculation

3. **Search Functionality**
   - Popular products browsing
   - Keyword-based search
   - Under retail deals detection
   - Brand-specific filtering

## Implementation Details

### Browser Automation

The scraper uses Selenium WebDriver with custom configurations to evade bot detection:

```python
def _prepare_driver(self):
    """
    Prepare the Selenium driver with additional settings to avoid detection
    """
    if not self.driver:
        return
        
    # StockX-specific browser settings to avoid detection
    self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            // Overwrite navigator properties to appear as a normal browser
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Modify other detection mechanisms
            window.chrome = {
                runtime: {}
            };
        """
    })
```

### Human-Like Behavior

The scraper implements sophisticated patterns to mimic human browsing:

```python
def _scroll_page_like_human(self):
    """
    Scroll the page in a way that mimics human behavior
    """
    # Calculate number of scroll steps with randomization
    num_steps = random.randint(5, 10)
    
    # Execute scrolling with random pauses and jiggle
    for i in range(num_steps):
        # Add randomness to scroll position
        target = int((i+1) * scroll_step * random.uniform(0.8, 1.2))
        
        # Execute scroll with random pauses
        self.driver.execute_script(f"window.scrollTo(0, {target});")
        time.sleep(random.uniform(0.5, 2.0))
```

## Usage Example

```python
from config.sites import SNEAKER_SITES
from scrapers.stockx import StockXScraper

# Get site config and initialize scraper
site_config = SNEAKER_SITES.get('stockx', {})
scraper = StockXScraper(site_config)

# Search for products
with scraper as s:
    # Get products on sale (below retail)
    sale_products = s.search_products(category='sale')
    
    # Search for specific sneakers
    jordan_products = s.search_products(keywords=['jordan', 'retro'])
    
    # Get detailed information about a product
    if jordan_products:
        product_url = jordan_products[0].get('url')
        details = s.get_product_details(product_url)
```

## Best Practices

1. **Rate Limiting**
   - The default rate limit is set to 20 seconds between requests
   - Adjust the `rate_limit` parameter in the site config for more aggressive or conservative scraping

2. **Proxy Rotation**
   - Use rotating proxies to prevent IP bans
   - Configure proxy settings in the main config file

3. **Session Management**
   - The scraper maintains session cookies between requests
   - Consider implementing session rotation for long scraping sessions

4. **Error Handling**
   - The scraper has comprehensive error handling and logging
   - Monitor logs for detection patterns and adjust scraping behavior accordingly

## Testing

A dedicated test script is provided (`test_stockx.py`) to validate the scraper's functionality. Run it using:

```bash
python test_stockx.py
```

Or use the batch file:

```bash
test_stockx.bat
```
