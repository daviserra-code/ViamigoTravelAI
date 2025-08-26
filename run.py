#!/usr/bin/env python3
"""
Entry point for Viamigo application deployment.
This file ensures proper startup for Replit deployments.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from main import app
import uvicorn

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )