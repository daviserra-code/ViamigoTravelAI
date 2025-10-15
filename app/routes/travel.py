"""
Travel-related API routes for Viamigo
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
import httpx
import json

from app.models import (
    TravelQuery, TravelResponse, RAGQuery, RAGResult, 
    DocumentChunk, ErrorResponse, TravelType
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

async def get_location_coordinates(location_name: str, city_context: str) -> Dict[str, float]:
    """Get real coordinates for a location using geocoding APIs"""
    try:
        # Database di coordinate locali per luoghi noti
        known_locations = {
            'genova': {
                'piazza de ferrari': {'lat': 44.4071, 'lng': 8.9348},
                'acquario di genova': {'lat': 44.4109, 'lng': 8.9326},
                'palazzo ducale': {'lat': 44.4071, 'lng': 8.9348},
                'teatro carlo felice': {'lat': 44.4076, 'lng': 8.9330},
                'cattedrale di san lorenzo': {'lat': 44.4082, 'lng': 8.9309},
                'palazzo rosso': {'lat': 44.4078, 'lng': 8.9314},
                'palazzo bianco': {'lat': 44.4082, 'lng': 8.9318},
                'spianata castelletto': {'lat': 44.4127, 'lng': 8.9264},
                'mercato orientale': {'lat': 44.4043, 'lng': 8.9380},
                'porto antico': {'lat': 44.4108, 'lng': 8.9279},
                'via del campo': {'lat': 44.4065, 'lng': 8.9298},
                'parchi di nervi': {'lat': 44.3897, 'lng': 8.9834},
                'museo giannettino luxoro': {'lat': 44.3890, 'lng': 8.9840},
                'caffè degli specchi': {'lat': 44.4071, 'lng': 8.9348},
                'lungomare di genova': {'lat': 44.4020, 'lng': 8.9450},
                'corso italia': {'lat': 44.3950, 'lng': 8.9500},
                'boccadasse': {'lat': 44.3945, 'lng': 8.9702},
                'nervi': {'lat': 44.3897, 'lng': 8.9834}
            }
        }
        
        # Normalizza i nomi per la ricerca
        city_key = city_context.lower().strip()
        location_key = location_name.lower().strip()
        
        # Cerca prima nel database locale
        if city_key in known_locations:
            city_locations = known_locations[city_key]
            
            # Match esatto
            if location_key in city_locations:
                coords = city_locations[location_key]
                logger.info(f"Coordinate locali trovate per {location_name}: {coords}")
                return coords
                
            # Match parziale
            for known_location, coords in city_locations.items():
                if known_location in location_key or location_key in known_location:
                    logger.info(f"Coordinate locali (match parziale) per {location_name}: {coords}")
                    return coords
        
        # Fallback: usa OpenStreetMap Nominatim API per geocoding dinamico
        query = f"{location_name}, {city_context}, Italy"
        nominatim_url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(nominatim_url, headers={
                'User-Agent': 'Viamigo/1.0 (travel planning app)'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    coords = {
                        'lat': float(data[0]['lat']),
                        'lng': float(data[0]['lon'])
                    }
                    logger.info(f"Coordinate da Nominatim per {location_name}: {coords}")
                    return coords
        
        # Ultimo fallback: coordinate del centro città
        city_centers = {
            'genova': {'lat': 44.4063, 'lng': 8.9314},
            'milano': {'lat': 45.4642, 'lng': 9.1900},
            'roma': {'lat': 41.9028, 'lng': 12.4964},
            'firenze': {'lat': 43.7696, 'lng': 11.2558}
        }
        
        fallback_coords = city_centers.get(city_key, city_centers['genova'])
        logger.warning(f"Usando coordinate fallback per {location_name}: {fallback_coords}")
        return fallback_coords
        
    except Exception as e:
        logger.error(f"Errore nel geocoding per {location_name}: {e}")
        # Fallback finale: Genova centro
        return {'lat': 44.4063, 'lng': 8.9314}

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

@router.post("/plan")
async def plan_itinerary(
    request: Request,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Create a travel itinerary plan"""
    try:
        body = await request.json()
        start = body.get('start', '')
        end = body.get('end', '')
        
        logger.info(f"Richiesta itinerario: da {start} a {end}")
        
        if not start or not end:
            return JSONResponse(
                status_code=400,
                content={"error": "Start and end locations are required"}
            )
        
        # Create travel query for RAG
        from datetime import date
        # Estrai la città dalla richiesta
        import re
        city_match = re.search(r'genova|milano|roma|firenze|venezia|napoli|torino|palermo|bologna', end.lower())
        destination_city = city_match.group() if city_match else "genova"
        
        query = TravelQuery(
            query_text=f"Pianifica un itinerario dettagliato SOLO a {destination_city.upper()}, Italia da {start} a {end} con orari, trasporti e attrazioni. IMPORTANTE: tutti i luoghi devono essere a {destination_city.upper()}, NON in altre città italiane.",
            destination=f"{destination_city}, Italia",
            travel_type=TravelType.CULTURAL,
            duration=1,
            start_date=date.today(),
            end_date=date.today(),
            interests=["cultura", "storia", "cibo"],
            budget=1500,
            group_size=1
        )
        
        # Get recommendations from RAG
        response = await rag_service.process_travel_query(query)
        
        # Convert recommendations to itinerary format
        itinerary = []
        current_time = 9.0  # Start at 9:00 AM
        
        for i, rec in enumerate(response.recommendations):
            # Add travel time between locations
            if i > 0:
                travel_duration = 0.5  # 30 minutes
                start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
                current_time += travel_duration
                end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
                
                itinerary.append({
                    "time": f"{start_time} - {end_time}",
                    "title": f"Trasferimento verso {rec.destination}",
                    "description": "Spostamento con mezzi pubblici o a piedi",
                    "type": "transport",
                    "context": "walk",
                    "coordinates": await get_location_coordinates(f"Trasferimento {end}", end)
                })
            
            # Add main activity
            activity_duration = 2.0  # 2 hours
            start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            current_time += activity_duration
            end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            
            itinerary.append({
                "time": f"{start_time} - {end_time}",
                "title": rec.destination,
                "description": rec.description,
                "type": "activity",
                "context": "museum",
                "coordinates": await get_location_coordinates(rec.destination, end)
            })
            
            # Add tip occasionally
            if i == 0 and rec.local_tips:
                itinerary.append({
                    "type": "tip",
                    "title": "Consiglio dell'AI",
                    "description": rec.local_tips[0]
                })
        
        return JSONResponse(content={"itinerary": itinerary})
        
    except Exception as e:
        logger.error(f"Error creating itinerary: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to create itinerary"}
        )

