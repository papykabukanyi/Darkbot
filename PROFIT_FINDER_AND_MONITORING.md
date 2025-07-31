# Darkbot Enhancements - Profit Analysis & Monitoring

## Overview of Improvements

This document outlines the enhancements made to the Darkbot sneaker scraping system to:
1. Find specific shoes based on profit potential across all brands (not just Jordans)
2. Improve testing and monitoring capabilities
3. Set up proper production logging
4. Enable local testing and monitoring

## Key Files Added or Modified

### 1. Enhanced StockX Profit Finder
- **File**: `enhanced_stockx_profit_finder.py`
- **Purpose**: Advanced tool to search for profitable sneakers across multiple brands and models
- **Features**:
  - Searches 12+ profitable brands (Nike, Adidas, Jordan, New Balance, etc.)
  - Searches 15+ popular models known for resale value
  - Calculates profit metrics (profit amount and percentage)
  - Ranks sneakers by profit potential
  - Saves results in structured JSON format
  - Detailed logging for monitoring

### 2. Updated StockX Test Batch File
- **File**: `test_stockx.bat`
- **Purpose**: Improved testing script for StockX scraper
- **Features**:
  - Runs the enhanced profit finder
  - Creates timestamped logs
  - Displays formatted top 10 profitable sneakers
  - Saves detailed results to JSON

### 3. Production Monitoring Tools
- **File**: `monitor_darkbot.py`
- **Purpose**: Comprehensive monitoring system for Darkbot
- **Features**:
  - Analyzes log files for errors and warnings
  - Checks scraper health and status
  - Monitors system resources (CPU, memory, disk)
  - Provides profit statistics analysis
  - Checks database connectivity and status
  - Dashboard-style visualization
  - Watch mode for real-time monitoring

### 4. Monitoring Dashboard Batch File
- **File**: `monitor_darkbot.bat`
- **Purpose**: Easy-to-run script for monitoring
- **Features**:
  - Checks for required dependencies
  - Installs missing packages if needed
  - Runs the monitoring dashboard in watch mode

## How to Use These Tools

### Finding the Most Profitable Sneakers
1. Run `test_stockx.bat` from the command line
2. The script will search for profitable sneakers across all configured brands and models
3. Results will be displayed on screen and saved to `stockx_profit_analysis.json`
4. Logs will be saved to the `logs` directory with timestamps

### Monitoring the Production Environment
1. Run `monitor_darkbot.bat` from the command line
2. The dashboard will display:
   - System resource usage
   - Scraper health status
   - Error and warning counts
   - Profit analysis statistics
   - Database connectivity status
3. The dashboard updates automatically every 60 seconds
4. Full results are also saved to `darkbot_monitor_summary.json`

### Adding More Brands or Models to Track
1. Open `enhanced_stockx_profit_finder.py`
2. Add brands to the `PROFITABLE_BRANDS` list
3. Add models to the `PROFITABLE_MODELS` list
4. Run the script again to include these in searches

## Production Logging Configuration

The monitoring system is designed to work with logs structured as follows:

1. Store all logs in a `logs` directory
2. Use proper logging format with timestamps and levels
3. Include detailed information in log messages
4. Use consistent logging pattern across scrapers

The monitoring tool will automatically find and analyze these logs.

## Technical Notes

### Dependencies
- Python 3.6+
- Required packages: psutil, tabulate, beautifulsoup4, requests, pymongo

### Configuration
- The monitoring system reads configuration from the standard config files
- No additional configuration is required
- The monitoring dashboard automatically adapts to your environment

### Best Practices
1. Run the profit finder weekly to stay updated on market trends
2. Check the monitoring dashboard daily in production
3. Review error logs regularly
4. Keep the database connection details secure

## Future Enhancements
1. Email or SMS alerts for critical errors
2. Web-based monitoring dashboard
3. Historical trend analysis for profit potential
4. Integration with additional market data sources

## Contact & Support
For any issues or questions regarding these enhancements, please contact the development team.
