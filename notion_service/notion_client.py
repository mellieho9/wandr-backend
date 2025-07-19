"""
Notion Client for database operations

This module provides functionality to interact with Notion databases,
including creating new entries and updating existing pages.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from notion_client import Client
from notion_client.errors import APIResponseError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class NotionClient:
    """Client for interacting with Notion API and databases."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Notion client.
        
        Args:
            api_key: Notion API key. If not provided, will use NOTION_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('NOTION_API_KEY')
        if not self.api_key:
            raise ValueError("NOTION_API_KEY environment variable is required")
        
        self.client = Client(auth=self.api_key)
        logger.info("Notion client initialized successfully")
    
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
            
            logger.info(f"Successfully created database entry with ID: {response['id']}")
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
            
            logger.info(f"Successfully updated page {page_id}")
            return response
            
        except APIResponseError as e:
            logger.error(f"Failed to update page: {e}")
            raise
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """
        Retrieve database information including schema.
        
        Args:
            database_id: The ID of the database
            
        Returns:
            Database object from Notion API
        """
        try:
            logger.info(f"Retrieving database {database_id}")
            
            response = self.client.databases.retrieve(database_id=database_id)
            
            logger.info(f"Successfully retrieved database {database_id}")
            return response
            
        except APIResponseError as e:
            logger.error(f"Failed to retrieve database: {e}")
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
            
            logger.info(f"Successfully queried database {database_id}, got {len(response['results'])} results")
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
        # Convert location data to Notion properties format
        properties = self._format_location_properties(location_data)
        
        return self.create_database_entry(database_id, properties)
    
    def _format_location_properties(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format location data into Notion properties format.
        
        Args:
            location_data: Raw location data
            
        Returns:
            Formatted properties for Notion API
        """
        properties = {}
        
        # Name of Place (title field)
        if location_data.get("name of place"):
            properties["Name of Place"] = {
                "title": [
                    {
                        "text": {
                            "content": location_data["name of place"]
                        }
                    }
                ]
            }
        
        # Source URL 
        if location_data.get("URL"):
            properties["Source URL"] = {
                "url": location_data["URL"]
            }
        
        # Address (with optional Google Maps link)
        if location_data.get("location"):
            address_content = {
                "text": {
                    "content": location_data["location"]
                }
            }
            
            # Add hyperlink if maps_link is available
            if location_data.get("maps_link"):
                address_content["text"]["link"] = {
                    "url": location_data["maps_link"]
                }
            
            properties["Address"] = {
                "rich_text": [address_content]
            }
        
        # Categories (multi-select)
        if location_data.get("place_category"):
            categories = location_data["place_category"]
            if isinstance(categories, list):
                properties["Categories"] = {
                    "multi_select": [
                        {"name": category} for category in categories
                    ]
                }
        
        # Recommendations
        if location_data.get("recommendations"):
            properties["Recommendations"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": location_data["recommendations"]
                        }
                    }
                ]
            }
        
        # My Personal Review
        if location_data.get("review"):
            properties["My Personal Review"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": location_data["review"]
                        }
                    }
                ]
            }
        
        # Hours
        if location_data.get("time"):
            properties["Hours"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": location_data["time"]
                        }
                    }
                ]
            }
        
        # Website
        if location_data.get("website"):
            properties["Website"] = {
                "url": location_data["website"]
            }
        
        # Is Popup (checkbox)
        properties["Is Popup"] = {
            "checkbox": False
        }
        
        # Visited (checkbox)
        if "visited" in location_data:
            properties["Visited"] = {
                "checkbox": location_data["visited"]
            }
        else:
            properties["Visited"] = {
                "checkbox": False
            }
        
        logger.debug(f"Formatted properties: {properties}")
        return properties
    
    def test_connection(self) -> bool:
        """
        Test the Notion API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test connection by getting user info
            response = self.client.users.me()
            logger.info(f"Connection test successful. Connected as: {response.get('name', 'Unknown')}")
            return True
            
        except APIResponseError as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_todays_urls(self, database_id: str, url_property: str = "URL", date_property: str = "Created") -> List[str]:
        """
        Query database for URLs posted today.
        
        Args:
            database_id: The ID of the database to query
            url_property: Name of the URL property in the database
            date_property: Name of the date property to filter by (default: "Created")
            
        Returns:
            List of URLs from today's entries
        """
        try:
            # Get today's date in ISO format
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            # Create filter for today's entries
            filter_conditions = {
                "property": date_property,
                "date": {
                    "on_or_after": today
                }
            }
            
            # Query the database
            response = self.query_database(
                database_id=database_id,
                filter_conditions=filter_conditions
            )
            
            urls = []
            for page in response.get('results', []):
                properties = page.get('properties', {})
                
                # Extract URL from the specified property
                url_prop = properties.get(url_property)
                if url_prop and url_prop.get('type') == 'url' and url_prop.get('url'):
                    urls.append(url_prop['url'])
            
            logger.info(f"Found {len(urls)} URLs from today in database {database_id}")
            return urls
            
        except Exception as e:
            logger.error(f"Failed to get today's URLs: {e}")
            return []
    
    def process_todays_urls(self, source_database_id: str, places_database_id: str, 
                           url_property: str = "URL", date_property: str = "Created") -> Dict[str, Any]:
        """
        Process all URLs from today and create place entries.
        
        Args:
            source_database_id: Database ID to pull URLs from
            places_database_id: Database ID to create place entries in
            url_property: Name of the URL property in source database
            date_property: Name of the date property to filter by
            
        Returns:
            Summary of processing results
        """
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        
        # Add parent directory to path
        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))
        
        from main import process_tiktok_url
        
        # Get today's URLs
        urls = self.get_todays_urls(source_database_id, url_property, date_property)
        
        if not urls:
            return {
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "urls": []
            }
        
        results = {
            "processed": len(urls),
            "successful": 0,
            "failed": 0,
            "urls": [],
            "errors": []
        }
        
        logger.info(f"Processing {len(urls)} URLs from today...")
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"Processing URL {i}/{len(urls)}: {url}")
                
                # Process the TikTok URL with Notion integration
                success = process_tiktok_url(
                    url=url,
                    place_category=None,  # Let AI determine categories
                    output_dir="results",
                    create_notion_entry=True,
                    database_id=places_database_id
                )
                
                if success:
                    results["successful"] += 1
                    results["urls"].append({"url": url, "status": "success"})
                    logger.info(f"✅ Successfully processed: {url}")
                else:
                    results["failed"] += 1
                    results["urls"].append({"url": url, "status": "failed"})
                    results["errors"].append(f"Processing failed for: {url}")
                    logger.error(f"❌ Failed to process: {url}")
                    
            except Exception as e:
                results["failed"] += 1
                results["urls"].append({"url": url, "status": "error"})
                results["errors"].append(f"Error processing {url}: {str(e)}")
                logger.error(f"❌ Error processing {url}: {e}")
        
        logger.info(f"Processing complete: {results['successful']} successful, {results['failed']} failed")
        return results