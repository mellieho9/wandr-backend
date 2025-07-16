#!/usr/bin/env python3
"""
Wandr Backend Main

Complete pipeline for processing TikTok videos and extracting location information.
"""

import argparse
import os

from video_processor import TikTokProcessor
from location_processor import LocationProcessor

def process_tiktok_url(url: str, place_category: list = None, output_dir: str = "results"):
    """Complete pipeline: download video, process content, extract location info"""
    
    print("🎬 Starting TikTok video processing pipeline...")
    
    # Step 1: Process video
    print("\n📹 Step 1: Processing video content...")
    vision_api_key = os.getenv("VISION_API_KEY")
    if not vision_api_key:
        print("⚠️ No VISION_API_KEY - OCR disabled")
    
    video_processor = TikTokProcessor(vision_api_key, "tiny")
    video_results = video_processor.process_url(url, "results", "tiktok")
    
    if not video_results['success']:
        print(f"❌ Video processing failed: {video_results.get('error', 'Unknown error')}")
        return False
    
    # Step 2: Extract location information
    print("\n📍 Step 2: Extracting location information...")
    location_processor = LocationProcessor()
    
    # Get video ID for file naming
    video_id = video_processor._extract_video_id(url)
    
    try:
        location_info = location_processor.process_video_results(
            video_id, output_dir, place_category
        )
        
        # Save location info
        location_output = f"{output_dir}/{video_id}_location.json"
        location_processor.save_location_info(location_info, location_output)
        
        # Print summary
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📄 Video results: {output_dir}/{video_id}_results.json")
        print(f"📍 Location info: {location_output}")
        print(f"\n📋 EXTRACTED INFO:")
        print(f"🏢 Place: {location_info.name_of_place}")
        print(f"📂 Categories: {', '.join(location_info.place_category) if location_info.place_category else 'None'}")
        print(f"📍 Location: {location_info.location}")
        print(f"🌐 Website: {location_info.website}")
        print(f"⏰ Time: {location_info.time}")
        print(f"⭐ Recommendations: {location_info.recommendations[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Location processing failed: {e}")
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
            print("📍 Running location extraction only...")
            location_processor = LocationProcessor()
            
            # Extract video ID
            temp_processor = TikTokProcessor()
            video_id = temp_processor._extract_video_id(args.url)
            
            location_info = location_processor.process_video_results(
                video_id, args.output_dir, args.category
            )
            
            location_output = f"{args.output_dir}/{video_id}_location.json"
            location_processor.save_location_info(location_info, location_output)
            print(f"✅ Location extraction completed: {location_output}")
            
        elif args.video_only:
            # Only run video processing
            print("📹 Running video processing only...")
            vision_api_key = os.getenv("VISION_API_KEY")
            video_processor = TikTokProcessor(vision_api_key, "tiny")
            results = video_processor.process_url(args.url, "results", "tiktok")
            
            if results['success']:
                video_id = video_processor._extract_video_id(args.url)
                print(f"✅ Video processing completed: results/{video_id}_results.json")
            else:
                print(f"❌ Video processing failed: {results.get('error', 'Unknown error')}")
                return 1
        else:
            # Run complete pipeline
            success = process_tiktok_url(args.url, args.category, args.output_dir)
            if not success:
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())