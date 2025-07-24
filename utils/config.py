"""
Configuration file for environment variables

This module centralizes all environment variable loading and provides
a single source of truth for configuration across the application.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class containing all environment variables."""
    
    # API Keys
    VISION_API_KEY: Optional[str] = os.getenv("VISION_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # Notion Configuration
    NOTION_API_KEY: Optional[str] = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_API_KEY")
    NOTION_PLACES_DB_ID: Optional[str] = os.getenv("NOTION_PLACES_DB_ID")
    NOTION_SOURCE_DB_ID: Optional[str] = os.getenv("NOTION_SOURCE_DB_ID")
    
    @classmethod
    def get_vision_api_key(cls) -> Optional[str]:
        """Get Google Vision API key."""
        return cls.VISION_API_KEY
    
    @classmethod
    def get_gemini_api_key(cls) -> Optional[str]:
        """Get Google Gemini API key."""
        return cls.GEMINI_API_KEY
    
    @classmethod
    def get_google_maps_api_key(cls) -> Optional[str]:
        """Get Google Maps API key."""
        return cls.GOOGLE_MAPS_API_KEY
    
    @classmethod
    def get_notion_api_key(cls) -> Optional[str]:
        """Get Notion API key (checks both NOTION_API_KEY and NOTION_API_KEY)."""
        return cls.NOTION_API_KEY
    
    @classmethod
    def get_notion_places_db_id(cls) -> Optional[str]:
        """Get Notion Places database ID."""
        return cls.NOTION_PLACES_DB_ID
    
    @classmethod
    def get_notion_source_db_id(cls) -> Optional[str]:
        """Get Notion Source database ID."""
        return cls.NOTION_SOURCE_DB_ID
    
    @classmethod
    def validate_required_keys(cls, required_keys: list[str]) -> dict[str, str]:
        """
        Validate that required environment variables are set.
        
        Args:
            required_keys: List of required configuration keys
            
        Returns:
            Dictionary of validated key-value pairs
            
        Raises:
            ValueError: If any required keys are missing
        """
        missing_keys = []
        config_values = {}
        
        for key in required_keys:
            value = getattr(cls, key, None)
            if not value:
                missing_keys.append(key)
            else:
                config_values[key] = value
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        return config_values


# Convenience access to config instance
config = Config()