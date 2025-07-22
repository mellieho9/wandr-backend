import pytest
from unittest.mock import Mock, patch, MagicMock
from notion_service.notion_client import NotionClient


class TestNotionClient:
    
    @pytest.mark.unit
    def test_notion_client_initialization_with_api_key(self):
        """Test NotionClient initialization with provided API key"""
        api_key = "test_api_key"
        
        with patch('notion_service.notion_client.Client') as mock_client:
            client = NotionClient(api_key)
            
            assert client.api_key == api_key
            mock_client.assert_called_once_with(auth=api_key)
    
    @pytest.mark.unit
    def test_notion_client_initialization_from_config(self):
        """Test NotionClient initialization using config"""
        with patch('notion_service.notion_client.config') as mock_config:
            mock_config.get_notion_api_key.return_value = "config_api_key"
            
            with patch('notion_service.notion_client.Client') as mock_client:
                client = NotionClient()
                
                assert client.api_key == "config_api_key"
                mock_client.assert_called_once_with(auth="config_api_key")
    
    @pytest.mark.unit
    def test_notion_client_initialization_no_api_key(self):
        """Test NotionClient initialization fails without API key"""
        with patch('notion_service.notion_client.config') as mock_config:
            mock_config.get_notion_api_key.return_value = None
            
            with pytest.raises(ValueError, match="NOTION_API_KEY environment variable is required"):
                NotionClient()
    
    @pytest.mark.unit
    def test_create_database_entry(self):
        """Test creating a database entry"""
        api_key = "test_api_key"
        database_id = "test_db_id"
        properties = {"title": {"title": [{"text": {"content": "Test"}}]}}
        
        with patch('notion_service.notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.pages.create.return_value = {"id": "page_123"}
            
            client = NotionClient(api_key)
            result = client.create_database_entry(database_id, properties)
            
            mock_client.pages.create.assert_called_once_with(
                parent={"database_id": database_id},
                properties=properties
            )
            assert result == {"id": "page_123"}
    
    @pytest.mark.unit
    def test_update_page(self):
        """Test updating a page"""
        api_key = "test_api_key"
        page_id = "page_123"
        properties = {"status": {"select": {"name": "Completed"}}}
        
        with patch('notion_service.notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.pages.update.return_value = {"id": "page_123"}
            
            client = NotionClient(api_key)
            result = client.update_page(page_id, properties)
            
            mock_client.pages.update.assert_called_once_with(
                page_id=page_id,
                properties=properties
            )
            assert result == {"id": "page_123"}
    
    @pytest.mark.unit
    def test_query_database(self):
        """Test querying a database"""
        api_key = "test_api_key"
        database_id = "test_db_id"
        filter_conditions = {"property": "Status", "select": {"equals": "Pending"}}
        
        with patch('notion_service.notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.databases.query.return_value = {"results": [{"id": "page_1"}]}
            
            client = NotionClient(api_key)
            result = client.query_database(database_id, filter_conditions)
            
            mock_client.databases.query.assert_called_once_with(
                database_id=database_id,
                filter=filter_conditions,
                page_size=100
            )
            assert result == {"results": [{"id": "page_1"}]}
    
    @pytest.mark.unit
    def test_create_location_entry_delegates_to_location_handler(self):
        """Test that create_location_entry delegates to LocationHandler"""
        api_key = "test_api_key"
        database_id = "test_db_id"
        location_data = {"name of place": "Test Restaurant"}
        
        with patch('notion_service.notion_client.Client'):
            with patch('notion_service.location_handler.LocationHandler') as mock_handler_class:
                mock_handler = Mock()
                mock_handler_class.return_value = mock_handler
                mock_handler.create_location_entry.return_value = {"id": "page_123"}
                
                client = NotionClient(api_key)
                result = client.create_location_entry(database_id, location_data)
                
                mock_handler_class.assert_called_once_with(client)
                mock_handler.create_location_entry.assert_called_once_with(database_id, location_data)
                assert result == {"id": "page_123"}
    
    @pytest.mark.unit
    def test_get_pending_urls_delegates_to_url_processor(self):
        """Test that get_pending_urls delegates to URLProcessor"""
        api_key = "test_api_key"
        database_id = "test_db_id"
        
        with patch('notion_service.notion_client.Client'):
            with patch('notion_service.url_processor.URLProcessor') as mock_processor_class:
                mock_processor = Mock()
                mock_processor_class.return_value = mock_processor
                mock_processor.get_pending_urls.return_value = [{"url": "test_url", "page_id": "page_123"}]
                
                client = NotionClient(api_key)
                result = client.get_pending_urls(database_id)
                
                mock_processor_class.assert_called_once_with(client)
                mock_processor.get_pending_urls.assert_called_once_with(database_id, "URL", "Created", "Status")
                assert result == [{"url": "test_url", "page_id": "page_123"}]
    
    @pytest.mark.unit
    def test_update_entry_status_delegates_to_url_processor(self):
        """Test that update_entry_status delegates to URLProcessor"""
        api_key = "test_api_key"
        page_id = "page_123"
        status = "Completed"
        
        with patch('notion_service.notion_client.Client'):
            with patch('notion_service.url_processor.URLProcessor') as mock_processor_class:
                mock_processor = Mock()
                mock_processor_class.return_value = mock_processor
                mock_processor.update_entry_status.return_value = True
                
                client = NotionClient(api_key)
                result = client.update_entry_status(page_id, status)
                
                mock_processor_class.assert_called_once_with(client)
                mock_processor.update_entry_status.assert_called_once_with(page_id, status, "Status")
                assert result is True
    
    @pytest.mark.unit
    def test_process_pending_urls_delegates_to_url_processor(self):
        """Test that process_pending_urls delegates to URLProcessor"""
        api_key = "test_api_key"
        source_db_id = "source_db"
        places_db_id = "places_db"
        
        with patch('notion_service.notion_client.Client'):
            with patch('notion_service.url_processor.URLProcessor') as mock_processor_class:
                mock_processor = Mock()
                mock_processor_class.return_value = mock_processor
                mock_processor.process_pending_urls.return_value = {"processed": 1, "successful": 1, "failed": 0}
                
                client = NotionClient(api_key)
                result = client.process_pending_urls(source_db_id, places_db_id)
                
                mock_processor_class.assert_called_once_with(client)
                mock_processor.process_pending_urls.assert_called_once_with(
                    source_db_id, places_db_id, "URL", "Created", "Status"
                )
                assert result == {"processed": 1, "successful": 1, "failed": 0}