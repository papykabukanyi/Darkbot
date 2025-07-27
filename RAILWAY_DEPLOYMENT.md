# Railway Deployment Guide for DarkBot

## Prerequisites

1. A [Railway](https://railway.app/) account
2. Git installed on your computer
3. The Railway CLI (optional)

## Deployment Steps

### 1. Prepare Your Repository

1. Make sure your code is in a Git repository
2. Ensure your repository has the following files:
   - `Dockerfile`
   - `Procfile`
   - `railway.json`
   - `requirements.txt`

### 2. Deploy to Railway

#### Option 1: Using Railway Dashboard

1. Log in to [Railway](https://railway.app/)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account if not already connected
5. Select your DarkBot repository
6. Railway will automatically detect your Dockerfile and deploy

#### Option 2: Using Railway CLI

1. Install the Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Log in:
   ```bash
   railway login
   ```

3. Link your project:
   ```bash
   railway link
   ```

4. Deploy:
   ```bash
   railway up
   ```

### 3. Configure Environment Variables

1. In the Railway dashboard, go to your project
2. Click on the "Variables" tab
3. Add the following environment variables:

   ```env
   MONGODB_CONNECTION_STRING=mongodb://username:password@hostname:port/
   MONGODB_DATABASE=sneakerbot
   MONGODB_COLLECTION=deals
   EMAIL_NOTIFICATIONS=True
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENTS=papykabukanyi@gmail.com,hoopstar385@gmail.com
   EMAIL_INTERVAL_MINUTES=30
   ```

4. Make sure to replace `your_email@gmail.com` and `your_app_password` with your actual email credentials

### 4. Verify Deployment

1. Go to the "Deployments" tab in your Railway project
2. Check the build and deployment logs
3. Make sure there are no errors in the logs
4. The bot should be running and checking for deals every 30 minutes

### 5. Monitoring

1. Railway provides logs for your application
2. Check these logs regularly to ensure the bot is running properly
3. If you see any errors, check the troubleshooting section below

## Troubleshooting

### Common Issues

1. **Email Authentication Failures**
   - Make sure you're using an App Password if using Gmail
   - Verify that EMAIL_SENDER and EMAIL_PASSWORD are correctly set

2. **MongoDB Connection Issues**
   - Check if the MongoDB connection string is correct
   - Make sure the MongoDB instance is accessible from Railway

3. **Bot Crashing**
   - Check the logs for error messages
   - Most common errors are related to website structure changes
   - Update the scraper code if necessary

4. **Railway Build Failures**
   - Make sure all dependencies are correctly listed in requirements.txt
   - Check for syntax errors in your Python code

## Keeping Your Bot Running

Railway will automatically restart your service if it crashes, but you should periodically check:

1. That the bot is still running (via Railway dashboard)
2. That you're receiving email notifications
3. That new deals are being saved to the MongoDB database

For any other issues, refer to the [Railway documentation](https://docs.railway.app/).
