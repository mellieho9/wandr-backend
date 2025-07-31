#!/usr/bin/env python3
"""
Enhanced TikTok Content Processing Pipeline
Supports both video and carousel content with edge case handling
"""

import os

from models.pipeline_models import ProcessingMode
import pandas as pd
from .video_downloader import TikTokDownloader
from .audio_transcriptor import AudioTranscriptor
from .video_frame_ocr import VideoFrameOCR
from utils import TikTokURLParser, ProcessingLogger

class TikTokProcessor:
    def __init__(self, vision_api_key=None, frame_interval=3.0, max_frames=8):
        """
        Initialize TikTok processor with configurable options.
        
        Args:
            vision_api_key: Google Vision API key for OCR
            frame_interval: Seconds between frame extractions
            max_frames: Maximum frames to extract for OCR
        """
        self.downloader = TikTokDownloader()
        self.transcriptor = AudioTranscriptor()
        self.ocr_processor = VideoFrameOCR(vision_api_key) if vision_api_key else None
        self.frame_interval = frame_interval
        self.max_frames = max_frames
        ProcessingLogger.log_initialization("TikTok processor")

    def process_with_data_return(self, url, processing_mode, output_dir="results"):
        """Process video and return both results and metadata without saving files"""
        metadata_file = TikTokURLParser.get_metadata_filename(url)
        metadata = self._process_metadata(url, output_dir, metadata_file)

        if processing_mode == ProcessingMode.METADATA_ONLY:
            results = None
        elif processing_mode == ProcessingMode.AUDIO_ONLY:
            results = self._process_audio_only_data(url, output_dir, metadata_file)
        else:
            results = self._process_video_data(url, output_dir, metadata_file)
        
        return results, metadata

    def _process_video_data(self, url, output_dir, metadata_file):
        """Process full video or carousel without saving results file"""
        # Download content using enhanced downloader
        ProcessingLogger.log_download_start(url)
        download_result = self.downloader.download_content(url, output_dir, metadata_file)

        if not download_result['success']:
            return {'success': False, 'error': f"Download failed: {download_result['error']}"}

        # Check content type and process accordingly
        content_type = download_result.get('content_type', 'video')
        
        if content_type == 'carousel':
            # Process carousel content
            ProcessingLogger.log_processing_start('carousel')
            results = ProcessingLogger.create_result_metadata(url, 'carousel')
            results['download_result'] = download_result

            # Get image files from download result
            image_files = download_result.get('image_files', [])
            if not image_files:
                return {'success': False, 'error': "No image files found in carousel download"}

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

            # Combine results for carousel
            all_text = []
            if results['ocr']['success']:
                combined_text = results['ocr'].get('combined_text', '')
                if combined_text:
                    all_text.append(f"Images: {combined_text}")
            results['combined_text'] = "\n".join(all_text)
            
            ProcessingLogger.log_carousel_summary(
                len(image_files), 
                results['ocr']['success'],
                results['ocr'].get('images_with_text', 0) if results['ocr']['success'] else 0
            )
            ProcessingLogger.log_text_preview(results['combined_text'])
            return results
        
        else:
            # Process video content
            results = ProcessingLogger.create_result_metadata(url, 'full')
            results['download_result'] = download_result

            # Get video path for processing
            video_files = download_result.get('video_files', [])
            video_path = video_files[0] if video_files else None
            
            if not video_path or not os.path.exists(video_path):
                return {'success': False, 'error': 'Video file not found after download'}

            results['video_path'] = video_path

            # Audio transcription
            ProcessingLogger.log_transcription_start()
            try:
                trans_result = self.transcriptor.transcribe_audio(video_path)
                results['transcription'] = {
                    'text': trans_result.get('text', ''),
                    'success': bool(trans_result.get('text', ''))
                }
            except Exception as e:
                results['transcription'] = {'success': False, 'error': str(e)}

            # OCR (if available)
            if self.ocr_processor:
                ProcessingLogger.log_frame_extraction_start()
                try:
                    ocr_results = self.ocr_processor.extract_frames_and_ocr(
                        video_path, 
                        max_frames=self.max_frames,
                        frame_interval=self.frame_interval
                    )
                    results['ocr'] = {
                        'success': bool(ocr_results.get('text_data')),
                        'text_data': ocr_results.get('text_data', []),
                        'frames_processed': ocr_results.get('frames_processed', 0)
                    }
                except Exception as e:
                    results['ocr'] = {'success': False, 'error': str(e)}
            else:
                results['ocr'] = {'success': False, 'reason': 'OCR processor not available'}

            # Combine text sources for video
            all_text = []
            if results['transcription']['success']:
                all_text.append(f"Audio: {results['transcription']['text']}")
            if results['ocr']['success']:
                for frame in results['ocr']['text_data']:
                    all_text.append(f"Frame: {frame['text']}")

            results['combined_text'] = "\n".join(all_text)
            return results

    def _process_metadata(self, url, output_dir, metadata_file):
        """Extract only metadata without saving results file"""
        # Extract metadata only
        ProcessingLogger.log_download_start(url)
        download_result = self.downloader.download_metadata_only(url, output_dir, metadata_file)

        if not download_result['success']:
            return {'success': False, 'error': f"Metadata extraction failed: {download_result['error']}"}

        # Create results structure
        results = ProcessingLogger.create_result_metadata(url, 'metadata-only')
        results['download_result'] = download_result

        # No audio or OCR processing for metadata-only
        results['transcription'] = {'success': False, 'reason': 'Metadata-only processing'}
        results['ocr'] = {'success': False, 'reason': 'Metadata-only processing'}

        # For combined_text, use video description from metadata if available
        if os.path.exists(metadata_file):
            df = pd.read_csv(metadata_file)
            if not df.empty and 'video_description' in df.columns:
                results['combined_text'] = df['video_description'].iloc[0] or ""
            else:
                results['combined_text'] = ""
        else:
            results['combined_text'] = ""

        return results

    def _process_audio_only_data(self, url, output_dir, metadata_file):
        """Process audio transcription only without saving results file"""
        # Download video (needed for audio extraction)
        ProcessingLogger.log_download_start(url)
        download_result = self.downloader.download_content(url, output_dir, metadata_file)

        if not download_result['success']:
            return {'success': False, 'error': f"Download failed: {download_result['error']}"}

        # Create results structure
        results = ProcessingLogger.create_result_metadata(url, 'audio-only')
        results['video_path'] = download_result.get('video_path')
        results['download_result'] = download_result

        # Audio transcription (same as _process_video)
        ProcessingLogger.log_transcription_start()
        video_path = download_result.get('video_path')
        try:
            trans_result = self.transcriptor.transcribe_audio(video_path)
            results['transcription'] = {
                'text': trans_result.get('text', ''),
                'success': bool(trans_result.get('text', ''))
            }
        except Exception as e:
            results['transcription'] = {'success': False, 'error': str(e)}

        # Skip OCR for audio-only
        results['ocr'] = {'success': False, 'reason': 'Audio-only processing'}

        # Combined text is just audio
        if results['transcription']['success']:
            results['combined_text'] = f"Audio: {results['transcription']['text']}"
        else:
            results['combined_text'] = ""

        return results

