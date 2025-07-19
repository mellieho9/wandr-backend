#!/usr/bin/env python3
"""
Wandr Backend Main

Complete pipeline for processing TikTok videos and extracting location information.
"""

import argparse
import logging
import os

from video_processor import TikTokProcessor
from location_processor import LocationProcessor
from utils.url_parser import TikTokURLParser

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

def process_tiktok_url(url: str, place_category: list = None, output_dir: str = "results"):
    """Complete pipeline: download video, process content, extract location info"""
    
    logger.info("Starting TikTok video processing pipeline...")
    
    # Step 1: Process video
    logger.info("Step 1: Processing video content...")
    vision_api_key = os.getenv("VISION_API_KEY")
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

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Complete TikTok video processing and location extraction pipeline"
    )
    
    # Input options
    parser.add_argument("--url", required=True, help="TikTok URL to process")
    parser.add_argument("--category", nargs="*", help="Place categories (e.g., restaurant chinese)")
    parser.add_argument("--output-dir", default="results", help="Output directory")
    
    # Processing options
    parser.add_argument("--video-only", action="store_true", help="Only process video, skip location extraction")
    parser.add_argument("--location-only", action="store_true", help="Only extract location from existing results")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.video_only and args.location_only:
        parser.error("Cannot use both --video-only and --location-only")
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        if args.location_only:
            # Only run location extraction
            logger.info("Running location extraction only...")
            location_processor = LocationProcessor()
            
            # Extract video ID
            video_id = TikTokURLParser.get_file_prefix(args.url)
            
            location_info = location_processor.process_video_results(
                video_id, args.output_dir, args.category
            )
            
            location_output = f"{args.output_dir}/{video_id}_location.json"
            location_processor.save_location_info(location_info, location_output)
            logger.info(f"Location extraction completed: {location_output}")
            
        elif args.video_only:
            # Only run video processing
            logger.info("Running video processing only...")
            vision_api_key = os.getenv("VISION_API_KEY")
            video_processor = TikTokProcessor(vision_api_key, "tiny")
            results = video_processor.process_url(args.url, "results", "tiktok")
            
            if results['success']:
                video_id = TikTokURLParser.get_file_prefix(args.url)
                logger.info(f"Video processing completed: results/{video_id}_results.json")
            else:
                logger.error(f"Video processing failed: {results.get('error', 'Unknown error')}")
                return 1
        else:
            # Run complete pipeline
            success = process_tiktok_url(args.url, args.category, args.output_dir)
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