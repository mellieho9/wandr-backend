"""
Centralized logging configuration and utilities for wandr pipeline
"""

import logging
import sys
from datetime import datetime
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "wandr-backend.log",
    console_output: bool = True
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file, None to disable file logging
        console_output: Whether to output to console
        
    Returns:
        Configured root logger
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to provide logger to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return logging.getLogger(self.__class__.__module__ + '.' + self.__class__.__name__)


class ProcessingLogger:
    """Utility class for consistent logging across TikTok processing pipeline"""
    
    @staticmethod
    def log_download_start(url: str):
        """Log start of content download"""
        logger.info(f"Downloading TikTok content: {url}")
    
    @staticmethod
    def log_processing_start(content_type: str):
        """Log start of content processing"""
        logger.info(f"Processing {content_type} content...")
    
    @staticmethod
    def log_ocr_start(count: int, content_type: str = "images"):
        """Log start of OCR processing"""
        logger.info(f"Extracting text from {count} {content_type}...")
    
    @staticmethod
    def log_transcription_start():
        """Log start of audio transcription"""
        logger.info("Transcribing audio...")
    
    @staticmethod
    def log_frame_extraction_start():
        """Log start of frame extraction"""
        logger.info("Extracting text from frames...")
    
    @staticmethod
    def log_results_saved(filename: str):
        """Log successful results saving"""
        logger.info(f"Results saved to: {filename}")
    
    @staticmethod
    def log_existing_results(filename: str):
        """Log when results already exist"""
        logger.info(f"Results already exist: {filename}")
    
    @staticmethod
    def log_file_not_found(expected_files: List[str]):
        """Log when expected files are not found"""
        logger.warning(f"Expected files not found: {expected_files}")
    
    @staticmethod
    def log_using_recent_file(filename: str):
        """Log when using most recent file as fallback"""
        logger.info(f"Using most recent file: {filename}")
    
    @staticmethod
    def log_selected_video_file(filename: str):
        """Log when video file is selected"""
        logger.info(f"Selected video file: {filename}")
    
    @staticmethod
    def log_carousel_summary(image_count: int, ocr_success: bool, images_with_text: int = 0):
        """Log carousel processing summary"""
        logger.info("CAROUSEL RESULTS:")
        logger.info(f"Images: {image_count}")
        logger.info(f"OCR: {'Success' if ocr_success else 'Failed'}")
        if ocr_success and images_with_text > 0:
            logger.info(f"Images with text: {images_with_text}")
    
    @staticmethod
    def log_video_summary(transcription_success: bool, ocr_success: bool, text_sources_count: int):
        """Log video processing summary"""
        logger.info("VIDEO RESULTS:")
        logger.info(f"Audio: {'Success' if transcription_success else 'Failed'}")
        logger.info(f"OCR: {'Success' if ocr_success else 'Failed'}")
        logger.info(f"Text sources: {text_sources_count}")
    
    @staticmethod
    def log_text_preview(combined_text: str, max_length: int = None):
        """Log preview of combined text"""
        if combined_text:
            from .constants import MAX_TEXT_PREVIEW_LENGTH
            max_len = max_length or MAX_TEXT_PREVIEW_LENGTH
            preview = combined_text[:max_len]
            logger.info(f"Combined text preview: {preview}...")
    
    @staticmethod
    def log_initialization(component: str):
        """Log component initialization"""
        logger.info(f"{component} initialized")
    
    @staticmethod
    def log_error(message: str):
        """Log error message"""
        logger.error(f"Error: {message}")
    
    @staticmethod
    def log_warning(message: str):
        """Log warning message"""
        logger.warning(f"Warning: {message}")
    
    @staticmethod
    def log_success(message: str):
        """Log success message"""
        logger.info(message)
    
    @staticmethod
    def create_result_metadata(url: str, content_type: str):
        """Create standard result metadata"""
        return {
            'original_url': url,
            'content_type': content_type,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }