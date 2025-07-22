"""
URL Processor for Notion Integration

This module handles URL processing operations for Notion databases,
including querying for pending URLs and batch processing.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class URLProcessor:
    """Handler for URL processing operations with Notion databases."""
    
    def __init__(self, notion_client):
        """
        Initialize URLProcessor with a NotionClient instance.
        
        Args:
            notion_client: Instance of NotionClient for database operations
        """
        self.notion_client = notion_client
    
    def get_pending_urls(self, database_id: str, url_property: str = "URL", 
                        date_property: str = "Created", status_property: str = "Status") -> List[Dict[str, Any]]:
        """
        Query database for URLs with 'Pending' status posted today.
        
        Args:
            database_id: The ID of the database to query
            url_property: Name of the URL property in the database
            date_property: Name of the date property to filter by (default: "Created")
            status_property: Name of the status property to filter by (default: "Status")
            
        Returns:
            List of dictionaries containing URL and page_id for pending entries
        """
        try:
            
            # Create compound filter for today's entries with 'Pending' status
            filter_conditions = {
                        "property": status_property,
                        "status": {
                            "equals": "Pending"
                        }
                    }
            
            # Query the database
            response = self.notion_client.query_database(
                database_id=database_id,
                filter_conditions=filter_conditions
            )
            
            url_entries = []
            for page in response.get('results', []):
                properties = page.get('properties', {})
                
                # Extract URL from the specified property
                url_prop = properties.get(url_property)
                if url_prop and url_prop.get('type') == 'url' and url_prop.get('url'):
                    url_entries.append({
                        'url': url_prop['url'],
                        'page_id': page['id']
                    })
            
            logger.info(f"Found {len(url_entries)} pending URLs from today in database {database_id}")
            return url_entries
            
        except Exception as e:
            logger.error(f"Failed to get pending URLs: {e}")
            return []
    
    def update_entry_status(self, page_id: str, status: str, status_property: str = "Status") -> bool:
        """
        Update the status of a Notion database entry.
        
        Args:
            page_id: The ID of the page to update
            status: The new status value (e.g., "Completed", "Failed")
            status_property: Name of the status property (default: "Status")
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            properties = {
                status_property: {
                    "status": {
                        "name": status
                    }
                }
            }
            
            self.notion_client.update_page(page_id, properties)
            logger.info(f"Updated entry {page_id} status to '{status}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update entry {page_id} status: {e}")
            return False
    
