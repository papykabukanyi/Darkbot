# Darkbot Fix Instructions

This document provides instructions for fixing the Darkbot import errors related to R2Storage.

## Problem

The application is failing to start in Railway due to an import error:
```
ImportError: cannot import name 'R2Storage'
```

## Solution

### Option 1: Use the update_fix_r2storage.bat script

1. Run the update_fix_r2storage.bat script I created, which will:
   - Create a backup of main.py
   - Update storage/__init__.py to remove R2Storage references
   - Create a simplified main.py that uses only MongoDB
   - Create a docker-healthcheck.sh script

2. Deploy the updated code to Railway

### Option 2: Manual fixes

If you prefer to make the changes manually, follow these steps:

1. Edit `storage/__init__.py`:
   - Remove any references to R2Storage
   - Ensure it only imports DealStorage and MongoDBStorage

2. Edit `main.py`:
   - Remove any references to R2Storage
   - Update any code that was using R2Storage to use only MongoDB

3. Make sure your Dockerfile has a proper healthcheck:
   ```dockerfile
   HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 CMD [ "docker-healthcheck" ]
   ```

4. Create a docker-healthcheck.sh script that checks if the Python environment is working correctly

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

## Testing

After making these changes:

1. Test locally:
   ```
   python main.py --verbose
   ```

2. If it runs without errors, deploy to Railway

3. Monitor the Railway logs to ensure there are no further issues

Remember: This fix removes the R2Storage functionality. If you need that functionality in the future, you'll need to properly install and configure boto3, botocore, and set up Cloudflare R2 credentials.
