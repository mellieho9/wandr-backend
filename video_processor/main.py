#!/usr/bin/env python3
"""
TikTok Video Processing Pipeline
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from video_downloader import TikTokDownloader
from audio_transcriptor import AudioTranscriptor
from video_frame_ocr import VideoFrameOCR

load_dotenv()

class TikTokProcessor:
    def __init__(self, vision_api_key=None, whisper_model="tiny"):
        self.downloader = TikTokDownloader()
        self.transcriptor = AudioTranscriptor(model_size=whisper_model)
        self.ocr_processor = VideoFrameOCR(vision_api_key) if vision_api_key else None
        print("✅ TikTok processor initialized")
    
    def process_url(self, url, output_dir="downloads", category="tiktok"):
        """Download and process TikTok video from URL"""
        # Extract video ID and check if files already exist
        video_id = self._extract_video_id(url)
        video_patterns = [f"t_{video_id}_.mp4", f"{video_id}_.mp4", f"t_{video_id}.mp4"]
        metadata_file = f"{category}_metadata.csv"
        
        # Check if video already exists
        existing_video = None
        for pattern in video_patterns:
            if os.path.exists(pattern):
                existing_video = pattern
                break
        
        if existing_video and os.path.exists(metadata_file):
            print(f"✅ Video already exists: {existing_video}")
            print(f"✅ Metadata already exists: {metadata_file}")
            print("🚀 Skipping download, proceeding to processing...")
            return self.process_video(existing_video, url)
        
        # Download if not exists
        print(f"📥 Downloading: {url}")
        download_result = self.downloader.download_video(url, output_dir, metadata_file)
        if not download_result['success']:
            return {'success': False, 'error': f"Download failed: {download_result['error']}"}
        
        # Find downloaded video
        video_path = None
        for pattern in video_patterns:
            if os.path.exists(pattern):
                video_path = pattern
                break
        
        if not video_path:
            # Fallback: find any recent .mp4 file
            mp4_files = list(Path(".").glob("*.mp4"))
            if mp4_files:
                video_path = str(max(mp4_files, key=os.path.getctime))
        
        if not video_path:
            return {'success': False, 'error': f"Video not found. Tried: {video_patterns}"}
        
        print(f"✅ Found video: {video_path}")
        return self.process_video(video_path, url)
    
    def process_video(self, video_path, original_url=None):
        """Process existing video file"""
        if not os.path.exists(video_path):
            return {'success': False, 'error': f"Video not found: {video_path}"}
        
        print(f"🎬 Processing: {Path(video_path).name}")
        
        results = {
            'video_path': video_path,
            'original_url': original_url,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }
        
        # Audio transcription
        print("🎵 Transcribing audio...")
        try:
            trans_result = self.transcriptor.transcribe_audio(video_path, language="en")
            results['transcription'] = {
                'text': trans_result.get('text', ''),
                'language': trans_result.get('language', 'en'),
                'success': bool(trans_result.get('text'))
            }
        except Exception as e:
            results['transcription'] = {'success': False, 'error': str(e)}
        
        # OCR (if available)
        if self.ocr_processor:
            print("📸 Extracting text from frames...")
            try:
                ocr_results = self.ocr_processor.extract_frames_and_ocr(video_path, frame_interval=3.0, max_frames=8)
                text_frames = [r for r in ocr_results if r.get('text')]
                results['ocr'] = {
                    'frames_with_text': len(text_frames),
                    'text_data': text_frames,
                    'success': len(text_frames) > 0
                }
            except Exception as e:
                results['ocr'] = {'success': False, 'error': str(e)}
        else:
            results['ocr'] = {'success': False, 'error': "No Vision API key"}
        
        # Combine results
        all_text = []
        if results['transcription']['success']:
            all_text.append(f"Audio: {results['transcription']['text']}")
        if results['ocr']['success']:
            for frame in results['ocr']['text_data']:
                all_text.append(f"Frame {frame['timestamp']}s: {frame['text']}")
        
        results['combined_text'] = "\n".join(all_text)
        
        # Print summary
        print(f"\n📋 RESULTS:")
        print(f"🎵 Audio: {'✅' if results['transcription']['success'] else '❌'}")
        print(f"📸 OCR: {'✅' if results['ocr']['success'] else '❌'}")
        print(f"📊 Text sources: {len(all_text)}")
        if all_text:
            print(f"📝 Combined text preview: {results['combined_text'][:200]}...")
        
        return results
    
    def _extract_video_id(self, url):
        """Extract video ID from TikTok URL"""
        if "/t/" in url:
            return url.rstrip('/').split('/t/')[-1].split('/')[0]
        elif "/video/" in url:
            return url.split('/video/')[-1].split('/')[0].split('?')[0]
        return "unknown"

def main():
    parser = argparse.ArgumentParser(description="TikTok Video Processor")
    parser.add_argument("--url", help="TikTok URL to download and process")
    parser.add_argument("--video", help="Local video file to process")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--category", default="tiktok", help="Category for metadata file")
    parser.add_argument("--model", default="tiny", choices=["tiny", "base", "small"], help="Whisper model")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR")
    
    args = parser.parse_args()
    
    if not args.url and not args.video:
        parser.error("Provide --url or --video")
    
    # Get API key
    vision_api_key = None if args.no_ocr else os.getenv("VISION_API_KEY")
    if not vision_api_key and not args.no_ocr:
        print("⚠️ No VISION_API_KEY - OCR disabled")
    
    # Process
    processor = TikTokProcessor(vision_api_key, args.model)
    
    if args.url:
        results = processor.process_url(args.url, category=args.category)
    else:
        results = processor.process_video(args.video)
    
    # Save results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved to: {args.output}")
    
    return 0 if results['success'] else 1

if __name__ == "__main__":
    exit(main())