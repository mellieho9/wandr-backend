import pytest
import os
from unittest.mock import patch, Mock
from main import process_tiktok_url
from models.location_models import LocationInfo, PlaceInfo


class TestMainPipeline:
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_pipeline_mock(self, temp_dir, sample_video_results, sample_location_data):
        """Test the complete pipeline with mocked components"""
        
        # Mock video processing
        with patch('main.TikTokProcessor') as mock_video_processor:
            mock_instance = Mock()
            mock_instance.process_url.return_value = sample_video_results
            mock_video_processor.return_value = mock_instance
            
            # Mock location processing
            with patch('main.LocationProcessor') as mock_location_processor:
                mock_loc_instance = Mock()
                
                # Create LocationInfo object from sample data
                place = PlaceInfo(
                    name=sample_location_data['places'][0]['name'],
                    address=sample_location_data['places'][0]['address'],
                    categories=sample_location_data['places'][0]['categories']
                )
                location_info = LocationInfo(
                    url=sample_location_data['url'],
                    content_type=sample_location_data['content_type'],
                    places=[place]
                )
                
                mock_loc_instance.process_video_results.return_value = location_info
                mock_loc_instance.save_location_info.return_value = None
                mock_location_processor.return_value = mock_loc_instance
                
                # Mock URL parser
                with patch('main.TikTokURLParser.get_file_prefix') as mock_prefix:
                    mock_prefix.return_value = "test_video_123"
                    
                    result = process_tiktok_url(
                        "https://www.tiktok.com/@test/video/123456789",
                        place_category=["restaurant"],
                        output_dir=temp_dir
                    )
                    
                    assert result is True
                    mock_instance.process_url.assert_called_once()
                    mock_loc_instance.process_video_results.assert_called_once()
    
    @pytest.mark.integration
    def test_pipeline_video_processing_failure(self, temp_dir):
        """Test pipeline when video processing fails"""
        
        with patch('main.TikTokProcessor') as mock_video_processor:
            mock_instance = Mock()
            mock_instance.process_url.return_value = {
                'success': False,
                'error': 'Download failed'
            }
            mock_video_processor.return_value = mock_instance
            
            result = process_tiktok_url(
                "https://www.tiktok.com/@test/video/123456789",
                output_dir=temp_dir
            )
            
            assert result is False