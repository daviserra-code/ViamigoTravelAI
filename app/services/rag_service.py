"""
RAG (Retrieval Augmented Generation) service for Viamigo
"""

import logging
from typing import List, Dict, Any, Optional
import time
import uuid
from datetime import datetime

from app.config import settings
from app.models import TravelQuery, TravelResponse, TravelRecommendation, RAGQuery, RAGResult
from app.services.chromadb_service import ChromaDBService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class RAGService:
    """RAG service for travel recommendations"""
    
    def __init__(self, chromadb_service: ChromaDBService):
        self.chromadb_service = chromadb_service
        self.llm_service = LLMService()
    
    async def process_travel_query(self, query: TravelQuery) -> TravelResponse:
        """Process travel query using RAG pipeline"""
        start_time = time.time()
        query_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Processing travel query {query_id}: {query.query_text}")
            
            # Step 1: Enhance the query for better retrieval
            enhanced_query = await self.llm_service.enhance_query(query.query_text)
            
            # Step 2: Retrieve relevant documents from ChromaDB
            relevant_docs = await self._retrieve_relevant_documents(enhanced_query, query)
            
            # Step 3: Generate recommendations using LLM with context
            context_documents = [doc.content for doc in relevant_docs]
            recommendations = await self.llm_service.generate_travel_recommendations(
                query, context_documents
            )
            
            # Step 4: Post-process and rank recommendations
            ranked_recommendations = await self._rank_recommendations(
                recommendations, query, relevant_docs
            )
            
            processing_time = time.time() - start_time
            
            response = TravelResponse(
                query_id=query_id,
                recommendations=ranked_recommendations,
                total_results=len(ranked_recommendations),
                processing_time=processing_time,
                generated_at=datetime.now()
            )
            
            logger.info(f"Completed travel query {query_id} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Failed to process travel query {query_id}: {e}")
            raise
    
    async def _retrieve_relevant_documents(
        self, 
        query: str, 
        travel_query: TravelQuery
    ) -> List[RAGResult]:
        """Retrieve relevant documents from ChromaDB"""
        try:
            # Build where clause for filtering
            where_clause = {}
            
            if travel_query.travel_type:
                where_clause["type"] = travel_query.travel_type.value
            
            if travel_query.budget:
                # Map budget ranges to categories
                if travel_query.budget < 1000:
                    budget_category = "low"
                elif travel_query.budget < 3000:
                    budget_category = "medium"
                else:
                    budget_category = "high"
                where_clause["budget"] = budget_category
            
            # Query ChromaDB
            results = await self.chromadb_service.query_documents(
                query=query,
                top_k=settings.TOP_K_RESULTS,
                where=where_clause if where_clause else None
            )
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results 
                if result.similarity_score >= settings.SIMILARITY_THRESHOLD
            ]
            
            logger.info(f"Retrieved {len(filtered_results)} relevant documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve relevant documents: {e}")
            return []
    
    async def _rank_recommendations(
        self,
        recommendations: List[TravelRecommendation],
        query: TravelQuery,
        retrieved_docs: List[RAGResult]
    ) -> List[TravelRecommendation]:
        """Rank and filter recommendations"""
        try:
            # Sort by confidence score
            ranked_recommendations = sorted(
                recommendations, 
                key=lambda x: x.confidence_score, 
                reverse=True
            )
            
            # Apply additional filtering based on query constraints
            filtered_recommendations = []
            
            for rec in ranked_recommendations:
                # Budget filtering
                if query.budget and rec.estimated_cost:
                    if rec.estimated_cost > query.budget * 1.2:  # Allow 20% flexibility
                        continue
                
                # Destination filtering
                if query.destination:
                    if query.destination.lower() not in rec.destination.lower():
                        # Only skip if destination is very specific and doesn't match
                        if len(query.destination) > 3:
                            continue
                
                filtered_recommendations.append(rec)
            
            logger.info(f"Ranked and filtered to {len(filtered_recommendations)} recommendations")
            return filtered_recommendations
            
        except Exception as e:
            logger.error(f"Failed to rank recommendations: {e}")
            return recommendations
    
    async def add_travel_data(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add new travel data to the knowledge base"""
        try:
            from app.models import DocumentChunk
            
            chunks = []
            for doc in documents:
                chunk = DocumentChunk(
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata", {}),
                    chunk_id=doc.get("id")
                )
                chunks.append(chunk)
            
            doc_ids = await self.chromadb_service.add_documents(chunks)
            logger.info(f"Added {len(doc_ids)} travel documents to knowledge base")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to add travel data: {e}")
            raise
    
    async def search_travel_data(self, query: RAGQuery) -> List[RAGResult]:
        """Search travel data in the knowledge base"""
        try:
            results = await self.chromadb_service.query_documents(
                query=query.query,
                top_k=query.top_k or 5
            )
            
            # Filter by similarity threshold
            threshold = query.similarity_threshold or 0.7
            filtered_results = [
                result for result in results 
                if result.similarity_score >= threshold
            ]
            
            logger.info(f"Found {len(filtered_results)} matching travel documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to search travel data: {e}")
            raise
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            stats = await self.chromadb_service.get_collection_stats()
            return {
                "knowledge_base": stats,
                "rag_config": {
                    "chunk_size": settings.CHUNK_SIZE,
                    "chunk_overlap": settings.CHUNK_OVERLAP,
                    "top_k_results": settings.TOP_K_RESULTS,
                    "similarity_threshold": settings.SIMILARITY_THRESHOLD
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {"error": str(e)}
