# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Complete TikTok Video Processing and Location Extraction Pipeline:

- Process TikTok videos to extract text and audio content
- Use AI (Gemini API) to extract location information from video content
- Enhance location data with Google Places API for address, hours, and website
- Output structured JSON data compatible with Notion schema
- Automated pipeline connecting video processing → location extraction → Notion-ready data

## Current Implementation Status

### Completed Components

#### Video Processing Pipeline (`/video_processor/`)

- **TikTok Downloader** (`video_downloader.py`): Downloads TikTok videos using pyktok with smart folder organization
- **Audio Transcription** (`audio_transcriptor.py`): Transcribes audio using OpenAI Whisper (local model)
- **Frame OCR** (`video_frame_ocr.py`): Extracts text from video frames using Google Vision API
- **Main Pipeline** (`main.py`): TikTokProcessor class integrating all video processing components

#### Location Processing Pipeline (`/location_processor/`)

- **Location Analyzer** (`location_analyzer.py`): Uses Gemini API to extract location info from video content
- **Google Places Service** (`google_places.py`): Enhances location data with Google Places API and generates Maps links
- **Main Processor** (`main.py`): LocationProcessor class with Google Maps validation and filtering

#### Notion Integration (`/notion_handler/`)

- **Notion Client** (`notion_client.py`): Direct Notion API integration with custom database schema support
- **Database Entry Creation**: Automated creation of location entries in Notion databases
- **Hyperlinked Addresses**: Address fields automatically link to Google Maps for one-click navigation
- **Batch Processing**: Automated daily processing of URLs from source databases
- **Today's URL Processing**: Query and process all URLs added to source database today

#### Root Integration (`/main.py`)

- **Complete Pipeline**: Connects video processing → location extraction → Notion database creation
- **Flexible Modes**: Video-only, location-only, or full pipeline processing
- **Notion Integration**: Optional automatic database entry creation with `--create-notion-entry`
- **Clean Output**: Organized results with progress indicators and summaries

#### Key Features

- ✅ Smart download detection (skips if video/metadata already exists)
- ✅ Multiple Whisper model sizes (tiny/base/small for memory optimization)
- ✅ Gemini AI integration for intelligent location extraction
- ✅ Google Places API integration for address lookup and business hours
- ✅ **Google Maps link generation** - Automatic Google Maps links for all locations
- ✅ **Location validation** - Only places with valid Google Maps locations are included
- ✅ Structured JSON output matching Notion schema
- ✅ **Notion database integration** - Direct creation of database entries with custom schema
- ✅ **Hyperlinked addresses** - Clickable address fields that open Google Maps
- ✅ **Automated daily processing** - Batch process all URLs added to source database today
- ✅ **Modular architecture** - Clean separation with models/, utils/, and service packages
- ✅ **Advanced URL parsing** - TikTok URL parsing with multiple format support
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
- `notion-client` - Official Notion SDK for Python
- `python-dotenv` - Environment variable management
- `pytest` - Testing framework for unit and integration tests

### Environment Variables Required

- `VISION_API_KEY` - Google Vision API key for OCR
- `GEMINI_API_KEY` - Google Gemini API key for location extraction
- `GOOGLE_MAPS_API_KEY` - Google Maps API key for Places data and Maps links
- `NOTION_API_KEY` - Notion API key for database operations
- `NOTION_PLACES_DB_ID` - (Optional) Default Notion database ID for places
- `NOTION_SOURCE_DB_ID` - (Optional) Source database ID for automated daily processing

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

# Complete pipeline with automatic Notion database entry creation
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --category restaurant chinese --create-notion-entry --database-id YOUR_DB_ID

# Using environment variable for database ID
export NOTION_PLACES_DB_ID=your_database_id
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --create-notion-entry
```

### Automated Daily Processing

```bash
# Process all URLs added to source database today and create place entries
python main.py --process-todays-urls --source-database-id SOURCE_DB_ID --places-database-id PLACES_DB_ID

# Using environment variables for database IDs
export NOTION_SOURCE_DB_ID=your_source_database_id
export NOTION_PLACES_DB_ID=your_places_database_id
python main.py --process-todays-urls

# This feature automatically:
# - Queries source database for URLs added today
# - Processes each TikTok video (download, transcribe, OCR)
# - Extracts location information using Gemini AI
# - Enhances with Google Places data
# - Creates entries in places database with hyperlinked addresses
```

### Notion Database Integration

```bash
# Create database entries from existing location file
python test.py  # Uses environment variables for API keys and database ID

# Location extraction + Notion entry creation
python main.py --url "https://www.tiktok.com/t/ZP8rwYBo3/" --location-only --create-notion-entry
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

