STREAMLINED SNEAKERBOT
=====================

A simplified bot for tracking sneaker releases and finding profitable opportunities.

QUICK START:
-----------
1. Run the sneakerbot.py to find profitable sneaker deals:
   - Command: python sneakerbot.py --check-profit

2. Run with notifications enabled:
   - Command: python sneakerbot.py --check-profit --notify

3. Save results to a specific file:
   - Command: python sneakerbot.py --check-profit --save results.json

4. Or use the batch file for easy execution:
   - Command: run_sneakerbot.bat

COMPONENTS:
----------
* sneakerbot.py - Main application for finding profitable sneakers
* simplified_config.py - Central configuration file
* scrapers/kicksonfire.py - Scraper for KicksOnFire website
* price_sources/stockx.py - Price adapter for StockX
* utils/profit_checker.py - Utility for checking profit potential

KEY FEATURES:
-----------
* Tracks new and upcoming sneaker releases from KicksOnFire
* Checks current market prices on StockX
* Calculates profit potential considering fees and shipping
* Identifies profitable opportunities based on configurable thresholds
* Saves results for further analysis

REQUIREMENTS:
-----------
* Python 3.7+
* Required packages: requests, beautifulsoup4, fake-useragent, lxml
