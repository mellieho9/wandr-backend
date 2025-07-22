import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from notion_service.notion_client import NotionClient
from notion_service.location_handler import LocationHandler
from notion_service.url_processor import URLProcessor


class TestNotionServiceIntegration:
    
    @pytest.mark.integration
    def test_notion_client_with_location_handler_integration(self):
        """Test NotionClient and LocationHandler working together"""
        with patch('notion_service.notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.pages.create.return_value = {"id": "page_123", "url": "https://notion.so/page_123"}
            
            # Test the integration
            notion_client = NotionClient("test_api_key")
            
            location_data = {
                "name of place": "Integration Test Restaurant",
                "location": "456 Test Ave, Test City",
                "place_category": ["restaurant", "test"],
                "recommendations": "Great for testing",
                "URL": "https://tiktok.com/integration-test"
            }
            
            # This should create a LocationHandler internally and call it
            result = notion_client.create_location_entry("test_db_id", location_data)
            
            # Verify the database entry was created
            mock_client.pages.create.assert_called_once()
            call_args = mock_client.pages.create.call_args
            
            # Check that the properties were formatted correctly
            properties = call_args[1]["properties"]
            assert properties["Name of Place"]["title"][0]["text"]["content"] == "Integration Test Restaurant"
            assert properties["Address"]["rich_text"][0]["text"]["content"] == "456 Test Ave, Test City"
            assert properties["Source URL"]["url"] == "https://tiktok.com/integration-test"
            
            assert result == {"id": "page_123", "url": "https://notion.so/page_123"}
    
    @pytest.mark.integration
    def test_notion_client_with_url_processor_integration(self):
        """Test NotionClient and URLProcessor working together"""
        with patch('notion_service.notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock the database query response
            mock_client.databases.query.return_value = {
                "results": [
                    {
                        "id": "page_1",
                        "properties": {
                            "URL": {
                                "type": "url",
                                "url": "https://tiktok.com/integration-test"
                            }
                        }
                    }
                ]
            }
            
            # Test the integration
            notion_client = NotionClient("test_api_key")
            
            # This should create a URLProcessor internally and call it
            result = notion_client.get_pending_urls("test_db_id")
            
            # Verify the database was queried
            mock_client.databases.query.assert_called_once()
            call_args = mock_client.databases.query.call_args
            
            # Check the filter was set up correctly
            filter_conditions = call_args[1]["filter"]
            assert filter_conditions["and"][0]["property"] == "Created"
            assert filter_conditions["and"][1]["property"] == "Status"
            assert filter_conditions["and"][1]["select"]["equals"] == "Pending"
            
            assert result == [{"url": "https://tiktok.com/integration-test", "page_id": "page_1"}]
    
    @pytest.mark.integration
    @patch('pipeline_runner.run_complete_pipeline')
    def test_full_pending_url_processing_flow(self, mock_pipeline):
        """Test the complete flow of processing pending URLs"""
        # Mock the pipeline to succeed
        mock_pipeline.return_value = True
        
        with patch('notion_service.notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock database query to return pending URLs
            mock_client.databases.query.return_value = {
                "results": [
                    {
                        "id": "page_1",
                        "properties": {
                            "URL": {
                                "type": "url",
                                "url": "https://tiktok.com/test1"
                            }
                        }
                    },
                    {
                        "id": "page_2", 
                        "properties": {
                            "URL": {
                                "type": "url",
                                "url": "https://tiktok.com/test2"
                            }
                        }
                    }
                ]
            }
            
            # Mock page updates to succeed
            mock_client.pages.update.return_value = {"id": "updated"}
            
            # Test the integration
            notion_client = NotionClient("test_api_key")
            result = notion_client.process_pending_urls("source_db", "places_db")
            
            # Verify the complete flow
            assert result["processed"] == 2
            assert result["successful"] == 2
            assert result["failed"] == 0
            
            # Verify database was queried for pending URLs
            mock_client.databases.query.assert_called_once()
            
            # Verify pipeline was called for each URL
            assert mock_pipeline.call_count == 2
            mock_pipeline.assert_any_call(
                url="https://tiktok.com/test1",
                place_category=None,
                output_dir="results", 
                create_notion_entry=True,
                database_id="places_db"
            )
            mock_pipeline.assert_any_call(
                url="https://tiktok.com/test2",
                place_category=None,
                output_dir="results",
                create_notion_entry=True, 
                database_id="places_db"
            )
            
            # Verify pages were updated to "Completed" status
            assert mock_client.pages.update.call_count == 2
    
    @pytest.mark.integration
    def test_location_handler_standalone(self):
        """Test LocationHandler as a standalone component"""
        mock_notion_client = Mock()
        mock_notion_client.create_database_entry.return_value = {"id": "test_page"}
        
        handler = LocationHandler(mock_notion_client)
        
        location_data = {
            "name of place": "Standalone Test Restaurant",
            "location": "789 Standalone St",
            "place_category": ["restaurant"],
            "maps_link": "https://maps.google.com/?q=place_id:ChIJStandalone123",
            "recommendations": "Perfect for unit testing",
            "time": "24/7 Testing Hours",
            "website": "https://test-restaurant.com",
            "visited": True,
            "URL": "https://tiktok.com/standalone-test"
        }
        
        result = handler.create_location_entry("test_db", location_data)
        
        # Verify the database entry was created
        mock_notion_client.create_database_entry.assert_called_once()
        call_args = mock_notion_client.create_database_entry.call_args
        
        database_id = call_args[0][0]
        properties = call_args[0][1]
        
        assert database_id == "test_db"
        
        # Verify all properties were formatted correctly
        assert properties["Name of Place"]["title"][0]["text"]["content"] == "Standalone Test Restaurant"
        assert properties["Address"]["rich_text"][0]["text"]["content"] == "789 Standalone St"
        assert properties["Address"]["rich_text"][0]["text"]["link"]["url"] == "https://maps.google.com/?q=place_id:ChIJStandalone123"
        assert properties["Categories"]["multi_select"][0]["name"] == "restaurant"
        assert properties["Recommendations"]["rich_text"][0]["text"]["content"] == "Perfect for unit testing"
        assert properties["Hours"]["rich_text"][0]["text"]["content"] == "24/7 Testing Hours"
        assert properties["Website"]["url"] == "https://test-restaurant.com"
        assert properties["Visited"]["checkbox"] is True
        assert properties["Source URL"]["url"] == "https://tiktok.com/standalone-test"
        
        assert result == {"id": "test_page"}
    
    @pytest.mark.integration 
    @patch('pipeline_runner.run_complete_pipeline')
    def test_url_processor_standalone(self, mock_pipeline):
        """Test URLProcessor as a standalone component"""
        # Mock pipeline success and failure
        mock_pipeline.side_effect = [True, False, Exception("Test error")]
        
        mock_notion_client = Mock()
        
        # Mock database query
        mock_notion_client.query_database.return_value = {
            "results": [
                {"id": "page_1", "properties": {"URL": {"type": "url", "url": "https://tiktok.com/success"}}},
                {"id": "page_2", "properties": {"URL": {"type": "url", "url": "https://tiktok.com/failure"}}},
                {"id": "page_3", "properties": {"URL": {"type": "url", "url": "https://tiktok.com/error"}}}
            ]
        }
        
        # Mock page updates
        mock_notion_client.update_page.return_value = {"id": "updated"}
        
        processor = URLProcessor(mock_notion_client)
        result = processor.process_pending_urls("source_db", "places_db")
        
        # Verify results
        assert result["processed"] == 3
        assert result["successful"] == 1
        assert result["failed"] == 2
        assert len(result["errors"]) == 2
        
        # Verify status updates were called correctly
        assert mock_notion_client.update_page.call_count == 3
        
        # Check that the correct statuses were set
        update_calls = mock_notion_client.update_page.call_args_list
        
        # First URL should be marked as Completed
        assert update_calls[0][0][1]["Status"]["select"]["name"] == "Completed"
        
        # Second URL should be marked as Failed
        assert update_calls[1][0][1]["Status"]["select"]["name"] == "Failed"
        
        # Third URL should be marked as Failed (due to exception)
        assert update_calls[2][0][1]["Status"]["select"]["name"] == "Failed"