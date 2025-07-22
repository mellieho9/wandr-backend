"""
Application constants and configuration values
"""

# Processing defaults
DEFAULT_WHISPER_MODEL = "tiny"
DEFAULT_FRAME_INTERVAL = 3.0
DEFAULT_MAX_FRAMES = 8
DEFAULT_OUTPUT_DIR = "results"

# OCR Configuration
DEFAULT_OCR_MAX_RETRIES = 3
DEFAULT_OCR_RATE_LIMIT_DELAY = 1.0

# Text processing limits
MAX_RECOMMENDATION_PREVIEW_LENGTH = 100
MAX_TEXT_PREVIEW_LENGTH = 200

# File extensions
SUPPORTED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv']
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

# API timeouts (seconds)
DEFAULT_API_TIMEOUT = 30
VISION_API_TIMEOUT = 30
NOTION_API_TIMEOUT = 30

# Whisper model sizes (ordered by quality/speed tradeoff)
WHISPER_MODELS = ['tiny', 'base', 'small', 'medium', 'large']