"""
ViamigoTravelAI - Intelligent Detail Handler
Scalable detail generation using database + AI + web scraping
"""

import logging
import re
import psycopg2
import os
from typing import Dict, Optional, List
from models import db, PlaceCache
from apify_integration import ApifyTravelIntegration
import requests
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


class IntelligentDetailHandler:
    """
    Scalable detail generation system that:
    1. First queries PostgreSQL comprehensive_attractions table
    2. Uses cached PlaceCache data
    3. Falls back to Apify for real-time data
    4. Uses AI-powered content generation as last resort
    """

    def __init__(self):
        self.apify = ApifyTravelIntegration()

    def get_details(self, context: str, user_data: Optional[Dict] = None) -> Dict:
        """
        Get detailed information using intelligent multi-stage approach
        """
        try:
            # Extract location information from context
            location_info = self._extract_location_info(context)

            # Stage 1: PostgreSQL Database Lookup
            db_result = self._query_database(location_info)
            if db_result and db_result.get('confidence', 0) >= 0.8:
                return self._format_detail_response(db_result, 'database')

            # Stage 2: PlaceCache Lookup
            cache_result = self._query_place_cache(location_info)
            if cache_result and cache_result.get('confidence', 0) >= 0.7:
                return self._format_detail_response(cache_result, 'cache')

            # Stage 3: Hardcoded/Heuristics (for major tourist attractions)
            heuristic_result = self._query_hardcoded_attractions(location_info)
            if heuristic_result and heuristic_result.get('confidence', 0) >= 0.8:
                # Cache hardcoded results for future use
                self._cache_heuristic_result(location_info, heuristic_result)
                return self._format_detail_response(heuristic_result, 'hardcoded')

            # Stage 4: Apify Real-time Data (EXPENSIVE - LAST RESORT)
            logger.warning(
                f"💰 EXPENSIVE APIFY CALL for {location_info.get('name', 'unknown')} - DB/cache/hardcoded failed")
            if self.apify.is_available():
                apify_result = self._query_apify_details(location_info)
                if apify_result and apify_result.get('confidence', 0) >= 0.6:
                    # IMPORTANT: Cache Apify results immediately to avoid future expensive calls
                    self._cache_apify_result(location_info, apify_result)
                    return self._format_detail_response(apify_result, 'apify')

            # Stage 5: AI-powered content generation
            ai_result = self._generate_ai_content(location_info, user_data)
            if ai_result:
                return self._format_detail_response(ai_result, 'ai')

            # Stage 5: Basic fallback
            return self._generate_basic_response(location_info)

        except Exception as e:
            logger.error(f"❌ Detail generation error: {e}")
            return self._generate_basic_response({'name': context})

    def _extract_location_info(self, context: str) -> Dict:
        """Extract location information from context string"""
        context_lower = context.lower()

        # Extract city
        city = self._extract_city_from_context(context_lower)

        # Extract attraction/place name
        name = self._clean_context_for_name(context)

        # Extract type (museum, restaurant, etc.)
        place_type = self._extract_place_type(context_lower)

        return {
            'name': name,
            'city': city,
            'type': place_type,
            'original_context': context
        }

    def _query_database(self, location_info: Dict) -> Optional[Dict]:
        """Query comprehensive_attractions PostgreSQL table"""
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return None

            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            cursor = conn.cursor()

            name = location_info.get('name', '')
            city = location_info.get('city', '')

            # Build flexible search query
            search_conditions = []
            params = []

            if name:
                search_conditions.append("LOWER(name) ILIKE %s")
                params.append(f"%{name.lower()}%")

            if city:
                search_conditions.append("LOWER(city) ILIKE %s")
                params.append(f"%{city.lower()}%")

            if not search_conditions:
                conn.close()
                return None

            query = f"""
                SELECT name, city, category, description, latitude, longitude, 
                       image_url, wikidata_id
                FROM comprehensive_attractions 
                WHERE {' AND '.join(search_conditions)}
                ORDER BY 
                    CASE 
                        WHEN LOWER(name) = %s THEN 1
                        WHEN LOWER(name) ILIKE %s THEN 2
                        WHEN LOWER(city) = %s THEN 3
                        ELSE 4
                    END
                LIMIT 5
            """

            # Add exact match parameters for ordering
            params.extend([name.lower() if name else '',
                          f"%{name.lower()}%" if name else '', city.lower() if city else ''])

            cursor.execute(query, params)
            results = cursor.fetchall()

            if results:
                result = results[0]  # Take best match
                name, city, category, description, lat, lng, image_url, wikidata_id = result

                # Calculate confidence
                confidence = self._calculate_database_confidence(
                    location_info, name, city)

                conn.close()
                return {
                    'name': name,
                    'city': city,
                    'category': category,
                    'description': description or self._generate_basic_description(name, city, category),
                    'coordinates': {'lat': lat, 'lng': lng} if lat and lng else None,
                    'image_url': image_url,
                    'wikidata_id': wikidata_id,
                    'website_url': None,  # Not available in current schema
                    'opening_hours': None,  # Not available in current schema
                    'confidence': confidence,
                    'details': self._enrich_with_category_details(name, city, category)
                }

            conn.close()
            return None

        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
            return None

    def _query_place_cache(self, location_info: Dict) -> Optional[Dict]:
        """Query PlaceCache for cached attraction data"""
        try:
            # Import Flask app to get context
            from flask_app import app

            with app.app_context():
                name = location_info['name']
                city = location_info['city']

                # Try different cache key variations
                cache_keys = []
                if name and city:
                    cache_keys.append(f"{name}_{city}")
                    cache_keys.append(f"{city}_{name}")
                if name:
                    cache_keys.append(name)

                for cache_key in cache_keys:
                    cached = PlaceCache.query.filter(
                        PlaceCache.cache_key.ilike(f"%{cache_key}%")
                    ).first()

                    if cached:
                        cached.update_access()  # Update access statistics
                        db.session.commit()

                        place_data = cached.get_place_data()
                        if place_data:
                            return {
                                'name': place_data.get('name', cached.place_name),
                                'city': place_data.get('city', cached.city),
                                'description': place_data.get('description', ''),
                                'category': place_data.get('category', 'attraction'),
                                'coordinates': place_data.get('coordinates'),
                                'image_url': place_data.get('image_url'),
                                'confidence': 0.7,
                                'details': place_data.get('details', {}),
                                'cache_info': {
                                    'access_count': cached.access_count,
                                    'last_accessed': cached.last_accessed,
                                    'priority': cached.priority_level
                                }
                            }

                return None

        except Exception as e:
            logger.error(f"❌ Cache query error: {e}")
            return None

    def _query_apify_details(self, location_info: Dict) -> Optional[Dict]:
        """Query Apify for detailed attraction information"""
        try:
            if not self.apify.is_available():
                return None

            city = location_info['city']
            name = location_info['name']

            if not city:
                return None

            # Get attractions for the city using the correct method
            apify_results = self.apify.get_authentic_places(
                city, ['tourist_attraction'])
            attractions = apify_results.get(
                'tourist_attraction', []) if apify_results else []

            # Find matching attraction
            best_match = None
            best_score = 0

            for attraction in attractions:
                score = self._calculate_apify_match_score(
                    location_info, attraction)
                if score > best_score:
                    best_score = score
                    best_match = attraction

            if best_match and best_score >= 0.5:
                return {
                    'name': best_match.get('name', name),
                    'city': city,
                    'description': best_match.get('description', ''),
                    'category': best_match.get('category', 'attraction'),
                    'coordinates': best_match.get('coordinates'),
                    'image_url': best_match.get('image_url'),
                    'website_url': best_match.get('website'),
                    'rating': best_match.get('rating'),
                    'confidence': best_score,
                    'details': self._extract_apify_details(best_match)
                }

            return None

        except Exception as e:
            logger.error(f"❌ Apify query error: {e}")
            return None

    def _generate_ai_content(self, location_info: Dict, user_data: Optional[Dict] = None) -> Optional[Dict]:
        """Generate AI-powered content for the attraction"""
        try:
            name = location_info['name']
            city = location_info['city']
            place_type = location_info.get('type', 'attraction')

            # Use AI content generation (integrate with your existing AI systems)
            description = self._generate_ai_description(
                name, city, place_type, user_data)
            details = self._generate_ai_details(name, city, place_type)

            return {
                'name': name,
                'city': city,
                'description': description,
                'category': place_type,
                'confidence': 0.6,
                'details': details,
                'ai_generated': True
            }

        except Exception as e:
            logger.error(f"❌ AI content generation error: {e}")
            return None

    def _generate_basic_response(self, location_info: Dict) -> Dict:
        """Generate basic fallback response"""
        name = location_info.get('name', 'Unknown Location')
        city = location_info.get('city', 'Unknown City')

        return {
            "success": True,
            "title": name,
            "description": f"Explore {name} in {city}. This beautiful location offers unique experiences for visitors.",
            "city": city,
            "category": "attraction",
            "confidence": 0.3,
            "source": "basic_fallback",
            "details": {
                "type": "General Information",
                "tips": ["Plan your visit in advance", "Check opening hours", "Bring comfortable shoes"],
                "highlights": [f"Beautiful views in {city}", "Rich cultural heritage", "Photo opportunities"]
            }
        }

    def _format_detail_response(self, data: Dict, source: str) -> Dict:
        """Format the response in the expected structure"""
        return {
            "success": True,
            "title": data.get('name', 'Unknown'),
            "description": data.get('description', 'No description available'),
            "city": data.get('city', 'Unknown'),
            "category": data.get('category', 'attraction'),
            "confidence": data.get('confidence', 0.5),
            "source": source,
            "coordinates": data.get('coordinates'),
            "image_url": data.get('image_url'),
            "website_url": data.get('website_url'),
            "wikidata_id": data.get('wikidata_id'),
            "opening_hours": data.get('opening_hours'),
            "rating": data.get('rating'),
            "details": data.get('details', {}),
            "ai_generated": data.get('ai_generated', False),
            "cache_info": data.get('cache_info')
        }

    # Helper methods
    def _extract_city_from_context(self, context_lower: str) -> Optional[str]:
        """Extract city from context with reverse lookup fallback"""
        italian_cities = [
            'roma', 'rome', 'milano', 'milan', 'napoli', 'naples', 'torino', 'turin',
            'firenze', 'florence', 'genova', 'genoa', 'bologna', 'venezia', 'venice',
            'palermo', 'catania', 'bari', 'messina', 'verona', 'padova', 'trieste'
        ]

        # First: Try direct city name match
        for city in italian_cities:
            if city in context_lower:
                return city

        # Second: Reverse lookup - find city from attraction name in database
        city_from_db = self._find_city_by_attraction_name(context_lower)
        if city_from_db:
            return city_from_db

        return None

    def _find_city_by_attraction_name(self, context_lower: str) -> Optional[str]:
        """Reverse lookup: find city by searching attraction name in place_cache and comprehensive_attractions"""
        try:
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return None

            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()

            # Try place_cache first (fastest, most accurate)
            cursor.execute("""
                SELECT city FROM place_cache 
                WHERE LOWER(place_name) ILIKE %s 
                   OR LOWER(cache_key) ILIKE %s
                LIMIT 1
            """, (f"%{context_lower}%", f"%{context_lower}%"))

            result = cursor.fetchone()
            if result and result[0]:
                conn.close()
                logger.info(
                    f"🔍 Reverse lookup (place_cache) found city: {result[0]} for {context_lower}")
                return result[0].lower()

            # Fallback: Try comprehensive_attractions
            cursor.execute("""
                SELECT city FROM comprehensive_attractions 
                WHERE LOWER(name) ILIKE %s 
                LIMIT 1
            """, (f"%{context_lower}%",))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                logger.info(
                    f"🔍 Reverse lookup (comprehensive_attractions) found city: {result[0]} for {context_lower}")
                return result[0].lower()

            return None

        except Exception as e:
            logger.error(f"❌ Reverse lookup error: {e}")
            return None

    def _clean_context_for_name(self, context: str) -> str:
        """Clean context to extract attraction name"""
        # Remove common suffixes and prefixes
        cleaned = re.sub(r'_(roma|milano|napoli|torino|firenze|genova|bologna|venezia|palermo)$',
                         '', context, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(visit|explore|see|discover)_',
                         '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace('_', ' ').title()
        return cleaned

    def _extract_place_type(self, context_lower: str) -> str:
        """Extract place type from context"""
        if any(word in context_lower for word in ['museum', 'museo', 'gallery', 'galleria']):
            return 'museum'
        elif any(word in context_lower for word in ['church', 'chiesa', 'basilica', 'cathedral', 'duomo']):
            return 'religious'
        elif any(word in context_lower for word in ['palace', 'palazzo', 'castle', 'castello']):
            return 'historic'
        elif any(word in context_lower for word in ['park', 'parco', 'garden', 'giardino']):
            return 'park'
        elif any(word in context_lower for word in ['restaurant', 'ristorante', 'trattoria', 'pizzeria']):
            return 'restaurant'
        else:
            return 'attraction'

    def _calculate_database_confidence(self, location_info: Dict, db_name: str, db_city: str) -> float:
        """Calculate confidence for database match"""
        name = location_info.get('name', '').lower()
        city = location_info.get('city', '').lower()

        name_match = 0
        if name and db_name:
            if name == db_name.lower():
                name_match = 1.0
            elif name in db_name.lower() or db_name.lower() in name:
                name_match = 0.8
            else:
                # Word overlap
                name_words = set(name.split())
                db_name_words = set(db_name.lower().split())
                overlap = len(name_words & db_name_words)
                if overlap > 0:
                    name_match = overlap / \
                        max(len(name_words), len(db_name_words))

        city_match = 0
        if city and db_city:
            if city == db_city.lower():
                city_match = 1.0
            elif city in db_city.lower() or db_city.lower() in city:
                city_match = 0.8

        return (name_match * 0.7 + city_match * 0.3)

    def _calculate_apify_match_score(self, location_info: Dict, attraction: Dict) -> float:
        """Calculate match score for Apify attraction"""
        name = location_info.get('name', '').lower()
        attraction_name = attraction.get('name', '').lower()

        if not name or not attraction_name:
            return 0

        # Exact match
        if name == attraction_name:
            return 1.0

        # Substring match
        if name in attraction_name or attraction_name in name:
            return 0.8

        # Word overlap
        name_words = set(name.split())
        attraction_words = set(attraction_name.split())
        overlap = len(name_words & attraction_words)

        if overlap > 0:
            return overlap / max(len(name_words), len(attraction_words))

        return 0

    def _enrich_with_category_details(self, name: str, city: str, category: str) -> Dict:
        """Add category-specific details"""
        details = {}

        if category == 'museum':
            details = {
                "type": "Museum",
                "tips": ["Check for special exhibitions", "Consider audio guides", "Photography rules may apply"],
                "typical_visit": "2-3 hours"
            }
        elif category == 'church' or category == 'religious':
            details = {
                "type": "Religious Site",
                "tips": ["Dress modestly", "Respect religious services", "Free entry typically"],
                "typical_visit": "30-60 minutes"
            }
        elif category == 'park':
            details = {
                "type": "Park/Garden",
                "tips": ["Best visited in good weather", "Great for photos", "Bring water"],
                "typical_visit": "1-2 hours"
            }
        else:
            details = {
                "type": "Attraction",
                "tips": ["Check opening hours", "Book tickets in advance if popular"],
                "typical_visit": "1-2 hours"
            }

        return details

    def _generate_basic_description(self, name: str, city: str, category: str) -> str:
        """Generate basic description based on category"""
        category_descriptions = {
            'museum': f"{name} is an important museum in {city}, showcasing significant cultural and historical collections.",
            'church': f"{name} is a beautiful religious building in {city}, representing important architectural and spiritual heritage.",
            'park': f"{name} is a lovely green space in {city}, perfect for relaxation and enjoying nature.",
            'palace': f"{name} is a magnificent palace in {city}, displaying remarkable architecture and historical significance.",
            'attraction': f"{name} is a notable attraction in {city}, offering visitors unique experiences and insights into local culture."
        }

        return category_descriptions.get(category, f"{name} is an interesting place to visit in {city}.")

    def _extract_apify_details(self, attraction: Dict) -> Dict:
        """Extract detailed information from Apify result"""
        return {
            "type": attraction.get('category', 'Attraction'),
            "rating": attraction.get('rating'),
            "price_level": attraction.get('price_level'),
            "reviews_count": attraction.get('reviews_count'),
            "highlights": attraction.get('highlights', []),
            "amenities": attraction.get('amenities', []),
            "contact": {
                "phone": attraction.get('phone'),
                "website": attraction.get('website'),
                "address": attraction.get('address')
            }
        }

    def _generate_ai_description(self, name: str, city: str, place_type: str, user_data: Optional[Dict] = None) -> str:
        """Generate AI description (integrate with your AI systems)"""
        # Placeholder - integrate with your existing AI content generation
        return f"{name} is a remarkable {place_type} in {city}. This location offers visitors an authentic experience of Italian culture and heritage, with unique features that make it a must-see destination."

    def _generate_ai_details(self, name: str, city: str, place_type: str) -> Dict:
        """Generate AI-powered details"""
        return {
            "type": place_type.title(),
            "ai_insights": [
                f"Popular destination in {city}",
                "Rich cultural significance",
                "Recommended for travelers"
            ],
            "tips": [
                "Plan your visit in advance",
                "Check current opening hours",
                "Consider visiting during less busy times"
            ]
        }

    def _query_hardcoded_attractions(self, location_info: Dict) -> Optional[Dict]:
        """Query hardcoded major tourist attractions"""
        try:
            from simple_enhanced_images import ATTRACTION_IMAGES

            name = location_info.get('name', '').lower()
            city = location_info.get('city', '').lower()

            # Major tourist attractions mapping
            hardcoded_attractions = {
                # Rome
                'colosseo': {
                    'name': 'Colosseo', 'city': 'Roma', 'category': 'historic:amphitheatre',
                    'description': 'The iconic Colosseum, an ancient amphitheatre and symbol of Imperial Rome.',
                    'coordinates': {'lat': 41.8902, 'lng': 12.4922},
                    'website_url': 'https://www.coopculture.it/heritage.cfm?id=402',
                    'opening_hours': 'Daily 8:30-19:00 (varies by season)',
                    'confidence': 0.95
                },
                'colosseum': {
                    'name': 'Colosseum', 'city': 'Roma', 'category': 'historic:amphitheatre',
                    'description': 'The iconic Colosseum, an ancient amphitheatre and symbol of Imperial Rome.',
                    'coordinates': {'lat': 41.8902, 'lng': 12.4922},
                    'website_url': 'https://www.coopculture.it/heritage.cfm?id=402',
                    'opening_hours': 'Daily 8:30-19:00 (varies by season)',
                    'confidence': 0.95
                },
                'piazza navona': {
                    'name': 'Piazza Navona', 'city': 'Roma', 'category': 'tourism:attraction',
                    'description': 'Beautiful baroque piazza with fountains, churches and street artists.',
                    'coordinates': {'lat': 41.8986, 'lng': 12.4731},
                    'website_url': None,
                    'opening_hours': 'Always open',
                    'confidence': 0.9
                },
                'fontana di trevi': {
                    'name': 'Fontana di Trevi', 'city': 'Roma', 'category': 'tourism:attraction',
                    'description': 'The famous Trevi Fountain where visitors throw coins to ensure their return to Rome.',
                    'coordinates': {'lat': 41.9009, 'lng': 12.4833},
                    'website_url': None,
                    'opening_hours': 'Always accessible',
                    'confidence': 0.9
                },
                'pantheon': {
                    'name': 'Pantheon', 'city': 'Roma', 'category': 'historic:monument',
                    'description': 'Ancient Roman temple, now a church, famous for its dome and oculus.',
                    'coordinates': {'lat': 41.8986, 'lng': 12.4768},
                    'website_url': 'https://www.pantheonroma.com/',
                    'opening_hours': 'Mon-Sat 9:00-19:15, Sun 9:00-18:00',
                    'confidence': 0.95
                }
            }

            # Search for matches
            for key, attraction in hardcoded_attractions.items():
                if key in name or any(word in name for word in key.split()):
                    if not city or city in attraction['city'].lower():
                        # Add image URL if available
                        image_key = key.replace(' ', '_').replace(
                            'colosseum', 'colosseo')
                        attraction['image_url'] = ATTRACTION_IMAGES.get(
                            image_key)

                        logger.info(
                            f"✅ Hardcoded match: {attraction['name']} in {attraction['city']}")
                        return attraction

            return None

        except Exception as e:
            logger.error(f"❌ Hardcoded query error: {e}")
            return None

    def _cache_heuristic_result(self, location_info: Dict, result: Dict):
        """Cache heuristic/hardcoded result for future use"""
        try:
            cache_key = f"hardcoded_{location_info['name']}_{location_info['city']}".lower(
            ).replace(' ', '_')

            cached = PlaceCache.query.filter_by(cache_key=cache_key).first()
            if not cached:
                cached = PlaceCache(
                    cache_key=cache_key,
                    place_name=result['name'],
                    city=result['city'],
                    country='Italy',  # Default for Italian attractions
                    place_data=str(result),
                    priority_level='hardcoded'
                )
                db.session.add(cached)

            db.session.commit()
            logger.info(f"💾 Cached hardcoded result: {result['name']}")

        except Exception as e:
            logger.error(f"❌ Hardcoded caching error: {e}")

    def _cache_apify_result(self, location_info: Dict, result: Dict):
        """Cache Apify result for future use"""
        try:
            cache_key = f"{location_info['name']}_{location_info['city']}".lower().replace(
                ' ', '_')

            # Extract country from result or provide default
            # Default to Italy for Italian attractions
            country = result.get('country', 'Italy')

            cached = PlaceCache.query.filter_by(cache_key=cache_key).first()
            if not cached:
                cached = PlaceCache(
                    cache_key=cache_key,
                    place_name=result['name'],
                    city=result['city'],
                    country=country,  # Add required country field
                    place_data=str(result),
                    priority_level='apify'
                )
                db.session.add(cached)
            else:
                cached.place_data = str(result)
                cached.country = country  # Update country field
                cached.last_accessed = datetime.utcnow()

            db.session.commit()
            logger.info(
                f"💾 Cached expensive Apify result: {result['name']} (avoid future costs)")

        except Exception as e:
            logger.error(f"❌ Caching error: {e}")


# Main entry point
def get_intelligent_details(context: str, user_data: Optional[Dict] = None) -> Dict:
    """
    Main entry point for intelligent detail generation
    """
    handler = IntelligentDetailHandler()
    return handler.get_details(context, user_data)
