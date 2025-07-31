"""Simple cleanup utility for removing processed files after pipeline completion."""

import os
from pathlib import Path
from .url_parser import generate_results_file_path, generate_metadata_file_path
from .logging_config import setup_logging

logger = setup_logging(logger_name=__name__)

def cleanup_video_files(video_id: str) -> bool:
    """Clean up all files for a specific video ID after processing"""
    try:
        cleaned_files = []
        
        # Clean up results JSON and metadata CSV
        for file_path in [generate_results_file_path(video_id), generate_metadata_file_path(video_id)]:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleaned_files.append(file_path)
        
        # Clean up video/image files with video_id pattern
        results_path = Path("results")
        if results_path.exists():
            for file_path in results_path.glob(f"*{video_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    cleaned_files.append(str(file_path))
        
        if cleaned_files:
            logger.info(f"Cleaned up {len(cleaned_files)} files for video {video_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to cleanup files for video {video_id}: {e}")
        return False