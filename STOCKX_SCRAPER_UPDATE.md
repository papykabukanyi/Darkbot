# StockX Scraper Update

## Overview

This update adds a sophisticated StockX scraper to the Darkbot system. The new scraper is designed to mimic human behavior to avoid bot detection while gathering valuable pricing data from StockX.com. This information can be used to identify profitable resale opportunities.

## What's New

1. **New StockX Scraper**
   - Created a dedicated `stockx.py` scraper with advanced anti-detection features
   - Implemented human-like behavior including random scrolling and mouse movements
   - Added detailed product data extraction including market prices, retail prices, and SKUs
   - Included resale value calculation for profit potential analysis

2. **Documentation**
   - Added detailed documentation in `docs/stockx_scraper.md`
   - Updated the main README.md to include StockX in the list of working scrapers

3. **Testing Tools**
   - Created `test_stockx.py` and `test_stockx.bat` for easy testing
   - Added a new scraper health check utility in `scripts/check_scrapers.py`

## Technical Details

The StockX scraper includes several advanced features to avoid detection:

1. **Browser Fingerprint Spoofing**
   - Overriding WebDriver detection properties
   - Emulating normal browser behavior
   - Custom user agent rotation

2. **Human-like Interaction Patterns**
   - Variable-speed scrolling with random pauses
   - Occasional "jiggle" movements to simulate human imprecision
   - Random timing between actions

3. **Session Management**
   - Cookie tracking between requests
   - Header consistency
   - Proxy rotation support

## Usage

### Basic Usage

To use the StockX scraper:

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
```

### Testing

Run the included test script to verify functionality:

```bash
python test_stockx.py
```

Or use the batch file:

```bash
test_stockx.bat
```

### Health Check

Use the new scraper health check utility to verify all scrapers:

```bash
python scripts/check_scrapers.py
```

Or check specific scrapers:

```bash
python scripts/check_scrapers.py --sites stockx nike adidas
```

## Conclusion

This update enhances Darkbot's market analysis capabilities by adding sophisticated access to StockX pricing data. The implementation uses advanced techniques to avoid detection while gathering valuable market insights for sneaker resale opportunities.
