"""
Simple RAG Helper - Lightweight context retrieval for AI Companion
Queries PostgreSQL cache to get real place data and prevent hallucinations
"""
import os
import json
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
import psycopg2

load_dotenv()
logger = logging.getLogger(__name__)

class SimpleRAGHelper:
    """Lightweight RAG helper using PostgreSQL cache"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    def get_city_context(self, city: str, categories: List[str] = None) -> Dict:
        """
        Get real place data from PostgreSQL cache for a city
        
        Args:
            city: City name (e.g., 'Bergamo', 'Milan', 'Rome')
            categories: List of categories to retrieve (default: all available)
        
        Returns:
            Dictionary with place data organized by category
        """
        if categories is None:
            categories = ['restaurant', 'tourist_attraction', 'hotel', 'cafe', 'museum']
        
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            city_lower = city.lower()
            context = {
                'city': city,
                'categories': {},
                'total_places': 0
            }
            
            for category in categories:
                cache_key = f"{city_lower}_{category}"
                
                cur.execute(
                    "SELECT place_data FROM place_cache WHERE cache_key = %s",
                    (cache_key,)
                )
                
                result = cur.fetchone()
                if result:
                    try:
                        places_data = json.loads(result[0])
                        context['categories'][category] = {
                            'count': len(places_data),
                            'places': places_data[:10]  # Top 10 for context
                        }
                        context['total_places'] += len(places_data)
                        logger.info(f"✅ Retrieved {len(places_data)} {category} for {city}")
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Invalid JSON for {cache_key}")
            
            cur.close()
            conn.close()
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error getting city context for {city}: {e}")
            return {
                'city': city,
                'categories': {},
                'total_places': 0,
                'error': str(e)
            }
    
    def format_context_for_prompt(self, city_context: Dict) -> str:
        """
        Format city context into a prompt-friendly string
        
        Args:
            city_context: Dictionary from get_city_context()
        
        Returns:
            Formatted string for AI prompt injection
        """
        if city_context.get('total_places', 0) == 0:
            return f"⚠️ No cached data available for {city_context.get('city', 'unknown city')}."
        
        lines = [
            f"📍 REAL DATA for {city_context['city']} ({city_context['total_places']} places in database):",
            ""
        ]
        
        for category, data in city_context.get('categories', {}).items():
            count = data.get('count', 0)
            places = data.get('places', [])
            
            if count > 0:
                lines.append(f"**{category.upper()}** ({count} total):")
                
                # List top 5 place names
                for i, place in enumerate(places[:5], 1):
                    name = place.get('name', place.get('title', 'Unknown'))
                    lines.append(f"  {i}. {name}")
                
                lines.append("")
        
        lines.append("⚠️ CRITICAL: Only suggest places from this list or verify they exist in this city!")
        
        return "\n".join(lines)
    
    def get_places_by_category(self, city: str, category: str, limit: int = 5) -> List[Dict]:
        """
        Get specific places by category for recommendations
        
        Args:
            city: City name
            category: Category (restaurant, tourist_attraction, etc.)
            limit: Max number of places to return
        
        Returns:
            List of place dictionaries
        """
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            cache_key = f"{city.lower()}_{category}"
            
            cur.execute(
                "SELECT place_data FROM place_cache WHERE cache_key = %s",
                (cache_key,)
            )
            
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                places_data = json.loads(result[0])
                return places_data[:limit]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting {category} for {city}: {e}")
            return []


# Global instance for easy import
rag_helper = SimpleRAGHelper()


def get_city_context_prompt(city: str, categories: List[str] = None) -> str:
    """
    Convenience function to get formatted context for AI prompts
    
    Usage:
        context = get_city_context_prompt("Bergamo", ["restaurant", "tourist_attraction"])
        prompt = f"{context}\n\nNow generate a Plan B for..."
    """
    city_context = rag_helper.get_city_context(city, categories)
    return rag_helper.format_context_for_prompt(city_context)
