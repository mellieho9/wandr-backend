# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Complete TikTok Video Processing and Location Extraction Pipeline:
- Process TikTok videos to extract text and audio content
- Use AI (Gemini API) to extract location information from video content
- Enhance location data with Google Places API for address, hours, and website
- Output structured JSON data compatible with Notion schema
- Automated pipeline connecting video processing → location extraction → Notion-ready data

## Current Implementation Status ✅ COMPLETE

### Completed Components

#### Video Processing Pipeline (`/video_processor/`)
- **TikTok Downloader** (`video_downloader.py`): Downloads TikTok videos using pyktok with smart folder organization
- **Audio Transcription** (`audio_transcriptor.py`): Transcribes audio using OpenAI Whisper (local model)
- **Frame OCR** (`video_frame_ocr.py`): Extracts text from video frames using Google Vision API
- **Main Pipeline** (`main.py`): TikTokProcessor class integrating all video processing components

#### Location Processing Pipeline (`/location_processor/`)
- **Location Analyzer** (`location_analyzer.py`): Uses Gemini API to extract location info from video content
- **Google Places Service** (`google_places.py`): Enhances location data with Google Places API
- **Main Processor** (`main.py`): LocationProcessor class combining AI analysis with Places API

#### Notion Integration (`/notion_service/`)
- **Notion Client** (`notion_client.py`): Direct Notion API integration for updating pages
- **Webhook Handler** (`webhook_handler.py`): Processes incoming webhooks from Notion
- **Main Service** (`main.py`): NotionService class for complete Notion integration

#### Root Integration (`/main.py`)
- **Complete Pipeline**: Connects video processing → location extraction in one command
- **Flexible Modes**: Video-only, location-only, or full pipeline processing
- **Clean Output**: Organized results with progress indicators and summaries

#### Key Features
- ✅ Smart download detection (skips if video/metadata already exists)
- ✅ Multiple Whisper model sizes (tiny/base/small for memory optimization)
- ✅ Gemini AI integration for intelligent location extraction
- ✅ Google Places API integration for address lookup and business hours
- ✅ Structured JSON output matching Notion schema
- ✅ Notion API integration for automatic page updates
- ✅ Webhook handling for automated processing from Notion
- ✅ Package-based architecture with clean separation of concerns
- ✅ Comprehensive error handling and progress reporting
- ✅ Results saved to organized `results/` folder with video ID naming
- ✅ **Unified logging system** - Replaced custom prints with proper Python logging
- ✅ **Comprehensive testing framework** - Unit and integration tests with pytest
- ✅ **TikTok carousel support** - Enhanced downloader for photo carousels
- ✅ **Edge case handling** - Improved robustness for various content types

### Dependencies
See `requirements.txt` for full list. Key dependencies:
- `pyktok` - TikTok video downloading
- `openai-whisper` - Audio transcription
- `opencv-python` - Video frame processing
- `google-cloud-vision` - OCR text extraction
- `google-generativeai` - Gemini AI for location extraction
- `googlemaps` - Google Places API integration
- `pandas` - Data processing for metadata
- `requests` - HTTP requests for Notion API
- `python-dotenv` - Environment variable management
- `pytest` - Testing framework for unit and integration tests

### Environment Variables Required
- `VISION_API_KEY` - Google Vision API key for OCR
- `GEMINI_API_KEY` - Google Gemini API key for location extraction
- `GOOGLE_MAPS_API_KEY` - Google Maps API key for Places data
- `NOTION_API_KEY` - Notion API key for page updates

## Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Create .env file with your API keys
```

## Testing

The project includes comprehensive testing with pytest:

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only

# Run tests with coverage
pytest --cov=. tests/

# Run specific test file
pytest tests/unit/test_location_models.py
```

## Usage

### Complete Pipeline (Recommended)
```bash
# Process TikTok video and extract location info in one command
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --category restaurant chinese

# Just the URL (no categories specified)
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/"
```

### Notion Integration
```bash
# Process TikTok and update Notion page directly
python -m notion_service.main process-url --page-id YOUR_PAGE_ID --url "https://www.tiktok.com/t/ZP8rwYBo3/" --category restaurant chinese

# Update Notion page from existing location file
python -m notion_service.main update-page --page-id YOUR_PAGE_ID --location-file results/ZP8rwYBo3_location.json

# Test Notion API connection
python -m notion_service.main test --page-id YOUR_PAGE_ID
```

### Individual Components
```bash
# Video processing only
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --video-only

# Location extraction only (from existing results)
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --location-only

# Package-specific commands
python -m video_processor.main --url "https://www.tiktok.com/t/ZP8rwYBo3/"
python -m location_processor.main --video-id ZP8rwYBo3 --category restaurant chinese
```

### Output Files
All results are saved to the `results/` directory:
- `{video_id}_results.json` - Video processing results (transcription + OCR)
- `{video_id}_metadata.csv` - TikTok metadata
- `{video_id}_location.json` - Structured location data for Notion

