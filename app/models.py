"""
Pydantic models for Viamigo application
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum

class TravelType(str, Enum):
    """Travel type enumeration"""
    LEISURE = "leisure"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    FAMILY = "family"
    ROMANTIC = "romantic"
    CULTURAL = "cultural"

class TravelQuery(BaseModel):
    """Travel query request model"""
    destination: Optional[str] = Field(None, description="Destination city or country")
    travel_type: Optional[TravelType] = Field(None, description="Type of travel")
    budget: Optional[float] = Field(None, gt=0, description="Budget in USD")
    duration: Optional[int] = Field(None, gt=0, description="Duration in days")
    start_date: Optional[date] = Field(None, description="Travel start date")
    end_date: Optional[date] = Field(None, description="Travel end date")
    interests: Optional[List[str]] = Field(default=[], description="User interests")
    group_size: Optional[int] = Field(1, gt=0, description="Number of travelers")
    preferences: Optional[Dict[str, Any]] = Field(default={}, description="Additional preferences")
    query_text: str = Field(..., description="Natural language travel query")

class TravelRecommendation(BaseModel):
    """Travel recommendation response model"""
    destination: str
    description: str
    estimated_cost: Optional[float] = None
    best_time_to_visit: Optional[str] = None
    activities: List[str] = []
    accommodations: List[str] = []
    local_tips: List[str] = []
    confidence_score: float = Field(..., ge=0, le=1)

class TravelResponse(BaseModel):
    """Travel query response model"""
    query_id: str
    recommendations: List[TravelRecommendation]
    total_results: int
    processing_time: float
    generated_at: datetime

class DocumentChunk(BaseModel):
    """Document chunk for RAG processing"""
    content: str
    metadata: Dict[str, Any] = {}
    chunk_id: Optional[str] = None

class RAGQuery(BaseModel):
    """RAG query model"""
    query: str
    top_k: Optional[int] = Field(5, description="Number of top results to retrieve")
    similarity_threshold: Optional[float] = Field(0.7, description="Minimum similarity threshold")

class RAGResult(BaseModel):
    """RAG query result model"""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    chunk_id: str

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None
