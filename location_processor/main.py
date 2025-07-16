#!/usr/bin/env python3
"""
Location Processor

Main processor that combines location analysis and Google Places services.
"""

import json
import os
import pandas as pd
from typing import Dict
from dataclasses import dataclass
from datetime import datetime

from .location_analyzer import LocationAnalyzer
from .google_places import GooglePlacesService

@dataclass
class LocationInfo:
    """Structured location information for Notion"""
    url: str
    place_category: list
    review: str
    name_of_place: str
    location: str
    recommendations: str
    time: str
    website: str
    visited: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            'URL': self.url,
            'place_category': self.place_category,
            'review': self.review,
            'name of place': self.name_of_place,
            'location': self.location,
            'recommendations': self.recommendations,
            'time': self.time,
            'website': self.website,
            'visited': self.visited
        }

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
        analysis_result = self.analyzer.analyze_content(combined_text, metadata)
        
        # Enhance with Google Places data
        places_data = {}
        place_name = analysis_result.get('name_of_place', '')
        location_hint = analysis_result.get('location_hint', '')
        
        if place_name:
            places_data = self.places_service.enhance_location_info(place_name, location_hint)
        
        # Get final location (prefer Google Places address, fallback to hint)
        final_location = places_data.get('formatted_address', location_hint)
        
        # Get recommendations without hours/website
        recommendations = analysis_result.get('recommendations', '')
        if not isinstance(recommendations, str):
            recommendations = str(recommendations) if recommendations else ''
        
        # Get hours for time field (prefer Gemini extraction, fallback to Google Places, then timestamp)
        gemini_time = analysis_result.get('time', '')
        time_info = gemini_time if gemini_time else places_data.get('hours', timestamp)
        
        # Get website
        website = places_data.get('website', '')
        
        # Combine results
        return LocationInfo(
            url=url,
            place_category=place_category or [],
            review='',  # Leave empty for user to fill in Notion
            name_of_place=place_name,
            location=final_location,
            recommendations=recommendations.strip(),
            time=time_info,
            website=website,
            visited=False  # Default to not visited
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
        print(f"🏢 Place: {location_info.name_of_place}")
        print(f"📂 Categories: {', '.join(location_info.place_category)}")
        print(f"📍 Location: {location_info.location}")
        print(f"💭 Review: {location_info.review[:100]}...")
        print(f"⭐ Recommendations: {location_info.recommendations[:100]}...")
        
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