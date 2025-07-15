# Wandr Backend

Backend for a Notion-based location curation system that processes TikTok videos to extract location information.

## 🎯 Overview

This system processes TikTok videos to extract text and audio content, which can then be used to identify locations and generate recommendations for a Notion-based travel curation system.

## ✨ Features

- **TikTok Video Download**: Downloads videos using pyktok
- **Audio Transcription**: Extracts and transcribes audio using OpenAI Whisper
- **Visual Text Extraction**: OCR text extraction from video frames using Google Vision API
- **Smart Processing**: Skips re-downloading existing files
- **Flexible Models**: Multiple Whisper model sizes for different performance needs
- **JSON Output**: Structured results for easy integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Vision API key (for OCR)
- OpenAI API key (optional, for Whisper API instead of local model)

### Installation

```bash
# Clone and navigate to project
git clone <repository-url>
cd wandr-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file with your API keys:
# VISION_API_KEY=your_google_vision_api_key
# TTS_API_KEY=your_openai_api_key (optional)
```

### Usage

#### Process a TikTok URL
```bash
python video_processor/main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --output results.json
```

#### Process an existing video file
```bash
python video_processor/main.py --video "video.mp4" --output results.json
```

#### Additional Options
```bash
# Skip OCR (audio transcription only)
python video_processor/main.py --video "video.mp4" --no-ocr

# Use different Whisper model (tiny/base/small)
python video_processor/main.py --video "video.mp4" --model base

# Custom category for metadata
python video_processor/main.py --url "https://www.tiktok.com/..." --category restaurants
```

## 📁 Project Structure

```
wandr-backend/
├── video_processor/           # Video processing pipeline
│   ├── main.py               # Main integration script
│   ├── video_downloader.py   # TikTok video downloading
│   ├── audio_transcriptor.py # Audio transcription (Whisper)
│   ├── video_frame_ocr.py    # Frame OCR (Google Vision)
│   └── downloads/            # Downloaded files (gitignored)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (gitignored)
├── .gitignore               # Git ignore rules
├── CLAUDE.md                # Developer guidance
└── README.md                # This file
```

## 🔧 Components

### Video Downloader (`video_downloader.py`)
- Downloads TikTok videos using pyktok
- Handles metadata extraction
- Supports batch processing

### Audio Transcriptor (`audio_transcriptor.py`)
- Uses OpenAI Whisper for local audio transcription
- Multiple model sizes (tiny, base, small, medium, large)
- Optimized for English content
- GPU acceleration when available

### Video Frame OCR (`video_frame_ocr.py`)
- Extracts text from video frames using Google Vision API
- Configurable frame intervals
- Handles API rate limiting and errors

### Main Pipeline (`main.py`)
- Integrates all components
- Smart file detection (skips existing downloads)
- Command-line interface
- JSON output format

## 📊 Output Format

The pipeline generates JSON output with the following structure:

```json
{
  "video_path": "t_ZP8rwYBo3_.mp4",
  "original_url": "https://www.tiktok.com/t/ZP8rwYBo3/",
  "timestamp": "2024-01-15T10:30:00",
  "success": true,
  "transcription": {
    "text": "my favorite restaurant in nyc...",
    "language": "en",
    "success": true
  },
  "ocr": {
    "frames_with_text": 3,
    "text_data": [
      {"timestamp": 0, "text": "grandma's beef noodle soup"},
      {"timestamp": 3, "text": "homemade fish cake"}
    ],
    "success": true
  },
  "combined_text": "Audio: my favorite restaurant...\nFrame 0s: grandma's beef noodle soup..."
}
```

## 🔑 Environment Variables

Create a `.env` file in the project root:

```bash
# Required for OCR functionality
VISION_API_KEY=your_google_vision_api_key_here

# Optional: for OpenAI Whisper API (instead of local model)
TTS_API_KEY=your_openai_api_key_here
```

## 🛠 Development

### Running Tests
```bash
# Test individual components
python video_processor/audio_transcriptor.py
python video_processor/video_frame_ocr.py
python video_processor/video_downloader.py
```

### Adding New Features
See `CLAUDE.md` for development guidance and architecture notes.

## 🗺 Roadmap

### ✅ Completed
- [x] TikTok video downloading
- [x] Audio transcription with Whisper
- [x] Video frame OCR with Google Vision
- [x] Integrated pipeline with CLI
- [x] Smart file detection and caching

### 🚧 Next Steps
- [ ] Notion API integration for webhook handling
- [ ] Claude API integration for location extraction
- [ ] Google Places API for address lookup
- [ ] RESTful API backend (FastAPI)
- [ ] Database integration for results storage
- [ ] Web interface for manual processing

## 📝 License

This project is for internal use in the location curation system.

## 🤝 Contributing

See `CLAUDE.md` for development guidelines and architecture details.
