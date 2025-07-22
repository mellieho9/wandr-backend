"""
Data models for pipeline operations
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from constants import DEFAULT_WHISPER_MODEL, DEFAULT_FRAME_INTERVAL, DEFAULT_MAX_FRAMES, DEFAULT_OUTPUT_DIR


class ProcessingStatus(Enum):
    """Status of processing operations"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class PipelineOptions:
    """Configuration options for pipeline execution"""
    url: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    output_dir: str = DEFAULT_OUTPUT_DIR
    create_notion_entry: bool = False
    database_id: Optional[str] = None
    
    # Processing options
    whisper_model: str = DEFAULT_WHISPER_MODEL
    frame_interval: float = DEFAULT_FRAME_INTERVAL
    max_frames: int = DEFAULT_MAX_FRAMES


@dataclass
class ProcessingResult:
    """Generic result container for processing operations"""
    status: ProcessingStatus
    data: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if processing was successful"""
        return self.status == ProcessingStatus.SUCCESS
    
    @property
    def failed(self) -> bool:
        """Check if processing failed"""
        return self.status == ProcessingStatus.FAILED


@dataclass
class VideoProcessingResult(ProcessingResult):
    """Result of video processing operations"""
    video_path: Optional[str] = None
    transcription_text: Optional[str] = None
    ocr_text: Optional[str] = None
    combined_text: Optional[str] = None


@dataclass
class LocationProcessingResult(ProcessingResult):
    """Result of location processing operations"""
    places_found: int = 0
    location_file: Optional[str] = None


@dataclass
class NotionProcessingResult(ProcessingResult):
    """Result of Notion integration operations"""
    entries_created: int = 0
    page_ids: List[str] = field(default_factory=list)


@dataclass
class BatchProcessingResult:
    """Result of batch processing operations"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_processed == 0:
            return 0.0
        return (self.successful / self.total_processed) * 100