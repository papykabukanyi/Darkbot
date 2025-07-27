# Sneaker Deal Bot

A powerful bot for finding and analyzing sneaker deals across multiple websites. This bot scrapes popular sneaker websites for discounts, analyzes potential profit margins, and sends notifications when profitable deals are found.

## Features

- 🌐 Scrapes multiple sneaker websites including Foot Locker, Champs Sports, Sneakers.com, and more
- 💰 Calculates potential profit based on retail vs. market price
- 📊 Stores deal data in CSV and/or MongoDB for analysis
- 📧 Sends email notifications for new deals
- 🤖 Supports scheduled runs for continuous monitoring
- 🔍 Built-in deal viewer for quickly checking recent finds
- ⚙️ Highly configurable through config.py and environment variables

## Setup

### Prerequisites

- Python 3.7+
- pip (Python package manager)
- Chrome/Chromium (for Selenium-based scraping)
- SMTP access for email notifications

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sneaker-deal-bot.git
   cd sneaker-deal-bot
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Create a `.env` file in the project root with your settings
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASS=your-password-or-app-password
   EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
   EMAIL_INTERVAL_MINUTES=30
   MONGODB_CONNECTION_STRING=mongodb://username:password@hostname:port/database
   MONGODB_DATABASE=sneakerbot
   MONGODB_COLLECTION=deals
   ```

## Usage

### Basic Usage

Run the bot once:
```
python main_improved.py
```

Run the bot continuously on a schedule:
```
python main_improved.py --continuous
```

Scrape specific websites only:
```
python main_improved.py --sites footlocker champssports
```

### Viewing Deals

View recent deals from CSV:
```
python view_deals.py
```

View recent deals from MongoDB:
```
python view_deals.py --source mongodb
```

Filter by minimum discount:
```
python view_deals.py --min-discount 40
```

Filter by brand:
```
python view_deals.py --brand "nike"
```

Export to JSON or CSV:
```
python view_deals.py --format json > deals.json
python view_deals.py --format csv > deals.csv
```

### Windows Batch Files

For Windows users, simple batch files are included:

- `run_improved_bot.bat` - Run the bot with arguments
- `view_deals.bat` - View recent deals with arguments

## Configuration

You can customize the bot by editing `config.py`:

- `WEBSITES`: Define target websites and rate limits
- `MIN_DISCOUNT_PERCENT`: Minimum discount to consider (default: 30%)
- `BRANDS_OF_INTEREST`: List of brands to focus on
- `SAVE_TO_CSV`: Whether to save to CSV (default: True)
- `CSV_FILENAME`: CSV file name (default: 'sneaker_deals.csv')
- `DATABASE_ENABLED`: Whether to use SQLite database (default: False)
- `MONGODB_ENABLED`: Whether to use MongoDB (default: True)
- `EMAIL_NOTIFICATIONS`: Enable email notifications (default: True)
- `EMAIL_INTERVAL_MINUTES`: Interval for email notifications (default: 30)

## Extending the Bot

### Adding New Websites

1. Create a new scraper class in the `scrapers` directory that inherits from `BaseSneakerScraper`
2. Implement the `search_products` and `get_product_details` methods
3. Add the website to the `WEBSITES` dictionary in `config.py`
4. Add the scraper to the mapping in `scrapers/factory.py`

### Troubleshooting

- Check logs in `sneaker_bot.log` for detailed error information
- For Selenium issues, try setting `HEADLESS_BROWSER = False` in `config.py` to see what's happening
- If a specific scraper fails, the bot will automatically fall back to the generic scraper

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Always respect website terms of service and robots.txt rules. The authors are not responsible for any misuse of this software.
