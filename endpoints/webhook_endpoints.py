"""
Webhook endpoints for handling Notion webhook requests
"""

from typing import Dict, Any
from flask import Blueprint, request, jsonify
from models.webhook_models import NotionWebhookPayload, NotionWebhookEvent, WebhookResponse
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
        logger.info(f"Raw request data: {request.data.decode('utf-8', errors='replace')}")
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
                '/webhook/notion-event - POST - Process Notion webhook event',
                '/webhook/debug - POST/GET - Debug webhook data logging',
                '/webhook/health - GET - Health check',
                '/webhook/status - GET - Service status'
            ]
        }
    )
    return jsonify(response.to_dict()), 200


def is_notion_webhook_event(data: Dict[str, Any]) -> bool:
    """Check if the data matches Notion webhook event structure"""
    required_fields = ['id', 'timestamp', 'type', 'entity']
    return all(field in data for field in required_fields)


@webhook_bp.route('/webhook/notion-event', methods=['POST'])
def process_notion_webhook_event():
    """Process a full Notion webhook event from automation"""
    endpoint_handler = WebhookEndpoints()
    
    try:
        logger.info(f"Raw Notion webhook data: {request.data.decode('utf-8', errors='replace')}")
        
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
        logger.info(f"Received Notion webhook event data: {data}")
        
        if not data:
            response = WebhookResponse(
                success=False,
                message="No JSON data provided",
                error="Empty request body"
            )
            return jsonify(response.to_dict()), 400
        
        # Validate Notion webhook event structure
        if not is_notion_webhook_event(data):
            response = WebhookResponse(
                success=False,
                message="Invalid Notion webhook event structure",
                error="Missing required fields: id, timestamp, type, entity"
            )
            return jsonify(response.to_dict()), 400
        
        # Create webhook event from request data
        webhook_event = NotionWebhookEvent.from_dict(data)
        
        # Log incoming event
        endpoint_handler.logger.info(f"Received Notion webhook event: ID={webhook_event.id}, Type={webhook_event.type}")
        
        # Process the webhook event
        result = endpoint_handler.processor.process_notion_webhook_event(webhook_event)
        
        if result['success']:
            response = WebhookResponse(
                success=True,
                message=result['message'],
                data={
                    'processing_type': result.get('processing_type'),
                    'results': serialize_results(result.get('results', {}))
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
        endpoint_handler.logger.error(f"Notion webhook event processing error: {e}")
        response = WebhookResponse(
            success=False,
            message="Internal server error",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500


@webhook_bp.route('/webhook/debug', methods=['POST', 'GET'])
def debug_webhook():
    """Debug endpoint that accepts any data format and logs everything"""
    try:
        logger.info("=== DEBUG WEBHOOK CALLED ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Raw data: {request.data.decode('utf-8', errors='replace')}")
        
        if request.is_json:
            data = request.get_json()
            logger.info(f"JSON data: {data}")
        else:
            logger.info("Request is not JSON")
            
        if request.form:
            logger.info(f"Form data: {dict(request.form)}")
            
        logger.info("=== END DEBUG ===")
        
        response = WebhookResponse(
            success=True,
            message="Debug data logged successfully",
            data={
                'method': request.method,
                'content_type': request.content_type,
                'headers': dict(request.headers),
                'has_json': request.is_json,
                'data_received': True
            }
        )
        return jsonify(response.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Debug webhook error: {e}")
        response = WebhookResponse(
            success=False,
            message="Debug endpoint error",
            error=str(e)
        )
        return jsonify(response.to_dict()), 500