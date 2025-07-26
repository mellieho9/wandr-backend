#!/usr/bin/env python3
"""
Location Analyzer

Uses Gemini API to extract location information from video content.
"""

import json
from typing import Dict
import google.generativeai as genai

from utils.config import config
from utils.logging_config import setup_logging, log_success

logger = setup_logging(logger_name=__name__)

class LocationAnalyzer:
    """Enhanced location analyzer with comprehensive edge case handling using Gemini API"""

    def __init__(self, api_key: str = None):
        """Initialize with Gemini API key"""
        self.api_key = api_key or config.get_gemini_api_key()

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini API initialized")
        else:
            self.client = None
            logger.warning("No Gemini API key - AI analysis disabled")

    def analyze_content(self, text_content: str, metadata: Dict = None,
                       categories: list = None) -> Dict:
        """Enhanced content analysis with comprehensive edge case handling"""

        if not self.client:
            return self._get_empty_result()

        # Prepare context
        context_parts = [f"Video content text:\n{text_content}"]
        if metadata:
            context_parts.append(f"\nMetadata:\n{json.dumps(metadata, indent=2)}")
        if categories:
            context_parts.append(f"\nExpected categories: {', '.join(categories)}")

        context = "\n".join(context_parts)

        prompt = f"""
Analyze this TikTok video content and extract comprehensive location information. Handle these edge cases:

1. **Single Places**: One restaurant/business featured in the video
2. **Multiple Places**: Area guides or videos featuring multiple locations
3. **Popup Events**: Temporary events, markets, or limited-time restaurants
4. **Carousel Content**: Multiple images with different text/locations per image
5. **Market Vendors**: Individual vendors/stalls within food courts, farmer's markets, flea markets, night markets
6. **Non-English Names**: Places with Chinese, Korean, Japanese, or other non-English names

{context}

**IMPORTANT**: Pay special attention to:
- Chinese characters or non-English place names (e.g., 满小满, 老友记, etc.)
- Market references ("inside [mall name] food court", "stall in", "vendor at", "farmer's market", "flea market", "night market")
- Address information mentioned in hashtags or location descriptions
- Mall, plaza, or market names that contain the individual vendors

Extract information in this EXACT JSON format:
{{
    "content_analysis": {{
        "content_type": "single_place|multiple_places|popup_event|area_guide",
        "confidence_score": 0.0-1.0,
        "primary_focus": "description of main subject"
    }},
    "places": [
        {{
            "name": "Restaurant/Business Name",
            "address": "Full address if mentioned",
            "neighborhood": "Area/neighborhood",
            "categories": ["restaurant", "chinese", "casual dining"],
            "recommendations": "Specific menu items or recommendations",
            "hours": "Opening hours or schedule",
            "website": "Website URL if mentioned",
            "is_popup": false,
            "popup_details": {{
                "duration": "how long the popup runs",
                "host_location": "where the popup is hosted",
                "event_type": "popup market|temporary restaurant|special event"
            }}
        }}
    ],
    "area_info": {{
        "area_theme": "neighborhood food guide|shopping district|etc",
        "total_places_mentioned": 0,
        "area_description": "overall area description"
    }}
}}

**CRITICAL INSTRUCTIONS**:
- For popups: Set is_popup=true and fill popup_details
- For area guides: Set content_type="area_guide" and fill area_info
- If no clear location info: Return empty places array
- Use exact JSON format - no extra text or explanations
- Extract specific menu items, not generic descriptions
- Look for temporal indicators like "this weekend", "popup", "limited time"
- DO NOT return generic names like "unnamed", "unknown", "restaurant", "cafe", "store", "business", etc.
- Only return specific, identifiable business names with actual place names
- If only generic descriptions are available, return empty places array
- ALWAYS extract Chinese/non-English place names - they are valid specific business names
- For market vendors WITH specific names: Use the actual vendor name and include market address
- For market vendors WITHOUT specific names: Format as directional location (e.g., "Corner Stall at Golden Mall Food Court", "Stand 5 at Union Square Farmer's Market", "Booth A12 at Brooklyn Flea")
- When market/mall address is mentioned, use that as the address for individual vendors
- Look for location clues in hashtags, descriptions, and 📍 location pins
"""

        try:
            response = self.client.generate_content(prompt)

            # Parse Gemini's response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0]
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0]

            extracted_data = json.loads(response_text)
            log_success(logger, f"Enhanced Gemini extraction completed: {extracted_data.get('content_type', 'unknown type')}")
            return extracted_data

        except (json.JSONDecodeError, ValueError, KeyError) as ex:
            logger.warning(f"Gemini extraction failed: {ex}")
            return self._get_empty_result()

    def _get_empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            "content_analysis": {
                "content_type": "unknown",
                "confidence_score": 0.0,
                "primary_focus": ""
            },
            "places": [],
            "area_info": {
                "area_theme": "",
                "total_places_mentioned": 0,
                "area_description": ""
            }
        }

    def extract_place_name(self, text_content: str, metadata: Dict = None) -> str:
        """Extract just the place name from content"""
        analysis = self.analyze_content(text_content, metadata)
        return analysis.get('name_of_place', '')
    
