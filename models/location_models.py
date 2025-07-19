"""
Location processing data models
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PlaceInfo:
    """Individual place information"""
    name: str
    address: Optional[str] = None
    neighborhood: Optional[str] = None
    categories: List[str] = None
    recommendations: Optional[str] = None
    hours: Optional[str] = None
    website: Optional[str] = None
    visited: bool = False
    is_popup: bool = False
    maps_link: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            'name': self.name,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'categories': self.categories or [],
            'recommendations': self.recommendations,
            'hours': self.hours,
            'website': self.website,
            'visited': self.visited,
            'is_popup': self.is_popup,
            'maps_link': self.maps_link
        }


@dataclass
class LocationInfo:
    """Simplified output structure with URL, content type, places array"""
    url: str
    content_type: str
    places: List[PlaceInfo]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            'url': self.url,
            'content_type': self.content_type,
            'places': [place.to_dict() for place in self.places]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LocationInfo':
        """Create from dictionary"""
        places = [
            PlaceInfo(
                name=place_data['name'],
                address=place_data.get('address'),
                neighborhood=place_data.get('neighborhood'),
                categories=place_data.get('categories', []),
                recommendations=place_data.get('recommendations'),
                hours=place_data.get('hours'),
                website=place_data.get('website'),
                visited=place_data.get('visited', False),
                is_popup=place_data.get('is_popup', False),
                maps_link=place_data.get('maps_link')
            )
            for place_data in data.get('places', [])
        ]
        
        return cls(
            url=data['url'],
            content_type=data['content_type'],
            places=places
        )