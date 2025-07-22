import pytest
from models.location_models import PlaceInfo, LocationInfo


class TestPlaceInfo:
    
    @pytest.mark.unit
    def test_place_info_creation(self):
        place = PlaceInfo(
            name="Test Restaurant",
            address="123 Main St",
            categories=["restaurant", "italian"]
        )
        assert place.name == "Test Restaurant"
        assert place.address == "123 Main St"
        assert place.categories == ["restaurant", "italian"]
        assert place.visited is False
        assert place.is_popup is False
    
    @pytest.mark.unit
    def test_place_info_to_dict(self):
        place = PlaceInfo(
            name="Test Restaurant",
            address="123 Main St",
            categories=["restaurant"]
        )
        result = place.to_dict()
        expected = {
            'name': 'Test Restaurant',
            'address': '123 Main St',
            'neighborhood': None,
            'categories': ['restaurant'],
            'recommendations': None,
            'hours': None,
            'website': None,
            'visited': False,
            'is_popup': False,
            'maps_link': None
        }
        assert result == expected


class TestLocationInfo:
    
    @pytest.mark.unit
    def test_location_info_creation(self):
        place = PlaceInfo(name="Test Place")
        location = LocationInfo(
            url="https://test.com",
            content_type="restaurant_review",
            places=[place]
        )
        assert location.url == "https://test.com"
        assert location.content_type == "restaurant_review"
        assert len(location.places) == 1
        assert location.places[0].name == "Test Place"
    
    @pytest.mark.unit
    def test_location_info_to_dict(self):
        place = PlaceInfo(name="Test Place", categories=["restaurant"])
        location = LocationInfo(
            url="https://test.com",
            content_type="restaurant_review", 
            places=[place]
        )
        result = location.to_dict()
        assert result['url'] == "https://test.com"
        assert result['content_type'] == "restaurant_review"
        assert len(result['places']) == 1
        assert result['places'][0]['name'] == "Test Place"
    
    @pytest.mark.unit
    def test_location_info_from_dict(self, sample_location_data):
        location = LocationInfo.from_dict(sample_location_data)
        assert location.url == sample_location_data['url']
        assert location.content_type == sample_location_data['content_type']
        assert len(location.places) == 1
        assert location.places[0].name == "Amazing Pizza Place"