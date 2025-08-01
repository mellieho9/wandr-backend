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
from utils.prompts import get_location_analysis_prompt

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

        prompt = get_location_analysis_prompt(context)
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
    
