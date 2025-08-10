"""
Command pattern implementation for pipeline operations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from utils.config import config
from services.video_processor import TikTokProcessor
from services.location_processor import LocationProcessor
from services.notion_service.notion_client import NotionClient
from services.notion_service.location_handler import LocationHandler
from utils.location_transformer import LocationToNotionTransformer
from models.pipeline_models import (
    PipelineOptions, ProcessingResult, ProcessingStatus,
    VideoProcessingResult, LocationProcessingResult, NotionProcessingResult
)
from utils.exceptions import VideoProcessingError, NotionIntegrationError
from utils.url_parser import TikTokURLParser
from utils.logging_config import setup_logging

logger = setup_logging(logger_name=__name__)


class Command(ABC):
    """Base command interface"""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ProcessingResult:
        """Execute the command"""
        pass


class ProcessVideoCommand(Command):
    """Command to process TikTok video content"""
    
    def __init__(self, options: PipelineOptions):
        self.options = options
        
        # Initialize video processor
        vision_api_key = config.get_vision_api_key()
        if not vision_api_key:
            logger.warning("No VISION_API_KEY - OCR will be disabled")
        
        self.processor = TikTokProcessor(
            vision_api_key, 
            options.frame_interval,
            options.max_frames
        )
    
    def execute(self, url: str) -> VideoProcessingResult:
        """
        Process video from URL based on processing mode.
        
        Args:
            url: TikTok URL to process
            
        Returns:
            VideoProcessingResult with processing outcome
        """
        try:
            logger.info(f"Processing video: {url} (mode: {self.options.processing_mode.value})")
            
            video_results, metadata = self.processor.process_with_data_return(url, self.options.processing_mode, self.options.output_dir)
            logger.info(f"video_results: {video_results}")
            if not video_results.get('success', False):
                error_msg = video_results.get('error', 'Unknown video processing error')
                raise VideoProcessingError(error_msg, context={'url': url})
            

            # Extract text content
            combined_text = video_results.get('combined_text', '')
            transcription_text = self._extract_transcription_text(video_results)
            ocr_text = self._extract_ocr_text(video_results)
            video_path = video_results.get('video_path')

            return VideoProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data={'video_results': video_results, 'metadata': metadata},
                video_path=video_path,
                transcription_text=transcription_text,
                ocr_text=ocr_text,
                combined_text=combined_text,
                metadata={
                    'url': url,
                    'content_type': video_results.get('content_type', 'unknown'),
                    'processing_mode': self.options.processing_mode.value
                }
            )
            
        except Exception as e:
            error_msg = f"Video processing failed: {str(e)}"
            logger.error(error_msg)
            
            return VideoProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=error_msg,
                metadata={'url': url, 'processing_mode': self.options.processing_mode.value}
            )
    
    def _extract_transcription_text(self, results: Dict[str, Any]) -> str:
        """Extract transcription text from results"""
        transcription = results.get('transcription', {})
        if transcription.get('success'):
            return transcription.get('text', '')
        return ''
    
    def _extract_ocr_text(self, results: Dict[str, Any]) -> str:
        """Extract OCR text from results"""
        ocr = results.get('ocr', {})
        if ocr.get('success'):
            text_data = ocr.get('text_data', [])
            return ' '.join([frame.get('text', '') for frame in text_data])
        return ''


class ExtractLocationCommand(Command):
    """Command to extract location information from video results"""
    
    def __init__(self, options: PipelineOptions):
        self.options = options
        self.processor = LocationProcessor()
    
    def execute_with_data(self, url: str, video_data: dict) -> LocationProcessingResult:
        """
        Extract location information using in-memory video data.
        
        Args:
            url: Original TikTok URL
            video_data: Dictionary containing video_results and metadata
            
        Returns:
            LocationProcessingResult with extraction outcome
        """
        try:
            logger.info(f"Extracting location information for: {url}")
            
            video_results = video_data.get('video_results', {})
            metadata = video_data.get('metadata', {})
            
            # Extract location info using in-memory data
            location_info = self.processor.extract_from_data(
                video_results, metadata, self.options.categories
            )
            
            return LocationProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data=location_info,
                places_found=len(location_info.places),
                location_file=None,  # No file saved in memory mode
                metadata={
                    'url': url,
                    'content_type': location_info.content_type
                }
            )
            
        except Exception as e:
            error_msg = f"Location extraction failed: {str(e)}"
            logger.error(error_msg)
            
            return LocationProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=error_msg,
                metadata={'url': url}
            )

    def execute(self, url: str) -> LocationProcessingResult:
        """
        Extract location information from processed video.
        
        Args:
            url: Original TikTok URL
            
        Returns:
            LocationProcessingResult with extraction outcome
        """
        try:
            logger.info(f"Extracting location information for: {url}")
            
            # Get video ID for file lookup
            video_id = TikTokURLParser.get_file_prefix(url)
            
            # Extract location info
            location_info = self.processor.process_video_results(
                video_id, self.options.output_dir, self.options.categories
            )
            
            # Save location info
            location_output = f"{self.options.output_dir}/{video_id}_location.json"
            self.processor.save_location_info(location_info, location_output)
            
            return LocationProcessingResult(
                status=ProcessingStatus.SUCCESS,
                data=location_info,
                places_found=len(location_info.places),
                location_file=location_output,
                metadata={
                    'url': url,
                    'video_id': video_id,
                    'content_type': location_info.content_type
                }
            )
            
        except Exception as e:
            error_msg = f"Location extraction failed: {str(e)}"
            logger.error(error_msg)
            
            return LocationProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=error_msg,
                metadata={'url': url}
            )


class CreateNotionEntryCommand(Command):
    """Command to create Notion database entries"""
    
    def __init__(self, database_id: str):
        self.database_id = database_id
        
        # Initialize Notion client
        api_key = config.get_notion_api_key()
        if not api_key:
            raise NotionIntegrationError("NOTION_API_KEY environment variable is required")
        
        self.notion_client = NotionClient(api_key)
        self.location_handler = LocationHandler(self.notion_client)
        self.transformer = LocationToNotionTransformer()
    
    def execute(self, location_result: LocationProcessingResult) -> NotionProcessingResult:
        """
        Create Notion entries from location information.
        
        Args:
            location_result: Result from location extraction
            
        Returns:
            NotionProcessingResult with creation outcome
        """
        try:
            if not location_result.success:
                raise NotionIntegrationError(
                    f"Cannot create Notion entries from failed location extraction: {location_result.error_message}"
                )
            
            location_info = location_result.data
            source_url = location_result.metadata.get('url')
            
            if not location_info.places:
                logger.warning("No places found to create Notion entries")
                return NotionProcessingResult(
                    status=ProcessingStatus.SUCCESS,
                    entries_created=0,
                    metadata={'message': 'No places to create'}
                )
            
            logger.info(f"Creating {len(location_info.places)} Notion entries...")
            
            created_page_ids = []
            duplicate_count = 0
            
            for i, place in enumerate(location_info.places, 1):
                try:
                    # Transform place data to Notion format
                    place_data = self.transformer.transform_place(place, source_url)
                    
                    # Create the entry (with duplicate checking)
                    response = self.location_handler.create_location_entry(self.database_id, place_data)
                    page_id = response['id']
                    created_page_ids.append(page_id)
                    
                    if response.get('duplicate', False):
                        duplicate_count += 1
                        logger.info(f"Duplicate entry {i}/{len(location_info.places)}: {place.name} (skipped)")
                        logger.info(f"   Existing Page ID: {page_id}")
                    else:
                        logger.info(f"Created Notion entry {i}/{len(location_info.places)}: {place.name}")
                        logger.info(f"   Page ID: {page_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to create entry for {place.name}: {e}")
                    continue
            
            new_entries_count = len(created_page_ids) - duplicate_count
            
            return NotionProcessingResult(
                status=ProcessingStatus.SUCCESS,
                entries_created=new_entries_count,
                page_ids=created_page_ids,
                metadata={
                    'total_places': len(location_info.places),
                    'new_entries': new_entries_count,
                    'duplicates_skipped': duplicate_count,
                    'source_url': source_url
                }
            )
            
        except Exception as e:
            error_msg = f"Notion entry creation failed: {str(e)}"
            logger.error(error_msg)
            
            return NotionProcessingResult(
                status=ProcessingStatus.FAILED,
                error_message=error_msg,
                metadata={'database_id': self.database_id}
            )