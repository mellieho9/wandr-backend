import pytest
import json
import os
from unittest.mock import Mock, patch
from location_processor import LocationProcessor
from models.location_models import LocationInfo, PlaceInfo


class TestLocationProcessorIntegration:
    
    @pytest.mark.integration
    def test_process_video_results_without_api_keys(self, temp_dir, sample_video_results):
        """Test location processing without API keys"""
        results_file = os.path.join(temp_dir, "test_results.json")
        with open(results_file, 'w') as f:
            json.dump(sample_video_results, f)
        
        processor = LocationProcessor(gemini_api_key=None, google_maps_api_key=None)
        
        # Mock the analyzer to return empty results
        with patch.object(processor.analyzer, 'analyze_content') as mock_analyze:
            mock_analyze.return_value = {
                'content_analysis': {'content_type': 'unknown', 'confidence_score': 0},
                'places': [],
                'area_info': {'total_places_mentioned': 0}
            }
            
            # This should work without API keys by using the mock
            with patch('location_processor.main.LocationProcessor.extract_from_files') as mock_extract:
                mock_extract.return_value = LocationInfo(
                    url=sample_video_results['original_url'],
                    content_type='unknown',
                    places=[]
                )
                
                result = processor.process_video_results("test", temp_dir)
                assert isinstance(result, LocationInfo)
                assert result.url == sample_video_results['original_url']
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_process_with_mock_apis(self, temp_dir, sample_video_results, mock_env_vars):
        """Test with mocked API responses"""
        results_file = os.path.join(temp_dir, "test_results.json")
        with open(results_file, 'w') as f:
            json.dump(sample_video_results, f)
        
        processor = LocationProcessor()
        
        # Mock successful API responses
        mock_gemini_response = {
            'content_analysis': {
                'content_type': 'restaurant_review',
                'confidence_score': 0.95
            },
            'places': [{
                'name': 'Amazing Pizza Place',
                'address': None,
                'neighborhood': 'Brooklyn',
                'categories': ['restaurant', 'pizza'],
                'recommendations': ['pizza'],
                'hours': None,
                'website': None,
                'is_primary': True,
                'is_popup': False
            }],
            'area_info': {'total_places_mentioned': 1}
        }
        
        with patch.object(processor.analyzer, 'analyze_content') as mock_analyze:
            mock_analyze.return_value = mock_gemini_response
            
            with patch.object(processor.places_service, 'enhance_location_info') as mock_places:
                mock_places.return_value = {
                    'has_valid_location': True,
                    'formatted_address': '123 Main St, Brooklyn, NY',
                    'website': 'https://example.com',
                    'hours': 'Mon-Sun: 11AM-11PM',
                    'maps_link': 'https://maps.google.com/?q=place_id:ChIJTest123'
                }
                
                result = processor.process_video_results("test", temp_dir)
                assert isinstance(result, LocationInfo)
                assert len(result.places) == 1
                assert result.places[0].name == 'Amazing Pizza Place'