import cv2
import io
import base64
import requests
import json
from PIL import Image
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class VideoFrameOCR:
    """
    Video frame OCR using Google Vision API
    """
    
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Google Vision API key is required")
        self.api_key = api_key
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"
        print("✅ Google Vision API initialized")

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
            
            print(f"🎬 Video info: {duration:.1f}s duration, {fps:.1f} FPS")
            
            results = []
            timestamps = [t for t in range(0, int(duration) + 1, int(frame_interval))]
            
            if max_frames:
                timestamps = timestamps[:max_frames]
            
            print(f"📸 Processing {len(timestamps)} frames...")
            
            for i, timestamp in enumerate(timestamps):
                try:
                    frame_number = int(timestamp * fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    ret, frame = cap.read()
                    
                    if not ret:
                        print(f"⚠️ Could not read frame at {timestamp}s")
                        continue
                    
                    print(f"🔍 Processing frame {i+1}/{len(timestamps)} at {timestamp}s...")
                    
                    frame_b64 = self._frame_to_base64(frame)
                    text = self._call_vision_api(frame_b64)
                    
                    results.append({'timestamp': timestamp, 'text': text})
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    print(f"❌ Error at {timestamp}s: {e}")
                    results.append({'timestamp': timestamp, 'text': '', 'error': str(e)})
            
            text_found = len([r for r in results if r.get('text')])
            print(f"✅ Complete: {text_found}/{len(results)} frames with text")
            
            return results
            
        finally:
            cap.release()
    
    def _frame_to_base64(self, frame):
        """Convert OpenCV frame to base64"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=90)
        img_bytes = img_byte_arr.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def _call_vision_api(self, image_b64):
        """Call Google Vision API for text detection"""
        request_data = {
            "requests": [{
                "image": {"content": image_b64},
                "features": [{"type": "TEXT_DETECTION", "maxResults": 50}]
            }]
        }
        
        url = f"{self.base_url}?key={self.api_key}"
        
        try:
            response = requests.post(
                url, 
                headers={'Content-Type': 'application/json'}, 
                data=json.dumps(request_data),
                timeout=30
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
                    text = ' '.join(text.split())  # Clean up whitespace
            
            return text
            
        except requests.RequestException as e:
            raise Exception(f"Network error calling Vision API: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Vision API: {e}")

# Example usage and testing
if __name__ == "__main__":
    api_key = os.getenv("VISION_API_KEY")
    if not api_key:
        print("❌ VISION_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        exit(1)
    
    try:
        processor = VideoFrameOCR(api_key=api_key)
        video_path = "t_ZP8rwYBo3_.mp4"
        
        if os.path.exists(video_path):
            results = processor.extract_frames_and_ocr(video_path, frame_interval=3.0)
            
            print(f"\n📝 OCR Results:")
            for r in results:
                if r.get('text'):
                    print(f"  {r['timestamp']}s: {r['text']}")
        else:
            print(f"❌ Video file not found: {video_path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")