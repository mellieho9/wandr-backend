#!/usr/bin/env python3
"""
Wandr Backend Main

Complete pipeline for processing TikTok videos and extracting location information.
"""

import argparse
import logging
import os

from config import config
from pipeline_runner import run_complete_pipeline
from notion_service.notion_client import NotionClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('wandr-backend.log')  # File output
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Command line interface for the complete TikTok processing pipeline"""
    parser = argparse.ArgumentParser(
        description="Complete TikTok video processing and location extraction pipeline."
    )
    
    # Input options
    parser.add_argument("--url", help="TikTok URL to process")
    parser.add_argument("--category", nargs="*", help="Place categories (e.g., restaurant chinese)")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    
    # Batch processing options
    parser.add_argument("--process-pending-urls", action="store_true", 
                       help="Process all pending URLs from today in source database")
    parser.add_argument("--source-database-id", 
                       help="Source database ID to pull URLs from (can also use NOTION_SOURCE_DB_ID env var)")
    parser.add_argument("--places-database-id", 
                       help="Places database ID to create entries in (can also use NOTION_PLACES_DB_ID env var)")
    
    # Notion integration options
    parser.add_argument("--create-notion-entry", action="store_true", help="Create Notion database entries after processing")
    parser.add_argument("--database-id", help="Notion database ID (can also use NOTION_PLACES_DB_ID env var)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.process_pending_urls and not args.url:
        parser.error("Either --url or --process-pending-urls is required")
    
    # Handle Notion database IDs
    database_id = args.database_id or config.get_notion_places_db_id()
    places_database_id = args.places_database_id or config.get_notion_places_db_id()
    source_database_id = args.source_database_id or config.get_notion_source_db_id()
    
    if args.create_notion_entry and not database_id:
        parser.error("--create-notion-entry requires --database-id or NOTION_PLACES_DB_ID env var")
    
    if args.process_pending_urls and not source_database_id:
        parser.error("--process-pending-urls requires --source-database-id or NOTION_SOURCE_DB_ID env var")
    
    if args.process_pending_urls and not places_database_id:
        parser.error("--process-pending-urls requires --places-database-id or NOTION_PLACES_DB_ID env var")
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        if args.process_pending_urls:
            # Process all pending URLs from today
            logger.info("Processing pending URLs from source database...")
            
            # Initialize Notion client
            api_key = config.get_notion_api_key()
            if not api_key:
                logger.error("NOTION_API_KEY or NOTION_TOKEN environment variable is required")
                return 1
            
            notion_client = NotionClient(api_key)
            
            # Process pending URLs
            results = notion_client.process_pending_urls(
                source_database_id=source_database_id,
                places_database_id=places_database_id
            )
            
            # Print summary
            logger.info("Processing Summary:")
            logger.info(f"  Total URLs processed: {results['processed']}")
            logger.info(f"  Successful: {results['successful']}")
            logger.info(f"  Failed: {results['failed']}")
            
            if results['errors']:
                logger.error("Errors encountered:")
                for error in results['errors']:
                    logger.error(f"  - {error}")
            
            # Return non-zero exit code if any processing failed
            return 0 if results['failed'] == 0 else 1
            
        else:
            # Run complete pipeline for single URL
            success = run_complete_pipeline(
                url=args.url,
                place_category=args.category,
                output_dir=args.output_dir,
                create_notion_entry=args.create_notion_entry,
                database_id=database_id
            )
            
            if not success:
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())