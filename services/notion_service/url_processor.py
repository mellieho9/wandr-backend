"""
URL Processor for Notion Integration

This module handles URL processing operations for Notion databases,
including querying for pending URLs and batch processing.
"""

from utils.logging_config import setup_logging

logger = setup_logging(logger_name=__name__)


class URLProcessor:
    """Handler for URL processing operations with Notion databases."""
    
    def __init__(self, notion_client):
        """
        Initialize URLProcessor with a NotionClient instance.
        
        Args:
            notion_client: Instance of NotionClient for database operations
        """
        self.notion_client = notion_client
    
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
    
