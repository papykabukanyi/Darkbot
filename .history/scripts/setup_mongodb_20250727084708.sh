#!/bin/bash
# Script to set up MongoDB indexes for better performance

# MongoDB connection string
CONNECTION_STRING="mongodb://mongo:SMhYDmJOIDZMrHqHhVJRIHzxcOfJUaNr@shortline.proxy.rlwy.net:51019"
DB_NAME="sneaker_deals"
COLLECTION="deals"

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
