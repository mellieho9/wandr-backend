"""
Location Handler for Notion Integration

This module handles location-specific operations for Notion databases,
including formatting location data and creating location entries.
"""

from typing import Dict, Any

from utils.logging_config import setup_logging

logger = setup_logging(logger_name=__name__)


class LocationHandler:
    """Handler for location-specific Notion database operations."""
    
    def __init__(self, notion_client):
        """
        Initialize LocationHandler with a NotionClient instance.
        
        Args:
            notion_client: Instance of NotionClient for database operations
        """
        self.notion_client = notion_client
    
    def create_location_entry(self, database_id: str, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a location entry specifically formatted for the wandr database schema.
        Prevents duplicates by checking if an entry with the same name already exists.
        
        Args:
            database_id: The ID of the database
            location_data: Location data in the format from location processor
            
        Returns:
            The created page object from Notion API, or existing page if duplicate found
        """
        # Check for duplicates before creating
        place_name = location_data.get("name of place")
        if place_name:
            existing_entry = self._find_existing_entry(database_id, place_name)
            if existing_entry:
                logger.info(f"Duplicate entry found for '{place_name}', skipping creation")
                return {
                    "id": existing_entry["id"],
                    "duplicate": True,
                    "message": f"Entry for '{place_name}' already exists"
                }
        
        # Convert location data to Notion properties format
        properties = self._format_location_properties(location_data)
        
        # Create new entry
        result = self.notion_client.create_database_entry(database_id, properties)
        result["duplicate"] = False
        logger.info(f"Created new entry for '{place_name}'")
        
        return result
    
    def _find_existing_entry(self, database_id: str, place_name: str) -> Dict[str, Any]:
        """
        Find existing entry with the same place name.
        
        Args:
            database_id: The ID of the database to search
            place_name: Name of the place to search for
            
        Returns:
            Existing entry dict if found, None otherwise
        """
        try:
            # Create filter to search for entries with matching "Name of Place" title
            filter_conditions = {
                "property": "Name of Place",
                "title": {
                    "equals": place_name
                }
            }
            
            # Query the database
            response = self.notion_client.query_database(
                database_id=database_id,
                filter_conditions=filter_conditions
            )
            
            # Return first matching result if any
            results = response.get('results', [])
            if results:
                logger.debug(f"Found existing entry for '{place_name}': {results[0]['id']}")
                return results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for existing entry '{place_name}': {e}")
            return None
    
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