@router.post("/get_details")
async def get_location_details(
    request: Request,
    rag_service: RAGService = Depends(get_rag_service)
):
    """Get detailed information about a location or context"""
    try:
        body = await request.json()
        context = body.get('context', '')
        
        logger.info(f"Richiesta dettagli per: {context}")
        
        if not context:
            return JSONResponse(
                status_code=400,
                content={"error": "Context is required"}
            )
        
        # Create query based on context
        if context == "museum":
            query_text = "Informazioni dettagliate sui musei di Genova, orari, prezzi e cosa vedere"
        elif context == "walk":
            query_text = "Consigli per camminare a Genova, percorsi pedonali e trasporti pubblici"
        elif context == "restaurant":
            query_text = "Migliori ristoranti di Genova, specialità locali e prezzi"
        else:
            query_text = f"Informazioni dettagliate su {context} a Genova"
        
        # Use RAG to get detailed information
        from datetime import date
        query = TravelQuery(
            query_text=query_text,
            destination="Genova",
            travel_type=TravelType.CULTURAL,
            duration=1,
            start_date=date.today(),
            end_date=date.today(),
            interests=["informazioni", "dettagli"],
            budget=1000,
            group_size=1
        )
        
        response = await rag_service.process_travel_query(query)
        
        if response.recommendations:
            # Combine information from all recommendations
            content = "\n\n".join([f"• {rec.description}" for rec in response.recommendations[:3]])
            title = "Informazioni Dettagliate"
        else:
            title = "Informazioni"
            content = "Al momento non ho informazioni specifiche disponibili per questa richiesta."
        
        return JSONResponse(content={
            "title": title,
            "content": content
        })
        
    except Exception as e:
        logger.error(f"Error getting details: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get details"}
        )

