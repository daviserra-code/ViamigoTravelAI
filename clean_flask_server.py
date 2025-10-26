#!/usr/bin/env python3
"""
Clean Flask app launcher without route conflicts
"""

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Simple test route to verify server is running
@app.route('/test')
def test():
    return jsonify({
        "status": "ok", 
        "message": "ViamigoTravelAI Clean Server Running",
        "database_configured": bool(os.getenv('DATABASE_URL'))
    })

# Register intelligent image classifier route
@app.route('/enhanced-images/<city>/<attraction>')
def enhanced_images(city, attraction):
    """Enhanced image classification endpoint"""
    try:
        from intelligent_image_classifier import IntelligentImageClassifier
        classifier = IntelligentImageClassifier()
        result = classifier.classify_image(city, attraction)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Image classification error: {e}")
        return jsonify({"error": str(e)}), 500

# Register intelligent detail handler route
@app.route('/intelligent-details/<context>')
def intelligent_details(context):
    """Intelligent detail generation endpoint"""
    try:
        from intelligent_detail_handler import IntelligentDetailHandler
        with app.app_context():
            handler = IntelligentDetailHandler()
            result = handler.get_intelligent_details(context)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Detail generation error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting ViamigoTravelAI Clean Server...")
    print(f"Database configured: {bool(os.getenv('DATABASE_URL'))}")
    print(f"Server will run on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)