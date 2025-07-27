# Use Python 3.9 as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables (will be overridden by Railway)
ENV MONGODB_CONNECTION_STRING="mongodb://mongo:SMhYDmJOIDZMrHqHhVJRIHzxcOfJUaNr@shortline.proxy.rlwy.net:51019"
ENV MONGODB_DATABASE="sneakerbot"
ENV MONGODB_COLLECTION="deals"
ENV EMAIL_NOTIFICATIONS="True"
ENV EMAIL_INTERVAL_MINUTES="30"
ENV EMAIL_RECIPIENTS="papykabukanyi@gmail.com,hoopstar385@gmail.com"

# Run the bot in continuous mode with 30-minute intervals
CMD ["python", "main.py", "--continuous", "--interval", "30", "--verbose"]
