"""
Notion Client for database operations

This module provides functionality to interact with Notion databases,
including creating new entries and updating existing pages.
"""

from typing import Dict, Any, Optional, List
from notion_client import Client
from notion_client.errors import APIResponseError

from utils.config import config
from utils.logging_config import setup_logging, log_success

logger = setup_logging(logger_name=__name__)


class NotionClient:
    """Client for interacting with Notion API and databases."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Notion client.
        
        Args:
            api_key: Notion API key. If not provided, will use NOTION_API_KEY env var.
        """
        self.api_key = api_key or config.get_notion_api_key()
        if not self.api_key:
            raise ValueError("NOTION_API_KEY environment variable is required")
        
        self.client = Client(auth=self.api_key)
        log_success(logger, "Notion client initialized")
    
    def create_database_entry(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entry in a Notion database.
        
        Args:
            database_id: The ID of the database to add the entry to
            properties: Properties for the new database entry
            
        Returns:
            The created page object from Notion API
            
        Raises:
            APIResponseError: If the API request fails
        """
        try:
            logger.info(f"Creating new entry in database {database_id}")
            
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            
            log_success(logger, f"Created database entry with ID: {response['id']}")
            return response
            
        except APIResponseError as e:
            logger.error(f"Failed to create database entry: {e}")
            raise
    
    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Notion page.
        
        Args:
            page_id: The ID of the page to update
            properties: Properties to update
            
        Returns:
            The updated page object from Notion API
        """
        try:
            logger.info(f"Updating page {page_id}")
            
            response = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            log_success(logger, f"Updated page {page_id}")
            return response
            
        except APIResponseError as e:
            logger.error(f"Failed to update page: {e}")
            raise
    
    def query_database(self, database_id: str, filter_conditions: Optional[Dict] = None, 
                      sorts: Optional[List[Dict]] = None, start_cursor: Optional[str] = None,
                      page_size: int = 100) -> Dict[str, Any]:
        """
        Query a database with optional filtering and sorting.
        
        Args:
            database_id: The ID of the database to query
            filter_conditions: Filter conditions for the query
            sorts: Sort conditions for the query
            start_cursor: Cursor for pagination
            page_size: Number of results per page (max 100)
            
        Returns:
            Query results from Notion API
        """
        try:
            logger.info(f"Querying database {database_id}")
            
            query_params = {
                "database_id": database_id,
                "page_size": min(page_size, 100)
            }
            
            if filter_conditions:
                query_params["filter"] = filter_conditions
            if sorts:
                query_params["sorts"] = sorts
            if start_cursor:
                query_params["start_cursor"] = start_cursor
            
            response = self.client.databases.query(**query_params)
            
            log_success(logger, f"Queried database {database_id}, got {len(response['results'])} results")
            return response
            
        except APIResponseError as e:
            logger.error(f"Failed to query database: {e}")
            raise
    
    def create_location_entry(self, database_id: str, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a location entry specifically formatted for the wandr database schema.
        
        Args:
            database_id: The ID of the database
            location_data: Location data in the format from location processor
            
        Returns:
            The created page object from Notion API
        """
        from .location_handler import LocationHandler
        
        location_handler = LocationHandler(self)
        return location_handler.create_location_entry(database_id, location_data)
    
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
        from .url_processor import URLProcessor
        
        url_processor = URLProcessor(self)
        return url_processor.update_entry_status(page_id, status, status_property)