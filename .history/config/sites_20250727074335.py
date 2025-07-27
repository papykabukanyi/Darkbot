"""
Configuration for sneaker websites to scrape.
"""

SNEAKER_SITES = {
    # Original sites
    "sneakers": {
        "url": "https://www.sneakers.com",
        "sale_url": "https://www.sneakers.com/collections/sale",
    },
    "champssports": {
        "url": "https://www.champssports.com",
        "sale_url": "https://www.champssports.com/category/sale/shoes.html",
    },
    "footlocker": {
        "url": "https://www.footlocker.com",
        "sale_url": "https://www.footlocker.com/category/sale/shoes.html",
    },
    "idsports": {
        "url": "https://www.idsports.com",
        "sale_url": "https://www.idsports.com/sale",
    },
    
    # Added popular sneaker sites
    "nike": {
        "url": "https://www.nike.com",
        "sale_url": "https://www.nike.com/w/sale-shoes-3yaepznik1",
    },
    "adidas": {
        "url": "https://www.adidas.com",
        "sale_url": "https://www.adidas.com/us/men-shoes-sale",
    },
    "finishline": {
        "url": "https://www.finishline.com",
        "sale_url": "https://www.finishline.com/store/sale/shoes/_/N-1xvxiZ1sZ256h",
    },
    "eastbay": {
        "url": "https://www.eastbay.com",
        "sale_url": "https://www.eastbay.com/category/sale/shoes.html",
    },
    "jdsports": {
        "url": "https://www.jdsports.com",
        "sale_url": "https://www.jdsports.com/store/sale/shoes/_/N-1og1qqrZ1z13xg2Z1sZ256h",
    },
    "stockx": {
        "url": "https://www.stockx.com",
        "sale_url": "https://stockx.com/sneakers",
        "market_price": True  # Use this site for market price comparison
    },
    "goat": {
        "url": "https://www.goat.com",
        "sale_url": "https://www.goat.com/sneakers",
        "market_price": True  # Use this site for market price comparison
    },
    "flightclub": {
        "url": "https://www.flightclub.com",
        "sale_url": "https://www.flightclub.com/sneakers/all",
    },
    "stadiumgoods": {
        "url": "https://www.stadiumgoods.com",
        "sale_url": "https://www.stadiumgoods.com/en-us/shopping/shoes-1",
    },
    "jimmyjazz": {
        "url": "https://www.jimmyjazz.com",
        "sale_url": "https://www.jimmyjazz.com/collections/sale-footwear",
    },
    "kickscrew": {
        "url": "https://www.kickscrew.com",
        "sale_url": "https://www.kickscrew.com/collections/sale",
    },
    "hibbett": {
        "url": "https://www.hibbett.com",
        "sale_url": "https://www.hibbett.com/sale/shoes/",
    },
    "footaction": {
        "url": "https://www.footaction.com",
        "sale_url": "https://www.footaction.com/category/sale/shoes.html",
    },
}

# Sites to use for market price comparison (resell value)
MARKET_PRICE_SITES = [site for site, config in SNEAKER_SITES.items() if config.get('market_price', False)]

# Default sites to scrape if none specified
DEFAULT_SITES = list(SNEAKER_SITES.keys())
