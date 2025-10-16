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


    def get_hotel_context(self, city: str, min_score: float = 8.0, limit: int = 5) -> Dict:
        """
        PATH C: Get rich hotel data from hotel_reviews table
        
        Args:
            city: City name (e.g., 'Milan', 'Rome')
            min_score: Minimum reviewer score (default: 8.0)
            limit: Max number of hotels to return
        
        Returns:
            Dictionary with top-rated hotels and review highlights
        """
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            query = """
                SELECT 
                    hotel_name,
                    hotel_address,
                    AVG(reviewer_score) as avg_score,
                    COUNT(*) as review_count,
                    STRING_AGG(
                        CASE WHEN LENGTH(positive_review) > 50 
                        THEN positive_review 
                        ELSE NULL END, 
                        ' | ' 
                    ) as highlights,
                    ARRAY_AGG(DISTINCT unnest(tags)) as all_tags
                FROM hotel_reviews
                WHERE city = %s 
                AND reviewer_score >= %s
                GROUP BY hotel_name, hotel_address
                ORDER BY avg_score DESC, review_count DESC
                LIMIT %s
            """
            
            cur.execute(query, (city, min_score, limit))
            hotels = cur.fetchall()
            
            cur.close()
            conn.close()
            
            if not hotels:
                return {
                    'city': city,
                    'hotels': [],
                    'count': 0
                }
            
            hotel_list = []
            for name, address, score, reviews, highlights, tags in hotels:
                hotel_list.append({
                    'name': name,
                    'address': address,
                    'score': round(float(score), 2) if score else 0,
                    'review_count': reviews,
                    'highlights': highlights[:300] if highlights else "",
                    'tags': tags if tags else []
                })
            
            return {
                'city': city,
                'hotels': hotel_list,
                'count': len(hotel_list)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting hotel context for {city}: {e}")
            return {
                'city': city,
                'hotels': [],
                'count': 0,
                'error': str(e)
            }
    
    def format_hotel_context_for_prompt(self, hotel_context: Dict) -> str:
        """
        Format hotel context for AI prompts with rich review data
        
        Args:
            hotel_context: Dictionary from get_hotel_context()
        
        Returns:
            Formatted string for AI prompt injection
        """
        if hotel_context.get('count', 0) == 0:
            return f"⚠️ No hotel data available for {hotel_context.get('city', 'unknown city')}."
        
        lines = [
            f"🏨 REAL HOTELS for {hotel_context['city']} (with verified reviews):",
            ""
        ]
        
        for i, hotel in enumerate(hotel_context.get('hotels', []), 1):
            lines.append(f"{i}. **{hotel['name']}** ({hotel['score']}/10)")
            lines.append(f"   📍 {hotel['address']}")
            lines.append(f"   ⭐ {hotel['review_count']} reviews")
            
            if hotel.get('highlights'):
                highlight_preview = hotel['highlights'][:150]
                lines.append(f"   💬 \"{highlight_preview}...\"")
            
            if hotel.get('tags'):
                tags_str = ", ".join(hotel['tags'][:5])
                lines.append(f"   🏷️ {tags_str}")
            
            lines.append("")
        
        lines.append("⚠️ CRITICAL: Only suggest these hotels - they have verified reviews!")
        
        return "\n".join(lines)


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


def get_hotel_context_prompt(city: str, min_score: float = 8.0, limit: int = 5) -> str:
    """
    PATH C: Get formatted hotel context with rich reviews
    
    Usage:
        hotel_context = get_hotel_context_prompt("Milan", min_score=8.5, limit=3)
        prompt = f"{hotel_context}\n\nSuggest hotels near..."
    """
    hotel_context = rag_helper.get_hotel_context(city, min_score, limit)
    return rag_helper.format_hotel_context_for_prompt(hotel_context)

