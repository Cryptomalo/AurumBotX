"""
Core utilities package for the trading platform.
This module initializes the utilities package and exposes key components.
"""

from .database_manager import DatabaseManager

__all__ = [
    'DatabaseManager',
]