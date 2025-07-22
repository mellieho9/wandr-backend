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
            # Get today's date in ISO format
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            # Create compound filter for today's entries with 'Pending' status
            filter_conditions = {
                "and": [
                    {
                        "property": date_property,
                        "date": {
                            "on_or_after": today
                        }
                    },
                    {
                        "property": status_property,
                        "select": {
                            "equals": "Pending"
                        }
                    }
                ]
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
                    "select": {
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
    
    def process_pending_urls(self, source_database_id: str, places_database_id: str, 
                            url_property: str = "URL", date_property: str = "Created", 
                            status_property: str = "Status") -> Dict[str, Any]:
        """
        Process all pending URLs from today and create place entries, updating status accordingly.
        
        Args:
            source_database_id: Database ID to pull URLs from
            places_database_id: Database ID to create place entries in
            url_property: Name of the URL property in source database
            date_property: Name of the date property to filter by
            status_property: Name of the status property to update
            
        Returns:
            Summary of processing results
        """
        # Import here to avoid circular imports
        from pipeline_runner import run_complete_pipeline
        
        # Get pending URLs with their page IDs
        url_entries = self.get_pending_urls(source_database_id, url_property, date_property, status_property)
        
        if not url_entries:
            return {
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "urls": []
            }
        
        results = {
            "processed": len(url_entries),
            "successful": 0,
            "failed": 0,
            "urls": [],
            "errors": []
        }
        
        logger.info(f"Processing {len(url_entries)} pending URLs from today...")
        
        for i, entry in enumerate(url_entries, 1):
            url = entry['url']
            page_id = entry['page_id']
            
            try:
                logger.info(f"Processing URL {i}/{len(url_entries)}: {url}")
                
                # Process the TikTok URL with Notion integration
                success = run_complete_pipeline(
                    url=url,
                    place_category=None,  # Let AI determine categories
                    output_dir="results",
                    create_notion_entry=True,
                    database_id=places_database_id
                )
                
                if success:
                    # Update status to 'Completed'
                    self.update_entry_status(page_id, "Completed", status_property)
                    results["successful"] += 1
                    results["urls"].append({"url": url, "status": "success", "page_id": page_id})
                    logger.info(f"✅ Successfully processed: {url}")
                else:
                    # Update status to 'Failed'
                    self.update_entry_status(page_id, "Failed", status_property)
                    results["failed"] += 1
                    results["urls"].append({"url": url, "status": "failed", "page_id": page_id})
                    results["errors"].append(f"Processing failed for: {url}")
                    logger.error(f"❌ Failed to process: {url}")
                    
            except Exception as e:
                # Update status to 'Failed' on exception
                self.update_entry_status(page_id, "Failed", status_property)
                results["failed"] += 1
                results["urls"].append({"url": url, "status": "error", "page_id": page_id})
                results["errors"].append(f"Error processing {url}: {str(e)}")
                logger.error(f"❌ Error processing {url}: {e}")
        
        logger.info(f"Processing complete: {results['successful']} successful, {results['failed']} failed")
        return results