import os
from openai import OpenAI
from pathlib import Path

from utils.logging_config import setup_logging, log_success

logger = setup_logging(logger_name=__name__)

class AudioTranscriptor:
    """
    Audio transcription using OpenAI's transcription model
    """
    
    def __init__(self):
        self.client = OpenAI()

    def transcribe_audio(self, audio_path):
        """
        Transcribe audio file
        
        Args:
            audio_path: Path to audio file (supports many formats: mp3, wav, mp4, etc.)
            
        Returns:
            transcription text or error message
        """
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        
        try:
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            logger.info(f"File: {Path(audio_path).name} ({file_size:.1f}MB)")

            logger.info("Transcribing audio...")
            
            result = self.client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file = audio_path,
                response_format="text",
            )
            
            log_success(logger, "Transcription completed")
            
            return {
                'text': result.text,
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                'text': '',
                'error': str(e),
                'file_path': audio_path
            }