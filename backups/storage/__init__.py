"""
Storage package for the sneaker bot.
"""

from storage.storage import DealStorage
from storage.mongodb import MongoDBStorage

__all__ = ['DealStorage', 'MongoDBStorage']
