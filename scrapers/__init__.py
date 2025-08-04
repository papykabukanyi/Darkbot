"""
Initialize the scrapers module.
"""

from scrapers.kicksonfire import KicksOnFireScraper
from scrapers.base_scraper import BaseSneakerScraper

__all__ = [
    "KicksOnFireScraper",
    "BaseSneakerScraper"
]
