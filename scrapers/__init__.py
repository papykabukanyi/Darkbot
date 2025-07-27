"""
Initialize the scrapers module.
"""

from scrapers.sneakers import SneakersScraper
from scrapers.champssports import ChampsScraper
from scrapers.footlocker import FootlockerScraper
from scrapers.idsports import IDSportsScraper

__all__ = [
    "SneakersScraper",
    "ChampsScraper",
    "FootlockerScraper", 
    "IDSportsScraper"
]
