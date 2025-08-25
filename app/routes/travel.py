"""
Travel-related API routes for Viamigo
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse

from app.models import (
    TravelQuery, TravelResponse, RAGQuery, RAGResult, 
    DocumentChunk, ErrorResponse
)
from app.services.rag_service import RAGService
from app.services.chromadb_service import ChromaDBService
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

def get_rag_service(request: Request) -> RAGService:
    """Dependency to get RAG service"""
    chromadb_service = request.app.state.chromadb_service
    return RAGService(chromadb_service)

@router.post("/travel/recommendations", response_model=TravelResponse)
async def get_travel_recommendations(
    query: TravelQuery,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get AI-powered travel recommendations"""
    try:
        logger.info(f"Received travel query: {query.query_text}")
        
        # Validate query
        if not query.query_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query text cannot be empty"
            )
        
        # Process query using RAG
        response = await rag_service.process_travel_query(query)
        
        if not response.recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No travel recommendations found for your query"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing travel query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate travel recommendations"
        )

@router.post("/travel/search", response_model=List[RAGResult])
async def search_travel_data(
    query: RAGQuery,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Search travel data in the knowledge base"""
    try:
        logger.info(f"Searching travel data: {query.query}")
        
        if not query.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        results = await rag_service.search_travel_data(query)
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching travel data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search travel data"
        )

@router.post("/travel/data", response_model=Dict[str, Any])
async def add_travel_data(
    documents: List[Dict[str, Any]],
    rag_service: RAGService = Depends(get_rag_service)
):
    """Add new travel data to the knowledge base"""
    try:
        logger.info(f"Adding {len(documents)} travel documents")
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents provided"
            )
        
        # Validate document structure
        for doc in documents:
            if "content" not in doc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Each document must have a 'content' field"
                )
        
        doc_ids = await rag_service.add_travel_data(documents)
        
        return {
            "message": f"Successfully added {len(doc_ids)} travel documents",
            "document_ids": doc_ids,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding travel data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add travel data"
        )

@router.get("/travel/stats", response_model=Dict[str, Any])
async def get_travel_stats(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get travel knowledge base statistics"""
    try:
        stats = await rag_service.get_knowledge_base_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting travel stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get travel statistics"
        )

@router.get("/travel/destinations", response_model=List[str])
async def get_popular_destinations(
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get list of popular travel destinations"""
    try:
        # Search for destinations in the knowledge base
        query = RAGQuery(query="popular travel destinations", top_k=20, similarity_threshold=0.5)
        results = await rag_service.search_travel_data(query)
        
        # Extract unique destinations from metadata
        destinations = set()
        for result in results:
            if "destination" in result.metadata:
                destinations.add(result.metadata["destination"])
        
        return sorted(list(destinations))
        
    except Exception as e:
        logger.error(f"Error getting popular destinations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular destinations"
        )

@router.get("/travel/types", response_model=List[str])
async def get_travel_types():
    """Get available travel types"""
    from app.models import TravelType
    return [travel_type.value for travel_type in TravelType]