### Single URL Processing

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TikTok URL    │───▶│  utils/          │───▶│  Video          │───▶│  Location       │
│   Input         │    │  url_parser.py   │    │  Processor      │    │  Processor      │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                ▼                        │                        │
                       ┌─────────────────┐              │                        │
                       │ URL Components  │              │                        │
                       │ & File Prefixes │              │                        │
                       └─────────────────┘              │                        │
                                                        │                        │
                                ┌───────────────────────┼─────────────┐         │
                                │                       ▼             │         │
                                │  ┌─────────────┐ ┌──────────┐      │         │
                                │  │  pyktok     │ │ Whisper  │      │         │
                                │  │ Downloader  │ │   Audio  │      │         │
                                │  │             │ │Transcript│      │         │
                                │  └─────────────┘ └──────────┘      │         │
                                │  ┌─────────────────────────┐       │         │
                                │  │   Google Vision OCR     │       │         │
                                │  │   (Frame Text Extract)  │       │         │
                                │  └─────────────────────────┘       │         │
                                └─────────────────────────────────────┘         │
                                                        │                        │
                                                        ▼                        │
                                               ┌─────────────────┐              │
                                               │   results/      │              │
                                               │ video_results   │              │
                                               │    .json        │              │
                                               └─────────────────┘              │
                                                                                │
                                        ┌───────────────────────────────────────┼──────────────┐
                                        │                                       ▼              │
                                        │  ┌─────────────┐ ┌──────────────────────────────────┐│
                                        │  │   Gemini    │ │      Google Places              ││
                                        │  │     AI      │ │   (Address, Hours, Website)     ││
                                        │  │ (Location   │ │   + Google Maps Link Gen        ││
                                        │  │ Analysis)   │ │                                 ││
                                        │  └─────────────┘ └──────────────────────────────────┘│
                                        └─────────────────────────────────────────────────────┘
                                                                                │
                                                                                ▼
                                                                       ┌─────────────────┐
                                                                       │ models/         │
                                                                       │ location_models │
                                                                       │ (PlaceInfo)     │
                                                                       └─────────────────┘
                                                                                │
                                                                                ▼
                                                                       ┌─────────────────┐
                                                                       │   results/      │
                                                                       │ location_info   │
                                                                       │ .json (Notion)  │
                                                                       └─────────────────┘
                                                                                │
                                                                                ▼
                                                                       ┌─────────────────┐
                                                                       │ notion_handler/ │
                                                                       │ notion_client   │
                                                                       │ (Hyperlinked)   │
                                                                       └─────────────────┘
```

### Automated Daily Processing

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Notion Source   │───▶│  notion_handler/ │───▶│   For Each URL  │
│   Database      │    │  notion_client   │    │  Run Pipeline   │
│ (Today's URLs)  │    │ get_todays_urls  │    │     Above       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Filtered URLs   │    │ Notion Places   │
                       │  (Created Today)│    │   Database      │
                       └─────────────────┘    │ (Auto-created   │
                                              │  Entries with   │
                                              │ Hyperlinks)     │
                                              └─────────────────┘
```

## File Structure

```
wandr-backend/
├── main.py                    # 🎯 Root pipeline orchestrator with batch processing
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
├── notion_handler/            # 🔗 Notion API integration package
│   ├── __init__.py
│   ├── notion_client.py      # Direct Notion API client with batch processing
├── models/                    # 📋 Data models and schemas
│   ├── __init__.py
│   ├── location_models.py    # PlaceInfo and LocationInfo data classes
│   ├── url_models.py         # URL parsing data structures
│   └── my_link.py            # Link processing utilities
├── utils/                     # 🛠️ Utility modules
│   ├── __init__.py
│   ├── url_parser.py         # TikTok URL parsing and filename generation
│   ├── logger.py             # Logging configuration
│   └── image_utils.py        # Image processing utilities
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
├── test_urls.md              # Test URLs for development
├── wandr-backend.log         # Application log file
├── .env                      # Environment variables (ignored)
├── .gitignore               # Git ignore rules
└── CLAUDE.md                # This file
```

## JSON Output Schema

### Location JSON Output

```json
{
  "url": "https://www.tiktok.com/t/ZP8rwYBo3/",
  "content_type": "single_place",
  "places": [
    {
      "name": "Grandma's Home",
      "address": "56 W 22nd St, New York, NY 10010, USA",
      "neighborhood": "Chelsea",
      "categories": ["restaurant", "chinese"],
      "recommendations": "beef noodle soup, fish cake, lotus root with sticky rice",
      "hours": "Monday: 11:30 AM – 3:00 PM, 5:00 – 9:30 PM\n...",
      "website": "https://www.grandmashome.us/",
      "visited": false,
      "is_popup": false,
      "maps_link": "https://maps.google.com/maps/place/?q=place_id:ChIJ..."
    }
  ]
}
```

### Notion Database Schema

The system creates entries with these fields:

- **Name of Place** (Title) - Restaurant/business name
- **Source URL** (URL) - Original TikTok video URL
- **Address** (Rich Text) - Automatically hyperlinked to Google Maps for one-click navigation
- **Categories** (Multi-select) - Place categories/tags
- **Recommendations** (Rich Text) - Menu items or recommendations
- **My Personal Review** (Rich Text) - Personal notes (empty by default)
- **Hours** (Rich Text) - Operating hours
- **Website** (URL) - Business website
- **Is Popup** (Checkbox) - Whether it's a temporary/popup location
- **Visited** (Checkbox) - Whether you've visited (false by default)

**Note**: Address fields are automatically converted to clickable links that open the location in Google Maps, eliminating the need to manually copy addresses for navigation.
