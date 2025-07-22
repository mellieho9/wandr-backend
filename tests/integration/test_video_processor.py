import pytest
import json
import os
from unittest.mock import Mock, patch
from services.video_processor import TikTokProcessor


class TestTikTokProcessorIntegration:
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_process_url_without_api_keys(self, temp_dir):
        """Test video processing without API keys (OCR disabled)"""
        processor = TikTokProcessor(vision_api_key=None, whisper_model="tiny")
        
        # This would normally download a video, but we'll mock it
        with patch.object(processor.downloader, 'download_content') as mock_download:
            mock_download.return_value = {
                'success': False,
                'error': 'Download failed for testing'
            }
            
            result = processor.process_url(
                "https://www.tiktok.com/@test/video/123456789",
                output_dir=temp_dir
            )
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.integration
    def test_process_existing_results(self, results_file):
        """Test processing when results already exist"""
        processor = TikTokProcessor(vision_api_key=None)
        
        # Mock the get_results_filename to return our test file
        with patch('utils.url_parser.TikTokURLParser.get_results_filename') as mock_filename:
            mock_filename.return_value = results_file
            
            result = processor.process_url("https://www.tiktok.com/@test/video/123456789")
            
            assert result['success'] is True
            assert result['content_type'] == 'video'