"""
Webhook data models for Notion integration
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from utils.constants import TAG_METADATA_ONLY, TAG_AUDIO_ONLY
from models.pipeline_models import ProcessingMode

# Use ProcessingMode from pipeline_models instead of duplicate enum
ProcessingType = ProcessingMode


@dataclass
class NotionWebhookPayload:
    """Payload structure for Notion webhook requests"""
    url: str
    tags: Optional[List[str]] = field(default_factory=list)
    
    def get_processing_type(self) -> ProcessingType:
        """Determine processing type based on tags"""
        if not self.tags:
            return ProcessingType.FULL
        
        # Convert tags to lowercase for comparison
        tags_lower = [tag.lower() for tag in self.tags]
        
        if TAG_METADATA_ONLY in tags_lower:
            return ProcessingType.METADATA_ONLY
        elif TAG_AUDIO_ONLY in tags_lower:
            return ProcessingType.AUDIO_ONLY
        else:
            return ProcessingType.FULL
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotionWebhookPayload':
        """Create payload from dictionary data"""
        return cls(
            url=data.get('url', ''),
            tags=data.get('tags', [])
        )


@dataclass
class WebhookResponse:
    """Standard response for webhook endpoints"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        response = {
            'success': self.success,
            'message': self.message
        }
        
        if self.data:
            response['data'] = self.data
        
        if self.error:
            response['error'] = self.error
        
        return response


@dataclass
class ProcessingOptions:
    """Processing options derived from webhook payload"""
    process_audio: bool = True
    process_screenshots: bool = True
    process_metadata: bool = True
    
    @classmethod
    def from_processing_type(cls, processing_type: ProcessingType) -> 'ProcessingOptions':
        """Create options based on processing type"""
        if processing_type == ProcessingType.METADATA_ONLY:
            return cls(
                process_audio=False,
                process_screenshots=False,
                process_metadata=True
            )
        elif processing_type == ProcessingType.AUDIO_ONLY:
            return cls(
                process_audio=True,
                process_screenshots=False,
                process_metadata=True
            )
        else:  # FULL
            return cls(
                process_audio=True,
                process_screenshots=True,
                process_metadata=True
            )