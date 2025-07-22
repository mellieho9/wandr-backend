"""
Pipeline Runner

This module contains the main pipeline execution logic for processing TikTok videos
and extracting location information.
"""

import logging

from config import config
from video_processor import TikTokProcessor
from location_processor import LocationProcessor
from notion_service.notion_client import NotionClient
from notion_service.location_handler import LocationHandler
from utils.url_parser import TikTokURLParser

logger = logging.getLogger(__name__)


def run_complete_pipeline(url: str, place_category: list = None, output_dir: str = "results", 
                         create_notion_entry: bool = False, database_id: str = None) -> bool:
    """
    Complete pipeline: download video, process content, extract location info, optionally create Notion entry
    
    Args:
        url: TikTok URL to process
        place_category: Optional list of place categories to filter by
        output_dir: Directory to save results
        create_notion_entry: Whether to create Notion database entries
        database_id: Notion database ID for creating entries
        
    Returns:
        True if pipeline completed successfully, False otherwise
    """
    
    logger.info("Starting TikTok video processing pipeline...")
    
    # Step 1: Process video
    logger.info("Step 1: Processing video content...")
    vision_api_key = config.get_vision_api_key()
    if not vision_api_key:
        logger.warning("No VISION_API_KEY - OCR disabled")
    
    video_processor = TikTokProcessor(vision_api_key, "tiny")
    video_results = video_processor.process_url(url, "results", "tiktok")
    
    if not video_results['success']:
        logger.error(f"Video processing failed: {video_results.get('error', 'Unknown error')}")
        return False
    
    # Step 2: Extract location information
    logger.info("Step 2: Extracting location information...")
    location_processor = LocationProcessor()
    
    # Get video ID for file naming
    video_id = TikTokURLParser.get_file_prefix(url)
    
    try:
        location_info = location_processor.process_video_results(
            video_id, output_dir, place_category
        )
        
        # Save location info
        location_output = f"{output_dir}/{video_id}_location.json"
        location_processor.save_location_info(location_info, location_output)
        
        # Step 3: Create Notion entries (optional)
        if create_notion_entry and database_id:
            logger.info("Step 3: Creating Notion database entries...")
            try:
                create_notion_entries_from_location_file(location_output, database_id, url)
            except Exception as e:
                logger.error(f"Notion entry creation failed: {e}")
                # Don't fail the whole pipeline for Notion errors
        
        # Print summary
        logger.info("Pipeline completed successfully!")
        logger.info(f"Video results: {output_dir}/{video_id}_results.json")
        logger.info(f"Location info: {location_output}")
        logger.info("EXTRACTED INFO:")
        if location_info.places:
            primary_place = location_info.places[0]  # Get first place
            logger.info(f"Place: {primary_place.name}")
            logger.info(f"Categories: {', '.join(primary_place.categories) if primary_place.categories else 'None'}")
            logger.info(f"Location: {primary_place.address or primary_place.neighborhood or 'N/A'}")
            logger.info(f"Website: {primary_place.website or 'N/A'}")
            logger.info(f"Time: {primary_place.hours or 'N/A'}")
            logger.info(f"Recommendations: {(primary_place.recommendations or 'N/A')[:100]}...")
        else:
            logger.warning("No places found in location info")
        
        return True
        
    except Exception as e:
        logger.error(f"Location processing failed: {e}")
        return False


def create_notion_entries_from_location_file(location_file: str, database_id: str, source_url: str = None):
    """Create Notion database entries from location data file"""
    import json
    
    # Load location data
    with open(location_file, "r") as f:
        location_data = json.load(f)
    
    # Initialize Notion client
    api_key = config.get_notion_api_key()
    if not api_key:
        raise ValueError("NOTION_API_KEY or NOTION_TOKEN environment variable is required")
    
    notion_client = NotionClient(api_key)
    location_handler = LocationHandler(notion_client)
    
    # Process each place in the location data
    places = location_data.get("places", [])
    if not places:
        logger.warning("No places found in location data")
        return
    
    logger.info(f"Creating {len(places)} Notion entries...")
    
    for i, place in enumerate(places, 1):
        try:
            # Format location data for this place
            place_data = {
                "name of place": place.get("name"),
                "location": place.get("address"),
                "place_category": place.get("categories", []),
                "recommendations": ", ".join(place.get("recommendations")) if isinstance(place.get("recommendations"), list) else (place.get("recommendations") or ""),
                "review": "",  # Empty by default
                "time": place.get("hours"),
                "website": place.get("website"),
                "visited": place.get("visited", False),
                "maps_link": place.get("maps_link"),
                "URL": source_url or location_data.get("url")
            }
            
            # Create the entry
            response = location_handler.create_location_entry(database_id, place_data)
            logger.info(f"Created Notion entry {i}/{len(places)}: {place.get('name', 'Unnamed Place')}")
            logger.info(f"   Page ID: {response['id']}")
            
        except Exception as e:
            logger.error(f"Failed to create entry for {place.get('name', 'Unnamed Place')}: {e}")
            continue
    
    logger.info("Notion entries creation completed!")