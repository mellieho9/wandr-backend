import os
import signal
from openai import OpenAI
from pathlib import Path

from utils.logging_config import setup_logging, log_success

logger = setup_logging(logger_name=__name__)

class AudioTranscriptor:
    """
    Audio transcription using OpenAI's transcription model
    """
    
    def __init__(self):  # 5 minutes default
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
            
            with open(audio_path, 'rb') as f:
                audio_content = f.read()
            
            file_tuple = (Path(audio_path).name, audio_content, "audio/mp4")
            
            result = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=file_tuple,
                response_format="text",
            )

            log_success(logger, "Transcription completed")
            
            return {
                'text': result,
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                'text': '',
                'error': str(e),
                'file_path': audio_path
            }