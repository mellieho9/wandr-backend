import pytest
from unittest.mock import Mock
from notion_service.location_handler import LocationHandler


class TestLocationHandler:
    
    @pytest.mark.unit
    def test_location_handler_initialization(self):
        """Test LocationHandler initialization"""
        mock_notion_client = Mock()
        handler = LocationHandler(mock_notion_client)
        
        assert handler.notion_client == mock_notion_client
    
    @pytest.mark.unit
    def test_create_location_entry(self):
        """Test creating a location entry"""
        mock_notion_client = Mock()
        mock_notion_client.create_database_entry.return_value = {"id": "page_123"}
        
        handler = LocationHandler(mock_notion_client)
        database_id = "test_db_id"
        location_data = {
            "name of place": "Test Restaurant",
            "location": "123 Main St",
            "place_category": ["restaurant", "italian"],
            "URL": "https://tiktok.com/test"
        }
        
        result = handler.create_location_entry(database_id, location_data)
        
        # Verify the method was called
        mock_notion_client.create_database_entry.assert_called_once()
        call_args = mock_notion_client.create_database_entry.call_args
        
        assert call_args[0][0] == database_id  # First positional arg is database_id
        assert result == {"id": "page_123"}
    
    @pytest.mark.unit
    def test_format_location_properties_basic(self):
        """Test formatting basic location properties"""
        mock_notion_client = Mock()
        handler = LocationHandler(mock_notion_client)
        
        location_data = {
            "name of place": "Test Restaurant",
            "location": "123 Main St",
            "place_category": ["restaurant"],
            "URL": "https://tiktok.com/test"
        }
        
        properties = handler._format_location_properties(location_data)
        
        # Check title field
        assert properties["Name of Place"]["title"][0]["text"]["content"] == "Test Restaurant"
        
        # Check URL field
        assert properties["Source URL"]["url"] == "https://tiktok.com/test"
        
        # Check address field
        assert properties["Address"]["rich_text"][0]["text"]["content"] == "123 Main St"
        
        # Check categories
        assert properties["Categories"]["multi_select"][0]["name"] == "restaurant"
        
        # Check default values
        assert properties["Is Popup"]["checkbox"] is False
        assert properties["Visited"]["checkbox"] is False
    
    @pytest.mark.unit
    def test_format_location_properties_with_maps_link(self):
        """Test formatting location properties with Google Maps link"""
        mock_notion_client = Mock()
        handler = LocationHandler(mock_notion_client)
        
        location_data = {
            "name of place": "Test Restaurant",
            "location": "123 Main St",
            "maps_link": "https://maps.google.com/?q=place_id:ChIJTest123"
        }
        
        properties = handler._format_location_properties(location_data)
        
        # Check that address has hyperlink
        address_rich_text = properties["Address"]["rich_text"][0]
        assert address_rich_text["text"]["content"] == "123 Main St"
        assert address_rich_text["text"]["link"]["url"] == "https://maps.google.com/?q=place_id:ChIJTest123"
    
    @pytest.mark.unit
    def test_format_location_properties_all_fields(self):
        """Test formatting all possible location properties"""
        mock_notion_client = Mock()
        handler = LocationHandler(mock_notion_client)
        
        location_data = {
            "name of place": "Test Restaurant",
            "location": "123 Main St",
            "place_category": ["restaurant", "italian"],
            "recommendations": "Great pasta, amazing service",
            "review": "Really enjoyed the food",
            "time": "Mon-Fri: 11AM-10PM",
            "website": "https://restaurant.com",
            "visited": True,
            "maps_link": "https://maps.google.com/?q=place_id:ChIJTest123",
            "URL": "https://tiktok.com/test"
        }
        
        properties = handler._format_location_properties(location_data)
        
        # Check all fields are present
        assert "Name of Place" in properties
        assert "Source URL" in properties
        assert "Address" in properties
        assert "Categories" in properties
        assert "Recommendations" in properties
        assert "My Personal Review" in properties
        assert "Hours" in properties
        assert "Website" in properties
        assert "Is Popup" in properties
        assert "Visited" in properties
        
        # Check specific values
        assert properties["Recommendations"]["rich_text"][0]["text"]["content"] == "Great pasta, amazing service"
        assert properties["My Personal Review"]["rich_text"][0]["text"]["content"] == "Really enjoyed the food"
        assert properties["Hours"]["rich_text"][0]["text"]["content"] == "Mon-Fri: 11AM-10PM"
        assert properties["Website"]["url"] == "https://restaurant.com"
        assert properties["Visited"]["checkbox"] is True
        assert len(properties["Categories"]["multi_select"]) == 2
    
    @pytest.mark.unit
    def test_format_location_properties_minimal(self):
        """Test formatting with minimal data"""
        mock_notion_client = Mock()
        handler = LocationHandler(mock_notion_client)
        
        location_data = {
            "name of place": "Simple Place"
        }
        
        properties = handler._format_location_properties(location_data)
        
        # Check that minimal data still creates valid properties
        assert properties["Name of Place"]["title"][0]["text"]["content"] == "Simple Place"
        assert properties["Is Popup"]["checkbox"] is False
        assert properties["Visited"]["checkbox"] is False
        
        # Check that optional fields are not included if not provided
        assert "Address" not in properties
        assert "Categories" not in properties
        assert "Recommendations" not in properties
    
    @pytest.mark.unit
    def test_format_location_properties_empty_categories(self):
        """Test formatting with empty categories list"""
        mock_notion_client = Mock()
        handler = LocationHandler(mock_notion_client)
        
        location_data = {
            "name of place": "Test Place",
            "place_category": []
        }
        
        properties = handler._format_location_properties(location_data)
        
        # Empty categories should not create the Categories property
        assert "Categories" not in properties