## Notion Integration Setup

### 1. Create Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Create a new integration and get your API key
3. Add the integration to your database/page
4. Set `NOTION_API_KEY` in your `.env` file

### 2. Get Page ID
- Open your Notion page in browser
- Copy the page ID from URL: `https://notion.so/[workspace]/[PAGE_ID]?...`
- Use this PAGE_ID in the commands

### 3. Webhook Setup (Optional)
For automated processing, you can set up webhooks:
- Use the `webhook_handler.py` to process incoming requests
- Deploy as a web service (FastAPI, Flask, etc.)
- Configure Notion to send webhooks to your endpoint

## Next Steps (Optional Future Enhancements)

### Potential Backend Integration
- [ ] RESTful API endpoints with FastAPI
- [ ] Web interface for manual processing
- [ ] Database storage for processed results
- [ ] Batch processing for multiple videos
- [ ] Advanced webhook validation and security

### Framework Options for API
- FastAPI for Python web API
- Node.js/Express for webhook handling

## Architecture Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   TikTok URL    │───▶│  Video           │───▶│  Location       │
│   Input         │    │  Processor       │    │  Processor      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                ┌───────────────┼─────────────┐         │
                │               ▼             │         │
                │  ┌─────────────┐ ┌──────────┐│         │
                │  │  pyktok     │ │ Whisper  ││         │
                │  │ Downloader  │ │   Audio  ││         │
                │  │             │ │Transcript││         │
                │  └─────────────┘ └──────────┘│         │
                │  ┌─────────────────────────┐ │         │
                │  │   Google Vision OCR     │ │         │
                │  │   (Frame Text Extract)  │ │         │
                │  └─────────────────────────┘ │         │
                └─────────────────────────────┘         │
                                │                        │
                                ▼                        │
                       ┌─────────────────┐              │
                       │   results/      │              │
                       │ video_results   │              │
                       │    .json        │              │
                       └─────────────────┘              │
                                                        │
                        ┌───────────────────────────────┼──────────────┐
                        │                               ▼              │
                        │  ┌─────────────┐ ┌──────────────────────────┐│
                        │  │   Gemini    │ │      Google Places       ││
                        │  │     AI      │ │   (Address, Hours, Web)  ││
                        │  │ (Location   │ │                          ││
                        │  │ Analysis)   │ │                          ││
                        │  └─────────────┘ └──────────────────────────┘│
                        └─────────────────────────────────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   results/      │
                                               │ location_info   │
                                               │ .json (Notion)  │
                                               └─────────────────┘
```

## File Structure

```
wandr-backend/
├── main.py                    # 🎯 Root pipeline orchestrator
├── video_processor/           # 📹 Video processing package
│   ├── __init__.py           
│   ├── main.py               # TikTokProcessor class
│   ├── video_downloader.py   # TikTok video downloading (with carousel support)
│   ├── audio_transcriptor.py # Audio transcription
│   └── video_frame_ocr.py    # Frame OCR processing (enhanced)
├── location_processor/        # 📍 Location extraction package
│   ├── __init__.py           
│   ├── main.py               # LocationProcessor class (improved logging)
│   ├── location_analyzer.py  # Gemini AI location analysis
│   └── google_places.py      # Google Places API integration
├── notion_service/            # 🔗 Notion API integration package
│   ├── __init__.py           
│   ├── main.py               # NotionService class
│   ├── notion_client.py      # Direct Notion API client
│   └── webhook_handler.py    # Webhook processing logic
├── tests/                     # 🧪 Testing framework
│   ├── __init__.py           
│   ├── conftest.py           # Pytest configuration
│   ├── unit/                 # Unit tests
│   │   ├── __init__.py
│   │   ├── test_location_models.py
│   │   └── test_url_parser.py
│   └── integration/          # Integration tests
│       ├── __init__.py
│       ├── test_location_processor.py
│       ├── test_main_pipeline.py
│       └── test_video_processor.py
├── results/                   # 📊 Generated output files
│   ├── {video_id}_results.json    # Video processing results
│   ├── {video_id}_metadata.csv    # TikTok metadata
│   └── {video_id}_location.json   # Notion-ready location data
├── Makefile                   # Build and test commands
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
├── notion_schema.md          # Notion database schema
├── .env                      # Environment variables (ignored)
├── .gitignore               # Git ignore rules
└── CLAUDE.md                # This file
```

## JSON Output Schema

### Location JSON (Notion-ready)
```json
{
  "URL": "https://www.tiktok.com/t/ZP8rwYBo3/",
  "place_category": ["restaurant", "chinese"],
  "review": "",
  "name of place": "Grandma's Home", 
  "location": "56 W 22nd St, New York, NY 10010, USA",
  "recommendations": "beef noodle soup, fish cake, lotus root with sticky rice",
  "time": "Monday: 11:30 AM – 3:00 PM, 5:00 – 9:30 PM\n...",
  "website": "https://www.grandmashome.us/",
  "visited": false
}
```