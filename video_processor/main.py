#!/usr/bin/env python3
"""
Enhanced TikTok Content Processing Pipeline
Supports both video and carousel content with edge case handling
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

from .video_downloader import TikTokDownloader
from .audio_transcriptor import AudioTranscriptor
from .video_frame_ocr import VideoFrameOCR
from utils import TikTokURLParser, ProcessingLogger

load_dotenv()

class TikTokProcessor:
    def __init__(self, vision_api_key=None, whisper_model="tiny"):
        self.downloader = TikTokDownloader()
        self.transcriptor = AudioTranscriptor(model_size=whisper_model)
        self.ocr_processor = VideoFrameOCR(vision_api_key) if vision_api_key else None
        ProcessingLogger.log_initialization("TikTok processor")

    def process_url(self, url, output_dir="results", category="tiktok"):
        """Enhanced method to download and process TikTok content (video or carousel)"""
        results_file = TikTokURLParser.get_results_filename(url)
        metadata_file = TikTokURLParser.get_metadata_filename(url)

        # Check if already processed
        if os.path.exists(results_file):
            ProcessingLogger.log_existing_results(results_file)
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Download content using enhanced downloader
        ProcessingLogger.log_download_start(url)
        download_result = self.downloader.download_content(url, output_dir, metadata_file)

        if not download_result['success']:
            return {'success': False, 'error': f"Download failed: {download_result['error']}"}

        # Determine content type and process accordingly
        content_type = download_result.get('content_type', 'unknown')

        if content_type == 'carousel':
            return self._process_carousel(download_result, url)
        return self._process_video(download_result, url)

    def _process_carousel(self, download_result, original_url):
        """Process carousel (image slideshow) content"""
        ProcessingLogger.log_processing_start('carousel')

        results = ProcessingLogger.create_result_metadata(original_url, 'carousel')
        results['download_result'] = download_result

        # Get image files from download result
        image_files = download_result.get('image_files', [])

        if not image_files:
            results['success'] = False
            results['error'] = "No image files found in carousel download"
            return results

        # OCR processing for carousel images
        if self.ocr_processor:
            ProcessingLogger.log_ocr_start(len(image_files))
            try:
                ocr_result = self.ocr_processor.extract_text_from_images(image_files)
                results['ocr'] = ocr_result
            except Exception as e:
                results['ocr'] = {'success': False, 'error': str(e)}
        else:
            results['ocr'] = {'success': False, 'error': "No Vision API key"}

        # No audio transcription for carousel content
        results['transcription'] = {'success': False, 'reason': 'Carousel content has no audio'}

        # Combine results
        all_text = []
        if results['ocr']['success']:
            combined_text = results['ocr'].get('combined_text', '')
            if combined_text:
                all_text.append(f"Images: {combined_text}")

        results['combined_text'] = "\n".join(all_text)

        # Print summary
        ProcessingLogger.log_carousel_summary(
            len(image_files), 
            results['ocr']['success'],
            results['ocr'].get('images_with_text', 0) if results['ocr']['success'] else 0
        )
        ProcessingLogger.log_text_preview(results['combined_text'])

        # Save results to file with proper naming
        self._save_results(results, original_url)

        return results

    def _process_video(self, download_result, original_url):
        """Process video content (enhanced version of existing process_video)"""
        ProcessingLogger.log_processing_start('video')

        expected_filenames = TikTokURLParser.get_expected_filenames(original_url)

        video_path = None
        # Check both root and results directory
        for filename in expected_filenames:
            # Check root directory
            if os.path.exists(filename):
                video_path = filename
                break
            # Check results directory
            results_path = f"results/{filename}"
            if os.path.exists(results_path):
                video_path = results_path
                break

        # If still not found, look for the most recent .mp4 file in results
        if not video_path:
            ProcessingLogger.log_file_not_found(expected_filenames)
            results_dir = Path("results")
            if results_dir.exists():
                mp4_files = list(results_dir.glob("*.mp4"))
                if mp4_files:
                    video_path = str(max(mp4_files, key=os.path.getctime))
                    ProcessingLogger.log_using_recent_file(os.path.basename(video_path))

        if not video_path:
            return {'success': False, 'error': f"No video file found in download results"}

        if not os.path.exists(video_path):
            return {'success': False, 'error': f"Video file not found at: {video_path}"}

        results = ProcessingLogger.create_result_metadata(original_url, 'video')
        results['video_path'] = video_path
        results['download_result'] = download_result

        # Audio transcription
        ProcessingLogger.log_transcription_start()
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
            ProcessingLogger.log_frame_extraction_start()
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
        ProcessingLogger.log_video_summary(
            results['transcription']['success'],
            results['ocr']['success'],
            len(all_text)
        )
        ProcessingLogger.log_text_preview(results['combined_text'])

        # Save results to file with proper naming
        self._save_results(results, original_url)

        return results

    def _save_results(self, results, original_url):
        """Save processing results to JSON file with proper naming"""
        results_file = TikTokURLParser.get_results_filename(original_url)
        os.makedirs("results", exist_ok=True)

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        ProcessingLogger.log_results_saved(results_file)

    def process_video(self, video_path, original_url=None):
        """Legacy method for backward compatibility - processes existing video file"""
        download_result = {
            'success': True,
            'content_type': 'video',
            'video_files': [video_path]
        }
        return self._process_video(download_result, original_url)


