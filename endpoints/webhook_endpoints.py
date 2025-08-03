"""
Webhook endpoints for handling Notion webhook requests
"""

from flask import Blueprint, request, jsonify
from models.webhook_models import NotionWebhookPayload, WebhookResponse
from services.webhook_service.webhook_processor import WebhookProcessor
from utils.logging_config import LoggerMixin, setup_logging

logger = setup_logging(logger_name=__name__)

webhook_bp = Blueprint('webhook', __name__)


def serialize_results(obj):
    """Convert non-serializable objects to JSON-serializable format"""
    if hasattr(obj, 'value'):  # Handle enum objects
        return obj.value
    elif hasattr(obj, '__dict__'):  # Handle custom objects
        return {key: serialize_results(value) for key, value in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {key: serialize_results(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_results(item) for item in obj]
    else:
        return obj


class WebhookEndpoints(LoggerMixin):
    """Webhook endpoint handlers"""
    
    def __init__(self):
        self.processor = WebhookProcessor()


@webhook_bp.route('/webhook/process', methods=['POST'])
def process_webhook():
    """Process a webhook request from Notion"""
    endpoint_handler = WebhookEndpoints()
    
    try:
        # Validate request content type
        if not request.is_json:
            response = WebhookResponse(
                success=False,
                message="Content-Type must be application/json",
                error="Invalid content type"
            )
            return jsonify(response.to_dict()), 400
        
        # Get JSON data
        data = request.get_json()
        logger.info(f"Received webhook data: {data}")
        
        if not data:
            response = WebhookResponse(
                success=False,
                message="No JSON data provided",
                error="Empty request body"
            )
            return jsonify(response.to_dict()), 400
        
        # Validate required fields
        if 'url' not in data:
            response = WebhookResponse(
                success=False,
                message="Missing required field: url",
                error="URL is required"
            )
            return jsonify(response.to_dict()), 400
        
        # Validate URL format
        url = data['url'].strip()
        if not url or not url.startswith(('http://', 'https://')):
            response = WebhookResponse(
                success=False,
                message="Invalid URL format",
                error="URL must be a valid HTTP/HTTPS URL"
            )
            return jsonify(response.to_dict()), 400
        
        # Create payload from request data
        payload = NotionWebhookPayload.from_dict(data)
        
        # Log incoming request
        endpoint_handler.logger.info(f"Received webhook request: URL={payload.url}, Tags={payload.tags}")
        
        # Process the webhook
        result = endpoint_handler.processor.process_webhook_payload(payload)
        
        if result['success']:
            response = WebhookResponse(
                success=True,
                message=result['message'],
                data={
                    'processing_type': result['processing_type'],
                    'results': serialize_results(result['results'])
                }
            )
            return jsonify(response.to_dict()), 200
        else:
            response = WebhookResponse(
                success=False,
                message=result['message'],
                error=result.get('error', 'Processing failed')
            )
            return jsonify(response.to_dict()), 500
            
    except Exception as e:
        endpoint_handler.logger.error(f"Webhook processing error: {e}")
        response = WebhookResponse(
            success=False,
            message="Internal server error",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500


@webhook_bp.route('/webhook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    response = WebhookResponse(
        success=True,
        message="Webhook service is healthy"
    )
    return jsonify(response.to_dict()), 200


@webhook_bp.route('/webhook/status', methods=['GET'])
def status():
    """Status endpoint with service information"""
    response = WebhookResponse(
        success=True,
        message="Webhook service status",
        data={
            'service': 'wandr-webhook-service',
            'version': '1.0.0',
            'supported_processing_types': ['full', 'metadata-only', 'audio-only'],
            'endpoints': [
                '/webhook/process - POST - Process webhook request',
                '/webhook/health - GET - Health check',
                '/webhook/status - GET - Service status'
            ]
        }
    )
    return jsonify(response.to_dict()), 200