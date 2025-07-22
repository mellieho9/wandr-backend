import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from notion_handlern_service.url_processor import URLProcessor


class TestURLProcessor:
    
    @pytest.mark.unit
    def test_url_processor_initialization(self):
        """Test URLProcessor initialization"""
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        assert processor.notion_client == mock_notion_client
    
    @pytest.mark.unit
    @patch('notion_handlern_service.url_processor.datetime')
    def test_get_pending_urls_success(self, mock_datetime):
        """Test getting pending URLs successfully"""
        # Mock datetime to return a consistent date
        mock_datetime.now.return_value.strftime.return_value = "2023-01-15"
        mock_datetime.timezone.utc = timezone.utc
        
        mock_notion_client = Mock()
        mock_notion_client.query_database.return_value = {
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
        
        processor = URLProcessor(mock_notion_client)
        result = processor.get_pending_urls("test_db_id")
        
        # Check the query was made with correct filter
        expected_filter = {
            "and": [
                {
                    "property": "Created",
                    "date": {
                        "on_or_after": "2023-01-15"
                    }
                },
                {
                    "property": "Status",
                    "select": {
                        "equals": "Pending"
                    }
                }
            ]
        }
        
        mock_notion_client.query_database.assert_called_once_with(
            database_id="test_db_id",
            filter_conditions=expected_filter
        )
        
        # Check the result
        assert len(result) == 2
        assert result[0] == {"url": "https://tiktok.com/test1", "page_id": "page_1"}
        assert result[1] == {"url": "https://tiktok.com/test2", "page_id": "page_2"}
    
    @pytest.mark.unit
    def test_get_pending_urls_no_results(self):
        """Test getting pending URLs when no results found"""
        mock_notion_client = Mock()
        mock_notion_client.query_database.return_value = {"results": []}
        
        processor = URLProcessor(mock_notion_client)
        result = processor.get_pending_urls("test_db_id")
        
        assert result == []
    
    @pytest.mark.unit
    def test_get_pending_urls_exception(self):
        """Test getting pending URLs when exception occurs"""
        mock_notion_client = Mock()
        mock_notion_client.query_database.side_effect = Exception("Database error")
        
        processor = URLProcessor(mock_notion_client)
        result = processor.get_pending_urls("test_db_id")
        
        assert result == []
    
    @pytest.mark.unit
    def test_update_entry_status_success(self):
        """Test updating entry status successfully"""
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        result = processor.update_entry_status("page_123", "Completed")
        
        expected_properties = {
            "Status": {
                "select": {
                    "name": "Completed"
                }
            }
        }
        
        mock_notion_client.update_page.assert_called_once_with("page_123", expected_properties)
        assert result is True
    
    @pytest.mark.unit
    def test_update_entry_status_exception(self):
        """Test updating entry status when exception occurs"""
        mock_notion_client = Mock()
        mock_notion_client.update_page.side_effect = Exception("Update failed")
        
        processor = URLProcessor(mock_notion_client)
        result = processor.update_entry_status("page_123", "Completed")
        
        assert result is False
    
    @pytest.mark.unit
    def test_update_entry_status_custom_property(self):
        """Test updating entry status with custom status property"""
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        result = processor.update_entry_status("page_123", "Done", "Custom Status")
        
        expected_properties = {
            "Custom Status": {
                "select": {
                    "name": "Done"
                }
            }
        }
        
        mock_notion_client.update_page.assert_called_once_with("page_123", expected_properties)
        assert result is True
    
    @pytest.mark.unit
    @patch('pipeline_runner.run_complete_pipeline')
    def test_process_pending_urls_success(self, mock_pipeline):
        """Test processing pending URLs successfully"""
        # Mock the pipeline to succeed
        mock_pipeline.return_value = True
        
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        # Mock get_pending_urls to return test data
        processor.get_pending_urls = Mock(return_value=[
            {"url": "https://tiktok.com/test1", "page_id": "page_1"},
            {"url": "https://tiktok.com/test2", "page_id": "page_2"}
        ])
        
        # Mock update_entry_status to succeed
        processor.update_entry_status = Mock(return_value=True)
        
        result = processor.process_pending_urls("source_db", "places_db")
        
        # Check the result
        assert result["processed"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert len(result["urls"]) == 2
        assert result["urls"][0]["status"] == "success"
        assert result["urls"][1]["status"] == "success"
        
        # Check that pipeline was called for each URL
        assert mock_pipeline.call_count == 2
        mock_pipeline.assert_any_call(
            url="https://tiktok.com/test1",
            place_category=None,
            output_dir="results",
            create_notion_entry=True,
            database_id="places_db"
        )
    
    @pytest.mark.unit
    @patch('pipeline_runner.run_complete_pipeline')
    def test_process_pending_urls_mixed_results(self, mock_pipeline):
        """Test processing pending URLs with mixed success/failure"""
        # Mock the pipeline to succeed for first URL, fail for second
        mock_pipeline.side_effect = [True, False]
        
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        # Mock get_pending_urls to return test data
        processor.get_pending_urls = Mock(return_value=[
            {"url": "https://tiktok.com/test1", "page_id": "page_1"},
            {"url": "https://tiktok.com/test2", "page_id": "page_2"}
        ])
        
        # Mock update_entry_status to succeed
        processor.update_entry_status = Mock(return_value=True)
        
        result = processor.process_pending_urls("source_db", "places_db")
        
        # Check the result
        assert result["processed"] == 2
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert len(result["urls"]) == 2
        assert result["urls"][0]["status"] == "success"
        assert result["urls"][1]["status"] == "failed"
        
        # Check that update_entry_status was called with correct statuses
        processor.update_entry_status.assert_any_call("page_1", "Completed", "Status")
        processor.update_entry_status.assert_any_call("page_2", "Failed", "Status")
    
    @pytest.mark.unit
    @patch('pipeline_runner.run_complete_pipeline')
    def test_process_pending_urls_with_exception(self, mock_pipeline):
        """Test processing pending URLs when pipeline raises exception"""
        # Mock the pipeline to raise an exception
        mock_pipeline.side_effect = Exception("Pipeline error")
        
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        # Mock get_pending_urls to return test data
        processor.get_pending_urls = Mock(return_value=[
            {"url": "https://tiktok.com/test1", "page_id": "page_1"}
        ])
        
        # Mock update_entry_status to succeed
        processor.update_entry_status = Mock(return_value=True)
        
        result = processor.process_pending_urls("source_db", "places_db")
        
        # Check the result
        assert result["processed"] == 1
        assert result["successful"] == 0
        assert result["failed"] == 1
        assert len(result["urls"]) == 1
        assert result["urls"][0]["status"] == "error"
        assert "Pipeline error" in result["errors"][0]
        
        # Check that status was updated to Failed
        processor.update_entry_status.assert_called_once_with("page_1", "Failed", "Status")
    
    @pytest.mark.unit
    def test_process_pending_urls_no_urls(self):
        """Test processing pending URLs when no URLs found"""
        mock_notion_client = Mock()
        processor = URLProcessor(mock_notion_client)
        
        # Mock get_pending_urls to return empty list
        processor.get_pending_urls = Mock(return_value=[])
        
        result = processor.process_pending_urls("source_db", "places_db")
        
        # Check the result
        assert result["processed"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0
        assert result["urls"] == []