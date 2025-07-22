"""
Pipeline orchestrator for coordinating processing operations
"""

import logging
from typing import Dict, Any, Optional

from config import config
from models.pipeline_models import (
    PipelineOptions, ProcessingResult, ProcessingStatus, BatchProcessingResult
)
from exceptions import ConfigurationError, WandrError
from notion_handlern_service.notion_client import NotionClient
from utils.logging_config import LoggerMixin
from .commands import ProcessVideoCommand, ExtractLocationCommand, CreateNotionEntryCommand

logger = logging.getLogger(__name__)


class PipelineOrchestrator(LoggerMixin):
    """Orchestrates the complete pipeline execution"""
    
    def __init__(self, options: PipelineOptions):
        """
        Initialize orchestrator with pipeline options.
        
        Args:
            options: Pipeline configuration options
        """
        self.options = options
        self._validate_configuration()
    
    def run_single_url(self, url: str) -> Dict[str, ProcessingResult]:
        """
        Process a single URL through the complete pipeline.
        
        Args:
            url: TikTok URL to process
            
        Returns:
            Dictionary containing results from each pipeline stage
        """
        self.logger.info(f"Starting pipeline for URL: {url}")
        
        results = {}
        
        try:
            # Step 1: Process video
            self.logger.info("Step 1: Processing video content...")
            video_command = ProcessVideoCommand(self.options)
            video_result = video_command.execute(url)
            results['video'] = video_result
            
            if not video_result.success:
                self.logger.error(f"Video processing failed: {video_result.error_message}")
                return results
            
            # Step 2: Extract location information
            self.logger.info("Step 2: Extracting location information...")
            location_command = ExtractLocationCommand(self.options)
            location_result = location_command.execute(url)
            results['location'] = location_result
            
            if not location_result.success:
                self.logger.error(f"Location extraction failed: {location_result.error_message}")
                return results
            
            # Step 3: Create Notion entries (optional)
            if self.options.create_notion_entry and self.options.database_id:
                self.logger.info("Step 3: Creating Notion database entries...")
                try:
                    notion_command = CreateNotionEntryCommand(self.options.database_id)
                    notion_result = notion_command.execute(location_result)
                    results['notion'] = notion_result
                    
                    if not notion_result.success:
                        self.logger.error(f"Notion entry creation failed: {notion_result.error_message}")
                        # Don't fail the whole pipeline for Notion errors
                except Exception as e:
                    self.logger.error(f"Notion entry creation failed: {e}")
                    results['notion'] = ProcessingResult(
                        status=ProcessingStatus.FAILED,
                        error_message=str(e)
                    )
            
            # Log summary
            self._log_pipeline_summary(results)
            
            self.logger.info("Pipeline completed successfully!")
            return results
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Add error result if not already present
            if 'error' not in results:
                results['error'] = ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error_message=error_msg
                )
            
            return results
    
    def run_batch_processing(self, source_database_id: str, places_database_id: str) -> BatchProcessingResult:
        """
        Process all pending URLs from source database and create place entries.
        
        Args:
            source_database_id: Database ID to pull URLs from
            places_database_id: Database ID to create place entries in
            
        Returns:
            BatchProcessingResult with processing summary
        """
        try:
            self.logger.info("Starting batch processing of pending URLs...")
            
            # Initialize Notion client
            api_key = config.get_notion_api_key()
            if not api_key:
                raise ConfigurationError("NOTION_API_KEY environment variable is required")
            
            notion_client = NotionClient(api_key)
            
            # Process pending URLs using existing method
            results = notion_client.process_pending_urls(
                source_database_id=source_database_id,
                places_database_id=places_database_id
            )
            
            # Convert to our result format
            batch_result = BatchProcessingResult(
                total_processed=results['processed'],
                successful=results['successful'],
                failed=results['failed'],
                errors=results['errors']
            )
            
            # Log summary
            self.logger.info("Batch Processing Summary:")
            self.logger.info(f"  Total URLs processed: {batch_result.total_processed}")
            self.logger.info(f"  Successful: {batch_result.successful}")
            self.logger.info(f"  Failed: {batch_result.failed}")
            self.logger.info(f"  Success rate: {batch_result.success_rate:.1f}%")
            
            if batch_result.errors:
                self.logger.error("Errors encountered:")
                for error in batch_result.errors:
                    self.logger.error(f"  - {error}")
            
            return batch_result
            
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            return BatchProcessingResult(
                total_processed=0,
                successful=0,
                failed=0,
                errors=[error_msg]
            )
    
    def _validate_configuration(self):
        """Validate pipeline configuration"""
        if self.options.create_notion_entry and not self.options.database_id:
            raise ConfigurationError(
                "database_id is required when create_notion_entry is True"
            )
        
        # Validate output directory
        if not self.options.output_dir:
            raise ConfigurationError("output_dir cannot be empty")
    
    def _log_pipeline_summary(self, results: Dict[str, ProcessingResult]):
        """Log a summary of pipeline results"""
        video_result = results.get('video')
        location_result = results.get('location')
        notion_result = results.get('notion')
        
        if video_result and video_result.success:
            video_id = video_result.metadata.get('url', 'unknown')
            self.logger.info(f"Video results: {self.options.output_dir}/{video_id}_results.json")
        
        if location_result and location_result.success:
            location_file = location_result.location_file
            self.logger.info(f"Location info: {location_file}")
            self.logger.info("EXTRACTED INFO:")
            
            location_info = location_result.data
            if location_info and location_info.places:
                primary_place = location_info.places[0]
                self.logger.info(f"Place: {primary_place.name}")
                self.logger.info(f"Categories: {', '.join(primary_place.categories) if primary_place.categories else 'None'}")
                self.logger.info(f"Location: {primary_place.address or primary_place.neighborhood or 'N/A'}")
                self.logger.info(f"Website: {primary_place.website or 'N/A'}")
                self.logger.info(f"Time: {primary_place.hours or 'N/A'}")
                if primary_place.recommendations:
                    from constants import MAX_RECOMMENDATION_PREVIEW_LENGTH
                    rec_text = str(primary_place.recommendations)
                    rec_preview = (rec_text[:MAX_RECOMMENDATION_PREVIEW_LENGTH] + "..." 
                                 if len(rec_text) > MAX_RECOMMENDATION_PREVIEW_LENGTH 
                                 else rec_text)
                    self.logger.info(f"Recommendations: {rec_preview}")
            else:
                self.logger.warning("No places found in location info")
        
        if notion_result and notion_result.success:
            self.logger.info(f"Created {notion_result.entries_created} Notion entries")