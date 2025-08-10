"""TikTok video downloader with carousel support."""
import os
import time
from pathlib import Path

import pyktok as pyk
import requests

from utils import ProcessingLogger
from utils.logging_config import setup_logging

logger = setup_logging(logger_name=__name__)

class TikTokDownloader:
    """TikTok video downloader using pyktok"""
    
    def __init__(self, browser='chrome'):
        """Initialize the downloader with specified browser"""
        self.browser = browser
        try:
            pyk.specify_browser(browser)
            ProcessingLogger.log_initialization(f"TikTok downloader with {browser}")
        except Exception as e:
            ProcessingLogger.log_initialization(f"TikTok downloader initialized without browser cookies: {e}")
            # Continue without browser cookies - pyktok can still work


    def _download_carousel_images(self, url, output_dir):
        """Download carousel images using the fixed method"""
        try:
            ProcessingLogger.log_download_start(url)
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Convert photo URL to video URL for API access
            video_url = url.replace('/photo/', '/video/')
            
            # Get TikTok JSON data
            tt_json = pyk.alt_get_tiktok_json(video_url=video_url)
            
            # Navigate through JSON structure with error handling
            try:
                data_slot = tt_json["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
            except KeyError as e:
                # Try alternative JSON paths if the expected structure doesn't exist
                ProcessingLogger.log_error(f"Expected JSON structure not found: {e}")
                
                # Try direct access to itemStruct in different locations
                for alt_path in [
                    ["__DEFAULT_SCOPE__", "webapp.video-detail", "itemStruct"],
                    ["itemInfo", "itemStruct"],
                    ["itemStruct"]
                ]:
                    try:
                        data_slot = tt_json
                        for key in alt_path:
                            data_slot = data_slot[key]
                        break
                    except (KeyError, TypeError):
                        continue
                else:
                    raise Exception(f"Could not find itemStruct in JSON response. Available keys: {list(tt_json.keys()) if isinstance(tt_json, dict) else 'Not a dict'}")
            
            # Extract image URLs with error handling
            try:
                image_urls = [img["imageURL"]["urlList"][0] for img in data_slot["imagePost"]["images"]]
            except KeyError as e:
                raise Exception(f"Could not extract image URLs from carousel data: {e}. Available keys in data_slot: {list(data_slot.keys()) if isinstance(data_slot, dict) else 'Not a dict'}")
            
            # Extract username and photo ID for consistent naming
            username = None
            photo_id = None
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part.startswith('@'):
                    username = part  # Keep the @ symbol
                elif part == "photo" and i + 1 < len(parts):
                    photo_id = parts[i + 1].split('?')[0]
            
            # Download images with descriptive filenames
            image_files = []
            for idx, img_url in enumerate(image_urls):
                img_data = requests.get(img_url, timeout=30).content
                img_filename = f"{username}_photo_{photo_id}_{idx:02d}.jpg"
                img_path = Path(output_dir) / img_filename
                
                with open(img_path, "wb") as f:
                    f.write(img_data)
                
                image_files.append(str(img_path))
                ProcessingLogger.log_success(f"Downloaded image {idx + 1}/{len(image_urls)}")

            return {
                'success': True,
                'content_type': 'carousel',
                'image_files': image_files,
                'image_count': len(image_files)
            }

        except Exception as e:
            ProcessingLogger.log_error(f"Error downloading carousel: {e}")
            return {
                'success': False,
                'content_type': 'carousel',
                'error': str(e)
            }

    def download_content(self, url, output_dir=".", metadata_file=None, is_carousel=False):
        """
        Download TikTok content (video or carousel)
        
        Args:
            url: TikTok URL to download
            output_dir: Directory to save the content
            metadata_file: Optional CSV file to save metadata
            
        Returns:
            Dictionary with download results
        """
        try:
            
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            if is_carousel:
                return self._download_carousel_images(url, output_dir)
            else:
                return self._download_video_content(url, output_dir, metadata_file)
            
        except Exception as e:
            error_msg = f"Error downloading {url}: {e}"
            ProcessingLogger.log_error(error_msg)
            return {
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    def _download_video_content(self, url, output_dir, metadata_file):
        """
        Download video content using pyktok
        
        Args:
            url: TikTok URL to download
            output_dir: Directory to save the video
            metadata_file: Optional CSV file to save metadata
            
        Returns:
            Dictionary with download results
        """
        # Save current directory and change to output directory
        # since pyktok downloads to current working directory
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        try:
            # Download video and metadata
            if metadata_file:
                # For metadata file, use relative path from output_dir
                metadata_filename = os.path.basename(metadata_file)
                pyk.save_tiktok(url, True, metadata_filename)
            else:
                pyk.save_tiktok(url, True)
                
            # Find downloaded video files (only files created in the last 10 seconds)
            current_time = time.time()
            video_files = []
            
            for ext in ['*.mp4', '*.mov', '*.avi', '*.webm']:
                for file_path in Path('.').glob(ext):
                    # Check if file was created very recently (within last 10 seconds)
                    if current_time - os.path.getctime(file_path) < 10:
                        video_files.append(file_path)
            
            # Convert to absolute paths and sort by creation time (newest first)
            video_paths = []
            for video_file in video_files:
                # Construct path relative to original working directory
                abs_path = str(Path(original_cwd) / output_dir / video_file)
                
                if os.path.exists(str(video_file)):
                    # File exists in current directory (which is output_dir)
                    video_paths.append(abs_path)
                elif os.path.exists(abs_path):
                    video_paths.append(abs_path)
            
            video_paths.sort(key=lambda f: os.path.getctime(f) if os.path.exists(f) else 0, reverse=True)
            
        finally:
            # Always return to original directory
            os.chdir(original_cwd)
        
        ProcessingLogger.log_success(f"Successfully downloaded video: {url}")
        
        return {
            'url': url,
            'success': True,
            'content_type': 'video',
            'output_dir': output_dir,
            'metadata_file': metadata_file,
            'video_files': video_paths
        }
    
    def download_metadata_only(self, url, output_dir=".", metadata_file=None):
        """
        Extract only metadata without downloading video content
        
        Args:
            url: TikTok URL to extract metadata from
            output_dir: Directory to save metadata
            metadata_file: Optional CSV file to save metadata
            
        Returns:
            Dictionary with metadata extraction results
        """
        try:
            ProcessingLogger.log_processing_start('metadata-only extraction')
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # For photo carousels, convert to video URL for metadata extraction
            process_url = url
            if '/photo/' in url:
                process_url = url.replace('/photo/', '/video/')
                logger.info(f"Converted photo URL to video URL for metadata: {process_url}")
            
            # Save current directory and change to output directory
            original_cwd = os.getcwd()
            os.chdir(output_dir)
            
            try:
                # Extract only metadata using pyktok (False = don't download video)
                if metadata_file:
                    metadata_filename = os.path.basename(metadata_file)
                    pyk.save_tiktok(process_url, False, metadata_filename)
                else:
                    pyk.save_tiktok(process_url, False)
                
            finally:
                os.chdir(original_cwd)
            
            ProcessingLogger.log_success(f"Successfully extracted metadata: {url}")
            
            return {
                'url': url,
                'success': True,
                'content_type': 'metadata-only',
                'output_dir': output_dir,
                'metadata_file': metadata_file
            }
            
        except Exception as e:
            error_msg = f"Error extracting metadata from {url}: {e}"
            ProcessingLogger.log_error(error_msg)
            return {
                'url': url,
                'success': False,
                'content_type': 'metadata-only',
                'error': str(e)
            }
