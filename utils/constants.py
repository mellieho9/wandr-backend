"""
Application constants and configuration values
"""

# Processing defaults
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

# Webhook processing constants
WEBHOOK_FRAME_INTERVAL = 3.0
WEBHOOK_MAX_FRAMES = 8
WEBHOOK_OUTPUT_DIR = "results"

# Processing tag constants
TAG_METADATA_ONLY = "metadata-only"
TAG_AUDIO_ONLY = "audio-only"

# ANSI color constants
class Colors:
    """ANSI color code constants for logging"""
    CYAN = '\033[36m'      # Debug
    WHITE = '\033[0m'      # Info/Default
    YELLOW = '\033[33m'    # Warning
    RED = '\033[31m'       # Error
    MAGENTA = '\033[35m'   # Critical
    GREEN = '\033[32m'     # Success
    RESET = '\033[0m'      # Reset to default