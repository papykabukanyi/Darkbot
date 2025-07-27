"""
Storage package for the sneaker bot.
"""

from storage.storage import DealStorage
from storage.cloudflare_r2 import R2Storage

__all__ = ['DealStorage', 'R2Storage']
