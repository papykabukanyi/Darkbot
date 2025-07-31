DARKBOT - Sneaker Deal Finder
============================

This application finds profitable sneaker deals from various websites.

QUICK START:
-----------
1. Run main.py to start the normal scraping process
   - Command: python main.py

2. Find profitable items across multiple sources:
   - Command: run_profit_finder.bat

3. Run specific test scripts:
   - Test Adidas scraper: test_adidas_scraper.bat
   - Test HTML unescaping: test_html_unescape.bat
   - Test all components: run_all_tests.bat

4. Monitor the application:
   - Run monitor_darkbot.bat

MAIN SCRIPTS:
------------
* main.py - Main application for finding deals
* monitor_darkbot.py - Monitoring dashboard for production
* multi_source_profit_finder.py - Cross-marketplace profit analysis tool
* enhanced_stockx_profit_finder.py - Advanced tool for finding profitable sneakers

KEY DIRECTORIES:
--------------
* scrapers/ - All website scrapers
* utils/ - Utility modules
* config/ - Configuration files
* logs/ - Application logs (created automatically)

CONFIGURATION:
-------------
Edit the following files to configure the application:
* config/sites.py - Website configurations
* config/__init__.py - General settings

USEFUL COMMANDS:
--------------
* Find deals on all sites: python main.py
* Find deals on specific site: python main.py --sites adidas
* Run in continuous mode: python main.py --continuous
* Send email notifications: python main.py --email
* Find multi-source profits: python multi_source_profit_finder.py
* Monitor application: python monitor_darkbot.py --watch

For more details on specific modules, check the documentation in each file.

REQUIREMENTS:
-----------
* Python 3.6+
* Required packages: requests, beautifulsoup4, selenium, pymongo, psutil, tabulate
