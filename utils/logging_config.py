"""
Centralized logging configuration and utilities for wandr pipeline
"""

import logging
import sys
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from utils.constants import Colors

logger = logging.getLogger(__name__)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # Map log levels to colors
    COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.WHITE,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA,
        'SUCCESS': Colors.GREEN,
    }
    RESET = Colors.RESET
    
    def format(self, record):
        # Get the color for this log level
        color = self.COLORS.get(record.levelname, Colors.WHITE)
        
        # Format the message
        formatted = super().format(record)
        
        # Add color to the entire line
        if color != Colors.WHITE:
            formatted = f"{color}{formatted}{Colors.RESET}"
        
        return formatted


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "wandr-backend.log",
    console_output: bool = True,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file, None to disable file logging
        console_output: Whether to output to console
        logger_name: Name for the logger (typically __name__)
        
    Returns:
        Configured logger for the module if logger_name provided, otherwise root logger
    """
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler without colors
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Return specific logger if name provided, otherwise root logger
    if logger_name:
        return logging.getLogger(logger_name)
    return root_logger


def log_success(logger_instance, message: str):
    """Log a success message with green color"""
    # Create a custom log record with SUCCESS level
    record = logging.LogRecord(
        name=logger_instance.name,
        level=25,  # Between INFO (20) and WARNING (30)
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.levelname = "SUCCESS"
    logger_instance.handle(record)


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
        if ocr_success:
            log_success(logger, "OCR: Success")
        else:
            logger.error("OCR: Failed")
        if ocr_success and images_with_text > 0:
            logger.info(f"Images with text: {images_with_text}")
    
    @staticmethod
    def log_video_summary(transcription_success: bool, ocr_success: bool, text_sources_count: int):
        """Log video processing summary"""
        logger.info("VIDEO RESULTS:")
        if transcription_success:
            log_success(logger, "Audio: Success")
        else:
            logger.error("Audio: Failed")
        if ocr_success:
            log_success(logger, "OCR: Success")
        else:
            logger.error("OCR: Failed")
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