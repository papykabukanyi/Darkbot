# Darkbot Fixes

This document provides instructions for fixing critical issues in Darkbot, including WebDriver crashes and the Undefeated scraper integration.

## Fixed Issues

### 1. WebDriver Initialization Crash

**Problem:** The WebDriver initialization was failing due to issues with ChromeDriver path detection, particularly in Linux/Docker environments. The system was trying to use THIRD_PARTY_NOTICES.chromedriver as the executable.

**Solution:** 
- Fixed the `setup_selenium_driver()` function in `base_scraper.py` to properly handle ChromeDriver paths
- Added improved error detection for NOTICES files and implemented proper fallback mechanisms
- Enhanced error handling with multiple initialization methods

### 2. Undefeated Scraper Integration

**Problem:** The Undefeated scraper needed proper site configuration and integration.

**Solution:**
- Added Undefeated site configuration in `config/sites.py` with all required parameters
- Added Undefeated to the DEFAULT_SITES list for automatic inclusion in scraping runs
- Updated the scraper factory in `factory.py` to properly create Undefeated scraper instances
- Fixed the site_config access in the Undefeated scraper

### 3. Error Handling and Logging

**Problem:** Limited error handling and diagnostics were making debugging difficult.

**Solution:**
- Added more detailed error handling in the Undefeated scraper
- Enhanced logging throughout the system
- Created comprehensive test scripts to verify functionality

## Verification Scripts

Several test scripts have been created to verify the fixes:

1. **test_webdriver.py** - Tests WebDriver initialization
2. **test_webdriver_file.py** - Tests WebDriver with file output
3. **test_undefeated.py** - Tests the Undefeated scraper
4. **test_undefeated_file.py** - Tests the Undefeated scraper with file output
5. **verify_fixes.py** - A comprehensive verification of all fixes

## How to Verify Fixes

Run the verification script to ensure all components are working correctly:

```
verify_fixes.bat
```

This will perform the following checks:
- WebDriver installation and initialization
- Undefeated scraper module availability
- Scraper factory configuration
- Site configuration completeness

Results will be saved to `verification_results.txt` for review.

## Previous R2Storage Fix

The previous R2Storage fix has been preserved. If you're encountering issues related to R2Storage, follow these instructions:

1. Run the update_fix_r2storage.bat script, which will:
   - Create a backup of main.py
   - Update storage/__init__.py to remove R2Storage references
   - Create a simplified main.py that uses only MongoDB
   - Create a docker-healthcheck.sh script

2. Deploy the updated code to Railway

## Configuration

Ensure these environment variables are properly set in Railway:

- `MONGODB_CONNECTION_STRING` - Your MongoDB connection string
- `MONGODB_DATABASE` - Database name (default: sneakerbot)
- `MONGODB_COLLECTION` - Collection name (default: deals)
- `EMAIL_NOTIFICATIONS` - Enable/disable email notifications (True/False)
- `EMAIL_INTERVAL_MINUTES` - How often to send email reports (default: 30)
- `EMAIL_RECIPIENTS` - Comma-separated list of email recipients
- `SMTP_HOST` - SMTP server hostname (default: smtp.gmail.com)
- `SMTP_PORT` - SMTP server port (default: 587)
- `SMTP_USER` - SMTP username (your email address)
- `SMTP_PASS` - SMTP password or app password
