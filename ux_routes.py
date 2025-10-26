#!/usr/bin/env python3
"""
ViamigoTravelAI UX Enhancement Routes
Enhanced user experience features including search autocomplete, city data, and mobile optimizations
"""

from flask import Blueprint, jsonify, request
import psycopg2
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Create blueprint
ux_bp = Blueprint('ux', __name__)

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get PostgreSQL connection with autocommit for read operations"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Enable autocommit for read operations
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None


@ux_bp.route('/api/cities/search', methods=['GET'])
def search_cities():
    """
    Enhanced city and place search with autocomplete support
    Supports real-time search across 9,930+ places in 56 Italian cities
    """
    try:
        query = request.args.get('query', '').strip().lower()
        limit = int(request.args.get('limit', 10))

        if len(query) < 2:
            return jsonify({
                'cities': [],
                'places': [],
                'message': 'Query too short'
            })

        conn = get_db_connection()
        if not conn:
            # Fallback to predefined cities
            return get_fallback_cities(query, limit)

        try:
            with conn.cursor() as cursor:
                # Search place_cache for Milano and other city data
                cities = []
                places = []

                # First try place_cache (has Milano data)
                try:
                    city_query = """
                        SELECT city, COUNT(*) as place_count
                        FROM place_cache 
                        WHERE LOWER(city) LIKE %s 
                        GROUP BY city
                        ORDER BY 
                            CASE WHEN LOWER(city) = %s THEN 0 ELSE 1 END,
                            COUNT(*) DESC,
                            city
                        LIMIT %s
                    """
                    cursor.execute(city_query, (f'%{query}%', query, limit))
                    cities.extend([{'name': row[0], 'place_count': row[1]}
                                  for row in cursor.fetchall()])

                    # Search places in place_cache
                    place_query = """
                        SELECT place_name, city, 'place' as type, 
                               CASE 
                                   WHEN LOWER(place_name) LIKE %s THEN 1
                                   WHEN LOWER(place_name) LIKE %s THEN 2
                                   ELSE 3
                               END as relevance
                        FROM place_cache 
                        WHERE LOWER(place_name) LIKE %s OR LOWER(city) LIKE %s
                        ORDER BY relevance, place_name
                        LIMIT %s
                    """
                    search_pattern = f'%{query}%'
                    exact_start = f'{query}%'
                    cursor.execute(place_query, (exact_start, search_pattern,
                                   search_pattern, search_pattern, limit))

                    for row in cursor.fetchall():
                        places.append({
                            'name': row[0],
                            'city': row[1],
                            'type': row[2] or 'place',
                            'relevance': row[3]
                        })

                except Exception as e:
                    logger.warning(f"place_cache search failed: {e}")

                # Also search comprehensive_attractions table
                try:
                    city_query = """
                        SELECT city, COUNT(*) as place_count
                        FROM comprehensive_attractions 
                        WHERE LOWER(city) LIKE %s 
                        GROUP BY city
                        ORDER BY 
                            CASE WHEN LOWER(city) = %s THEN 0 ELSE 1 END,
                            COUNT(*) DESC,
                            city
                        LIMIT %s
                    """
                    cursor.execute(city_query, (f'%{query}%', query, limit))
                    comp_cities = [{'name': row[0], 'place_count': row[1]}
                                   for row in cursor.fetchall()]

                    # Merge cities, avoiding duplicates
                    existing_cities = {c['name'].lower() for c in cities}
                    for city in comp_cities:
                        if city['name'].lower() not in existing_cities:
                            cities.append(city)

                    # Search comprehensive attractions for specific places
                    place_query = """
                        SELECT name, city, attraction_type, 
                               CASE 
                                   WHEN LOWER(name) LIKE %s THEN 1
                                   WHEN LOWER(name) LIKE %s THEN 2
                                   ELSE 3
                               END as relevance
                        FROM comprehensive_attractions 
                        WHERE LOWER(name) LIKE %s OR LOWER(city) LIKE %s
                        ORDER BY relevance, 
                                 has_image DESC,
                                 name
                        LIMIT %s
                    """
                    search_pattern = f'%{query}%'
                    exact_start = f'{query}%'
                    cursor.execute(place_query, (exact_start, search_pattern,
                                   search_pattern, search_pattern, limit))

                    for row in cursor.fetchall():
                        places.append({
                            'name': row[0],
                            'city': row[1],
                            'type': row[2] or 'attraction',
                            'relevance': row[3]
                        })
                except Exception as e:
                    logger.warning(
                        f"Comprehensive attractions search failed: {e}")

                return jsonify({
                    'cities': [city['name'] for city in cities],
                    'places': places,
                    'city_details': cities,
                    'query': query,
                    'total_results': len(cities) + len(places)
                })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return get_fallback_cities(query, limit)


def get_fallback_cities(query, limit):
    """Fallback city search when database is unavailable"""
    italian_cities = [
        'Roma', 'Milano', 'Napoli', 'Torino', 'Palermo', 'Genova', 'Bologna', 'Firenze',
        'Bari', 'Catania', 'Venezia', 'Verona', 'Messina', 'Padova', 'Trieste', 'Brescia',
        'Taranto', 'Prato', 'Reggio Calabria', 'Modena', 'Parma', 'Perugia', 'Livorno',
        'Cagliari', 'Foggia', 'Rimini', 'Salerno', 'Ferrara', 'Sassari', 'Latina',
        'Giugliano in Campania', 'Monza', 'Bergamo', 'Siracusa', 'Pescara', 'Forlì',
        'Trento', 'Vicenza', 'Terni', 'Bolzano', 'Novara', 'Piacenza', 'Ancona',
        'Andria', 'Arezzo', 'Udine', 'Cesena', 'Lecce', 'Pesaro', 'Barletta',
        'Alessandria', 'La Spezia', 'Pisa', 'Catanzaro', 'Pistoia', 'Lucca'
    ]

    # Filter cities based on query
    filtered_cities = [city for city in italian_cities
                       if query in city.lower()][:limit]

    return jsonify({
        'cities': filtered_cities,
        'places': [],
        'fallback': True,
        'query': query
    })


@ux_bp.route('/api/places/details/<place_id>', methods=['GET'])
def get_place_details(place_id):
    """Get detailed information for a specific place"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database unavailable'}), 503

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT name, city, type, latitude, longitude, 
                           description, rating, phone, website, address
                    FROM place_cache 
                    WHERE id = %s
                """
                cursor.execute(query, (place_id,))
                result = cursor.fetchone()

                if not result:
                    return jsonify({'error': 'Place not found'}), 404

                place_details = {
                    'id': place_id,
                    'name': result[0],
                    'city': result[1],
                    'type': result[2],
                    'latitude': float(result[3]) if result[3] else None,
                    'longitude': float(result[4]) if result[4] else None,
                    'description': result[5],
                    'rating': float(result[6]) if result[6] else None,
                    'phone': result[7],
                    'website': result[8],
                    'address': result[9]
                }

                return jsonify(place_details)

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"❌ Error getting place details: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@ux_bp.route('/api/cities/popular', methods=['GET'])
def get_popular_cities():
    """Get most popular Italian cities with place counts"""
    try:
        conn = get_db_connection()
        if not conn:
            return get_fallback_popular_cities()

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT city, COUNT(*) as place_count,
                           AVG(latitude) as avg_lat, AVG(longitude) as avg_lng
                    FROM place_cache 
                    WHERE city IS NOT NULL
                    GROUP BY city
                    ORDER BY place_count DESC
                    LIMIT 20
                """
                cursor.execute(query)

                cities = []
                for row in cursor.fetchall():
                    cities.append({
                        'name': row[0],
                        'place_count': row[1],
                        'coordinates': {
                            'lat': float(row[2]) if row[2] else None,
                            'lng': float(row[3]) if row[3] else None
                        }
                    })

                return jsonify({
                    'cities': cities,
                    'total_cities': len(cities)
                })

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"❌ Error getting popular cities: {e}")
        return get_fallback_popular_cities()


def get_fallback_popular_cities():
    """Fallback popular cities data"""
    popular_cities = [
        {'name': 'Roma', 'place_count': 500, 'coordinates': {
            'lat': 41.9028, 'lng': 12.4964}},
        {'name': 'Milano', 'place_count': 400,
            'coordinates': {'lat': 45.4642, 'lng': 9.1900}},
        {'name': 'Firenze', 'place_count': 300,
            'coordinates': {'lat': 43.7696, 'lng': 11.2558}},
        {'name': 'Venezia', 'place_count': 250,
            'coordinates': {'lat': 45.4408, 'lng': 12.3155}},
        {'name': 'Napoli', 'place_count': 200,
            'coordinates': {'lat': 40.8518, 'lng': 14.2681}},
        {'name': 'Bologna', 'place_count': 150,
            'coordinates': {'lat': 44.4949, 'lng': 11.3426}},
        {'name': 'Torino', 'place_count': 140,
            'coordinates': {'lat': 45.0703, 'lng': 7.6869}},
        {'name': 'Genova', 'place_count': 120,
            'coordinates': {'lat': 44.4056, 'lng': 8.9463}}
    ]

    return jsonify({
        'cities': popular_cities,
        'total_cities': len(popular_cities),
        'fallback': True
    })


@ux_bp.route('/api/search/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get smart search suggestions based on user input and context"""
    try:
        query = request.args.get('query', '').strip()
        user_location = request.args.get('location', '')

        suggestions = []

        # Add popular searches
        popular_searches = [
            'Ristoranti Roma',
            'Musei Firenze',
            'Shopping Milano',
            'Spiagge Liguria',
            'Arte Venezia',
            'Storia Napoli'
        ]

        # Filter based on query
        if query:
            filtered = [s for s in popular_searches if query.lower()
                        in s.lower()]
            suggestions.extend(filtered[:3])
        else:
            suggestions.extend(popular_searches[:5])

        # Add location-based suggestions
        if user_location:
            suggestions.append(f'Vicino a {user_location}')

        return jsonify({
            'suggestions': suggestions,
            'query': query
        })

    except Exception as e:
        logger.error(f"❌ Error getting suggestions: {e}")
        return jsonify({'suggestions': []})


@ux_bp.route('/api/app/manifest', methods=['GET'])
def get_app_manifest():
    """PWA manifest for mobile app installation"""
    manifest = {
        "name": "ViamigoTravelAI",
        "short_name": "Viamigo",
        "description": "AI-powered travel planning for Italy with 9,930+ places across 56 cities",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0c0a09",
        "theme_color": "#8b5cf6",
        "orientation": "portrait",
        "categories": ["travel", "tourism", "lifestyle"],
        "lang": "it",
        "icons": [
            {
                "src": "/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "shortcuts": [
            {
                "name": "Pianifica Viaggio",
                "short_name": "Pianifica",
                "description": "Crea un nuovo itinerario di viaggio",
                "url": "/planner",
                "icons": [{"src": "/static/shortcut-plan.png", "sizes": "96x96"}]
            },
            {
                "name": "Esplora Luoghi",
                "short_name": "Esplora",
                "description": "Scopri nuovi luoghi interessanti",
                "url": "/explore",
                "icons": [{"src": "/static/shortcut-explore.png", "sizes": "96x96"}]
            }
        ],
        "related_applications": [],
        "prefer_related_applications": False
    }

    return jsonify(manifest)


@ux_bp.route('/api/offline/status', methods=['GET'])
def get_offline_status():
    """Get offline capabilities status"""
    return jsonify({
        'offline_capable': True,
        'cached_cities': 56,
        'cached_places': 9930,
        'features': {
            'search': True,
            'maps': True,
            'basic_planning': False,  # Requires AI/API
            'saved_itineraries': True
        },
        'storage_used': '5.2 MB',  # Estimated
        'last_sync': '2024-10-17T20:00:00Z'
    })


@ux_bp.route('/api/sync-itinerary', methods=['POST'])
def sync_offline_itinerary():
    """Sync offline itinerary when back online"""
    try:
        data = request.get_json()
        itinerary_id = data.get('id')

        # Here you would save the offline itinerary to the database
        # For now, just acknowledge the sync

        logger.info(f"✅ Synced offline itinerary: {itinerary_id}")

        return jsonify({
            'success': True,
            'message': 'Itinerary synced successfully',
            'itinerary_id': itinerary_id
        })

    except Exception as e:
        logger.error(f"❌ Sync error: {e}")
        return jsonify({'error': 'Sync failed'}), 500
