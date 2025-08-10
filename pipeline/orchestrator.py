"""
Pipeline orchestrator for coordinating processing operations
"""
import traceback
from utils.config import config
from typing import Dict
from services.notion_service.notion_client import NotionClient
from utils.constants import MAX_RECOMMENDATION_PREVIEW_LENGTH
from models.pipeline_models import (
    PipelineOptions, ProcessingResult, ProcessingStatus, BatchProcessingResult, ProcessingMode
)
from utils.exceptions import ConfigurationError
from utils.logging_config import LoggerMixin, setup_logging, log_success
from utils.cleanup import cleanup_video_files
from .commands import ProcessVideoCommand, ExtractLocationCommand, CreateNotionEntryCommand

logger = setup_logging(logger_name=__name__)


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
    
    # Tag to processing mode mapping
    TAG_TO_MODE = {
        "metadata-only": ProcessingMode.METADATA_ONLY,
        "audio-only": ProcessingMode.AUDIO_ONLY,
        "carousel": ProcessingMode.CAROUSEL
    }
    
    def _determine_processing_mode(self, tag):
        """Determine processing mode from tags using mapping."""
        if not tag:
            return ProcessingMode.FULL
        
        clean_tag = tag.lower().strip()
        if clean_tag in self.TAG_TO_MODE:
            return self.TAG_TO_MODE[clean_tag]
    
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
            
            # Step 2: Extract location information using in-memory data
            self.logger.info("Step 2: Extracting location information...")
            location_command = ExtractLocationCommand(self.options)
            location_result = location_command.execute_with_data(url, video_result.data)
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
            
            # Clean up processed files
            if video_result and video_result.success and video_result.metadata.get('video_id'):
                video_id = video_result.metadata['video_id']
                if cleanup_video_files(video_id):
                    self.logger.info(f"Cleaned up processed files for video {video_id}")
            
            log_success(self.logger, "Pipeline completed!")
            return results
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            
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
            
            # Get pending URLs
            url_entries = notion_client.get_pending_urls(source_database_id)
            
            if not url_entries:
                self.logger.info("No pending URLs found for today")
                return BatchProcessingResult(
                    total_processed=0,
                    successful=0,
                    failed=0,
                    errors=[]
                )
            
            self.logger.info(f"Processing {len(url_entries)} pending URLs...")
            
            results = {
                "processed": len(url_entries),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            # Process each URL through the pipeline
            for i, entry in enumerate(url_entries, 1):
                url = entry['url']
                page_id = entry['page_id']
                tag = entry.get('tag')
                logger.info(f"Processing URL {i}/{len(url_entries)}: {url} (tag: {tag})")
                
                try:
                    # Determine processing mode from tags
                    processing_mode = self._determine_processing_mode(tag)
                    self.logger.info(f"Processing URL {i}/{len(url_entries)}: {url} (mode: {processing_mode})")
                    
                    # Create URL-specific options with the determined processing mode
                    url_options = PipelineOptions(
                        frame_interval=self.options.frame_interval,
                        max_frames=self.options.max_frames,
                        output_dir=self.options.output_dir,
                        categories=self.options.categories,
                        create_notion_entry=True,
                        database_id=places_database_id,
                        processing_mode=processing_mode
                    )
                    
                    # Create URL-specific orchestrator
                    url_orchestrator = PipelineOrchestrator(url_options)
                    pipeline_results = url_orchestrator.run_single_url(url)
                    
                    # Check if processing was successful
                    video_result = pipeline_results.get('video')
                    location_result = pipeline_results.get('location')
                    notion_result = pipeline_results.get('notion')
                    
                    video_success = video_result and video_result.status == ProcessingStatus.SUCCESS
                    location_success = location_result and location_result.status == ProcessingStatus.SUCCESS
                    notion_success = notion_result and notion_result.status == ProcessingStatus.SUCCESS
                    
                    if video_success and location_success and notion_success:
                        # Update status to 'Completed'
                        notion_client.update_entry_status(page_id, "Completed")
                        results["successful"] += 1
                        log_success(self.logger, f"Successfully processed: {url}")
                    else:
                        # Update status to 'Failed'
                        notion_client.update_entry_status(page_id, "Failed")
                        results["failed"] += 1
                        error_msg = f"Processing failed for: {url}"
                        results["errors"].append(error_msg)
                        self.logger.error(f"{error_msg}")
                        
                except Exception as e:
                    # Update status to 'Failed' on exception
                    notion_client.update_entry_status(page_id, "Failed")
                    results["failed"] += 1
                    error_msg = f"Error processing {url}: {str(e)}"
                    results["errors"].append(error_msg)
                    self.logger.error(f"{error_msg}")
            
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
            log_success(self.logger, f"Successful: {batch_result.successful}")
            if batch_result.failed > 0:
                self.logger.error(f"Failed: {batch_result.failed}")
            else:
                self.logger.info(f"Failed: {batch_result.failed}")
            log_success(self.logger, f"Success rate: {batch_result.success_rate:.1f}%")
            
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
                    rec_text = str(primary_place.recommendations)
                    rec_preview = (rec_text[:MAX_RECOMMENDATION_PREVIEW_LENGTH] + "..." 
                                 if len(rec_text) > MAX_RECOMMENDATION_PREVIEW_LENGTH 
                                 else rec_text)
                    self.logger.info(f"Recommendations: {rec_preview}")
            else:
                self.logger.warning("No places found in location info")
        
        if notion_result and notion_result.success:
            self.logger.info(f"Created {notion_result.entries_created} Notion entries")