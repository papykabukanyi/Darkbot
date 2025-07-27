# Proxy Configuration

This document provides instructions for configuring and using the proxy rotation system in Darkbot. The proxy system helps avoid IP bans and detection while scraping sneaker websites.

## Overview

The proxy system includes the following features:

- IP rotation to avoid detection and bans
- CAPTCHA detection and handling
- Support for multiple proxy types (HTTP, HTTPS, SOCKS5)
- Automatic proxy verification
- Performance tracking and optimization
- Free proxy auto-fetching
- Easy management via command line

## Configuration

Proxy settings can be configured in `config.py`:

```python
# Proxy settings
USE_PROXY = True
PROXY_CONFIG = {
    'proxy_file': 'proxies.json',       # File to store proxy list
    'max_fails': 3,                      # Maximum failures before banning a proxy
    'ban_time': 1800,                    # Ban time in seconds (30 minutes)
    'verify_on_startup': True,           # Verify proxies when starting
    'auto_fetch_free': True,             # Fetch free proxies if none available
    'rotation_strategy': 'round-robin',  # Rotation strategy
    'captcha_detection': True            # Enable CAPTCHA detection
}
```

To disable the proxy system, set `USE_PROXY = False`.

## Adding Proxies

### Manually Add Proxies

Create a text file with one proxy per line in any of these formats:

```
123.45.67.89:8080
http://123.45.67.89:8080
https://123.45.67.89:8080
socks5://123.45.67.89:8080
username:password@123.45.67.89:8080
http://username:password@123.45.67.89:8080
```

Then add them to the proxy system:

```bash
python proxy_manager.py add my_proxies.txt
```

### Fetch Free Proxies

The system can automatically fetch free proxies from public sources:

```bash
python proxy_manager.py fetch
```

Note: Free proxies often have lower reliability. For best results, use paid proxy services.

## Testing Proxies

To test all configured proxies:

```bash
python proxy_manager.py test
```

This will:
1. Test each proxy against multiple test sites
2. Show statistics on working vs. non-working proxies
3. Display the fastest proxies for optimal performance

## Proxy System Commands

```bash
# Initialize the proxy system
python proxy_manager.py init

# Add proxies from a text file
python proxy_manager.py add my_proxies.txt

# Fetch free proxies from public sources
python proxy_manager.py fetch

# Test all proxies
python proxy_manager.py test
```

## Recommended Proxy Providers

For best results, consider using paid proxy services:

- Bright Data (formerly Luminati)
- Oxylabs
- SmartProxy
- ProxyBonanza
- Storm Proxies

These providers offer better reliability, performance, and IP diversity compared to free proxies.

## Troubleshooting

If you encounter issues with proxies:

1. Verify that your proxies are working:
   ```bash
   python proxy_test.py test
   ```

2. Check if you're being blocked due to CAPTCHAs:
   ```bash
   python proxy_test.py test --captcha
   ```

3. Try fetching new proxies:
   ```bash
   python proxy_manager.py fetch
   ```

4. Common issues:
   - **All proxies failing**: Most free proxies have short lifespans. Try using paid services.
   - **CAPTCHA detection**: Some sites have advanced bot detection. Try decreasing scraping frequency.
   - **Slow performance**: Some proxies can be slow. Use the test command to identify faster proxies.
