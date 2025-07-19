#!/usr/bin/env python3
"""
Location Processor

Main processor that combines location analysis and Google Places services.
"""

import json
import os
import pandas as pd
from typing import Dict
from datetime import datetime

from .location_analyzer import LocationAnalyzer
from .google_places import GooglePlacesService
from models.location_models import LocationInfo, PlaceInfo

class LocationProcessor:
    """Main processor combining location analysis and Google Places services"""
    
    def __init__(self, gemini_api_key: str = None, google_maps_api_key: str = None):
        """Initialize with API keys"""
        self.analyzer = LocationAnalyzer(gemini_api_key)
        self.places_service = GooglePlacesService(google_maps_api_key)
        print("✅ Location processor initialized")
    
    def process_video_results(self, video_id: str, results_dir: str = "results", place_category: list = None) -> LocationInfo:
        """Process results for a specific video ID"""
        
        results_file = f"{results_dir}/{video_id}_results.json"
        metadata_file = f"{results_dir}/{video_id}_metadata.csv"
        
        if not os.path.exists(results_file):
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        return self.extract_from_files(results_file, metadata_file, place_category)
    
    def extract_from_files(self, results_file: str, metadata_file: str = None, place_category: list = None) -> LocationInfo:
        """Extract location info from video processing results"""
        
        # Load results JSON
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Load metadata CSV if available
        metadata = None
        if metadata_file and os.path.exists(metadata_file):
            try:
                metadata_df = pd.read_csv(metadata_file)
                if not metadata_df.empty:
                    metadata = metadata_df.iloc[0].to_dict()
            except Exception as e:
                print(f"⚠️ Could not load metadata: {e}")
        
        # Extract basic info
        url = results.get('original_url', '')
        timestamp = results.get('timestamp', datetime.now().isoformat())
        
        # Get combined text for analysis
        combined_text = self._get_combined_text(results)
        
        # Use analyzer for intelligent extraction
        analysis_result = self.analyzer.analyze_content(combined_text, metadata, place_category)
        
        # Get content type
        content_type = analysis_result.get('content_analysis', {}).get('content_type', 'single_place')
        
        # Process all places
        places_list = []
        
        if analysis_result.get('places'):
            for place_data in analysis_result['places']:
                # Create PlaceInfo object
                place_info = PlaceInfo(
                    name=place_data.get('name', ''),
                    address=place_data.get('address'),
                    neighborhood=place_data.get('neighborhood'),
                    categories=place_data.get('categories', []),
                    recommendations=place_data.get('recommendations'),
                    hours=place_data.get('hours'),
                    website=place_data.get('website'),
                    visited=False,  # Default to not visited
                    is_popup=place_data.get('is_popup', False)
                )
                
                # Enhance with Google Places data for all places
                if place_info.name:
                    location_hint = place_info.address or place_info.neighborhood or ''
                    places_data = self.places_service.enhance_location_info(place_info.name, location_hint)
                    
                    # Update place info with Google Places data
                    if places_data.get('formatted_address'):
                        place_info.address = places_data['formatted_address']
                    if places_data.get('website'):
                        place_info.website = places_data['website']
                    if places_data.get('hours') and not place_info.hours:
                        place_info.hours = places_data['hours']
                
                places_list.append(place_info)
        
        # Combine results
        return LocationInfo(
            url=url,
            content_type=content_type,
            places=places_list if places_list else []
        )
    
    def _get_combined_text(self, results: Dict) -> str:
        """Extract and combine text from results"""
        combined_text = results.get('combined_text', '')
        
        if not combined_text:
            # Fallback: combine transcription and OCR
            text_parts = []
            if results.get('transcription', {}).get('success'):
                text_parts.append(f"Audio: {results['transcription']['text']}")
            if results.get('ocr', {}).get('success'):
                for frame in results['ocr']['text_data']:
                    text_parts.append(f"Frame: {frame['text']}")
            combined_text = "\n".join(text_parts)
        
        return combined_text
    
    def save_location_info(self, location_info: LocationInfo, output_file: str):
        """Save location info to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(location_info.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"💾 Location info saved to: {output_file}")

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract location info from video results")
    parser.add_argument("--video-id", required=True, help="Video ID to process")
    parser.add_argument("--results-dir", default="results", help="Results directory")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--category", nargs="*", help="Place categories (e.g., restaurant chinese)")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = LocationProcessor()
    
    # Process video
    try:
        location_info = processor.process_video_results(args.video_id, args.results_dir, args.category)
        
        # Print results
        print(f"\n📍 EXTRACTED LOCATION INFO:")
        print(f"🔗 URL: {location_info.url}")
        print(f"🏪 Content Type: {location_info.content_type}")
        print(f"📍 Total Places: {len(location_info.places)}")
        for i, place in enumerate(location_info.places):
            print(f"  {i+1}. {place.name} ({'visited' if place.visited else 'not visited'})")
            if place.address:
                print(f"     📍 {place.address}")
            if place.recommendations:
                print(f"     ⭐ {place.recommendations[:50]}...")
        
        # Save to file
        if args.output:
            output_file = args.output
        else:
            output_file = f"{args.results_dir}/{args.video_id}_location.json"
        
        processor.save_location_info(location_info, output_file)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())