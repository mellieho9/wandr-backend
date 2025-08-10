#!/usr/bin/env python3
"""
Wandr Backend Main

Complete pipeline for processing TikTok videos and extracting location information.
"""

import argparse
import sys
from pathlib import Path

from utils.logging_config import setup_logging
from utils.config import config
from models.pipeline_models import PipelineOptions
from pipeline.orchestrator import PipelineOrchestrator
from utils.exceptions import ConfigurationError, WandrError

# Setup logging
logger = setup_logging(level="INFO", log_file="wandr-backend.log", console_output=True, logger_name=__name__)


def main():
    """Command line interface for the complete TikTok processing pipeline"""
    parser = argparse.ArgumentParser(
        description="Complete TikTok video processing and location extraction pipeline."
    )
    
    # Input options
    parser.add_argument("--url", help="TikTok URL to process")
    parser.add_argument("--category", nargs="*", help="Place categories (e.g., restaurant chinese)")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    
    # Processing options
    parser.add_argument("--frame-interval", type=float, default=3.0,
                       help="Interval between frame extractions (seconds)")
    parser.add_argument("--max-frames", type=int, default=8,
                       help="Maximum number of frames to extract")
    
    # Batch processing options
    parser.add_argument("--process-pending-urls", action="store_true", 
                       help="Process all pending URLs from today in source database")
    parser.add_argument("--source-database-id", 
                       help="Source database ID to pull URLs from (can also use NOTION_SOURCE_DB_ID env var)")
    parser.add_argument("--places-database-id", 
                       help="Places database ID to create entries in (can also use NOTION_PLACES_DB_ID env var)")
    
    # Notion integration options
    parser.add_argument("--create-notion-entry", action="store_true", 
                       help="Create Notion database entries after processing")
    parser.add_argument("--database-id", 
                       help="Notion database ID (can also use NOTION_PLACES_DB_ID env var)")
    
    args = parser.parse_args()
    
    try:
        # Handle different modes of operation
        if args.process_pending_urls:
            # Batch processing mode
            places_database_id = args.places_database_id or config.get_notion_places_db_id()
            source_database_id = args.source_database_id or config.get_notion_source_db_id()
            
            if not source_database_id:
                raise ConfigurationError("Source database ID is required. Set NOTION_SOURCE_DB_ID or use --source-database-id")
            if not places_database_id:
                raise ConfigurationError("Places database ID is required. Set NOTION_PLACES_DB_ID or use --places-database-id")

            # Create pipeline options for batch processing
            options = PipelineOptions(
                categories=args.category or [],
                output_dir=args.output_dir,
                create_notion_entry=True,
                database_id=places_database_id,
                frame_interval=args.frame_interval,
                max_frames=args.max_frames
            )
            
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting batch processing from database: {source_database_id}")
            logger.info(f"Creating places in database: {places_database_id}")
            
            # Initialize orchestrator and run batch processing
            orchestrator = PipelineOrchestrator(options)
            batch_result = orchestrator.run_batch_processing(
                source_database_id=source_database_id,
                places_database_id=places_database_id
            )
            return 0 if batch_result.failed == 0 else 1
            
        elif args.url:
            # Single URL processing mode
            options = PipelineOptions(
                url=args.url,
                categories=args.category or [],
                output_dir=args.output_dir,
                create_notion_entry=args.create_notion_entry,
                database_id=args.database_id or config.get_notion_places_db_id(),
                frame_interval=args.frame_interval,
                max_frames=args.max_frames
            )
            
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize orchestrator and process single URL
            orchestrator = PipelineOrchestrator(options)
            pipeline_results = orchestrator.run_single_url(args.url)
            
            # Check for success
            video_result = pipeline_results.get('video')
            location_result = pipeline_results.get('location')
            
            if video_result and video_result.success and location_result and location_result.success:
                logger.info("Processing completed successfully!")
                return 0
            else:
                logger.error("Processing failed!")
                return 1
        
        else:
            parser.error("Either --url or --process-pending-urls is required")
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except WandrError as e:
        logger.error(f"Processing error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())