"""
Viamigo - AI-Powered Travel Organizer
Main FastAPI application entry point
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.routes import travel, health
from app.services.chromadb_service import ChromaDBService
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global ChromaDB service instance
chromadb_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global chromadb_service
    
    # Startup
    logger.info("Starting Viamigo Travel Organizer...")
    try:
        chromadb_service = ChromaDBService()
        await chromadb_service.initialize()
        app.state.chromadb_service = chromadb_service
        logger.info("ChromaDB service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Viamigo Travel Organizer...")
    if chromadb_service:
        await chromadb_service.close()

# Create FastAPI application
app = FastAPI(
    title="Viamigo",
    description="AI-Powered Travel Organizer with RAG and LLM Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(travel.router, prefix="/api/v1", tags=["Travel"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Viamigo - Your AI-Powered Travel Organizer",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG,
        log_level="info"
    )
