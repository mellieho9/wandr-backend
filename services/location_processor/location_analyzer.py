#!/usr/bin/env python3
"""
Location Analyzer

Uses Gemini API to extract location information from video content.
"""

import json
import logging
from typing import Dict
import google.generativeai as genai

from utils.config import config
logger = logging.getLogger(__name__)

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

{context}

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
            "is_primary": true,
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
- For single place videos: Return 1 place with is_primary=true
- For multiple places: Return multiple places, mark the main one as is_primary=true
- For popups: Set is_popup=true and fill popup_details
- For area guides: Set content_type="area_guide" and fill area_info
- If no clear location info: Return empty places array
- Use exact JSON format - no extra text or explanations
- Extract specific menu items, not generic descriptions
- Look for temporal indicators like "this weekend", "popup", "limited time"
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
            logger.info("Enhanced Gemini extraction completed ", extracted_data)
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
    
