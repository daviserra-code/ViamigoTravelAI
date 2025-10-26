#!/usr/bin/env python3
"""
Minimal test of image routes
"""
from image_storage_routes import image_routes_bp
from flask import Flask
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Create minimal Flask app
app = Flask(__name__)
app.register_blueprint(image_routes_bp)

if __name__ == '__main__':
    print("🧪 Testing image routes on port 8000")
    app.run(host='0.0.0.0', port=8000, debug=True)
