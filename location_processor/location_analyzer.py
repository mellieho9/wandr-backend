#!/usr/bin/env python3
"""
Location Analyzer

Uses Gemini API to extract location information from video content.
"""

import json
import os
from typing import Dict
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LocationAnalyzer:
    """Extract location information using Gemini API"""
    
    def __init__(self, api_key: str = None):
        """Initialize with Gemini API key"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Gemini API initialized")
        else:
            self.client = None
            print("⚠️ No Gemini API key - AI analysis disabled")
    
    def analyze_content(self, text_content: str, metadata: Dict = None) -> Dict:
        """Analyze video content and extract location information"""
        
        if not self.client:
            return {
                'name_of_place': '',
                'recommendations': '',
                'location_hint': '',
                'time': ''
            }
        
        # Prepare context
        context_parts = [f"Video content text:\n{text_content}"]
        if metadata:
            context_parts.append(f"\nMetadata:\n{json.dumps(metadata, indent=2)}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
Analyze this TikTok video content and extract location information in JSON format.

{context}

Extract the following information:
1. "name_of_place": The specific restaurant/business name
2. "recommendations": Specific menu items or things recommended
3. "location_hint": Any address, neighborhood, or location clues found
4. "time": Opening hours or schedule information (e.g., "Monday-Friday 11am-3pm" or specific hours mentioned)

Return ONLY a valid JSON object with these fields. If information is not available, use empty string.
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
            print("✅ Gemini extraction completed")
            return extracted_data
                
        except Exception as e:
            print(f"⚠️ Gemini extraction failed: {e}")
            return {
                'name_of_place': '',
                'recommendations': '',
                'location_hint': '',
                'time': ''
            }
    
    
    def extract_place_name(self, text_content: str, metadata: Dict = None) -> str:
        """Extract just the place name from content"""
        analysis = self.analyze_content(text_content, metadata)
        return analysis.get('name_of_place', '')
    
