#!/usr/bin/env python3
"""
Entry point for Viamigo application deployment.
This file ensures proper startup for Replit deployments.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app instead of FastAPI
from flask_app import app, create_tables

# Import all routes and blueprints
import routes  # Main routes
import advanced_routes  # Advanced features
from auth_routes import auth_bp
from dashboard_routes import dashboard_bp  
from create_profile_routes import create_profile_bp
from pure_instant_routes import pure_instant_bp
from ai_companion_routes import ai_companion_bp
from advanced_routes import advanced_bp

# Register all blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp)
app.register_blueprint(create_profile_bp)
app.register_blueprint(pure_instant_bp)
app.register_blueprint(ai_companion_bp)
app.register_blueprint(advanced_bp)

if __name__ == "__main__":
    # Create tables after all imports are complete
    create_tables()
    
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Run Flask app (not uvicorn)
    app.run(
        host="0.0.0.0", 
        port=port,
        debug=False  # Production mode
    )