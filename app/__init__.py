"""
MoodFlix Application Package.
This module initializes the Flask application and registers all components.
"""
from flask import Flask
import datetime
import json
import os

from app.core.config import settings

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling dates and other complex types."""
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

def create_app() -> Flask:
    """
    Factory function that creates and configures the Flask application.
    
    Returns:
        Flask: The configured Flask application
    """
    # Initialize Flask app
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configure app
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['DEBUG'] = settings.DEBUG
    app.json_encoder = CustomJSONEncoder
    
    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix=settings.API_PREFIX)
    
    # Register web routes
    from app.web.routes import web_bp
    app.register_blueprint(web_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Validate settings
    settings.validate()
    
    return app

def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the Flask application.
    
    Args:
        app: The Flask application
    """
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return {'error': 'Internal server error'}, 500
