#!/bin/bash
# Deployment startup script for Viamigo

# Set default port if not provided
export PORT=${PORT:-5000}

# Start the application
exec python run.py