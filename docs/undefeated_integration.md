# Undefeated.com Integration Documentation

## Overview

This document describes the integration of Undefeated.com into the Darkbot sneaker scraper system. The integration includes a dedicated scraper for Undefeated.com, updates to the site configuration, and enhancements to the email notification system.

## Files Modified/Added

1. **config/sites.py**
   - Added Undefeated.com to the site configuration
   - Added it to DEFAULT_SITES list

2. **scrapers/undefeated.py**
   - New dedicated scraper for Undefeated.com
   - Includes search_products and get_product_details methods
   - Has brand detection from product titles

3. **scrapers/factory.py**
   - Added mapping for the Undefeated scraper

4. **notifications.py**
   - Updated email templates to include Undefeated.com
   - Enhanced site listing in email notifications
   - Dynamic generation of site lists from configuration

5. **run_with_undefeated.py**
   - New script to run the bot with focus on Undefeated.com
   - Custom command line arguments
   - Specialized scheduling and email reporting

6. **test_undefeated.py**
   - Test script to verify the Undefeated scraper functionality
   - Tests basic product search, sale products, and details

7. **test_deal_intelligence.py**
   - New script to test cross-site product comparison
   - Helps identify the same product at different prices across sites

8. **README.md**
   - Updated to include Undefeated.com
   - Added section on the new run script
   - Added July 2025 update notes

## Usage Instructions

### Running with Undefeated Focus

To run the bot with a focus on Undefeated.com:

```bash
python run_with_undefeated.py
```

Options:
- `--interval N`: Set minutes between scans (default: 30)
- `--no-continuous`: Run once and exit instead of continuously

### Testing the Undefeated Scraper

```bash
python test_undefeated.py
```

### Testing Deal Intelligence

```bash
python test_deal_intelligence.py
```

## Technical Implementation Details

### Undefeated.com Scraper

The Undefeated scraper is implemented as a class that inherits from BaseSneakerScraper. Key features:

1. **Product Search**: Scrapes product listings from Undefeated.com
   - Handles both regular and sale product pages
   - Extracts title, brand, price, original price, image URLs
   - Calculates discount percentages

2. **Product Details**: Gets detailed information about specific products
   - Extracts full product information from product pages
   - Handles various page structures with fallbacks
   - Extracts SKU/style codes when available

3. **Brand Detection**: Uses a method to extract brand names from product titles

### Deal Intelligence System

The deal intelligence system helps identify the same products across different sites:

1. Uses string similarity to match product titles
2. Compares prices across sites to find the best deals
3. Prioritizes matches above a specified similarity threshold

### Email Notification Enhancements

1. Dynamic generation of site lists from actual configuration
2. Ensures Undefeated is always included in the list
3. Properly formats site URLs for display in both HTML and plain text emails

## Testing and Validation

1. The Undefeated scraper has been tested with both search_products and get_product_details methods
2. The email notification system has been tested with the updated site listings
3. The deal intelligence system has been tested for cross-site product matching
