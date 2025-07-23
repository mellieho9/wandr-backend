# Wandr

## Project Overview
Get the content you see on Tiktok to your notes in no time

## Key Features

- ✅ Smart download detection (skips if video/metadata already exists)
- ✅ Gemini AI integration for intelligent location extraction
- ✅ Google Places API integration for address lookup and business hours
- ✅ **Location validation** - Only places with valid Google Maps locations are included
- ✅ **Notion database integration** - Direct creation of database entries with custom schema
- ✅ **Hyperlinked addresses** - Clickable address fields that open Google Maps
- ✅ **Automated daily processing** - Batch process all URLs added to source database today
- ✅ **TikTok carousel support** - Enhanced downloader for photo carousels

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
python main.py --process-pending-urls

# This feature automatically:
# - Queries source database for unprocessed URLs
# - Processes each TikTok video (download, transcribe, OCR)
# - Extracts location information using Gemini AI
# - Enhances with Google Places data
# - Creates entries in places database with hyperlinked addresses
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

## File Structure

```
wandr-backend/
├── main.py                           # Root pipeline CLI
├── pipeline/                         # Pipeline orchestration
│   ├── orchestrator.py              # Main pipeline coordinator
│   └── commands.py                  # Command pattern implementation
├── services/                         # Core service packages
│   ├── video_processor/             # TikTok video processing
│   │   ├── video_downloader.py     # Download with carousel support
│   │   ├── audio_transcriptor.py   # Whisper transcription
│   │   └── video_frame_ocr.py      # Google Vision OCR
│   ├── location_processor/          # Location extraction
│   │   ├── location_analyzer.py    # Gemini AI analysis
│   │   └── google_places.py        # Google Places enhancement
│   └── notion_service/              # Notion integration
│       ├── notion_client.py         # API client
│       ├── location_handler.py      # Location-specific operations
│       └── url_processor.py         # URL batch processing
├── models/                           # Data models
│   ├── pipeline_models.py          # Pipeline configurations
│   └── location_models.py          # Location data structures
├── utils/                            # Utilities
│   ├── logging_config.py           # Centralized colored logging
│   ├── config.py                   # Configuration management
│   ├── constants.py                # Application constants
│   ├── url_parser.py               # TikTok URL parsing
│   ├── location_transformer.py     # Data transformation
│   └── exceptions/                 # Custom exceptions
├── tests/                           # Test suite
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests
├── results/                         # Output files
└── requirements.txt                 # Dependencies
```