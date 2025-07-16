#!/usr/bin/env python3
"""
Webhook Handler

Handles incoming webhooks from Notion and processes TikTok URLs.
"""

import os
import json
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs
import re

from .notion_client import NotionClient

class WebhookHandler:
    """Handles Notion webhooks and processes TikTok URLs"""
    
    def __init__(self, notion_client: NotionClient = None):
        """Initialize webhook handler"""
        self.notion_client = notion_client or NotionClient()
        print("✅ Webhook handler initialized")
    
    def process_webhook(self, webhook_data: Dict) -> Dict:
        """Process incoming webhook from Notion"""
        
        try:
            # Extract page information from webhook
            page_info = self._extract_page_info(webhook_data)
            if not page_info:
                return {"success": False, "error": "Could not extract page info from webhook"}
            
            page_id = page_info['page_id']
            tiktok_url = page_info['tiktok_url']
            
            print(f"📨 Processing webhook for page: {page_id}")
            print(f"🎬 TikTok URL: {tiktok_url}")
            
            # Validate TikTok URL
            if not self._is_valid_tiktok_url(tiktok_url):
                return {"success": False, "error": f"Invalid TikTok URL: {tiktok_url}"}
            
            # Process the TikTok video and extract location
            result = self._process_tiktok_video(tiktok_url, page_id)
            
            if result['success']:
                print(f"✅ Successfully processed webhook for page {page_id}")
            else:
                print(f"❌ Failed to process webhook: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"Webhook processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _extract_page_info(self, webhook_data: Dict) -> Optional[Dict]:
        """Extract page ID and TikTok URL from webhook data"""
        
        # Notion webhook structure varies, but typically contains page info
        # This is a simplified example - you may need to adjust based on actual webhook format
        
        page_id = None
        tiktok_url = None
        
        # Try to extract page ID from different possible locations
        if 'page' in webhook_data:
            page_id = webhook_data['page'].get('id')
        elif 'object' in webhook_data and webhook_data['object'] == 'page':
            page_id = webhook_data.get('id')
        elif 'data' in webhook_data:
            page_id = webhook_data['data'].get('page_id')
        
        if not page_id:
            print("⚠️ Could not find page ID in webhook data")
            return None
        
        # Get the page to extract TikTok URL from properties
        page_data = self.notion_client.get_page(page_id)
        if not page_data:
            print("⚠️ Could not retrieve page data")
            return None
        
        # Extract TikTok URL from page properties
        properties = page_data.get('properties', {})
        
        # Look for URL property (adjust field name as needed)
        url_property = properties.get('URL') or properties.get('url') or properties.get('Link')
        
        if url_property and url_property.get('url'):
            tiktok_url = url_property['url']
        elif url_property and url_property.get('rich_text'):
            # Sometimes URLs are stored as rich text
            rich_text = url_property['rich_text']
            if rich_text and len(rich_text) > 0:
                tiktok_url = rich_text[0].get('text', {}).get('content', '')
        
        if not tiktok_url:
            print("⚠️ Could not find TikTok URL in page properties")
            return None
        
        return {
            'page_id': page_id,
            'tiktok_url': tiktok_url
        }
    
    def _is_valid_tiktok_url(self, url: str) -> bool:
        """Validate if URL is a valid TikTok URL"""
        if not url:
            return False
        
        tiktok_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:www\.)?tiktok\.com/t/[\w]+/?',
            r'https?://vm\.tiktok\.com/[\w]+/?'
        ]
        
        return any(re.match(pattern, url) for pattern in tiktok_patterns)
    
    def _process_tiktok_video(self, tiktok_url: str, page_id: str) -> Dict:
        """Process TikTok video and update Notion page"""
        
        try:
            # Import here to avoid circular imports
            from video_processor import TikTokProcessor
            from location_processor import LocationProcessor
            
            # Step 1: Process video
            print("📹 Processing TikTok video...")
            vision_api_key = os.getenv("VISION_API_KEY")
            video_processor = TikTokProcessor(vision_api_key, "tiny")
            video_results = video_processor.process_url(tiktok_url, "results", "tiktok")
            
            if not video_results['success']:
                return {"success": False, "error": f"Video processing failed: {video_results.get('error')}"}
            
            # Step 2: Extract location information
            print("📍 Extracting location information...")
            location_processor = LocationProcessor()
            video_id = video_processor._extract_video_id(tiktok_url)
            
            # For now, use empty categories - could be extracted from page properties if needed
            location_info = location_processor.process_video_results(video_id, "results", [])
            
            # Step 3: Update Notion page
            print("📝 Updating Notion page...")
            success = self.notion_client.update_page_with_location_data(
                page_id, 
                location_info.to_dict()
            )
            
            if success:
                return {
                    "success": True,
                    "page_id": page_id,
                    "video_id": video_id,
                    "location_info": location_info.to_dict()
                }
            else:
                return {"success": False, "error": "Failed to update Notion page"}
                
        except Exception as e:
            return {"success": False, "error": f"Processing error: {str(e)}"}
    
    def process_url_directly(self, tiktok_url: str, page_id: str, place_categories: list = None) -> Dict:
        """Direct processing method for manual calls"""
        
        if not self._is_valid_tiktok_url(tiktok_url):
            return {"success": False, "error": f"Invalid TikTok URL: {tiktok_url}"}
        
        print(f"🎯 Direct processing: {tiktok_url} → {page_id}")
        return self._process_tiktok_video(tiktok_url, page_id)