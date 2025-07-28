import os
import subprocess
import json
import tempfile
from pathlib import Path

from utils.logging_config import setup_logging, log_success

logger = setup_logging(logger_name=__name__)

class AudioTranscriptor:
    """
    Audio transcription using CLI Whisper from optimized Docker image
    """
    
    def __init__(self, model_size="base"):
        """
        Initialize Whisper CLI transcriptor
        
        Args:
            model_size: Model size to use
                - "tiny": Fastest, least accurate (~39 MB)
                - "base": Good balance (~74 MB) 
                - "small": Better accuracy (~244 MB)
                - "medium": Higher accuracy (~769 MB)
                - "large": Best accuracy (~1550 MB)
                - "turbo": Optimized for speed (~809 MB)
        """
        self.model_size = model_size
        logger.info(f"Using Whisper CLI with model: {model_size}")
        
        # Check if whisper CLI is available
        try:
            result = subprocess.run(['whisper', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                log_success(logger, "Whisper CLI available")
            else:
                logger.warning("Whisper CLI help failed, but continuing...")
        except Exception as e:
            logger.warning(f"Could not verify Whisper CLI: {e}")
            # Continue anyway since it might still work

    def transcribe_audio(self, audio_path, language=None, temperature=0):
        """
        Transcribe audio file using Whisper CLI
        
        Args:
            audio_path: Path to audio file (supports many formats: mp3, wav, mp4, etc.)
            language: Language code (e.g., 'en', 'es', 'fr'). If None, auto-detect
            temperature: Sampling temperature (0-1). Lower = more focused/deterministic
            
        Returns:
            Dictionary containing transcription and metadata
        """
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        
        try:
            # Get file info
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            logger.info(f"File: {Path(audio_path).name} ({file_size:.1f}MB)")
            
            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info("Transcribing audio with Whisper CLI...")
                
                # Build whisper command
                cmd = [
                    'whisper', 
                    audio_path,
                    '--model', self.model_size,
                    '--output_dir', temp_dir,
                    '--output_format', 'json',
                    '--temperature', str(temperature)
                ]
                
                # Add language if specified
                if language:
                    cmd.extend(['--language', language])
                
                # Run whisper command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    raise Exception(f"Whisper CLI failed: {result.stderr}")
                
                # Find the JSON output file
                audio_name = Path(audio_path).stem
                json_file = Path(temp_dir) / f"{audio_name}.json"
                
                if not json_file.exists():
                    raise Exception(f"JSON output file not found: {json_file}")
                
                # Load JSON results
                with open(json_file, 'r', encoding='utf-8') as f:
                    whisper_result = json.load(f)
                
                log_success(logger, "Transcription completed")
                
                # Return comprehensive results
                return {
                    'text': whisper_result.get('text', '').strip(),
                    'language': whisper_result.get('language', 'unknown'),
                    'segments': whisper_result.get('segments', []),
                    'file_path': audio_path,
                    'model_used': self.model_size
                }
                
        except subprocess.TimeoutExpired:
            logger.error("Transcription timed out (5 minutes)")
            return {
                'text': '',
                'error': 'Transcription timed out',
                'file_path': audio_path
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                'text': '',
                'error': str(e),
                'file_path': audio_path
            }

    def transcribe_with_timestamps(self, audio_path, language=None):
        """
        Transcribe with detailed timestamps for each segment
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
            
        Returns:
            List of segments with text and timestamps
        """
        result = self.transcribe_audio(audio_path, language)
        
        if 'segments' not in result:
            return []
        
        segments = []
        for segment in result['segments']:
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': segment.get('avg_logprob', 0)
            })
        
        return segments

    def get_model_info(self):
        """Get information about the CLI model"""
        return {
            'model_size': self.model_size,
            'transcription_method': 'CLI',
            'base_image': 'manzolo/openai-whisper-docker'
        }

    @staticmethod
    def list_available_models():
        """List all available Whisper models"""
        return ["tiny", "base", "small", "medium", "large", "turbo"]

    @staticmethod
    def get_supported_languages():
        """Get list of supported languages"""
        # Common languages supported by Whisper
        return [
            'english', 'chinese', 'german', 'spanish', 'russian', 'korean', 
            'french', 'japanese', 'portuguese', 'turkish', 'polish', 'catalan',
            'dutch', 'arabic', 'swedish', 'italian', 'indonesian', 'hindi',
            'finnish', 'vietnamese', 'hebrew', 'ukrainian', 'greek', 'malay',
            'czech', 'romanian', 'danish', 'hungarian', 'tamil', 'norwegian'
        ]
