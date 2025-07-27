#!/bin/bash
# Script to set up MongoDB indexes for better performance

# MongoDB connection string - Load from environment
if [ -z "$MONGODB_CONNECTION_STRING" ]; then
  # Load from .env file if exists
  if [ -f "../.env" ]; then
    source ../.env
  fi
  # Set default if still not found
  if [ -z "$MONGODB_CONNECTION_STRING" ]; then
    CONNECTION_STRING="mongodb://localhost:27017"
  else
    CONNECTION_STRING="$MONGODB_CONNECTION_STRING"
  fi
else
  CONNECTION_STRING="$MONGODB_CONNECTION_STRING"
fi

# Get database and collection from environment or use defaults
DB_NAME="${MONGODB_DATABASE:-sneaker_deals}"
COLLECTION="${MONGODB_COLLECTION:-deals}"

# Create MongoDB indexes for performance optimization
mongo $CONNECTION_STRING <<EOF
use $DB_NAME;

// Create indexes
db.$COLLECTION.createIndex({"brand": 1});
db.$COLLECTION.createIndex({"price": 1});
db.$COLLECTION.createIndex({"discount_percent": -1});
db.$COLLECTION.createIndex({"profit_percentage": -1});
db.$COLLECTION.createIndex({"profit_amount": -1});
db.$COLLECTION.createIndex({"is_profitable": -1});
db.$COLLECTION.createIndex({"created_at": -1});
db.$COLLECTION.createIndex({"source": 1});
db.$COLLECTION.createIndex({"url": 1}, {"unique": true});

// Create stats collection
db.createCollection("deal_stats");
db.deal_stats.createIndex({"date": 1});

// Print confirmation
print("MongoDB indexes created successfully!");
EOF

echo "MongoDB setup completed!"
