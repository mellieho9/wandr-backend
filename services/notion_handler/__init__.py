"""
Notion Service Package

This package provides functionality for interacting with Notion API,
including creating database entries and handling webhooks.
"""

from .notion_client import NotionClient
from .location_handler import LocationHandler

__all__ = ['NotionClient', 'LocationHandler']