#!/usr/bin/env python3
"""
Notion Service Main

Main service for handling Notion integration and webhooks.
"""

import argparse
import json
import logging
import os
from pathlib import Path

from .notion_client import NotionClient
from .webhook_handler import WebhookHandler

logger = logging.getLogger(__name__)

class NotionService:
    """Main service combining Notion client and webhook handling"""
    
    def __init__(self, notion_api_key: str = None):
        """Initialize service with API key"""
        self.client = NotionClient(notion_api_key)
        self.webhook_handler = WebhookHandler(self.client)
        logger.info("Notion service initialized")
    
    def update_page_from_location_file(self, page_id: str, location_file: str) -> bool:
        """Update Notion page from existing location JSON file"""
        
        if not os.path.exists(location_file):
            print(f"❌ Location file not found: {location_file}")
            return False
        
        try:
            with open(location_file, 'r', encoding='utf-8') as f:
                location_data = json.load(f)
            
            print(f"📄 Loading location data from: {location_file}")
            success = self.client.update_page_with_location_data(page_id, location_data)
            
            if success:
                print(f"✅ Successfully updated page {page_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to update page from file: {e}")
            return False
    
    def process_tiktok_and_update_page(self, tiktok_url: str, page_id: str, place_categories: list = None) -> Dict:
        """Complete pipeline: process TikTok video and update Notion page"""
        
        result = self.webhook_handler.process_url_directly(tiktok_url, page_id, place_categories)
        
        if result['success']:
            print(f"🎉 Complete pipeline success!")
            print(f"📄 Page: {page_id}")
            print(f"🎬 Video: {tiktok_url}")
            print(f"📍 Location: {result.get('location_info', {}).get('name of place', 'Unknown')}")
        
        return result
    
    def handle_webhook_request(self, webhook_data: Dict) -> Dict:
        """Handle incoming webhook request"""
        return self.webhook_handler.process_webhook(webhook_data)

def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Notion Service for TikTok location processing")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Update page from file
    update_parser = subparsers.add_parser('update-page', help='Update Notion page from location file')
    update_parser.add_argument('--page-id', required=True, help='Notion page ID')
    update_parser.add_argument('--location-file', required=True, help='Path to location JSON file')
    
    # Process TikTok URL
    process_parser = subparsers.add_parser('process-url', help='Process TikTok URL and update page')
    process_parser.add_argument('--page-id', required=True, help='Notion page ID')
    process_parser.add_argument('--url', required=True, help='TikTok URL')
    process_parser.add_argument('--category', nargs='*', help='Place categories')
    
    # Test connection
    test_parser = subparsers.add_parser('test', help='Test Notion API connection')
    test_parser.add_argument('--page-id', help='Page ID to test with')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize service
    service = NotionService()
    
    try:
        if args.command == 'update-page':
            success = service.update_page_from_location_file(args.page_id, args.location_file)
            return 0 if success else 1
            
        elif args.command == 'process-url':
            result = service.process_tiktok_and_update_page(
                args.url, 
                args.page_id, 
                args.category
            )
            return 0 if result['success'] else 1
            
        elif args.command == 'test':
            if args.page_id:
                page_data = service.client.get_page(args.page_id)
                if page_data:
                    print(f"✅ Successfully connected to Notion")
                    print(f"📄 Page title: {page_data.get('properties', {}).get('title', 'No title')}")
                    return 0
                else:
                    print("❌ Failed to retrieve page")
                    return 1
            else:
                # Just test API key
                if service.client.api_key:
                    print("✅ Notion API key found")
                    return 0
                else:
                    print("❌ No Notion API key found")
                    return 1
        
    except KeyboardInterrupt:
        print("\n🛑 Process interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())