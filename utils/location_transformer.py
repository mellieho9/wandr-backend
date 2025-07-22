"""
Transform location data between different formats
"""

import logging
from typing import Dict, Any, List
from models.location_models import PlaceInfo

logger = logging.getLogger(__name__)


class LocationToNotionTransformer:
    """Transform location data to Notion-compatible format"""
    
    @staticmethod
    def transform_place(place: PlaceInfo, source_url: str = None) -> Dict[str, Any]:
        """
        Transform a PlaceInfo object to Notion database entry format.
        
        Args:
            place: PlaceInfo object to transform
            source_url: Original source URL for the place
            
        Returns:
            Dictionary formatted for Notion database entry
        """
        return {
            "name of place": place.name,
            "location": place.address,
            "place_category": place.categories,
            "recommendations": LocationToNotionTransformer._format_recommendations(place.recommendations),
            "review": "",  # Empty by default
            "time": place.hours,
            "website": place.website,
            "visited": place.visited,
            "maps_link": place.maps_link,
            "URL": source_url
        }
    
    @staticmethod
    def transform_places_list(places: List[PlaceInfo], source_url: str = None) -> List[Dict[str, Any]]:
        """
        Transform a list of PlaceInfo objects to Notion format.
        
        Args:
            places: List of PlaceInfo objects
            source_url: Original source URL
            
        Returns:
            List of dictionaries formatted for Notion
        """
        return [
            LocationToNotionTransformer.transform_place(place, source_url)
            for place in places
        ]
    
    @staticmethod
    def _format_recommendations(recommendations: Any) -> str:
        """
        Format recommendations to consistent string format.
        
        Args:
            recommendations: Recommendations in various formats
            
        Returns:
            Formatted recommendations string
        """
        if not recommendations:
            return ""
        
        if isinstance(recommendations, list):
            return ", ".join(str(item) for item in recommendations)
        
        return str(recommendations)