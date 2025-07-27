# Darkbot Sneaker Deal Finder

A sophisticated web scraper for finding profitable sneaker deals from popular retail sites with anti-bot detection measures.

## Supported Websites

### Retail Sites (Working Scrapers)

- FootLocker (www.footlocker.com)
- FinishLine (www.finishline.com)
- JDSports (www.jdsports.com)
- Nike (www.nike.com)
- Adidas (www.adidas.com)

### Market Price Sites

- StockX (www.stockx.com)
- GOAT (www.goat.com)
- FlightClub (www.flightclub.com)

### Additional Sites (Require Configuration)

- Eastbay (www.eastbay.com)
- Champs Sports (www.champssports.com)
- New Balance (www.newbalance.com)
- Puma (www.puma.com)
- Stadium Goods (www.stadiumgoods.com)

## Features

- Price tracking and comparison with StockX and GOAT
- Human-like browsing behavior to avoid detection
- IP rotation and proxy management to prevent bans
- CAPTCHA detection and avoidance
- MongoDB database for deal storage and analytics
- Intelligent profit calculation and trend analysis
- Email notifications for profitable deals
- Scheduled execution at regular intervals
- Multiple data export formats (CSV, JSON)
- Adaptive iteration based on deal discovery

## Requirements

- Python 3.8+
- Required packages are listed in requirements.txt

## Setup

1. Set up a virtual environment (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure settings in `config.py`
   - Set your email notification preferences
   - Configure MongoDB connection settings
   - Adjust website URLs and rate limits
   - Set minimum discount percentage

4. MongoDB Configuration:
   - You need to configure your MongoDB connection details in the .env file
   - The format should be:

   ```text
   MONGODB_CONNECTION_STRING=mongodb://username:password@hostname:port/
   ```

   - You can also modify settings in config.py or use command-line arguments

## Running the Bot

### Railway Deployment (Recommended for 24/7 Operation)

For continuous 24/7 operation, deploy the bot to Railway:

1. Follow the instructions in [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
2. Railway will keep the bot running automatically
3. No need to keep your computer on
4. Automatic restart if the bot crashes

### Local Automatic Mode

For running on your local machine:

- `auto_start.bat` - Sets up environment, installs requirements, and starts the bot in continuous mode with 30-minute intervals

This script will:

1. Create a virtual environment if needed
2. Install all required packages
3. Start the bot in continuous mode with 30-minute intervals
4. Log all output to a timestamped log file
5. Send email notifications every 30 minutes to configured recipients

### Other Quick Start Options

Alternative batch files for different use cases:

- `run_fixed_bot.bat` - Runs the bot with all working scrapers and logs output
- `run_working_scrapers.bat` - Runs only the verified scrapers

### Command Line Usage

```bash
# Basic usage
python main.py                                        # Run once
python main.py --continuous --interval 30             # Run every 30 minutes

# Site selection
python main.py --sites sneakers champssports          # Run for specific sites
python main.py --list-sites                           # Show all available sites

# MongoDB specific options
python main.py --mongodb                              # Force enable MongoDB storage
python main.py --mongodb-connection "your-connection-string"

# Advanced usage
python main.py --continuous --interval 30 --iterate   # Auto-continue if new deals found
python main.py --export-json                          # Export deals to JSON
python main.py --verbose                              # Show detailed output
```

## Troubleshooting

If you encounter issues:

1. Make sure you're using the correct Python version:

   ```bash
   python --version  # Should be 3.8+
   ```

2. Run the debug script to test scrapers:

   ```bash
   python debug_scraping.py
   ```

3. Check for log files:

   ```text
   bot_test.log
   darkbot_run_*.log
   ```

4. Common issues:
   - **No output**: Make sure you're using `--verbose` flag
   - **Scraper errors**: Some websites may have changed their structure
   - **MongoDB errors**: Verify your connection string is valid
   - **IP bans**: Check your proxy configuration in [PROXY_CONFIGURATION.md](PROXY_CONFIGURATION.md)

## Recent Fixes

- Fixed missing `scrape()` method in scrapers
- Updated MongoDB connection handling
- Added additional debugging tools
- Increased page load timeout for more reliable scraping
- Created convenient batch files for easier use

## Disclaimer

This tool is for educational purposes only. Always respect website terms of service and robots.txt rules. Use responsibly and implement proper rate limiting to avoid impacting website performance.
