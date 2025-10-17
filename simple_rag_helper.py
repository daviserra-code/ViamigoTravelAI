"""
Optimized RAG Helper - Enhanced context retrieval for AI Companion
Queries PostgreSQL cache with in-memory caching, semantic search, and performance optimization
"""
import os
import json
import logging
import time
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import psycopg2
from functools import lru_cache
from datetime import datetime, timedelta
import chromadb

load_dotenv()
logger = logging.getLogger(__name__)


class OptimizedRAGHelper:
    """Enhanced RAG helper with caching, performance optimization, and semantic search"""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self._cache = {}  # In-memory cache
        self._cache_ttl = 300  # 5 minutes TTL
        self._performance_metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'db_queries': 0,
            'avg_response_time': 0,
            'semantic_queries': 0
        }

        # Initialize ChromaDB for semantic search
        self._chroma_client = None
        self._chroma_collection = None
        self._init_chromadb()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False

        cached_time = self._cache[cache_key].get('timestamp')
        if not cached_time:
            return False

        return (datetime.now() - cached_time).seconds < self._cache_ttl

    def _init_chromadb(self):
        """Initialize ChromaDB connection for semantic search"""
        try:
            self._chroma_client = chromadb.PersistentClient(
                path="./chromadb_data")
            self._chroma_collection = self._chroma_client.get_collection(
                "viamigo_travel_data")
            logger.info("🔗 ChromaDB initialized for semantic search")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB initialization failed: {e}")
            self._chroma_client = None
            self._chroma_collection = None

    def semantic_search_places(
        self,
        query: str,
        city: str = None,
        categories: List[str] = None,
        n_results: int = 10
    ) -> List[Dict]:
        """
        Semantic search for places using ChromaDB

        Args:
            query: Natural language query (e.g., "romantic restaurants with view")
            city: Filter by city (optional)
            categories: Filter by categories (optional)  
            n_results: Maximum number of results to return

        Returns:
            List of matching places with relevance scores
        """
        if not self._chroma_collection:
            logger.warning("🚫 ChromaDB not available for semantic search")
            return []

        try:
            self._performance_metrics['semantic_queries'] += 1
            start_time = time.time()

            # Prepare where filter - ChromaDB only supports one operator at a time
            where_filter = None
            if city and categories:
                # Priority: filter by city first, then post-filter by categories
                where_filter = {"city": {"$eq": city.lower()}}
            elif city:
                where_filter = {"city": {"$eq": city.lower()}}
            elif categories:
                where_filter = {"category": {"$in": categories}}

            # Perform semantic search
            results = self._chroma_collection.query(
                query_texts=[query],
                n_results=n_results * 2,  # Get extra to allow for category filtering
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            # Process results
            places = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    document = results['documents'][0][i]

                    # Post-filter by categories if needed
                    if categories and metadata.get('category') not in categories:
                        continue

                    # Calculate relevance score (1 - distance, normalized)
                    relevance_score = max(0, 1 - distance)

                    place = {
                        'name': metadata.get('name', 'Unknown'),
                        'city': metadata.get('city', 'Unknown'),
                        'category': metadata.get('category', 'Unknown'),
                        'description': document,
                        'relevance_score': round(relevance_score, 3),
                        'semantic_match': True,
                        **{k: v for k, v in metadata.items() if k not in ['name', 'city', 'category']}
                    }
                    places.append(place)

                    # Stop when we have enough results
                    if len(places) >= n_results:
                        break

            query_time = time.time() - start_time
            logger.info(
                f"🔍 Semantic search '{query}' found {len(places)} results in {query_time:.3f}s")

            return places

        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return []

    def hybrid_search_places(
        self,
        query: str,
        city: str,
        categories: List[str] = None,
        semantic_weight: float = 0.3,
        n_results: int = 15
    ) -> List[Dict]:
        """
        Hybrid search combining PostgreSQL category-based search with ChromaDB semantic search

        Args:
            query: Natural language query for semantic component
            city: City to search in
            categories: Categories for PostgreSQL component
            semantic_weight: Weight given to semantic results (0.0-1.0)
            n_results: Total number of results to return

        Returns:
            Combined and ranked list of places
        """
        results = []

        # 1. Get traditional category-based results
        if categories:
            city_context = self.get_city_context(city, categories)
            traditional_places = []

            for category, data in city_context.get('categories', {}).items():
                for place in data.get('places', []):
                    place_copy = place.copy()
                    place_copy['search_source'] = 'traditional'
                    place_copy['category_match'] = category
                    traditional_places.append(place_copy)

            # Sort traditional results by quality
            traditional_places = self._sort_places_by_quality(
                traditional_places)
            results.extend(traditional_places[:int(
                n_results * (1 - semantic_weight))])

        # 2. Get semantic search results
        semantic_places = self.semantic_search_places(
            query=query,
            city=city,
            categories=categories,
            # Get extra to account for deduplication
            n_results=int(n_results * semantic_weight) + 5
        )

        # Mark semantic results
        for place in semantic_places:
            place['search_source'] = 'semantic'

        # 3. Combine and deduplicate results
        combined_places = self._merge_search_results(results, semantic_places)

        # 4. Final ranking considering both quality and semantic relevance
        final_results = self._rank_hybrid_results(
            combined_places, semantic_weight)

        logger.info(
            f"🔄 Hybrid search for '{query}' in {city}: {len(final_results)} combined results")

        return final_results[:n_results]

    def _merge_search_results(self, traditional: List[Dict], semantic: List[Dict]) -> List[Dict]:
        """
        Merge traditional and semantic search results, removing duplicates

        Args:
            traditional: Results from category-based search
            semantic: Results from semantic search

        Returns:
            Merged list with duplicates removed
        """
        # Create lookup for traditional results by name (case-insensitive)
        traditional_names = {
            place.get('name', '').lower(): place for place in traditional}
        merged = traditional.copy()

        # Add semantic results that don't duplicate traditional ones
        for semantic_place in semantic:
            name_key = semantic_place.get('name', '').lower()

            if name_key not in traditional_names:
                merged.append(semantic_place)
            else:
                # Enhance traditional place with semantic data
                traditional_place = traditional_names[name_key]
                traditional_place['relevance_score'] = semantic_place.get(
                    'relevance_score', 0)
                traditional_place['semantic_enhanced'] = True

        return merged

    def _rank_hybrid_results(self, places: List[Dict], semantic_weight: float) -> List[Dict]:
        """
        Rank hybrid search results considering both quality and semantic relevance

        Args:
            places: Combined list of places
            semantic_weight: Weight given to semantic relevance (0.0-1.0)

        Returns:
            Ranked list of places
        """
        def hybrid_score(place: Dict) -> float:
            # Base quality score (0-30 range typically)
            quality_score = self._calculate_quality_score(place)

            # Semantic relevance score (0-1 range)
            # Default moderate relevance
            semantic_score = place.get('relevance_score', 0.5)

            # Combine scores
            normalized_quality = min(
                1.0, quality_score / 30.0)  # Normalize to 0-1

            final_score = (
                (1 - semantic_weight) * normalized_quality +
                semantic_weight * semantic_score
            )

            # Bonus for places that appear in both sources
            if place.get('semantic_enhanced'):
                final_score += 0.1

            return final_score

        return sorted(places, key=hybrid_score, reverse=True)

    def _calculate_quality_score(self, place: Dict) -> float:
        """Calculate quality score for a place (extracted from _sort_places_by_quality logic)"""
        score = 0.0

        # Rating weight (0-5 scale)
        rating = place.get('rating', 0)
        if rating:
            score += float(rating) * 2  # Max 10 points

        # Review count weight (logarithmic scale)
        review_count = place.get('user_ratings_total', 0)
        if review_count:
            score += min(10, review_count / 10)  # Max 10 points

        # Wikipedia/external info weight
        if place.get('wikipedia') or place.get('wikidata'):
            score += 5

        # Description quality weight
        description = place.get('description', '')
        if len(description) > 50:
            score += 3
        elif len(description) > 20:
            score += 1

        # Name quality (avoid empty/generic names)
        name = place.get('name', '')
        if name and len(name) > 3 and name != 'Unknown':
            score += 2

        # Historic/tourism type bonus
        if place.get('historic_type') or place.get('tourism_type'):
            score += 2

        return score

    def search_places_by_description(
        self,
        description: str,
        city: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find places by natural language description

        Args:
            description: Natural language description (e.g., "museum with ancient art")
            city: Filter by city (optional)
            limit: Maximum number of results

        Returns:
            List of matching places with relevance scores
        """
        # Use semantic search for description matching
        return self.semantic_search_places(
            query=description,
            city=city,
            n_results=limit
        )

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from in-memory cache if valid"""
        if self._is_cache_valid(cache_key):
            self._performance_metrics['cache_hits'] += 1
            logger.debug(f"🎯 Cache hit for {cache_key}")
            return self._cache[cache_key]['data']
        return None

    def _store_in_cache(self, cache_key: str, data: Dict):
        """Store data in in-memory cache with timestamp"""
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.debug(f"💾 Cached data for {cache_key}")

    def get_performance_metrics(self) -> Dict:
        """Get performance statistics"""
        total_queries = self._performance_metrics['total_queries']
        cache_hits = self._performance_metrics['cache_hits']

        return {
            **self._performance_metrics,
            'cache_hit_rate': (cache_hits / total_queries * 100) if total_queries > 0 else 0,
            'cache_size': len(self._cache)
        }

    def get_city_context_with_semantic(
        self,
        city: str,
        categories: List[str] = None,
        semantic_query: str = None,
        include_semantic: bool = True,
        semantic_weight: float = 0.2
    ) -> Dict:
        """
        Enhanced city context retrieval with optional semantic search integration

        Args:
            city: City name (e.g., 'Bergamo', 'Milan', 'Rome')
            categories: List of categories to retrieve (default: all available)
            semantic_query: Natural language query for semantic enhancement
            include_semantic: Whether to include semantic search results
            semantic_weight: Weight given to semantic results (0.0-1.0)

        Returns:
            Dictionary with place data organized by category, optionally enhanced with semantic results
        """
        # Get base context using traditional method
        base_context = self.get_city_context(city, categories)

        if not include_semantic or not semantic_query or not self._chroma_collection:
            return base_context

        try:
            # Enhance with semantic search results
            semantic_places = self.semantic_search_places(
                query=semantic_query,
                city=city,
                categories=categories,
                n_results=10
            )

            if semantic_places:
                # Add semantic results to context
                if 'semantic_results' not in base_context:
                    base_context['semantic_results'] = {
                        'query': semantic_query,
                        'places': semantic_places,
                        'count': len(semantic_places)
                    }

                # Enhance existing categories with semantic relevance scores
                for category, data in base_context.get('categories', {}).items():
                    enhanced_places = []

                    for place in data.get('places', []):
                        place_name = place.get('name', '').lower()

                        # Find semantic match for this place
                        semantic_match = None
                        for sem_place in semantic_places:
                            if sem_place.get('name', '').lower() == place_name:
                                semantic_match = sem_place
                                break

                        # Enhance place with semantic data
                        enhanced_place = place.copy()
                        if semantic_match:
                            enhanced_place['semantic_relevance'] = semantic_match.get(
                                'relevance_score', 0)
                            enhanced_place['semantic_enhanced'] = True
                        else:
                            # Default neutral relevance
                            enhanced_place['semantic_relevance'] = 0.5

                        enhanced_places.append(enhanced_place)

                    # Re-sort by hybrid score (quality + semantic relevance)
                    enhanced_places = self._rank_hybrid_results(
                        enhanced_places, semantic_weight)
                    data['places'] = enhanced_places

                base_context['semantic_enhanced'] = True
                base_context['semantic_query'] = semantic_query
                logger.info(
                    f"🔍 Enhanced {city} context with semantic query: '{semantic_query}'")

            return base_context

        except Exception as e:
            logger.error(
                f"❌ Error enhancing context with semantic search: {e}")
            return base_context

    def get_city_context(self, city: str, categories: List[str] = None) -> Dict:
        """
        Get real place data from PostgreSQL cache for a city with optimization
        Supports both legacy format (city_category) and new OSM format (osm:city:id)
        Includes in-memory caching and performance monitoring

        Args:
            city: City name (e.g., 'Bergamo', 'Milan', 'Rome')
            categories: List of categories to retrieve (default: all available)

        Returns:
            Dictionary with place data organized by category
        """
        start_time = time.time()
        self._performance_metrics['total_queries'] += 1

        if categories is None:
            categories = ['restaurant', 'tourist_attraction',
                          'hotel', 'cafe', 'museum']

        # Create cache key
        cache_key = f"{city.lower()}_{'+'.join(sorted(categories))}"

        # Try cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            cached_result['cache_status'] = 'hit'
            return cached_result

        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            self._performance_metrics['db_queries'] += 1

            city_lower = city.lower()
            context = {
                'city': city,
                'categories': {},
                'total_places': 0,
                'source': 'mixed',  # Will track data sources
                'query_time': 0,  # Will be set at the end
                'cache_status': 'miss'
            }

            # 1. Try legacy format first with batch query
            legacy_cache_keys = [
                f"{city_lower}_{category}" for category in categories]

            # Batch query for legacy format
            if legacy_cache_keys:
                placeholders = ','.join(['%s'] * len(legacy_cache_keys))
                cur.execute(
                    f"SELECT cache_key, place_data FROM place_cache WHERE cache_key IN ({placeholders})",
                    legacy_cache_keys
                )

                legacy_results = cur.fetchall()
                legacy_found = False

                for cache_key_result, place_data_json in legacy_results:
                    try:
                        # Extract category from cache_key
                        category = cache_key_result.split('_', 1)[1]
                        places_data = json.loads(place_data_json)

                        context['categories'][category] = {
                            'count': len(places_data),
                            'places': places_data[:10],  # Top 10 for context
                            'source': 'legacy'
                        }
                        context['total_places'] += len(places_data)
                        legacy_found = True
                        logger.debug(
                            f"✅ Retrieved {len(places_data)} {category} (legacy) for {city}")
                    except (json.JSONDecodeError, IndexError):
                        logger.warning(
                            f"⚠️ Invalid data for {cache_key_result}")

            # 2. If no legacy data, try new OSM format (optimized query)
            if not legacy_found:
                cur.execute(
                    "SELECT cache_key, place_data FROM place_cache WHERE cache_key LIKE %s ORDER BY cache_key",
                    (f"osm:{city_lower}:%",)
                )

                osm_results = cur.fetchall()
                if osm_results:
                    # Organize OSM data by category based on place types
                    osm_categories = {}
                    processed_count = 0

                    for cache_key_result, place_data_json in osm_results:
                        try:
                            place_data = json.loads(place_data_json)

                            # Determine category from place types/tags
                            place_category = self._categorize_osm_place_enhanced(
                                place_data)

                            if place_category in categories:
                                if place_category not in osm_categories:
                                    osm_categories[place_category] = []
                                osm_categories[place_category].append(
                                    place_data)
                                processed_count += 1

                        except json.JSONDecodeError:
                            logger.warning(
                                f"⚠️ Invalid JSON for OSM {cache_key_result}")

                    # Add OSM categories to context with smart limiting
                    for category, places in osm_categories.items():
                        # Intelligent selection: prioritize places with ratings, descriptions, etc.
                        sorted_places = self._sort_places_by_quality(places)

                        context['categories'][category] = {
                            'count': len(places),
                            'places': sorted_places[:10],  # Top 10 for context
                            'source': 'osm'
                        }
                        context['total_places'] += len(places)
                        logger.debug(
                            f"✅ Retrieved {len(places)} {category} (OSM) for {city}")

                    if osm_categories:
                        context['source'] = 'osm'
                        logger.info(
                            f"📊 Processed {processed_count} OSM places for {city}")

            # 3. If still no data, try semantic fallback
            if context['total_places'] == 0:
                fallback_context = self._get_semantic_fallback(
                    city, categories)
                if fallback_context:
                    context.update(fallback_context)
                    context['source'] = 'semantic_fallback'
                else:
                    logger.warning(
                        f"⚠️ No data found for {city} in any format")

            cur.close()
            conn.close()

            # Calculate query time and update metrics
            query_time = time.time() - start_time
            context['query_time'] = round(query_time, 3)

            # Update performance metrics
            total_queries = self._performance_metrics['total_queries']
            current_avg = self._performance_metrics['avg_response_time']
            self._performance_metrics['avg_response_time'] = (
                (current_avg * (total_queries - 1) + query_time) / total_queries
            )

            # Cache the result
            self._store_in_cache(cache_key, context)

            logger.info(
                f"🏁 Query completed for {city}: {context['total_places']} places in {query_time:.3f}s")
            return context

        except Exception as e:
            logger.error(f"❌ Error getting city context for {city}: {e}")
            return {
                'city': city,
                'categories': {},
                'total_places': 0,
                'error': str(e),
                'query_time': time.time() - start_time,
                'cache_status': 'error'
            }

    def _categorize_osm_place(self, place_data: Dict) -> str:
        """
        Categorize an OSM place based on its types and tags

        Args:
            place_data: Dictionary containing place information

        Returns:
            Category string ('restaurant', 'tourist_attraction', etc.)
        """
        types = place_data.get('types', [])
        tourism_type = place_data.get('tourism_type', '')
        historic_type = place_data.get('historic_type', '')
        cuisine = place_data.get('cuisine', '')

        # Restaurant/Food categories
        if any(t in ['restaurant', 'food', 'meal_takeaway', 'cafe', 'bar'] for t in types) or cuisine:
            return 'restaurant'

        # Tourist attractions
        if any(t in ['tourist_attraction', 'museum', 'art_gallery', 'zoo', 'amusement_park'] for t in types) or tourism_type or historic_type:
            return 'tourist_attraction'

        # Hotels/Accommodation
        if any(t in ['lodging', 'hotel', 'guest_house'] for t in types) or tourism_type == 'hotel':
            return 'hotel'

        # Museums
        if any(t in ['museum', 'art_gallery', 'library'] for t in types):
            return 'museum'

        # Default to tourist_attraction for uncategorized places
        return 'tourist_attraction'

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

        # Add source indicator
        source = city_context.get('source', 'unknown')
        source_indicator = {
            'legacy': '📊 [Legacy Data]',
            'osm': '🗺️ [OpenStreetMap Data]',
            'mixed': '🔀 [Mixed Sources]'
        }.get(source, '❓ [Unknown Source]')

        lines = [
            f"📍 REAL DATA for {city_context['city']} ({city_context['total_places']} places in database) {source_indicator}:",
            ""
        ]

        for category, data in city_context.get('categories', {}).items():
            count = data.get('count', 0)
            places = data.get('places', [])
            cat_source = data.get('source', source)

            if count > 0:
                source_tag = f" [{cat_source}]" if source == 'mixed' else ""
                lines.append(
                    f"**{category.upper()}**{source_tag} ({count} total):")

                # List top 5 place names with additional info for OSM data
                for i, place in enumerate(places[:5], 1):
                    name = place.get('name', place.get('title', 'Unknown'))

                    # Add extra context for OSM data
                    if cat_source == 'osm':
                        vicinity = place.get('vicinity', '')
                        types = place.get('types', [])
                        if vicinity:
                            name += f" ({vicinity})"
                        elif types:
                            name += f" [{', '.join(types[:2])}]"

                    lines.append(f"  {i}. {name}")

                lines.append("")

        lines.append(
            "⚠️ CRITICAL: Only suggest places from this list or verify they exist in this city!")

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

        lines.append(
            "⚠️ CRITICAL: Only suggest these hotels - they have verified reviews!")

        return "\n".join(lines)

    def _categorize_osm_place_enhanced(self, place_data: Dict) -> str:
        """
        Enhanced categorization with more sophisticated logic

        Args:
            place_data: Dictionary containing place information

        Returns:
            Category string with better accuracy
        """
        types = place_data.get('types', [])
        tourism_type = place_data.get('tourism_type', '')
        historic_type = place_data.get('historic_type', '')
        cuisine = place_data.get('cuisine', '')
        name = place_data.get('name', '').lower()

        # Advanced restaurant/food detection
        food_keywords = ['ristorante', 'pizzeria', 'trattoria',
                         'osteria', 'bar', 'caffè', 'gelateria', 'pasticceria']
        if (any(t in ['restaurant', 'food', 'meal_takeaway', 'cafe', 'bar'] for t in types) or
            cuisine or
                any(keyword in name for keyword in food_keywords)):
            return 'restaurant'

        # Advanced tourist attraction detection
        attraction_keywords = ['museo', 'chiesa', 'basilica', 'duomo',
                               'palazzo', 'castello', 'torre', 'piazza', 'fontana']
        if (any(t in ['tourist_attraction', 'museum', 'art_gallery', 'zoo', 'amusement_park', 'place_of_worship'] for t in types) or
            tourism_type or
            historic_type or
                any(keyword in name for keyword in attraction_keywords)):
            return 'tourist_attraction'

        # Hotels/Accommodation with better detection
        hotel_keywords = ['hotel', 'albergo', 'pensione', 'bed', 'b&b']
        if (any(t in ['lodging', 'hotel', 'guest_house'] for t in types) or
            tourism_type == 'hotel' or
                any(keyword in name for keyword in hotel_keywords)):
            return 'hotel'

        # Museums with cultural detection
        museum_keywords = ['museo', 'galleria', 'pinacoteca', 'biblioteca']
        if (any(t in ['museum', 'art_gallery', 'library'] for t in types) or
                any(keyword in name for keyword in museum_keywords)):
            return 'museum'

        # Default classification based on context
        return 'tourist_attraction'

    def _sort_places_by_quality(self, places: List[Dict]) -> List[Dict]:
        """
        Sort places by quality indicators (ratings, reviews, Wikipedia presence, etc.)

        Args:
            places: List of place dictionaries

        Returns:
            Sorted list with highest quality places first
        """
        def quality_score(place: Dict) -> float:
            score = 0.0

            # Rating weight (0-5 scale)
            rating = place.get('rating', 0)
            if rating:
                score += float(rating) * 2  # Max 10 points

            # Review count weight (logarithmic scale)
            review_count = place.get('user_ratings_total', 0)
            if review_count:
                score += min(10, review_count / 10)  # Max 10 points

            # Wikipedia/external info weight
            if place.get('wikipedia') or place.get('wikidata'):
                score += 5

            # Description quality weight
            description = place.get('description', '')
            if len(description) > 50:
                score += 3
            elif len(description) > 20:
                score += 1

            # Name quality (avoid empty/generic names)
            name = place.get('name', '')
            if name and len(name) > 3 and name != 'Unknown':
                score += 2

            # Historic/tourism type bonus
            if place.get('historic_type') or place.get('tourism_type'):
                score += 2

            return score

        return sorted(places, key=quality_score, reverse=True)

    def _get_semantic_fallback(self, city: str, categories: List[str]) -> Optional[Dict]:
        """
        Intelligent fallback using semantic search and nearby cities

        Args:
            city: Original city name
            categories: Requested categories

        Returns:
            Fallback context or None
        """
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()

            # Try to find similar city names (fuzzy matching)
            city_variants = [
                city.lower(),
                city.lower().replace('à', 'a').replace('è', 'e').replace(
                    'ì', 'i').replace('ò', 'o').replace('ù', 'u'),
                city.lower() + 'a',  # Many Italian cities end in 'a'
                # Remove last character
                city.lower()[:-1] if len(city) > 3 else city.lower(),
            ]

            for variant in city_variants:
                cur.execute(
                    "SELECT DISTINCT SPLIT_PART(cache_key, ':', 2) FROM place_cache WHERE cache_key LIKE %s LIMIT 1",
                    (f"%{variant}%",)
                )
                result = cur.fetchone()
                if result:
                    similar_city = result[0]
                    logger.info(
                        f"🔄 Found similar city '{similar_city}' for '{city}'")

                    # Get data for similar city
                    return {
                        'fallback_city': similar_city,
                        'original_city': city,
                        'message': f"Dati trovati per città simile: {similar_city}"
                    }

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Semantic fallback error: {e}")

        return None

    def clear_cache(self):
        """Clear the in-memory cache"""
        self._cache.clear()
        logger.info("🧹 Cache cleared")

    def get_cache_info(self) -> Dict:
        """Get information about current cache state"""
        return {
            'cache_size': len(self._cache),
            'cached_cities': list(set(key.split('_')[0] for key in self._cache.keys())),
            'ttl_seconds': self._cache_ttl
        }


# Create alias for backward compatibility
SimpleRAGHelper = OptimizedRAGHelper


# Global instance for easy import
rag_helper = OptimizedRAGHelper()


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


# New semantic search convenience functions
def semantic_search_places(query: str, city: str = None, categories: List[str] = None, n_results: int = 10) -> List[Dict]:
    """
    Convenience function for semantic search of places

    Usage:
        places = semantic_search_places("romantic restaurants with view", "Rome")
        places = semantic_search_places("museums with ancient art", "Florence", ["museum"])
    """
    return rag_helper.semantic_search_places(query, city, categories, n_results)


def hybrid_search_places(query: str, city: str, categories: List[str] = None, semantic_weight: float = 0.3, n_results: int = 15) -> List[Dict]:
    """
    Convenience function for hybrid search combining traditional + semantic

    Usage:
        places = hybrid_search_places("cozy authentic pizza places", "Naples", ["restaurant"])
        places = hybrid_search_places("historic churches", "Rome", ["tourist_attraction"], semantic_weight=0.4)
    """
    return rag_helper.hybrid_search_places(query, city, categories, semantic_weight, n_results)


def search_places_by_description(description: str, city: str = None, limit: int = 10) -> List[Dict]:
    """
    Convenience function to search places by natural language description

    Usage:
        places = search_places_by_description("museum with ancient Roman artifacts", "Rome")
        places = search_places_by_description("traditional osteria with local wine")
    """
    return rag_helper.search_places_by_description(description, city, limit)


def get_city_context_with_semantic(city: str, categories: List[str] = None, semantic_query: str = None) -> Dict:
    """
    Convenience function for enhanced city context with semantic search

    Usage:
        context = get_city_context_with_semantic("Milan", ["restaurant"], "romantic dinner spots")
        context = get_city_context_with_semantic("Florence", ["museum"], "Renaissance art collections")
    """
    return rag_helper.get_city_context_with_semantic(city, categories, semantic_query)
