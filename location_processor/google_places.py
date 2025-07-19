#!/usr/bin/env python3
"""
Google Places Service

Handles Google Maps Places API integration for location lookup and enhancement.
"""

import logging
import os
from typing import Dict, Optional
import googlemaps
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GooglePlacesService:
    """Google Places API integration for location enhancement"""
    
    def __init__(self, api_key: str = None):
        """Initialize with Google Maps API key"""
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        
        if self.api_key:
            self.client = googlemaps.Client(key=self.api_key)
            logger.info("Google Maps API initialized")
        else:
            self.client = None
            logger.warning("No Google Maps API key - address lookup disabled")
    
    def search_place(self, place_name: str, location_hint: str = None) -> Optional[Dict]:
        """Search for a place and return basic information"""
        
        if not self.client:
            return None
        
        try:
            # Build search query
            search_query = place_name
            if location_hint:
                search_query += f" {location_hint}"
            
            # Search for places
            places_result = self.client.places(query=search_query)
            
            if places_result['results']:
                place = places_result['results'][0]
                return {
                    'place_id': place['place_id'],
                    'name': place.get('name', ''),
                    'formatted_address': place.get('formatted_address', ''),
                    'types': place.get('types', []),
                    'rating': place.get('rating'),
                    'geometry': place.get('geometry', {})
                }
        
        except Exception as e:
            print(f"⚠️ Google Places search failed: {e}")
        
        return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information for a specific place"""
        
        if not self.client:
            return None
        
        try:
            details = self.client.place(place_id=place_id, fields=[
                'name', 'formatted_address', 'opening_hours',
                'website', 'formatted_phone_number'
            ])
            
            return details.get('result', {})
            
        except Exception as e:
            print(f"⚠️ Google Places details failed: {e}")
        
        return None
    
    def enhance_location_info(self, place_name: str, location_hint: str = None) -> Dict:
        """Search and enhance location information"""
        
        result = {
            'formatted_address': '',
            'hours': '',
            'website': ''
        }
        
        if not self.client:
            return result
        
        try:
            # Search for the place
            place_info = self.search_place(place_name, location_hint)
            if not place_info:
                return result
            
            # Get detailed information
            details = self.get_place_details(place_info['place_id'])
            if not details:
                return result
            
            # Extract relevant information
            result['formatted_address'] = details.get('formatted_address', '')
            result['website'] = details.get('website', '')
            
            # Format opening hours
            if 'opening_hours' in details and 'weekday_text' in details['opening_hours']:
                hours = details['opening_hours']['weekday_text']
                result['hours'] = '\n'.join(hours)
            
            print(f"✅ Google Places enhancement completed for: {place_name}")
            
        except Exception as e:
            print(f"⚠️ Google Places enhancement failed: {e}")
        
        return result
    
    def validate_address(self, address: str) -> bool:
        """Validate if an address exists"""
        
        if not self.client:
            return False
        
        try:
            geocode_result = self.client.geocode(address)
            return len(geocode_result) > 0
            
        except Exception:
            return False