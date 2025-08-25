"""
LLM service for AI-powered travel recommendations
"""

import json
import logging
from typing import Dict, Any, List, Optional
import os
from openai import OpenAI

from app.config import settings
from app.models import TravelQuery, TravelRecommendation

logger = logging.getLogger(__name__)

class LLMService:
    """LLM service for generating travel recommendations"""
    
    def __init__(self):
        self.openai_client = None
        self.provider = settings.DEFAULT_LLM_PROVIDER
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            if settings.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not found")
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM clients: {e}")
    
    async def generate_travel_recommendations(
        self, 
        query: TravelQuery, 
        context_documents: Optional[List[str]] = None
    ) -> List[TravelRecommendation]:
        """Generate travel recommendations using LLM"""
        try:
            if not self.openai_client:
                raise Exception("No LLM client available")
            
            # Prepare context
            context = self._prepare_context(query, context_documents)
            
            # Generate recommendations using OpenAI
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse response
            response_content = response.choices[0].message.content
            if response_content:
                result = json.loads(response_content)
                recommendations = self._parse_recommendations(result)
            else:
                recommendations = []
            
            logger.info(f"Generated {len(recommendations)} travel recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate travel recommendations: {e}")
            raise
    
    def _prepare_context(self, query: TravelQuery, context_documents: Optional[List[str]] = None) -> str:
        """Prepare context for LLM"""
        context_parts = []
        
        # Add query information
        context_parts.append("Travel Query:")
        context_parts.append(f"- Query: {query.query_text}")
        
        if query.destination:
            context_parts.append(f"- Destination: {query.destination}")
        
        if query.travel_type:
            context_parts.append(f"- Travel Type: {query.travel_type}")
        
        if query.budget:
            context_parts.append(f"- Budget: ${query.budget}")
        
        if query.duration:
            context_parts.append(f"- Duration: {query.duration} days")
        
        if query.start_date:
            context_parts.append(f"- Start Date: {query.start_date}")
        
        if query.end_date:
            context_parts.append(f"- End Date: {query.end_date}")
        
        if query.interests:
            context_parts.append(f"- Interests: {', '.join(query.interests)}")
        
        if query.group_size:
            context_parts.append(f"- Group Size: {query.group_size}")
        
        # Add context documents from RAG
        if context_documents:
            context_parts.append("\nRelevant Travel Information:")
            for i, doc in enumerate(context_documents, 1):
                context_parts.append(f"{i}. {doc}")
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for travel recommendations"""
        return """You are Viamigo, an AI travel expert that provides personalized travel recommendations. 
        
        Based on the user's travel query and any relevant travel information provided, generate detailed travel recommendations.
        
        Respond with a JSON object containing an array of recommendations with this structure:
        {
            "recommendations": [
                {
                    "destination": "string",
                    "description": "string",
                    "estimated_cost": number or null,
                    "best_time_to_visit": "string or null",
                    "activities": ["string array"],
                    "accommodations": ["string array"],
                    "local_tips": ["string array"],
                    "confidence_score": number between 0 and 1
                }
            ]
        }
        
        Guidelines:
        - Provide 1-3 recommendations maximum
        - Be specific and detailed in descriptions
        - Include practical information like costs, timing, and activities
        - Base recommendations on the user's preferences and context
        - Assign confidence scores based on how well the recommendation matches the query
        - If budget is mentioned, provide cost estimates in USD
        - Include local tips and cultural insights when relevant
        """
    
    def _parse_recommendations(self, result: Dict[str, Any]) -> List[TravelRecommendation]:
        """Parse LLM response into TravelRecommendation objects"""
        recommendations = []
        
        try:
            if "recommendations" in result:
                for rec_data in result["recommendations"]:
                    recommendation = TravelRecommendation(
                        destination=rec_data.get("destination", "Unknown"),
                        description=rec_data.get("description", ""),
                        estimated_cost=rec_data.get("estimated_cost"),
                        best_time_to_visit=rec_data.get("best_time_to_visit"),
                        activities=rec_data.get("activities", []),
                        accommodations=rec_data.get("accommodations", []),
                        local_tips=rec_data.get("local_tips", []),
                        confidence_score=rec_data.get("confidence_score", 0.5)
                    )
                    recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}")
            # Return a default recommendation if parsing fails
            recommendations = [
                TravelRecommendation(
                    destination="Unknown",
                    description="Unable to generate recommendations. Please try again with a different query.",
                    confidence_score=0.1
                )
            ]
        
        return recommendations
    
    async def enhance_query(self, query_text: str) -> str:
        """Enhance user query for better RAG retrieval"""
        try:
            if not self.openai_client:
                return query_text
            
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,  # the newest OpenAI model is "gpt-5" which was released August 7, 2025. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel query enhancer. Expand the user's travel query to include relevant keywords and synonyms that would help retrieve better travel information. Keep it concise but comprehensive."
                    },
                    {
                        "role": "user",
                        "content": f"Enhance this travel query for better information retrieval: {query_text}"
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            enhanced_query = response.choices[0].message.content or query_text
            logger.info(f"Enhanced query: {enhanced_query}")
            return enhanced_query
            
        except Exception as e:
            logger.error(f"Failed to enhance query: {e}")
            return query_text
