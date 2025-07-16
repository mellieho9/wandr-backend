#!/usr/bin/env python3
"""
Notion API Client

Handles direct interaction with Notion API for updating pages.
"""

import os
import json
from typing import Dict, Optional, List
import requests
from dotenv import load_dotenv

load_dotenv()

class NotionClient:
    """Client for interacting with Notion API"""
    
    def __init__(self, api_key: str = None):
        """Initialize with Notion API key"""
        self.api_key = api_key or os.getenv('NOTION_API_KEY')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        if not self.api_key:
            print("⚠️ No NOTION_API_KEY found - Notion integration disabled")
        else:
            print("✅ Notion API client initialized")
    
    def get_page(self, page_id: str) -> Optional[Dict]:
        """Get page properties from Notion"""
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/pages/{page_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get page {page_id}: {e}")
            return None
    
    def update_page_properties(self, page_id: str, properties: Dict) -> bool:
        """Update page properties in Notion"""
        if not self.api_key:
            print("⚠️ No Notion API key - cannot update page")
            return False
        
        try:
            url = f"{self.base_url}/pages/{page_id}"
            data = {"properties": properties}
            
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            print(f"✅ Successfully updated Notion page: {page_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update page {page_id}: {e}")
            return False
    
    def update_page_with_location_data(self, page_id: str, location_data: Dict) -> bool:
        """Update page with structured location data"""
        
        # Convert location data to Notion properties format
        properties = self._convert_to_notion_properties(location_data)
        
        return self.update_page_properties(page_id, properties)
    
    def _convert_to_notion_properties(self, location_data: Dict) -> Dict:
        """Convert location JSON to Notion properties format"""
        properties = {}
        
        # URL (link)
        if location_data.get('URL'):
            properties['URL'] = {
                "url": location_data['URL']
            }
        
        # Place category (multi-select)
        if location_data.get('place_category'):
            properties['place_category'] = {
                "multi_select": [
                    {"name": category} for category in location_data['place_category']
                ]
            }
        
        # Review (rich text)
        if location_data.get('review'):
            properties['review'] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": location_data['review']}
                    }
                ]
            }
        
        # Name of place (title or rich text)
        if location_data.get('name of place'):
            properties['name of place'] = {
                "rich_text": [
                    {
                        "type": "text", 
                        "text": {"content": location_data['name of place']}
                    }
                ]
            }
        
        # Location (rich text - Notion doesn't have native location type)
        if location_data.get('location'):
            properties['location'] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": location_data['location']}
                    }
                ]
            }
        
        # Recommendations (rich text)
        if location_data.get('recommendations'):
            properties['recommendations'] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": location_data['recommendations']}
                    }
                ]
            }
        
        # Time (rich text)
        if location_data.get('time'):
            properties['time'] = {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": location_data['time']}
                    }
                ]
            }
        
        # Website (URL)
        if location_data.get('website'):
            properties['website'] = {
                "url": location_data['website']
            }
        
        # Visited (checkbox)
        if 'visited' in location_data:
            properties['visited'] = {
                "checkbox": location_data['visited']
            }
        
        return properties
    
    def get_database_properties(self, database_id: str) -> Optional[Dict]:
        """Get database schema to understand property types"""
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/databases/{database_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('properties', {})
        except Exception as e:
            print(f"❌ Failed to get database schema: {e}")
            return None