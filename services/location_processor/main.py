#!/usr/bin/env python3
"""
Location Processor

Main processor that combines location analysis and Google Places services.
"""

import json
import logging
import os
import pandas as pd
from typing import Dict

from .location_analyzer import LocationAnalyzer
from .google_places import GooglePlacesService
from models.location_models import LocationInfo, PlaceInfo

logger = logging.getLogger(__name__)

class LocationProcessor:
    """Main processor combining location analysis and Google Places services"""
    
    def __init__(self, gemini_api_key: str = None, google_maps_api_key: str = None):
        """Initialize with API keys"""
        self.analyzer = LocationAnalyzer(gemini_api_key)
        self.places_service = GooglePlacesService(google_maps_api_key)
        logger.info("Location processor initialized")
    
    def process_video_results(self, video_id: str, results_dir: str = "results", place_category: list = None) -> LocationInfo:
        """Process results for a specific video ID"""
        
        results_file = f"{results_dir}/{video_id}_results.json"
        metadata_file = f"{results_dir}/{video_id}_metadata.csv"
        
        if not os.path.exists(results_file):
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        return self.extract_from_files(results_file, metadata_file, place_category)
    
    def extract_from_files(self, results_file: str, metadata_file: str = None, place_category: list = None) -> LocationInfo:
        """Extract location info from video processing results"""
        
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        metadata = None
        if metadata_file and os.path.exists(metadata_file):
            try:
                metadata_df = pd.read_csv(metadata_file)
                if not metadata_df.empty:
                    metadata = metadata_df.iloc[0].to_dict()
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
        
        url = results.get('original_url', '')

        combined_text = self._get_combined_text(results)
        
        analysis_result = self.analyzer.analyze_content(combined_text, metadata, place_category)
        
        content_type = analysis_result.get('content_analysis', {}).get('content_type', 'single_place')
        
        # Process all places and filter based on Google Maps validation
        places_list = []
        
        if analysis_result.get('places'):
            for place_data in analysis_result['places']:
                place_name = place_data.get('name', '').strip()
                
                if not place_name:
                    continue
                
                place_info = PlaceInfo(
                    name=place_name,
                    address=place_data.get('address'),
                    neighborhood=place_data.get('neighborhood'),
                    categories=place_data.get('categories', []),
                    recommendations=place_data.get('recommendations'),
                    hours=place_data.get('hours'),
                    website=place_data.get('website'),
                    visited=False,
                    is_popup=place_data.get('is_popup', False)
                )
                
                # Enhance with Google Places data and get Maps link
                location_hint = place_info.address or place_info.neighborhood or ''
                places_data = self.places_service.enhance_location_info(place_name, location_hint)
                
                # Skip places without valid Google Maps location
                if not places_data.get('has_valid_location'):
                    continue
                
                # Update place info with Google Places data
                if places_data.get('formatted_address'):
                    place_info.address = places_data['formatted_address']
                if places_data.get('website'):
                    place_info.website = places_data['website']
                if places_data.get('hours') and not place_info.hours:
                    place_info.hours = places_data['hours']
                
                # Add the Google Maps link
                place_info.maps_link = places_data.get('maps_link', '')
                
                if place_info.maps_link:
                    places_list.append(place_info)
        
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
        logger.info(f"Location info saved to: {output_file}")

# Removed redundant CLI - use main.py instead