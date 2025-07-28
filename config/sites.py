"""
Configuration for sneaker websites to scrape.
"""

SNEAKER_SITES = {
    # Original sites
    "sneakers": {
        "url": "https://www.sneakersnstuff.com",
        "sale_url": "https://www.sneakersnstuff.com/en/937/sale",
        "rate_limit": 15,
    },
    "champssports": {
        "url": "https://www.champssports.com",
        "sale_url": "https://www.champssports.com/category/sale.html",
        "rate_limit": 12,
    },
    "footlocker": {
        "url": "https://www.footlocker.com",
        "sale_url": "https://www.footlocker.com/category/sale.html",
        "rate_limit": 12,
    },
    "hibbett": {
        "url": "https://www.hibbett.com",
        "sale_url": "https://www.hibbett.com/sale/shoes/",
        "rate_limit": 10,
    },
    
    # Popular sneaker sites with good deals
    "nike": {
        "url": "https://www.nike.com",
        "sale_url": "https://www.nike.com/w/sale-shoes-3yaepznik1",
        "rate_limit": 15,
    },
    "adidas": {
        "url": "https://www.adidas.com",
        "sale_url": "https://www.adidas.com/us/men-shoes-sale",
        "rate_limit": 15,
    },
    "finishline": {
        "url": "https://www.finishline.com",
        "sale_url": "https://www.finishline.com/store/sale/mens/shoes/_/N-1y3ctepZ1z141xuZ1yzcml3",
        "rate_limit": 12,
    },
    "jdsports": {
        "url": "https://www.jdsports.com",
        "sale_url": "https://www.jdsports.com/sale/mens/shoes/",
        "rate_limit": 12,
    },
    "dtlr": {
        "url": "https://www.dtlr.com",
        "sale_url": "https://www.dtlr.com/collections/sale-shoes",
        "rate_limit": 10,
    },
    "stockx": {
        "url": "https://www.stockx.com",
        "sale_url": "https://stockx.com/sneakers",
        "market_price": True,  # Use this site for market price comparison
        "rate_limit": 20,
    },
    "goat": {
        "url": "https://www.goat.com",
        "sale_url": "https://www.goat.com/sneakers/under-retail",
        "market_price": True,  # Use this site for market price comparison
        "rate_limit": 20,
    },
    "flightclub": {
        "url": "https://www.flightclub.com",
        "sale_url": "https://www.flightclub.com/sale",
        "market_price": True,  # Use this site for market price comparison
        "rate_limit": 15,
    },
    "klekt": {
        "url": "https://www.klekt.com",
        "sale_url": "https://www.klekt.com/store/sneakers",
        "market_price": True,  # Use this site for market price comparison
        "rate_limit": 15,
    },
    "grailed": {
        "url": "https://www.grailed.com",
        "sale_url": "https://www.grailed.com/categories/sneakers",
        "market_price": True,  # Use this site for market price comparison
        "rate_limit": 15,
    },
    "stadiumgoods": {
        "url": "https://www.stadiumgoods.com",
        "sale_url": "https://www.stadiumgoods.com/en-us/shopping/sale-15538",
        "rate_limit": 15,
    },
    "jimmyjazz": {
        "url": "https://www.jimmyjazz.com",
        "sale_url": "https://www.jimmyjazz.com/collections/sale-footwear",
        "rate_limit": 10,
    },
    "kickscrew": {
        "url": "https://www.kickscrew.com",
        "sale_url": "https://www.kickscrew.com/collections/sale",
        "rate_limit": 10,
    },
    "snipes": {
        "url": "https://www.snipesusa.com",
        "sale_url": "https://www.snipesusa.com/mens/sale/?prefn1=type&prefv1=Sneakers",
        "rate_limit": 12,
    },
    "shoepalace": {
        "url": "https://www.shoepalace.com",
        "sale_url": "https://www.shoepalace.com/collections/on-sale",
        "rate_limit": 10,
    },
    "undefeated": {
        "url": "https://www.undefeated.com",
        "sale_url": "https://www.undefeated.com/collections/sale",
        "rate_limit": 12,
    },
}

# Sites to use for market price comparison (resell value)
MARKET_PRICE_SITES = [site for site, config in SNEAKER_SITES.items() if config.get('market_price', False)]

# Default sites to scrape if none specified - prioritize sites with good deals and working scrapers
DEFAULT_SITES = ["nike", "adidas", "footlocker", "jdsports", "finishline", "hibbett", "undefeated"]
