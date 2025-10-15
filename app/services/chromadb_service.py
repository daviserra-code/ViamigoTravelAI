"""
ChromaDB service for vector storage and retrieval
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import uuid

from app.config import settings
from app.models import DocumentChunk, RAGResult

logger = logging.getLogger(__name__)

class ChromaDBService:
    """ChromaDB service for vector operations"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = "viamigo_travel_data"
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.CHROMADB_PERSIST_DIRECTORY,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Travel data for Viamigo recommendations"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
                # Add some initial travel data
                await self._add_initial_data()
            
            logger.info("ChromaDB service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def _add_initial_data(self):
        """Add initial travel data to the collection"""
        initial_documents = [
            {
                "content": "Paris, France is known for its romantic atmosphere, world-class museums like the Louvre, iconic landmarks such as the Eiffel Tower, and exquisite cuisine. Best visited in spring or fall with moderate weather.",
                "metadata": {"destination": "Paris", "country": "France", "type": "cultural", "budget": "medium"}
            },
            {
                "content": "Tokyo, Japan offers a unique blend of traditional culture and modern technology. Experience cherry blossoms, visit ancient temples, enjoy sushi, and explore vibrant neighborhoods like Shibuya.",
                "metadata": {"destination": "Tokyo", "country": "Japan", "type": "cultural", "budget": "high"}
            },
            {
                "content": "Bali, Indonesia is perfect for tropical relaxation with beautiful beaches, rice terraces, Hindu temples, and affordable luxury resorts. Great for both adventure and leisure travel.",
                "metadata": {"destination": "Bali", "country": "Indonesia", "type": "leisure", "budget": "low"}
            },
            {
                "content": "New York City offers world-class Broadway shows, diverse neighborhoods, iconic skyline, Central Park, and endless dining options. A hub for business and leisure travel.",
                "metadata": {"destination": "New York", "country": "USA", "type": "business", "budget": "high"}
            },
            {
                "content": "Iceland provides stunning natural landscapes including geysers, waterfalls, Northern Lights, and the Blue Lagoon. Perfect for adventure travelers and nature enthusiasts.",
                "metadata": {"destination": "Iceland", "country": "Iceland", "type": "adventure", "budget": "high"}
            }
        ]
        
        documents = []
        metadatas = []
        ids = []
        
        for doc in initial_documents:
            doc_id = str(uuid.uuid4())
            documents.append(doc["content"])
            metadatas.append(doc["metadata"])
            ids.append(doc_id)
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(initial_documents)} initial travel documents")
    
    async def add_documents(self, chunks: List[DocumentChunk]) -> List[str]:
        """Add document chunks to the collection"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for chunk in chunks:
                chunk_id = chunk.chunk_id or str(uuid.uuid4())
                documents.append(chunk.content)
                metadatas.append(chunk.metadata)
                ids.append(chunk_id)
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} documents to ChromaDB")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise
    
    async def query_documents(
        self, 
        query: str, 
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[RAGResult]:
        """Query documents from the collection"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where
            )
            
            rag_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    rag_result = RAGResult(
                        content=doc,
                        metadata=results['metadatas'][0][i] if results['metadatas'][0] else {},
                        similarity_score=1 - results['distances'][0][i] if results['distances'][0] else 0.0,
                        chunk_id=results['ids'][0][i]
                    )
                    rag_results.append(rag_result)
            
            logger.info(f"Retrieved {len(rag_results)} documents for query")
            return rag_results
            
        except Exception as e:
            logger.error(f"Failed to query ChromaDB: {e}")
            raise
    
    async def update_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Update a document in the collection"""
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
            logger.info(f"Updated document {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise
    
    async def delete_document(self, doc_id: str):
        """Delete a document from the collection"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close ChromaDB connection"""
        try:
            if self.client:
                # ChromaDB doesn't require explicit closing for persistent client
                logger.info("ChromaDB service closed")
                
        except Exception as e:
            logger.error(f"Error closing ChromaDB: {e}")
