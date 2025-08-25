"""
Health check routes for Viamigo
"""

import logging
from fastapi import APIRouter, Request
from datetime import datetime

from app.models import HealthResponse
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint"""
    try:
        services_status = {}
        
        # Check ChromaDB service
        try:
            chromadb_service = request.app.state.chromadb_service
            stats = await chromadb_service.get_collection_stats()
            services_status["chromadb"] = "healthy" if stats.get("status") == "healthy" else "unhealthy"
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            services_status["chromadb"] = "unhealthy"
        
        # Check LLM service
        try:
            if settings.OPENAI_API_KEY:
                services_status["llm"] = "configured"
            else:
                services_status["llm"] = "not_configured"
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            services_status["llm"] = "unhealthy"
        
        # Overall status
        overall_status = "healthy" if all(
            status in ["healthy", "configured"] for status in services_status.values()
        ) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version="1.0.0",
            services=services_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0",
            services={"error": str(e)}
        )

@router.get("/health/ready")
async def readiness_check(request: Request):
    """Readiness check endpoint"""
    try:
        # Check if all required services are ready
        chromadb_service = request.app.state.chromadb_service
        
        if not chromadb_service:
            return {"status": "not_ready", "reason": "ChromaDB service not initialized"}
        
        # Check if collection is accessible
        stats = await chromadb_service.get_collection_stats()
        if stats.get("status") != "healthy":
            return {"status": "not_ready", "reason": "ChromaDB collection not accessible"}
        
        return {"status": "ready"}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "reason": str(e)}

@router.get("/health/live")
async def liveness_check():
    """Liveness check endpoint"""
    return {"status": "alive", "timestamp": datetime.now()}
