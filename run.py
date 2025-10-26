from flask_app import app, create_tables
import routes  # Main routes
import advanced_routes  # Advanced features
from auth_routes import auth_bp
from create_profile_routes import create_profile_bp
from pure_instant_routes import pure_instant_bp
from ai_companion_routes import ai_companion_bp
from advanced_routes import advanced_bp
from dashboard_routes import dashboard_bp
from image_storage_routes import image_routes_bp
from demo_routes import demo_bp
import os
import sys
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

#!/usr/bin/env python3
"""
Entry point for Viamigo application deployment.
This file ensures proper startup for Replit deployments.
"""


# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app instead of FastAPI

# Import all routes and blueprints

# Register all blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
# app.register_blueprint(dashboard_bp)  # Removed duplicate registration
app.register_blueprint(create_profile_bp)
app.register_blueprint(pure_instant_bp)
# app.register_blueprint(ai_companion_bp)  # Removed duplicate registration
app.register_blueprint(advanced_bp)
app.register_blueprint(image_routes_bp)
app.register_blueprint(demo_bp)

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
