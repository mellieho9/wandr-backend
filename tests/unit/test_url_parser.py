import pytest
from utils.url_parser import TikTokURLParser


class TestTikTokURLParser:
    
    @pytest.mark.unit
    def test_get_file_prefix_standard_url(self):
        url = "https://www.tiktok.com/@user/video/1234567890"
        result = TikTokURLParser.get_file_prefix(url)
        assert result == "user_video_1234567890"
    
    @pytest.mark.unit
    def test_get_file_prefix_with_params(self):
        url = "https://www.tiktok.com/@user/video/1234567890?param=value"
        result = TikTokURLParser.get_file_prefix(url)
        assert result == "user_video_1234567890"
    
    @pytest.mark.unit
    def test_get_results_filename(self):
        url = "https://www.tiktok.com/@user/video/1234567890"
        result = TikTokURLParser.get_results_filename(url)
        assert result == "results/user_video_1234567890_results.json"
    
    @pytest.mark.unit
    def test_get_metadata_filename(self):
        url = "https://www.tiktok.com/@user/video/1234567890"
        result = TikTokURLParser.get_metadata_filename(url)
        assert result == "results/user_video_1234567890_metadata.csv"