"""
TikTok URL parsing utilities
Handles all URL parsing, video ID extraction, and filename generation
"""

from typing import Tuple, List, Optional
from models.url_models import URLComponents


class TikTokURLParser:
    """Utility class for parsing TikTok URLs and generating filenames"""
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract video ID from TikTok URL"""
        if "/t/" in url:
            return url.rstrip('/').split('/t/')[-1].split('/')[0]
        if "/video/" in url:
            return url.split('/video/')[-1].split('/')[0].split('?')[0]
        if "/photo/" in url:
            return url.split('/photo/')[-1].split('/')[0].split('?')[0]
        return "unknown"
    
    @staticmethod
    def parse_url_components(url: str) -> URLComponents:
        """Parse URL to extract all components"""
        video_id = TikTokURLParser.extract_video_id(url)
        username = None
        content_type = None
        
        if "/t/" in url:
            content_type = "short"
        elif "/@" in url:
            parts = url.split('/')
            for part in parts:
                if part.startswith('@'):
                    username = part[1:]  # Remove @ for file prefix
                    break
            
            if "/video/" in url:
                content_type = "video"
            elif "/photo/" in url:
                content_type = "photo"
        
        return URLComponents(
            video_id=video_id,
            username=username,
            content_type=content_type or "unknown",
            raw_url=url
        )
    
    @staticmethod
    def get_file_prefix(url: str) -> str:
        """Get file prefix based on URL format"""
        components = TikTokURLParser.parse_url_components(url)
        
        if components.content_type == "short":
            return f"t_{components.video_id}"
        if components.content_type == "video" and components.username:
            return f"{components.username}_video_{components.video_id}"
        if components.content_type == "photo" and components.username:
            return f"{components.username}_photo_{components.video_id}"
        return components.video_id
    
    @staticmethod
    def get_expected_filenames(url: str) -> List[str]:
        """Get expected filename patterns based on URL format"""
        components = TikTokURLParser.parse_url_components(url)
        
        if components.content_type == "short":
            return [f"t_{components.video_id}_.mp4", f"t_{components.video_id}.mp4"]
        if components.content_type == "video" and components.username:
            return [
                f"@{components.username}_video_{components.video_id}.mp4", 
                f"{components.username}_video_{components.video_id}.mp4"
            ]
        if components.content_type == "photo" and components.username:
            return [
                f"@{components.username}_photo_{components.video_id}.mp4", 
                f"{components.username}_photo_{components.video_id}.mp4"
            ]
        
        # Fallback patterns
        return [f"{components.video_id}.mp4", f"t_{components.video_id}.mp4"]
    
    @staticmethod
    def get_results_filename(url: str, suffix: str = "results") -> str:
        """Get results filename for a given URL"""
        file_prefix = TikTokURLParser.get_file_prefix(url)
        return f"results/{file_prefix}_{suffix}.json"
    
    @staticmethod
    def get_metadata_filename(url: str) -> str:
        """Get metadata filename for a given URL"""
        file_prefix = TikTokURLParser.get_file_prefix(url)
        return f"results/{file_prefix}_metadata.csv"