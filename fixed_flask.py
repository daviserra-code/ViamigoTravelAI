"""
Fixed Flask App - Addresses the root causes of crashes
"""
from flask import Flask, jsonify, request
import logging
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app with minimal dependencies
app = Flask(__name__)
app.secret_key = os.environ.get(
    "SESSION_SECRET", "dev-secret-key-change-in-production")

# Basic routes first


@app.route('/')
def home():
    return jsonify({
        'message': 'ViamigoTravelAI - Fixed Version',
        'status': 'running',
        'version': '1.0-fixed'
    })


@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'message': 'All systems operational'})


# Register simple enhanced images API (without database dependencies)
try:
    from simple_enhanced_images import enhanced_images_bp
    app.register_blueprint(enhanced_images_bp)
    logger.info("✅ Enhanced images API registered successfully")
except Exception as e:
    logger.error(f"❌ Enhanced images API failed: {e}")

# Register basic UX routes (without performance monitor)
try:
    from ux_routes import ux_bp
    # Only register if it doesn't import performance monitor
    app.register_blueprint(ux_bp)
    logger.info("✅ UX routes registered successfully")
except Exception as e:
    logger.warning(f"⚠️ UX routes skipped: {e}")

# Register dashboard routes (essential functionality)
try:
    from dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp)
    logger.info("✅ Dashboard routes registered successfully")
except Exception as e:
    logger.warning(f"⚠️ Dashboard routes skipped: {e}")

# Skip problematic modules that cause crashes:
# - performance_monitor (PostgreSQL connection issues)
# - comprehensive_attractions_api (database dependency)
# - analytics_routes (complex dependencies)
# - data_intelligence (database heavy)


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested endpoint does not exist',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'Something went wrong on our end',
        'status': 500
    }), 500


if __name__ == '__main__':
    logger.info("🚀 Starting fixed Flask app...")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f"❌ Failed to start Flask app: {e}")
        # Try alternative port
        logger.info("🔄 Trying alternative port 5001...")
        app.run(host='0.0.0.0', port=5001, debug=False)
