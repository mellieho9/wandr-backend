"""
My Link data model for Notion integration
"""

from typing import Optional, Dict, Any
from datetime import datetime


class MyLink:
    """
    Simple data model for My Links database
    Contains just URL and processing status
    """
    
    def __init__(self, url: str, title: Optional[str] = None, status: str = "pending", created_time: Optional[datetime] = None):
        self.url = url
        self.title = title
        self.status = status
        self.created_time = created_time or datetime.now()

    def to_notion_dict(self) -> Dict[str, Any]:
        """Convert to Notion database format for My Links"""
        return {
            "URL": {
                "url": self.url
            },
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": self.title or "TikTok Video"
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": self.status
                }
            }
            # created_time is auto-populated by Notion
        }


