#!/usr/bin/env python3
"""
Wandr Webhook Service
Flask web server for handling Notion webhook requests
"""

import os
from flask import Flask, jsonify
from endpoints.webhook_endpoints import webhook_bp
from utils.logging_config import setup_logging
from utils.config import config

# Setup logging
logger = setup_logging(level="INFO", log_file="wandr-webhook.log", console_output=True, logger_name=__name__)


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(webhook_bp)
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found',
            'error': 'The requested endpoint does not exist'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error': 'The requested method is not allowed for this endpoint'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': 'An unexpected error occurred'
        }), 500
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'success': True,
            'message': 'Wandr Webhook Service',
            'data': {
                'service': 'wandr-webhook-service',
                'version': '1.0.0',
                'description': 'Webhook service for processing TikTok videos from Notion',
                'endpoints': {
                    '/webhook/process': 'POST - Process webhook request',
                    '/webhook/health': 'GET - Health check',
                    '/webhook/status': 'GET - Service status'
                }
            }
        }), 200
    
    return app


def main():
    """Main entry point for the webhook service"""
    app = create_app()
    
    # Get configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Wandr Webhook Service on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    # Start the Flask development server
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()