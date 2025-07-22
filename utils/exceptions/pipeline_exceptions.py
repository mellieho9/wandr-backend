"""
Exception hierarchy for wandr pipeline operations
"""

from typing import Optional, Dict, Any


class WandrError(Exception):
    """Base exception for wandr pipeline operations"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"{self.message} (context: {context_str})"
        return self.message


class VideoProcessingError(WandrError):
    """Raised when video processing operations fail"""
    pass


class LocationExtractionError(WandrError):
    """Raised when location extraction operations fail"""
    pass


class NotionIntegrationError(WandrError):
    """Raised when Notion API operations fail"""
    pass


class ConfigurationError(WandrError):
    """Raised when configuration is invalid or missing"""
    pass