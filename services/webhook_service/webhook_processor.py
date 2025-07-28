"""
Webhook processing service for handling Notion webhook requests
"""

from typing import Dict, Any
from models.webhook_models import NotionWebhookPayload, ProcessingType
from models.pipeline_models import PipelineOptions, ProcessingMode
from pipeline.orchestrator import PipelineOrchestrator
from utils.logging_config import LoggerMixin, setup_logging
from utils.config import config
from utils.constants import (
    WEBHOOK_WHISPER_MODEL, WEBHOOK_FRAME_INTERVAL, 
    WEBHOOK_MAX_FRAMES, WEBHOOK_OUTPUT_DIR
)

logger = setup_logging(logger_name=__name__)


class WebhookProcessor(LoggerMixin):
    """Processes webhook requests using pipeline orchestrator"""
    
    def __init__(self):
        """Initialize the webhook processor"""
        pass
    
    def process_webhook_payload(self, payload: NotionWebhookPayload) -> Dict[str, Any]:
        """
        Process a webhook payload and execute the appropriate pipeline
        
        Args:
            payload: Validated webhook payload containing URL and tags
            
        Returns:
            Dictionary containing processing results
        """
        self.logger.info(f"Processing webhook for URL: {payload.url}")
        self.logger.info(f"Tags: {payload.tags}")
        
        # Determine processing type
        processing_type = payload.get_processing_type()
        
        self.logger.info(f"Processing type: {processing_type.value}")
        
        try:
            # Since ProcessingType and ProcessingMode are now the same, use directly
            mode = processing_type
            
            # Process using unified pipeline with mode
            results = self._process_with_mode(payload.url, mode)
            
            # Check if any step had errors and raise exception if so
            if 'error' in results:
                raise Exception(results['error'])
            
            return {
                'success': True,
                'processing_type': processing_type.value,
                'results': results,
                'message': f'Successfully processed {payload.url}'
            }
            
        except Exception as e:
            error_msg = f"Failed to process webhook: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'message': f'Failed to process {payload.url}'
            }
    
    def _process_with_mode(self, url: str, mode: ProcessingMode) -> Dict[str, Any]:
        """Process using pipeline orchestrator with specified mode"""
        self.logger.info(f"Processing with mode: {mode.value}")
        
        try:
            # Create pipeline options with the processing mode
            # Only create Notion entry if database_id is configured
            database_id = config.get_notion_places_db_id()
            create_notion_entry = bool(database_id)
            
            options = PipelineOptions(
                url=url,
                categories=[],
                output_dir=WEBHOOK_OUTPUT_DIR,
                create_notion_entry=create_notion_entry,
                database_id=database_id,
                whisper_model=WEBHOOK_WHISPER_MODEL,
                frame_interval=WEBHOOK_FRAME_INTERVAL,
                max_frames=WEBHOOK_MAX_FRAMES,
                processing_mode=mode
            )
            
            # Let the pipeline orchestrator handle all the logic
            orchestrator = PipelineOrchestrator(options)
            results = orchestrator.run_single_url(url)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Processing failed for mode {mode.value}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_type': mode.value
            }