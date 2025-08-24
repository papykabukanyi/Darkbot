# Use Python 3.10 as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install essential dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Fix Flask/Werkzeug compatibility issues
RUN pip uninstall -y flask werkzeug && \
    pip install flask==2.0.1 werkzeug==2.0.2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Chrome (needed for Selenium / undetected-chromedriver)
RUN set -eux; \
    apt-get update; \
    cd /tmp; \
    wget -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; \
    apt-get install -y ./google-chrome.deb --no-install-recommends; \
    rm google-chrome.deb; \
    rm -rf /var/lib/apt/lists/*

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data/cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV CHROME_BIN=/usr/bin/google-chrome

# Expose port for the API
EXPOSE 8080

# Create a simple healthcheck script
RUN echo '#!/bin/bash\ncurl -f http://localhost:${PORT:-8080}/api/status || exit 1' > /usr/local/bin/healthcheck \
    && chmod +x /usr/local/bin/healthcheck

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD [ "/usr/local/bin/healthcheck" ]

# Command to run
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
