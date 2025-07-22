#!/usr/bin/env python3
"""
Wandr Backend Main

Complete pipeline for processing TikTok videos and extracting location information.
"""

import argparse
import sys
from pathlib import Path

from utils.logging_config import setup_logging
from config import config
from models.pipeline_models import PipelineOptions
from pipeline.orchestrator import PipelineOrchestrator
from exceptions import ConfigurationError, WandrError

# Setup logging
setup_logging(level="INFO", log_file="wandr-backend.log", console_output=True)


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
    parser.add_argument("--whisper-model", default="tiny", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size for transcription")
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
        # Create pipeline options
        options = PipelineOptions(
            url=args.url,
            categories=args.category or [],
            output_dir=args.output_dir,
            create_notion_entry=args.create_notion_entry,
            database_id=args.database_id or config.get_notion_places_db_id(),
            whisper_model=args.whisper_model,
            frame_interval=args.frame_interval,
            max_frames=args.max_frames
        )
        
        # Validate arguments
        if not args.process_pending_urls and not args.url:
            parser.error("Either --url or --process-pending-urls is required")
        
        # Handle database IDs for batch processing
        places_database_id = args.places_database_id or config.get_notion_places_db_id()
        source_database_id = args.source_database_id or config.get_notion_source_db_id()
        
        # Validation
        if args.create_notion_entry and not options.database_id:
            parser.error("--create-notion-entry requires --database-id or NOTION_PLACES_DB_ID env var")
        
        if args.process_pending_urls:
            if not source_database_id:
                parser.error("--process-pending-urls requires --source-database-id or NOTION_SOURCE_DB_ID env var")
            if not places_database_id:
                parser.error("--process-pending-urls requires --places-database-id or NOTION_PLACES_DB_ID env var")
        
        # Ensure output directory exists
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(options)
        
        if args.process_pending_urls:
            # Process all pending URLs from today
            batch_result = orchestrator.run_batch_processing(
                source_database_id=source_database_id,
                places_database_id=places_database_id
            )
            
            # Return non-zero exit code if any processing failed
            return 0 if batch_result.failed == 0 else 1
            
        else:
            # Run complete pipeline for single URL
            pipeline_results = orchestrator.run_single_url(args.url)
            
            # Check if any critical steps failed
            video_result = pipeline_results.get('video')
            location_result = pipeline_results.get('location')
            
            if not video_result or not video_result.success:
                return 1
            if not location_result or not location_result.success:
                return 1
            
            # Notion failure is not critical
            return 0
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except WandrError as e:
        print(f"Processing error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Process interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())