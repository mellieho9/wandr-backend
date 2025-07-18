"""
Processing logger utilities
Handles consistent logging and progress reporting across the pipeline
"""

from datetime import datetime
from typing import Dict, Any, List


class ProcessingLogger:
    """Utility class for consistent logging across TikTok processing pipeline"""
    
    @staticmethod
    def log_download_start(url: str):
        """Log start of content download"""
        print(f"📥 Downloading TikTok content: {url}")
    
    @staticmethod
    def log_processing_start(content_type: str):
        """Log start of content processing"""
        emoji = "🖼️" if content_type == "carousel" else "🎬"
        print(f"{emoji} Processing {content_type} content...")
    
    @staticmethod
    def log_ocr_start(count: int, content_type: str = "images"):
        """Log start of OCR processing"""
        print(f"📸 Extracting text from {count} {content_type}...")
    
    @staticmethod
    def log_transcription_start():
        """Log start of audio transcription"""
        print("🎵 Transcribing audio...")
    
    @staticmethod
    def log_frame_extraction_start():
        """Log start of frame extraction"""
        print("📸 Extracting text from frames...")
    
    @staticmethod
    def log_results_saved(filename: str):
        """Log successful results saving"""
        print(f"💾 Results saved to: {filename}")
    
    @staticmethod
    def log_existing_results(filename: str):
        """Log when results already exist"""
        print(f"✅ Results already exist: {filename}")
    
    @staticmethod
    def log_file_not_found(expected_files: List[str]):
        """Log when expected files are not found"""
        print(f"⚠️ Expected files not found: {expected_files}")
    
    @staticmethod
    def log_using_recent_file(filename: str):
        """Log when using most recent file as fallback"""
        print(f"📁 Using most recent file: {filename}")
    
    @staticmethod
    def log_selected_video_file(filename: str):
        """Log when video file is selected"""
        print(f"✅ Selected video file: {filename}")
    
    @staticmethod
    def log_carousel_summary(image_count: int, ocr_success: bool, images_with_text: int = 0):
        """Log carousel processing summary"""
        print(f"\n📋 CAROUSEL RESULTS:")
        print(f"🖼️ Images: {image_count}")
        print(f"📸 OCR: {'✅' if ocr_success else '❌'}")
        if ocr_success and images_with_text > 0:
            print(f"📊 Images with text: {images_with_text}")
    
    @staticmethod
    def log_video_summary(transcription_success: bool, ocr_success: bool, text_sources_count: int):
        """Log video processing summary"""
        print(f"\n📋 VIDEO RESULTS:")
        print(f"🎵 Audio: {'✅' if transcription_success else '❌'}")
        print(f"📸 OCR: {'✅' if ocr_success else '❌'}")
        print(f"📊 Text sources: {text_sources_count}")
    
    @staticmethod
    def log_text_preview(combined_text: str, max_length: int = 200):
        """Log preview of combined text"""
        if combined_text:
            preview = combined_text[:max_length]
            print(f"📝 Combined text preview: {preview}...")
    
    @staticmethod
    def log_initialization(component: str):
        """Log component initialization"""
        print(f"✅ {component} initialized")
    
    @staticmethod
    def log_error(message: str):
        """Log error message"""
        print(f"❌ Error: {message}")
    
    @staticmethod
    def log_warning(message: str):
        """Log warning message"""
        print(f"⚠️ Warning: {message}")
    
    @staticmethod
    def log_success(message: str):
        """Log success message"""
        print(f"✅ {message}")
    
    @staticmethod
    def create_result_metadata(url: str, content_type: str) -> Dict[str, Any]:
        """Create standard result metadata"""
        return {
            'original_url': url,
            'content_type': content_type,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }