"""
🌍 MULTI-SOURCE DATA AGGREGATION
Combines data from multiple sources for richer content
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class MultiSourceAggregator:
    """Aggregates data from multiple travel data sources"""
    
    def __init__(self, db_session, apify_client=None):
        self.db = db_session
        self.apify = apify_client
        self.source_weights = {
            'apify': 1.0,
            'database': 0.9,
            'tripadvisor': 0.8,
            'local_knowledge': 0.7,
            'wikipedia': 0.6
        }
    
    def aggregate_place_data(self, city: str, place_name: str, category: str) -> Dict:
        """
        Aggregate place information from all available sources
        
        Returns:
            Enriched place data with confidence scores
        """
        sources = []
        
        # Source 1: Database cache
        db_data = self._get_from_database(city, place_name, category)
        if db_data:
            sources.append({
                'source': 'database',
                'data': db_data,
                'weight': self.source_weights['database'],
                'timestamp': db_data.get('cached_at')
            })
        
        # Source 2: Apify (Google Maps)
        if self.apify and not db_data:
            apify_data = self._get_from_apify(city, place_name, category)
            if apify_data:
                sources.append({
                    'source': 'apify',
                    'data': apify_data,
                    'weight': self.source_weights['apify'],
                    'timestamp': datetime.now()
                })
        
        # Source 3: Wikipedia summary
        wiki_data = self._get_from_wikipedia(place_name, city)
        if wiki_data:
            sources.append({
                'source': 'wikipedia',
                'data': wiki_data,
                'weight': self.source_weights['wikipedia'],
                'timestamp': datetime.now()
            })
        
        # Source 4: Local knowledge base (hardcoded insights)
        local_data = self._get_local_knowledge(city, place_name)
        if local_data:
            sources.append({
                'source': 'local_knowledge',
                'data': local_data,
                'weight': self.source_weights['local_knowledge'],
                'timestamp': None
            })
        
        # Merge all sources
        merged = self._merge_sources(sources)
        merged['sources_used'] = [s['source'] for s in sources]
        merged['confidence_score'] = self._calculate_confidence(sources)
        
        return merged
    
    def _get_from_database(self, city: str, place_name: str, category: str) -> Optional[Dict]:
        """Fetch from PlaceCache"""
        from models import PlaceCache
        
        cache = self.db.query(PlaceCache).filter(
            PlaceCache.city.ilike(f'%{city}%'),
            PlaceCache.data['name'].astext.ilike(f'%{place_name}%'),
            PlaceCache.category == category
        ).first()
        
        if cache:
            data = cache.data.copy() if isinstance(cache.data, dict) else {}
            data['cached_at'] = cache.cached_at
            return data
        
        return None
    
    def _get_from_apify(self, city: str, place_name: str, category: str) -> Optional[Dict]:
        """Fetch fresh data from Apify"""
        if not self.apify:
            return None
        
        try:
            from apify_integration import search_google_maps_places
            
            query = f"{place_name} {city}"
            results = search_google_maps_places(
                search_query=query,
                category=category,
                max_results=1
            )
            
            return results[0] if results else None
        
        except Exception as e:
            logger.warning(f"⚠️ Apify fetch failed for {place_name}: {e}")
            return None
    
    def _get_from_wikipedia(self, place_name: str, city: str) -> Optional[Dict]:
        """
        Fetch Wikipedia summary
        NOTE: Requires wikipedia-api package (pip install wikipedia-api)
        """
        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia('en')
            
            # Try exact match
            page = wiki.page(place_name)
            if not page.exists():
                # Try with city
                page = wiki.page(f"{place_name}, {city}")
            
            if page.exists():
                return {
                    'summary': page.summary[:500],  # First 500 chars
                    'url': page.fullurl,
                    'historical_context': True
                }
        
        except ImportError:
            logger.debug("Wikipedia API not installed - pip install wikipedia-api")
        except Exception as e:
            logger.debug(f"Wikipedia fetch failed: {e}")
        
        return None
    
    def _get_local_knowledge(self, city: str, place_name: str) -> Optional[Dict]:
        """Get hardcoded local insights and tips"""
        
        # Local knowledge base (example)
        knowledge_base = {
            'Torino': {
                'Museo Egizio': {
                    'insider_tip': 'Book online to skip the 1-hour queue. Best time: Tuesday morning at 9 AM.',
                    'must_see': 'Sala delle mummie (Mummy Room)',
                    'average_visit_time': '2-3 hours',
                    'accessibility': 'Wheelchair accessible'
                },
                'Mole Antonelliana': {
                    'insider_tip': 'Take the panoramic elevator to the top for 360° views',
                    'must_see': 'Cinema Museum inside',
                    'average_visit_time': '1.5-2 hours',
                    'best_photo_spot': 'Piazza Castello at sunset'
                }
            },
            'Roma': {
                'Colosseo': {
                    'insider_tip': 'Buy combined ticket with Roman Forum. Enter through Palatine Hill (shorter queue).',
                    'must_see': 'Underground chambers (hypogeum)',
                    'average_visit_time': '2-3 hours',
                    'best_time': 'Early morning (8:30 AM) or late afternoon'
                }
            }
        }
        
        city_data = knowledge_base.get(city, {})
        place_data = city_data.get(place_name, {})
        
        return place_data if place_data else None
    
    def _merge_sources(self, sources: List[Dict]) -> Dict:
        """Merge data from multiple sources intelligently"""
        
        if not sources:
            return {}
        
        merged = {}
        
        # Prioritize by weight
        sources_sorted = sorted(sources, key=lambda x: x['weight'], reverse=True)
        
        # Start with highest weighted source
        merged = sources_sorted[0]['data'].copy()
        
        # Enrich with additional fields from other sources
        for source in sources_sorted[1:]:
            for key, value in source['data'].items():
                # Add if missing
                if key not in merged:
                    merged[key] = value
                # Enrich arrays
                elif isinstance(value, list) and isinstance(merged[key], list):
                    merged[key].extend([v for v in value if v not in merged[key]])
                # Add as alternative field
                elif key not in ['name', 'address']:  # Don't duplicate core fields
                    merged[f"{key}_{source['source']}"] = value
        
        return merged
    
    def _calculate_confidence(self, sources: List[Dict]) -> float:
        """Calculate confidence score based on source agreement"""
        
        if not sources:
            return 0.0
        
        # Base confidence from number of sources
        base_confidence = min(len(sources) / 3, 1.0) * 50
        
        # Weighted confidence from source quality
        weight_sum = sum(s['weight'] for s in sources)
        weighted_confidence = (weight_sum / len(sources)) * 50
        
        return base_confidence + weighted_confidence


class DataEnrichmentPipeline:
    """Enriches scraped data with additional context"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def enrich_place(self, place_data: Dict, city: str) -> Dict:
        """
        Add enrichments to place data
        
        Enrichments:
        - Nearby attractions
        - Best visit times
        - Accessibility info
        - Price category
        - Crowd predictions
        """
        enriched = place_data.copy()
        
        # Add nearby attractions
        enriched['nearby_attractions'] = self._find_nearby(
            place_data.get('coordinates', {}),
            city,
            radius_km=0.5
        )
        
        # Add visit recommendations
        enriched['visit_recommendations'] = self._generate_visit_tips(place_data)
        
        # Add price category
        enriched['price_category'] = self._estimate_price_category(place_data)
        
        # Add accessibility info
        enriched['accessibility_score'] = self._estimate_accessibility(place_data)
        
        return enriched
    
    def _find_nearby(self, coordinates: Dict, city: str, radius_km: float) -> List[str]:
        """Find nearby attractions within radius"""
        from models import PlaceCache
        from sqlalchemy import func
        
        if not coordinates or 'latitude' not in coordinates:
            return []
        
        lat = coordinates['latitude']
        lng = coordinates['longitude']
        
        # Simplified distance calculation (Haversine approximation)
        # Note: For production, use PostGIS or proper geospatial queries
        nearby = self.db.query(PlaceCache).filter(
            PlaceCache.city.ilike(f'%{city}%'),
            PlaceCache.category == 'tourist_attraction'
        ).limit(100).all()
        
        nearby_names = []
        for place in nearby:
            if isinstance(place.data, dict) and 'coordinates' in place.data:
                p_coords = place.data['coordinates']
                if 'latitude' in p_coords:
                    # Simple distance check
                    dist = ((lat - p_coords['latitude']) ** 2 + 
                           (lng - p_coords['longitude']) ** 2) ** 0.5
                    
                    if dist < (radius_km / 111):  # Rough conversion
                        nearby_names.append(place.data.get('name', ''))
        
        return nearby_names[:5]
    
    def _generate_visit_tips(self, place_data: Dict) -> Dict:
        """Generate visit recommendations"""
        tips = {
            'best_time': 'Morning (9-11 AM)',
            'average_duration': '1-2 hours',
            'booking_required': False
        }
        
        # Adjust based on category
        category = place_data.get('category', '')
        if 'museum' in category.lower():
            tips['booking_required'] = True
            tips['average_duration'] = '2-3 hours'
        
        # Adjust based on rating
        rating = place_data.get('rating', 0)
        if rating >= 4.5:
            tips['popularity'] = 'Very popular - expect crowds'
        
        return tips
    
    def _estimate_price_category(self, place_data: Dict) -> str:
        """Estimate price category (€, €€, €€€)"""
        
        # Check if price info exists
        if 'price_level' in place_data:
            level = place_data['price_level']
            if level <= 1:
                return '€'
            elif level == 2:
                return '€€'
            else:
                return '€€€'
        
        # Estimate from category
        category = place_data.get('category', '').lower()
        if 'museum' in category or 'monument' in category:
            return '€€'
        elif 'restaurant' in category:
            return '€€'
        else:
            return '€'
    
    def _estimate_accessibility(self, place_data: Dict) -> int:
        """Estimate accessibility score (0-100)"""
        score = 50  # Default neutral
        
        # Check description for accessibility keywords
        description = str(place_data.get('description', '')).lower()
        
        if 'wheelchair' in description or 'accessible' in description:
            score += 30
        
        if 'elevator' in description or 'lift' in description:
            score += 10
        
        if 'stairs only' in description or 'no elevator' in description:
            score -= 20
        
        return min(max(score, 0), 100)


# Integration functions

def create_enriched_place_profile(city: str, place_name: str, category: str, db_session) -> Dict:
    """
    Create a comprehensive enriched profile for a place
    
    Returns:
        Fully enriched place data from all sources
    """
    aggregator = MultiSourceAggregator(db_session)
    enrichment = DataEnrichmentPipeline(db_session)
    
    # Aggregate from sources
    aggregated = aggregator.aggregate_place_data(city, place_name, category)
    
    # Enrich with additional context
    enriched = enrichment.enrich_place(aggregated, city)
    
    logger.info(f"✨ Enriched profile for {place_name}: {len(enriched['sources_used'])} sources, {enriched['confidence_score']:.1f}% confidence")
    
    return enriched
