import pytest
import os
import tempfile
import json
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_video_results():
    """Sample video processing results for testing"""
    return {
        "original_url": "https://www.tiktok.com/@test/video/123456789",
        "content_type": "video", 
        "timestamp": "2024-01-01T00:00:00.000000",
        "success": True,
        "transcription": {
            "text": "This is a great restaurant in Brooklyn",
            "language": "en",
            "success": True
        },
        "ocr": {
            "frames_with_text": 2,
            "text_data": [
                {"timestamp": 0, "text": "Amazing Pizza Place"},
                {"timestamp": 5, "text": "123 Main St, Brooklyn NY"}
            ],
            "success": True
        },
        "combined_text": "Audio: This is a great restaurant in Brooklyn\nFrame 0s: Amazing Pizza Place\nFrame 5s: 123 Main St, Brooklyn NY"
    }


@pytest.fixture
def sample_location_data():
    """Sample location data for testing"""
    return {
        "url": "https://www.tiktok.com/@test/video/123456789",
        "content_type": "restaurant_review",
        "places": [
            {
                "name": "Amazing Pizza Place",
                "address": "123 Main St, Brooklyn, NY 11201, USA",
                "neighborhood": "Brooklyn Heights",
                "categories": ["restaurant", "pizza"],
                "recommendations": ["margherita pizza", "garlic knots"],
                "hours": "Mon-Sun: 11:00 AM - 11:00 PM",
                "website": "https://amazingpizza.com",
                "visited": False,
                "is_popup": False
            }
        ]
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    test_vars = {
        "VISION_API_KEY": "test_vision_key",
        "GEMINI_API_KEY": "test_gemini_key", 
        "GOOGLE_MAPS_API_KEY": "test_maps_key",
        "NOTION_API_KEY": "test_notion_key"
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_vars


@pytest.fixture
def results_file(temp_dir, sample_video_results):
    """Create a temporary results file for testing"""
    results_path = Path(temp_dir) / "test_results.json"
    with open(results_path, 'w') as f:
        json.dump(sample_video_results, f)
    return str(results_path)