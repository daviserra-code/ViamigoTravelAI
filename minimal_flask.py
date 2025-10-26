"""
Minimal Flask App for Testing - Avoiding Database Issues
"""

from flask import Flask, jsonify, request
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "test-secret-key"

# Import the simple enhanced images API
try:
    from simple_enhanced_images import enhanced_images_bp
    app.register_blueprint(enhanced_images_bp)
    logger.info("✅ Simple Enhanced images API registered successfully")
except ImportError as e:
    logger.error(f"❌ Enhanced images API not available: {e}")


@app.route('/')
def home():
    return jsonify({
        'message': 'ViamigoTravelAI - Minimal Version',
        'status': 'running',
        'available_endpoints': [
            '/api/images/classify',
            '/api/images/batch',
            '/api/images/test'
        ]
    })


@app.route('/test')
def test():
    return jsonify({
        'message': 'Test endpoint working!',
        'status': 'ok'
    })


if __name__ == '__main__':
    logger.info("🚀 Starting minimal Flask app...")
    app.run(host='0.0.0.0', port=5000, debug=False)
