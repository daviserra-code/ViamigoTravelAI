"""
ViamigoTravelAI - Intelligent Image Classification System
Scalable, data-driven approach using database + ChromaDB + Apify integration
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from models import db, PlaceCache
from apify_integration import ApifyTravelIntegration
from attraction_classifier import AttractionImageClassifier
import psycopg2
import os

logger = logging.getLogger(__name__)

class IntelligentImageClassifier:
    """
    Scalable image classification system that:
    1. First queries PostgreSQL comprehensive_attractions table
    2. Uses ChromaDB for semantic similarity
    3. Falls back to Apify for missing data
    4. Caches results for performance
    """
    
    def __init__(self):
        self.apify = ApifyTravelIntegration()
        self.legacy_classifier = AttractionImageClassifier()
        
    def classify_image(self, title: str, context: str = "") -> Dict:
        """
        Classify image using intelligent multi-stage approach
        """
        try:
            # Stage 1: PostgreSQL Database Lookup
            db_result = self._query_database(title, context)
            if db_result and db_result.get('classification', {}).get('confidence', 0) >= 0.8:
                return db_result
            
            # Stage 2: Semantic Search with ChromaDB
            semantic_result = self._semantic_search(title, context)
            if semantic_result and semantic_result.get('classification', {}).get('confidence', 0) >= 0.7:
                return semantic_result
                
            # Stage 3: Apify Real-time Data
            if self.apify.is_available():
                apify_result = self._query_apify(title, context)
                if apify_result and apify_result.get('classification', {}).get('confidence', 0) >= 0.6:
                    return apify_result
            
            # Stage 4: Legacy classifier as fallback
            legacy_result = self._legacy_classify(title, context)
            if legacy_result:
                return legacy_result
                
            # Stage 5: Generic response
            return self._generate_generic_response(title, context)
            
        except Exception as e:
            logger.error(f"❌ Image classification error: {e}")
            return self._generate_generic_response(title, context)
    
    def _query_database(self, title: str, context: str) -> Optional[Dict]:
        """Query comprehensive_attractions PostgreSQL table"""
        try:
            # Extract potential city and attraction names
            search_terms = self._extract_search_terms(title, context)
            
            # Connect to PostgreSQL
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return None
                
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Search comprehensive_attractions table
            for term in search_terms:
                query = """
                    SELECT name, city, category, latitude, longitude, image_url, wikidata_id
                    FROM comprehensive_attractions 
                    WHERE 
                        LOWER(name) ILIKE %s 
                        OR LOWER(city) ILIKE %s
                        OR LOWER(category) ILIKE %s
                    ORDER BY 
                        CASE 
                            WHEN LOWER(name) ILIKE %s THEN 1
                            WHEN LOWER(city) ILIKE %s THEN 2  
                            ELSE 3
                        END
                    LIMIT 5
                """
                search_pattern = f"%{term.lower()}%"
                cursor.execute(query, [search_pattern] * 5)
                results = cursor.fetchall()
                
                if results:
                    # Find best match
                    best_match = results[0]  # First result is highest priority
                    name, city, category, lat, lng, image_url, wikidata_id = best_match
                    
                    # Calculate confidence based on match quality
                    confidence = self._calculate_db_confidence(term, name, city)
                    
                    if confidence >= 0.5:
                        conn.close()
                        return {
                            "success": True,
                            "classification": {
                                "attraction": name,
                                "city": city,
                                "category": category,
                                "confidence": confidence
                            },
                            "image_url": image_url or self._get_fallback_image(name, city),
                            "coordinates": {"lat": lat, "lng": lng} if lat and lng else None,
                            "source": "database",
                            "wikidata_id": wikidata_id
                        }
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
            return None
    
    def _semantic_search(self, title: str, context: str) -> Optional[Dict]:
        """Use ChromaDB for semantic similarity search"""
        try:
            # Import ChromaDB modules (only if available)
            try:
                import chromadb
            except ImportError:
                logger.info("ChromaDB not available, skipping semantic search")
                return None
            
            # Check if ChromaDB data exists
            chroma_path = "/workspaces/ViamigoTravelAI/chromadb_data"
            if not os.path.exists(chroma_path):
                return None
            
            # Perform semantic search
            client = chromadb.PersistentClient(path=chroma_path)
            collections = client.list_collections()
            
            if not collections:
                return None
            
            # Search in the first available collection
            collection = collections[0]
            search_query = f"{title} {context}".strip()
            
            results = collection.query(
                query_texts=[search_query],
                n_results=3
            )
            
            if results['documents'] and len(results['documents'][0]) > 0:
                # Get best semantic match
                best_doc = results['documents'][0][0]
                distance = results['distances'][0][0] if results['distances'] else 1.0
                confidence = max(0.1, 1 - distance)  # Convert distance to confidence
                
                # Extract attraction info from document
                attraction_info = self._parse_semantic_result(best_doc)
                
                if attraction_info and confidence >= 0.6:
                    return {
                        "success": True,
                        "classification": {
                            "attraction": attraction_info['name'],
                            "city": attraction_info['city'],
                            "confidence": confidence
                        },
                        "image_url": self._get_fallback_image(attraction_info['name'], attraction_info['city']),
                        "source": "chromadb"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return None
    
    def _query_apify(self, title: str, context: str) -> Optional[Dict]:
        """Query Apify for real-time attraction data"""
        try:
            if not self.apify.is_available():
                return None
            
            # Extract city from context
            city = self._extract_city(title, context)
            if not city:
                return None
            
            # Use existing Apify integration with correct method
            apify_results = self.apify.get_authentic_places(city, ['tourist_attraction'])
            attractions = apify_results.get('tourist_attraction', []) if apify_results else []
            
            if attractions:
                # Find best matching attraction
                search_terms = self._extract_search_terms(title, context)
                best_match = None
                best_score = 0
                
                for attraction in attractions:
                    score = self._calculate_apify_match_score(search_terms, attraction)
                    if score > best_score:
                        best_score = score
                        best_match = attraction
                
                if best_match and best_score >= 0.6:
                    return {
                        "success": True,
                        "classification": {
                            "attraction": best_match.get('name', 'Unknown'),
                            "city": city,
                            "confidence": best_score
                        },
                        "image_url": best_match.get('image_url') or self._get_fallback_image(
                            best_match.get('name', ''), city
                        ),
                        "coordinates": best_match.get('coordinates'),
                        "source": "apify"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Apify query error: {e}")
            return None
    
    def _legacy_classify(self, title: str, context: str) -> Optional[Dict]:
        """Use legacy AttractionImageClassifier as fallback"""
        try:
            result = self.legacy_classifier.classify_image({
                'title': title,
                'description': context
            })
            
            if result and 'attraction' in result:
                return {
                    "success": True,
                    "classification": {
                        "attraction": result['attraction'],
                        "city": result.get('city', 'Unknown'),
                        "confidence": result.get('confidence', 0.5)
                    },
                    "image_url": self._get_fallback_image(result['attraction'], result.get('city', '')),
                    "source": "legacy"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Legacy classification error: {e}")
            return None
    
    def _generate_generic_response(self, title: str, context: str) -> Dict:
        """Generate generic response when no specific match found"""
        city = self._extract_city(title, context) or "Unknown"
        
        return {
            "success": True,
            "classification": {
                "attraction": title.title(),
                "city": city.title(),
                "confidence": 0.3
            },
            "image_url": self._get_fallback_image(title, city),
            "source": "generic"
        }
    
    def _extract_search_terms(self, title: str, context: str) -> List[str]:
        """Extract meaningful search terms from title and context"""
        text = f"{title} {context}".lower()
        
        # Remove common words and normalize
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'di', 'del', 'della', 'dei'}
        words = re.findall(r'\b\w+\b', text)
        meaningful_words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Create search terms of different lengths
        terms = []
        terms.extend(meaningful_words)  # Individual words
        
        # 2-word combinations
        for i in range(len(meaningful_words) - 1):
            terms.append(f"{meaningful_words[i]} {meaningful_words[i+1]}")
        
        # 3-word combinations for specific attractions
        for i in range(len(meaningful_words) - 2):
            terms.append(f"{meaningful_words[i]} {meaningful_words[i+1]} {meaningful_words[i+2]}")
        
        return terms[:10]  # Limit to top 10 terms
    
    def _extract_city(self, title: str, context: str) -> Optional[str]:
        """Extract city name from title and context"""
        text = f"{title} {context}".lower()
        
        # Common Italian cities pattern matching
        italian_cities = [
            'roma', 'rome', 'milano', 'milan', 'napoli', 'naples', 'torino', 'turin',
            'firenze', 'florence', 'genova', 'genoa', 'bologna', 'venezia', 'venice',
            'palermo', 'catania', 'bari', 'messina', 'verona', 'padova', 'trieste',
            'brescia', 'parma', 'modena', 'reggio emilia', 'perugia', 'livorno'
        ]
        
        for city in italian_cities:
            if city in text:
                return city
        
        # Try to find capitalized words that might be cities
        words = re.findall(r'\b[A-Z][a-z]+\b', f"{title} {context}")
        if words:
            return words[0].lower()
        
        return None
    
    def _calculate_db_confidence(self, search_term: str, name: str, city: str) -> float:
        """Calculate confidence score for database match"""
        search_lower = search_term.lower()
        name_lower = name.lower() 
        city_lower = city.lower()
        
        # Exact match gets highest score
        if search_lower == name_lower:
            return 0.95
        
        # Substring match in name
        if search_lower in name_lower or name_lower in search_lower:
            return 0.85
        
        # City match
        if search_lower == city_lower:
            return 0.75
        
        # Partial matches
        search_words = search_lower.split()
        name_words = name_lower.split()
        
        matches = sum(1 for word in search_words if any(word in nw for nw in name_words))
        if matches > 0:
            return 0.6 + (matches / len(search_words)) * 0.2
        
        return 0.3
    
    def _parse_semantic_result(self, document: str) -> Optional[Dict]:
        """Parse ChromaDB document to extract attraction info"""
        try:
            # Assuming document format has attraction and city info
            # Adjust this based on your ChromaDB document structure
            lines = document.split('\n')
            info = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip().lower()] = value.strip()
            
            return {
                'name': info.get('name', info.get('attraction', '')),
                'city': info.get('city', info.get('location', ''))
            }
            
        except Exception:
            return None
    
    def _calculate_apify_match_score(self, search_terms: List[str], attraction: Dict) -> float:
        """Calculate match score for Apify attraction"""
        name = attraction.get('name', '').lower()
        description = attraction.get('description', '').lower()
        
        score = 0
        for term in search_terms:
            term_lower = term.lower()
            if term_lower in name:
                score += 0.4
            elif term_lower in description:
                score += 0.2
        
        return min(1.0, score)
    
    def _get_fallback_image(self, attraction: str, city: str) -> str:
        """Get fallback image URL for attraction"""
        # Use existing simple_enhanced_images logic or default images
        attraction_key = re.sub(r'[^a-z0-9]', '_', f"{attraction}_{city}".lower())
        
        # Fallback to generic city/attraction images
        return f"https://images.unsplash.com/photo-1551632811-561732d1e306?w=800&q=80"


# Flask route integration
def classify_image_intelligent(title: str, context: str = "") -> Dict:
    """
    Main entry point for intelligent image classification
    """
    classifier = IntelligentImageClassifier() 
    return classifier.classify_image(title, context)