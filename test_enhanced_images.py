#!/usr/bin/env python3
"""
Ultra-minimal Flask app to test enhanced images API
"""
from flask import Flask
import logging

# Disable excessive logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)


@app.route('/')
def home():
    return {'status': 'running', 'message': 'Enhanced Images Test Server'}


# Register only the enhanced images API
try:
    from simple_enhanced_images import enhanced_images_bp
    app.register_blueprint(enhanced_images_bp)
    print("✅ Enhanced images API registered")
except Exception as e:
    print(f"❌ Enhanced images API failed: {e}")
    exit(1)

if __name__ == '__main__':
    print("🚀 Starting Enhanced Images Test Server on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
