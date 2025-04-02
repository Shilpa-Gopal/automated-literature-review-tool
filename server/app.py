from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import spacy
from datetime import datetime, timedelta
from server.models import db
from server.models.user import User
from server.models.project import Project
from server.models.citation import Citation, TrainingSelection
from server.api.auth import auth_api
from server.api.projects import projects_api
from server.api.citations import citations_api
from server.config import Config
from flask_jwt_extended import JWTManager

def create_app(config_class=Config):
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    #CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    jwt = JWTManager(app) # Initialize JWT manager
    
    # Add spaCy model loading
    def load_spacy_model():
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            print("Downloading spaCy model...")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            return spacy.load("en_core_web_sm")
    
    # Load the model
    app.nlp = load_spacy_model()
    
    # Register blueprints
    app.register_blueprint(auth_api, url_prefix='/api/auth')
    app.register_blueprint(projects_api, url_prefix='/api/projects')
    app.register_blueprint(citations_api, url_prefix='/api/citations')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'app': 'Literature Review Assistant API',
            'version': '1.0.0',
            'status': 'running'
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create required directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('exports', exist_ok=True)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
