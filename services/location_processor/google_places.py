#!/usr/bin/env python3
"""
Google Places Service

Handles Google Maps Places API integration for location lookup and enhancement.
"""

import logging
from typing import Dict, Optional
import googlemaps

from config import config
logger = logging.getLogger(__name__)

class GooglePlacesService:
    """Google Places API integration for location enhancement"""
    
    def __init__(self, api_key: str = None):
        """Initialize with Google Maps API key"""
        self.api_key = api_key or config.get_google_maps_api_key()
        
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
            logger.warning(f"Google Places search failed: {e}")
        
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
            logger.warning(f"Google Places details failed: {e}")
        
        return None
    
    def generate_maps_link(self, place_id: str = None, place_name: str = None, address: str = None) -> str:
        """Generate a Google Maps link for the location"""
        
        if place_id:
            # Most accurate: use place_id
            return f"https://maps.google.com/maps/place/?q=place_id:{place_id}"
        elif address:
            # Use formatted address
            import urllib.parse
            encoded_address = urllib.parse.quote_plus(address)
            return f"https://maps.google.com/maps/search/{encoded_address}"
        elif place_name:
            # Fallback: use place name
            import urllib.parse
            encoded_name = urllib.parse.quote_plus(place_name)
            return f"https://maps.google.com/maps/search/{encoded_name}"
        
        return ""

    def enhance_location_info(self, place_name: str, location_hint: str = None) -> Dict:
        """Search and enhance location information with Google Maps link"""
        
        result = {
            'formatted_address': '',
            'hours': '',
            'website': '',
            'maps_link': '',
            'place_id': '',
            'has_valid_location': False
        }
        
        if not self.client:
            return result
        
        try:
            # Search for the place
            place_info = self.search_place(place_name, location_hint)
            if not place_info:
                logger.info(f"No Google Places result found for: {place_name}")
                return result
            
            # Store place_id for maps link
            place_id = place_info.get('place_id', '')
            result['place_id'] = place_id
            
            # Get detailed information
            details = self.get_place_details(place_id)
            if not details:
                logger.info(f"No place details found for: {place_name}")
                return result
            
            # Extract relevant information
            formatted_address = details.get('formatted_address', '')
            result['formatted_address'] = formatted_address
            result['website'] = details.get('website', '')
            
            # Format opening hours
            if 'opening_hours' in details and 'weekday_text' in details['opening_hours']:
                hours = details['opening_hours']['weekday_text']
                result['hours'] = '\n'.join(hours)
            
            # Generate Google Maps link
            if place_id:
                result['maps_link'] = self.generate_maps_link(place_id=place_id)
                result['has_valid_location'] = True
                logger.info(f"Google Places enhancement completed for: {place_name}")
            elif formatted_address:
                result['maps_link'] = self.generate_maps_link(address=formatted_address)
                result['has_valid_location'] = True
                logger.info(f"Google Places enhancement with address for: {place_name}")
            else:
                logger.warning(f"No valid location found for: {place_name}")
            
        except Exception as e:
            logger.warning(f"Google Places enhancement failed: {e}")
        
        return result