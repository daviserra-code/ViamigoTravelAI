#!/usr/bin/env python3
"""
Robust startup script for ViamigoTravelAI
Handles graceful startup, error recovery, and process management
"""

import os
import sys
import signal
import logging
from datetime import datetime

# Configure robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('viamigo.log')
    ]
)
logger = logging.getLogger(__name__)


def signal_handler(signum, frame):
    """Handle graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    """Main startup function with error handling"""
    try:
        logger.info("🚀 Starting ViamigoTravelAI with robust error handling...")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Import and start the app
        from run import app

        port = int(os.environ.get("PORT", 3000))

        logger.info(f"✅ Starting Flask app on port {port}")
        logger.info(f"🌐 App will be available at http://localhost:{port}")

        # Start with production-ready settings
        app.run(
            host="0.0.0.0",
            port=port,
            debug=False,
            use_reloader=False,  # Disable reloader to prevent conflicts
            threaded=True
        )

    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        logger.error(f"💡 Please check your environment setup and dependencies")
        sys.exit(1)


if __name__ == "__main__":
    main()
