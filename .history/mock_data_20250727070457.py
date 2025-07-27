"""
Mock data generator for testing the bot without hitting real websites.
"""

import os
import json
import random
from datetime import datetime, timedelta

def generate_mock_product(brand=None, on_sale=True, min_discount=20, max_discount=70):
    """Generate a mock product data dictionary."""
    
    # List of mock brands
    brands = ["Nike", "Adidas", "Jordan", "New Balance", "Puma", "Reebok"]
    
    # List of mock model names
    models = [
        "Air Max", "ZoomX", "Ultra Boost", "Superstar", "Air Jordan", "990v5",
        "RS-X", "Classic Leather", "Air Force 1", "Dunk Low", "Yeezy", "574",
        "Future Rider", "Club C", "Air Huarache", "Stan Smith", "NMD", "327"
    ]
    
    # List of mock colors
    colors = ["Black", "White", "Red", "Blue", "Green", "Grey", "Navy", "Pink",
             "Purple", "Yellow", "Orange", "Cream", "Brown", "Multicolor"]
    
    # Select a random brand if not provided
    if not brand:
        brand = random.choice(brands)
    
    # Generate a model name
    model = random.choice(models)
    
    # Generate color(s)
    primary_color = random.choice(colors)
    secondary_color = random.choice(colors)
    if primary_color == secondary_color:
        color_text = primary_color
    else:
        color_text = f"{primary_color}/{secondary_color}"
    
    # Generate price information
    if on_sale:
        original_price = random.uniform(100, 250)
        discount = random.uniform(min_discount, max_discount) / 100
        price = original_price * (1 - discount)
        discount_percent = round(discount * 100)
    else:
        original_price = random.uniform(80, 200)
        price = original_price
        discount_percent = 0
    
    # Generate available sizes
    all_sizes = ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "11.5", "12", "13"]
    available_sizes = []
    for size in all_sizes:
        # Random availability (70% chance of being available)
        if random.random() < 0.7:
            available_sizes.append({
                "size": size,
                "available": True
            })
        else:
            available_sizes.append({
                "size": size,
                "available": False
            })
    
    # Generate a product ID
    product_id = f"{brand[0:2]}{random.randint(10000, 99999)}"
    
    # Generate a timestamp within the last week
    days_ago = random.randint(0, 7)
    timestamp = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate source website
    sources = ["Sneakers.com", "Champs Sports", "Footlocker", "ID Sports"]
    source = random.choice(sources)
    
    # Create the product dictionary
    product = {
        "title": f"{brand} {model} {color_text}",
        "price": round(price, 2),
        "original_price": round(original_price, 2),
        "url": f"https://example.com/{brand.lower()}/{model.lower().replace(' ', '-')}-{primary_color.lower()}",
        "image_url": f"https://example.com/images/{brand.lower()}-{model.lower().replace(' ', '-')}.jpg",
        "description": f"The {brand} {model} in {color_text} offers premium comfort and style. Perfect for everyday wear.",
        "brand": brand,
        "product_id": product_id,
        "sizes": available_sizes,
        "source": source,
        "on_sale": on_sale,
        "discount_percent": discount_percent,
        "timestamp": timestamp
    }
    
    # Calculate profit potential
    market_value = original_price * 1.2  # Assume 20% over original is market value
    estimated_fees = market_value * 0.10  # Assume 10% marketplace fees
    shipping_cost = 15  # Estimated shipping cost
    profit = market_value - price - estimated_fees - shipping_cost
    roi_percentage = (profit / price) * 100 if price > 0 else 0
    
    product["profit"] = round(profit, 2)
    product["roi"] = f"{roi_percentage:.1f}%"
    product["worth_buying"] = profit > 20 and roi_percentage > 15
    
    return product

def generate_mock_dataset(num_products=50, save_to_file=True):
    """Generate a set of mock products."""
    
    products = []
    
    # Generate a mix of products
    for _ in range(num_products):
        # Determine if on sale (80% of products)
        on_sale = random.random() < 0.8
        
        # Generate the product
        product = generate_mock_product(on_sale=on_sale)
        products.append(product)
    
    # Save to file if requested
    if save_to_file:
        with open("mock_data.json", "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2)
        print(f"Generated {num_products} mock products and saved to mock_data.json")
    
    return products

def load_mock_dataset():
    """Load mock dataset from file if available, otherwise generate new data."""
    if os.path.exists("mock_data.json"):
        try:
            with open("mock_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded {len(data)} mock products from mock_data.json")
            return data
        except Exception as e:
            print(f"Error loading mock data: {e}")
    
    # Generate new data if file doesn't exist or couldn't be loaded
    return generate_mock_dataset()

if __name__ == "__main__":
    # Generate a test dataset
    products = generate_mock_dataset(num_products=50)
    
    # Print some sample data
    print("\nSample Products:")
    for i, product in enumerate(products[:5]):
        print(f"\nProduct {i+1}:")
        print(f"Title: {product['title']}")
        print(f"Brand: {product['brand']}")
        print(f"Price: ${product['price']} (was ${product['original_price']})")
        print(f"Discount: {product['discount_percent']}%")
        print(f"Profit potential: ${product['profit']} ({product['roi']})")
        print(f"Worth buying: {'Yes' if product['worth_buying'] else 'No'}")
        print(f"Source: {product['source']}")
