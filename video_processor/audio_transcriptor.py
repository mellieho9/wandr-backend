import os
import whisper
import torch
from pathlib import Path

class AudioTranscriptor:
    """
    Audio transcription using Open Source Whisper
    """
    
    def __init__(self, model_size="base"):
        """
        Initialize Whisper model
        
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
        print(f"🔄 Loading Whisper model: {model_size}")
        
        # Check if CUDA is available for GPU acceleration
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️  Using device: {device}")
        
        try:
            self.model = whisper.load_model(model_size, device=device)
            print(f"✅ Whisper model '{model_size}' loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

    def transcribe_audio(self, audio_path, language=None, temperature=0):
        """
        Transcribe audio file using Whisper
        
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
            print(f"📁 File: {Path(audio_path).name} ({file_size:.1f}MB)")
            
            # Transcribe using Whisper
            print(f"🎵 Transcribing audio...")
            
            result = self.model.transcribe(
                audio_path,
                language=language,
                temperature=temperature,
                verbose=False  # Set to True for progress updates
            )
            
            print("✅ Transcription completed")
            
            # Return comprehensive results
            return {
                'text': result['text'].strip(),
                'language': result['language'],
                'segments': result.get('segments', []),
                'file_path': audio_path,
                'model_used': self.model_size
            }
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
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
        """Get information about the loaded model"""
        return {
            'model_size': self.model_size,
            'device': next(self.model.parameters()).device,
            'model_dims': self.model.dims.__dict__ if hasattr(self.model, 'dims') else None
        }

    @staticmethod
    def list_available_models():
        """List all available Whisper models"""
        return ["tiny", "base", "small", "medium", "large", "turbo"]

    @staticmethod
    def get_supported_languages():
        """Get list of supported languages"""
        return list(whisper.tokenizer.LANGUAGES.values())

# Utility functions
def batch_transcribe(file_paths, model_size="tiny", language="en"):
    """
    Transcribe multiple files in batch
    
    Args:
        file_paths: List of audio file paths
        model_size: Whisper model size to use
        language: Language code (default: English)
        
    Returns:
        List of transcription results
    """
    transcriptor = AudioTranscriptor(model_size=model_size)
    results = []
    
    for file_path in file_paths:
        print(f"\n📁 Processing: {file_path}")
        result = transcriptor.transcribe_audio(file_path, language=language)
        results.append(result)
    
    return results

# Example usage and testing
if __name__ == "__main__":
    # Initialize transcriptor (using tiny model for speed)
    transcriptor = AudioTranscriptor(model_size="tiny")
    
    # Print model info
    print(f"\n🔍 Model Info: {transcriptor.get_model_info()}")
    
    # Example video file
    video_path = "t_ZP8rwYBo3_.mp4"
    
    if os.path.exists(video_path):
        print(f"\n🎬 Processing video file: {video_path}")
        
        # Basic transcription (English only for speed)
        result = transcriptor.transcribe_audio(video_path, language="en")
        
        if result.get('text'):
            print(f"\n📝 Transcript:\n{result['text']}")
            print(f"\n🌍 Language: {result['language']}")
        else:
            print("❌ No transcript generated")
            if 'error' in result:
                print(f"Error: {result['error']}")
    else:
        print(f"❌ Video file not found: {video_path}")
        print("🔍 Please ensure the file exists in the current directory")
