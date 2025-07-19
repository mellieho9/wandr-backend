"""
URL parsing and component data models
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class URLComponents:
    """Parsed components of a TikTok URL"""
    video_id: str
    username: Optional[str]
    content_type: str  # 'short', 'video', 'photo'
    raw_url: str