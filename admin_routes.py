"""
ADMIN ROUTES - Database Population & Management
Protected endpoints for populating PostgreSQL cache with Apify data
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import os
import json
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin secret key (set in .env)
ADMIN_SECRET = os.environ.get(
    'ADMIN_SECRET', 'change-this-secret-key-in-production')

# 🎯 SUPPORTED CATEGORIES - Full list for comprehensive itineraries
SUPPORTED_CATEGORIES = [
    'restaurant',
    'tourist_attraction',
    'hotel',
    'cafe',
    'museum',
    'monument',
    'park',
    'shopping',
    'nightlife',
    'bar',
    'bakery',
    'church'
]

# Default categories for basic population
DEFAULT_CATEGORIES = ['restaurant',
                      'tourist_attraction', 'hotel', 'cafe', 'museum']


def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('X-Admin-Secret')
        if not auth_header or auth_header != ADMIN_SECRET:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid or missing admin secret'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/populate-city', methods=['POST'])
@require_admin
def populate_city():
    """
    Populate PostgreSQL cache for a city using Apify

    POST /admin/populate-city
    Headers: X-Admin-Secret: your-secret-key
    Body: {
        "city": "Bergamo",
        "categories": ["tourist_attraction", "restaurant", "hotel", "cafe", "museum"],
        "force_refresh": false
    }

    Supported categories:
    - restaurant, tourist_attraction, hotel, cafe, museum
    - monument, park, shopping, nightlife, bar, bakery, church

    Returns: {
        "success": true,
        "city": "Bergamo",
        "results": {
            "tourist_attraction": 15,
            "restaurant": 10,
            "hotel": 8,
            "cafe": 5,
            "museum": 3
        },
        "duration_seconds": 120.5
    }
    """
    # Import here to avoid circular imports
    from apify_integration import apify_travel
    from models import db, PlaceCache

    try:
        data = request.get_json()
        city = data.get('city')
        categories = data.get('categories', DEFAULT_CATEGORIES)
        force_refresh = data.get('force_refresh', False)

        if not city:
            return jsonify({'error': 'City parameter is required'}), 400

        # Validate categories
        invalid_categories = [
            cat for cat in categories if cat not in SUPPORTED_CATEGORIES]
        if invalid_categories:
            return jsonify({
                'error': 'Invalid categories',
                'invalid': invalid_categories,
                'supported': SUPPORTED_CATEGORIES
            }), 400

        if not apify_travel.is_available():
            return jsonify({'error': 'Apify is not configured'}), 503

        start_time = datetime.now()
        results = {}

        print(f"\n{'='*60}")
        print(f"🔧 ADMIN: Populating cache for {city}")
        print(f"{'='*60}\n")

        for category in categories:
            print(f"\n📍 Processing category: {category}")

            # Check if cache exists
            cache_key = f"{city.lower()}_{category}"
            existing_cache = PlaceCache.query.filter_by(
                cache_key=cache_key).first()

            if existing_cache and not force_refresh:
                cached_data = json.loads(existing_cache.place_data)
                print(
                    f"✅ Cache already exists: {len(cached_data)} places (use force_refresh=true to update)")
                results[category] = {
                    'cached': True,
                    'count': len(cached_data),
                    'cache_age_hours': (datetime.now() - existing_cache.created_at).total_seconds() / 3600
                }
                continue

            # Call Apify to get fresh data
            print(f"🚀 Calling Apify for {city} - {category}...")
            places = apify_travel.search_google_maps_places(
                city=city,
                category=category,
                max_results=15
            )

            if places:
                # Cache the results
                print(
                    f"💾 Caching {len(places)} places for {city} - {category}")
                apify_travel.cache_places(city, category, places)
                results[category] = {
                    'cached': False,
                    'count': len(places),
                    'sample': places[0].get('name') if places else None
                }
                print(f"✅ Successfully cached {len(places)} places")
            else:
                print(f"⚠️ No places returned from Apify")
                results[category] = {
                    'cached': False,
                    'count': 0,
                    'error': 'No results from Apify'
                }

        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n{'='*60}")
        print(f"✅ ADMIN: Completed cache population for {city}")
        print(f"Duration: {duration:.1f} seconds")
        print(f"{'='*60}\n")

        return jsonify({
            'success': True,
            'city': city,
            'results': results,
            'duration_seconds': round(duration, 2)
        })

    except Exception as e:
        print(f"❌ ADMIN ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/populate-cities-batch', methods=['POST'])
@require_admin
def populate_cities_batch():
    """
    Populate multiple cities in one request

    POST /admin/populate-cities-batch
    Headers: X-Admin-Secret: your-secret-key
    Body: {
        "cities": ["Bergamo", "Bologna", "Verona", "Firenze"],
        "categories": ["tourist_attraction", "restaurant"],
        "delay_seconds": 5
    }

    Returns: {
        "success": true,
        "total_cities": 4,
        "results": { ... },
        "total_duration_seconds": 500.2
    }
    """
    # Import here to avoid circular imports
    from apify_integration import apify_travel
    from models import db, PlaceCache

    try:
        import time

        data = request.get_json()
        cities = data.get('cities', [])
        categories = data.get(
            'categories', ['tourist_attraction', 'restaurant'])
        delay_seconds = data.get('delay_seconds', 5)

        if not cities:
            return jsonify({'error': 'Cities list is required'}), 400

        if not apify_travel.is_available():
            return jsonify({'error': 'Apify is not configured'}), 503

        start_time = datetime.now()
        all_results = {}

        print(f"\n{'='*60}")
        print(f"🔧 ADMIN: Batch populating {len(cities)} cities")
        print(f"{'='*60}\n")

        for i, city in enumerate(cities, 1):
            print(f"\n[{i}/{len(cities)}] Processing {city}...")

            city_results = {}
            for category in categories:
                cache_key = f"{city.lower()}_{category}"
                existing = PlaceCache.query.filter_by(
                    cache_key=cache_key).first()

                if existing:
                    cached_data = json.loads(existing.place_data)
                    print(
                        f"  ✅ {category}: {len(cached_data)} places (cached)")
                    city_results[category] = {
                        'count': len(cached_data), 'cached': True}
                    continue

                print(f"  🚀 {category}: Calling Apify...")
                places = apify_travel.search_google_maps_places(
                    city, category, 15)

                if places:
                    apify_travel.cache_places(city, category, places)
                    print(f"  ✅ {category}: {len(places)} places cached")
                    city_results[category] = {
                        'count': len(places), 'cached': False}
                else:
                    print(f"  ⚠️ {category}: No results")
                    city_results[category] = {'count': 0, 'cached': False}

                # Delay between calls to avoid rate limiting
                if category != categories[-1] or city != cities[-1]:
                    print(f"  ⏳ Waiting {delay_seconds}s before next call...")
                    time.sleep(delay_seconds)

            all_results[city] = city_results

        duration = (datetime.now() - start_time).total_seconds()

        print(f"\n{'='*60}")
        print(f"✅ ADMIN: Batch completed")
        print(f"Total duration: {duration:.1f} seconds")
        print(f"{'='*60}\n")

        return jsonify({
            'success': True,
            'total_cities': len(cities),
            'results': all_results,
            'total_duration_seconds': round(duration, 2)
        })

    except Exception as e:
        print(f"❌ ADMIN BATCH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/cache-status', methods=['GET'])
@require_admin
def cache_status():
    """
    Get current cache status for all cities

    GET /admin/cache-status
    Headers: X-Admin-Secret: your-secret-key

    Returns: {
        "total_cached_cities": 15,
        "total_entries": 30,
        "cities": { ... }
    }
    """
    # Import here to avoid circular imports
    from models import PlaceCache

    try:
        all_caches = PlaceCache.query.all()

        cities_data = {}
        for cache in all_caches:
            parts = cache.cache_key.split('_', 1)
            if len(parts) == 2:
                city, category = parts
                if city not in cities_data:
                    cities_data[city] = {}

                place_data = json.loads(cache.place_data)
                cities_data[city][category] = {
                    'count': len(place_data) if isinstance(place_data, list) else 1,
                    'cache_age_hours': round((datetime.now() - cache.created_at).total_seconds() / 3600, 1),
                    'created_at': cache.created_at.isoformat()
                }

        return jsonify({
            'success': True,
            'total_cached_cities': len(cities_data),
            'total_entries': len(all_caches),
            'cities': cities_data
        })

    except Exception as e:
        print(f"❌ ADMIN ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/clear-cache', methods=['POST'])
@require_admin
def clear_cache():
    """
    Clear cache for specific city or all cities

    POST /admin/clear-cache
    Headers: X-Admin-Secret: your-secret-key
    Body: {
        "city": "Bergamo",  // optional, omit to clear all
        "category": "tourist_attraction"  // optional
    }
    """
    # Import here to avoid circular imports
    from models import db, PlaceCache

    try:
        data = request.get_json() or {}
        city = data.get('city')
        category = data.get('category')

        if city and category:
            cache_key = f"{city.lower()}_{category}"
            deleted = PlaceCache.query.filter_by(cache_key=cache_key).delete()
        elif city:
            deleted = PlaceCache.query.filter(
                PlaceCache.cache_key.startswith(f"{city.lower()}_")).delete()
        else:
            deleted = PlaceCache.query.delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_entries': deleted,
            'message': f'Cleared {deleted} cache entries'
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ ADMIN ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_bp.route('/supported-categories', methods=['GET'])
def supported_categories():
    """
    Get list of supported categories (no auth required for info endpoint)

    GET /admin/supported-categories

    Returns: {
        "supported_categories": [...],
        "default_categories": [...],
        "total": 12
    }
    """
    return jsonify({
        'supported_categories': SUPPORTED_CATEGORIES,
        'default_categories': DEFAULT_CATEGORIES,
        'total': len(SUPPORTED_CATEGORIES),
        'info': {
            'restaurant': 'Best restaurants and trattorias',
            'tourist_attraction': 'Top attractions and sights',
            'hotel': 'Hotels and accommodations',
            'cafe': 'Cafes and coffee shops',
            'museum': 'Museums and galleries',
            'monument': 'Monuments and landmarks',
            'park': 'Parks and gardens',
            'shopping': 'Shopping centers and markets',
            'nightlife': 'Nightclubs and entertainment',
            'bar': 'Bars and pubs',
            'bakery': 'Bakeries and pastry shops',
            'church': 'Churches and religious sites'
        }
    })
