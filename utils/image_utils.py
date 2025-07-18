"""
Image processing utilities for TikTok content pipeline
Handles base64 encoding, text cleaning, and other image-related operations
"""

import base64
import cv2
import time
from typing import List, Optional


class ImageUtils:
    """Utility class for image processing operations"""
    
    @staticmethod
    def file_to_base64(file_path: str) -> str:
        """Convert image file to base64 string"""
        with open(file_path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded
    
    @staticmethod
    def frame_to_base64(frame, quality: int = 90) -> str:
        """Convert OpenCV frame to base64 string"""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        encoded = base64.b64encode(buffer).decode('utf-8')
        return encoded
    
    @staticmethod
    def clean_extracted_text(text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        return ' '.join(text.split())
    
    @staticmethod
    def get_text_preview(text: str, max_length: int = 100) -> str:
        """Get a preview of text with ellipsis if too long"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."


class APIRateLimiter:
    """Utility class for API rate limiting"""
    
    DEFAULT_DELAY = 0.1
    
    @classmethod
    def apply_rate_limit(cls, delay: Optional[float] = None):
        """Apply rate limiting delay"""
        if delay is None:
            delay = cls.DEFAULT_DELAY
        time.sleep(delay)


class OCRConfig:
    """Configuration constants for OCR operations"""
    
    DEFAULT_FRAME_INTERVAL = 3.0
    RATE_LIMIT_DELAY = 0.1
    JPEG_QUALITY = 90
    API_TIMEOUT = 30
    MAX_RESULTS = 50
    TEXT_PREVIEW_LENGTH = 100
    
    # Vision API settings
    VISION_API_BASE_URL = "https://vision.googleapis.com/v1/images:annotate"
    MAX_RETRIES = 3