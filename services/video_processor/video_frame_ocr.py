import cv2
import requests
import json
import os

from utils import ProcessingLogger, ImageUtils, APIRateLimiter, OCRConfig
from utils.logging_config import setup_logging

logger = setup_logging(logger_name=__name__)

class VideoFrameOCR:
    """
    Enhanced OCR processor for both video frames and image files using Google Vision API
    """
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Google Vision API key is required")
        self.api_key = api_key
        self.base_url = OCRConfig.VISION_API_BASE_URL
        ProcessingLogger.log_initialization("Google Vision API")

    def extract_frames_and_ocr(self, video_path, frame_interval=3.0, max_frames=None):
        """
        Extract frames every N seconds and perform OCR using Google Vision API
        
        Args:
            video_path: Path to video file
            frame_interval: Seconds between frame extraction
            max_frames: Maximum number of frames to process
            
        Returns:
            List of dictionaries with timestamp and extracted text
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            ProcessingLogger.log_success(f"Video info: {duration:.1f}s duration, {fps:.1f} FPS")
            
            results = []
            timestamps = [t for t in range(0, int(duration) + 1, int(frame_interval))]
            
            if max_frames:
                timestamps = timestamps[:max_frames]
            
            ProcessingLogger.log_ocr_start(len(timestamps), "frames")
            
            for timestamp in timestamps:
                try:
                    frame_number = int(timestamp * fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    ret, frame = cap.read()
                    
                    if not ret:
                        ProcessingLogger.log_warning(f"Could not read frame at {timestamp}s")
                        continue
                    
                    # Progress logging handled by ProcessingLogger
                    
                    frame_b64 = ImageUtils.frame_to_base64(frame, OCRConfig.JPEG_QUALITY)
                    text = self._call_vision_api(frame_b64)
                    
                    results.append({'timestamp': timestamp, 'text': text})
                    APIRateLimiter.apply_rate_limit()
                    
                except Exception as e:
                    ProcessingLogger.log_error(f"Error at {timestamp}s: {e}")
                    results.append({'timestamp': timestamp, 'text': '', 'error': str(e)})
            
            text_found = len([r for r in results if r.get('text')])
            ProcessingLogger.log_success(f"Complete: {text_found}/{len(results)} frames with text")
            
            return results
            
        finally:
            cap.release()
    
    
    def extract_text_from_image(self, image_path):
        """
        Extract text from a single image file
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image path and extracted text
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            ProcessingLogger.log_success(f"Processing image: {os.path.basename(image_path)}")
            
            # Load and convert image to base64
            image_b64 = ImageUtils.file_to_base64(image_path)
            
            # Extract text using Vision API
            text = self._call_vision_api(image_b64)
            
            result = {
                'image_path': image_path,
                'text': text,
                'success': True
            }
            
            if text:
                preview = ImageUtils.get_text_preview(text, OCRConfig.TEXT_PREVIEW_LENGTH)
                ProcessingLogger.log_success(f"Found text: {preview}")
            else:
                ProcessingLogger.log_success("No text found in image")
            
            return result
            
        except Exception as e:
            ProcessingLogger.log_error(f"Error processing {image_path}: {e}")
            return {
                'image_path': image_path,
                'text': '',
                'success': False,
                'error': str(e)
            }
    
    def extract_text_from_images(self, image_paths):
        """
        Extract text from multiple image files (for carousel content)
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Dictionary with combined results and individual image results
        """
        if not image_paths:
            return {
                'combined_text': '',
                'image_results': [],
                'success': False,
                'error': 'No image paths provided'
            }
        
        ProcessingLogger.log_ocr_start(len(image_paths))
        
        image_results = []
        all_text = []
        
        for image_path in image_paths:
            # Progress logging handled by individual image processing
            
            result = self.extract_text_from_image(image_path)
            image_results.append(result)
            
            if result['success'] and result['text']:
                all_text.append(result['text'])
            
            # Rate limiting
            APIRateLimiter.apply_rate_limit()
        
        # Combine all text from images
        combined_text = ' '.join(all_text)
        combined_text = ImageUtils.clean_extracted_text(combined_text)
        
        success_count = len([r for r in image_results if r['success']])
        text_count = len([r for r in image_results if r.get('text')])
        
        ProcessingLogger.log_success(f"Processed {success_count}/{len(image_paths)} images, {text_count} with text")
        
        return {
            'combined_text': combined_text,
            'image_results': image_results,
            'success': success_count > 0,
            'images_processed': success_count,
            'images_with_text': text_count
        }
    
    def _call_vision_api(self, image_b64):
        """Call Google Vision API for text detection"""
        request_data = {
            "requests": [{
                "image": {"content": image_b64},
                "features": [{"type": "TEXT_DETECTION", "maxResults": OCRConfig.MAX_RESULTS}]
            }]
        }
        
        url = f"{self.base_url}?key={self.api_key}"
        
        try:
            response = requests.post(
                url, 
                headers={'Content-Type': 'application/json'}, 
                data=json.dumps(request_data),
                timeout=OCRConfig.API_TIMEOUT
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Check for API errors
            if 'error' in result:
                raise Exception(f"Vision API error: {result['error']}")
            
            # Extract text from response
            text = ''
            responses = result.get('responses', [])
            if responses and 'textAnnotations' in responses[0]:
                annotations = responses[0]['textAnnotations']
                if annotations:
                    text = annotations[0]['description'].strip()
                    text = ImageUtils.clean_extracted_text(text)
            
            return text
            
        except requests.RequestException as e:
            raise Exception(f"Network error calling Vision API: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Vision API: {e}")