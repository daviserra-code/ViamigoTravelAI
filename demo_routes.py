"""
Demo routes for testing image system
"""
from flask import Blueprint, render_template_string, send_from_directory
import os

demo_bp = Blueprint('demo', __name__)


@demo_bp.route('/demo/images')
def image_demo():
    """Serve the image demo page"""
    try:
        demo_path = os.path.join(os.path.dirname(
            __file__), 'static', 'image_demo.html')
        with open(demo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error loading demo: {e}", 500


@demo_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)
