"""
Flask routes for Hotels Integration
Provides API endpoints for hotel search, recommendations, and route integration
"""

from flask import Blueprint, jsonify, request
from hotels_integration import HotelsIntegration, get_accommodation_suggestions
from hotel_availability_checker import check_hotel_availability, get_supported_cities, normalize_city_name
import logging

# Create blueprint
hotels_bp = Blueprint('hotels', __name__, url_prefix='/api/hotels')
logger = logging.getLogger(__name__)


@hotels_bp.route('/availability/<city>', methods=['GET'])
def check_city_availability(city):
    """
    Check if hotel data is available for a given city
    CALL THIS FIRST before showing hotel features in frontend

    Returns:
        {
            "available": true/false,
            "city": "Milan",
            "hotel_count": 161,
            "avg_rating": 8.4,
            "message": "Hotel data available for Milan"
        }

    Example: GET /api/hotels/availability/Milan
    Example: GET /api/hotels/availability/Florence (will return available=false)
    """
    try:
        result = check_hotel_availability(city)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        logger.error(f"Error checking availability for {city}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'available': False,
            'city': city,
            'message': 'Error checking hotel availability'
        }), 500


@hotels_bp.route('/supported-cities', methods=['GET'])
def list_supported_cities():
    """
    Get list of all cities with hotel data
    Use this to show users which cities have hotel features enabled

    Returns:
        {
            "success": true,
            "count": 2,
            "cities": [
                {
                    "city": "Milan",
                    "hotel_count": 161,
                    "avg_rating": 8.4,
                    "total_reviews": 37138,
                    "luxury_count": 25,
                    "premium_count": 36,
                    "mid_range_count": 67,
                    "budget_count": 33
                }
            ]
        }

    Example: GET /api/hotels/supported-cities
    """
    try:
        cities = get_supported_cities()

        return jsonify({
            'success': True,
            'count': len(cities),
            'cities': cities
        })

    except Exception as e:
        logger.error(f"Error getting supported cities: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'cities': []
        }), 500


@hotels_bp.route('/search', methods=['GET'])
def search_hotels():
    """
    Search for hotels in a city

    Query params:
        city: City name (default: Milan)
        q: Search query (optional)
        min_rating: Minimum rating (default: 8.0)
        limit: Max results (default: 10)

    Returns:
        JSON list of hotels
    """
    try:
        city = request.args.get('city', 'Milan')
        query = request.args.get('q', None)
        min_rating = float(request.args.get('min_rating', 8.0))
        limit = int(request.args.get('limit', 10))

        hotels = HotelsIntegration()
        results = hotels.search_hotels(
            city=city,
            search_term=query,
            min_rating=min_rating,
            limit=limit
        )

        logger.info(
            f"🏨 Hotel search: city={city}, query={query}, found={len(results)}")

        return jsonify({
            'success': True,
            'count': len(results),
            'hotels': results
        })

    except Exception as e:
        logger.error(f"❌ Hotel search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@hotels_bp.route('/nearby', methods=['GET'])
def nearby_hotels():
    """
    Get hotels near a location

    Query params:
        lat: Latitude (required)
        lng: Longitude (required)
        radius: Radius in km (default: 1.0)
        min_rating: Minimum rating (default: 8.0)
        limit: Max results (default: 10)

    Returns:
        JSON list of nearby hotels with distances
    """
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        radius = float(request.args.get('radius', 1.0))
        min_rating = float(request.args.get('min_rating', 8.0))
        limit = int(request.args.get('limit', 10))

        hotels = HotelsIntegration()
        results = hotels.get_hotels_near_location(
            latitude=lat,
            longitude=lng,
            radius_km=radius,
            min_rating=min_rating,
            limit=limit
        )

        logger.info(
            f"🏨 Nearby hotels: ({lat}, {lng}), radius={radius}km, found={len(results)}")

        return jsonify({
            'success': True,
            'count': len(results),
            'hotels': results,
            'center': {'lat': lat, 'lng': lng},
            'radius_km': radius
        })

    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
    except Exception as e:
        logger.error(f"❌ Nearby hotels error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@hotels_bp.route('/top/<city>', methods=['GET'])
def top_hotels(city):
    """
    Get top-rated hotels in a city

    URL params:
        city: City name

    Query params:
        category: luxury/premium/mid-range/budget/all (default: all)
        limit: Max results (default: 20)

    Returns:
        JSON list of top hotels
    """
    try:
        category = request.args.get('category', 'all')
        limit = int(request.args.get('limit', 20))

        hotels = HotelsIntegration()
        results = hotels.get_top_hotels_by_city(
            city=city,
            category=category,
            limit=limit
        )

        logger.info(
            f"🏨 Top hotels: city={city}, category={category}, found={len(results)}")

        return jsonify({
            'success': True,
            'city': city,
            'category': category,
            'count': len(results),
            'hotels': results
        })

    except Exception as e:
        logger.error(f"❌ Top hotels error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@hotels_bp.route('/details/<hotel_name>', methods=['GET'])
def hotel_details(hotel_name):
    """
    Get details for a specific hotel

    URL params:
        hotel_name: Name of the hotel

    Query params:
        city: City name (optional but recommended)

    Returns:
        JSON hotel details
    """
    try:
        city = request.args.get('city', None)

        hotels = HotelsIntegration()
        hotel = hotels.get_hotel_by_name(hotel_name, city)

        if hotel:
            logger.info(f"🏨 Hotel details: {hotel_name} found")
            return jsonify({
                'success': True,
                'hotel': hotel
            })
        else:
            logger.warning(f"⚠️ Hotel not found: {hotel_name}")
            return jsonify({
                'success': False,
                'error': 'Hotel not found'
            }), 404

    except Exception as e:
        logger.error(f"❌ Hotel details error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@hotels_bp.route('/accommodation-suggestions', methods=['POST'])
def accommodation_suggestions():
    """
    Get hotel suggestions for a route or location

    POST body:
        lat: Latitude
        lng: Longitude
        city: City name (default: Milan)

    Returns:
        JSON list of suggested hotels
    """
    try:
        data = request.get_json()
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        city = data.get('city', 'Milan')

        suggestions = get_accommodation_suggestions(lat, lng, city)

        logger.info(
            f"🏨 Accommodation suggestions: ({lat}, {lng}), found={len(suggestions)}")

        return jsonify({
            'success': True,
            'count': len(suggestions),
            'suggestions': suggestions
        })

    except (ValueError, KeyError):
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    except Exception as e:
        logger.error(f"❌ Accommodation suggestions error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@hotels_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    Get available hotel categories with definitions

    Returns:
        JSON with category information
    """
    categories = {
        'luxury': {
            'name': 'Luxury',
            'min_rating': 9.0,
            'description': 'Five-star luxury hotels with exceptional service'
        },
        'premium': {
            'name': 'Premium',
            'min_rating': 8.5,
            'description': 'High-quality hotels with excellent amenities'
        },
        'mid-range': {
            'name': 'Mid-Range',
            'min_rating': 8.0,
            'description': 'Good quality hotels at reasonable prices'
        },
        'budget': {
            'name': 'Budget',
            'min_rating': 7.0,
            'description': 'Affordable hotels with basic amenities'
        },
        'all': {
            'name': 'All Categories',
            'min_rating': 0.0,
            'description': 'All hotels regardless of rating'
        }
    }

    return jsonify({
        'success': True,
        'categories': categories
    })


@hotels_bp.route('/stats/<city>', methods=['GET'])
def city_stats(city):
    """
    Get statistics about hotels in a city

    URL params:
        city: City name

    Returns:
        JSON with hotel statistics
    """
    try:
        hotels = HotelsIntegration()
        conn = hotels.get_connection()
        cursor = conn.cursor()

        # Get stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT hotel_name) as hotel_count,
                COUNT(*) as review_count,
                AVG(average_score) as avg_rating,
                MAX(average_score) as max_rating,
                MIN(average_score) as min_rating
            FROM hotel_reviews
            WHERE city = %s OR LOWER(city) LIKE LOWER(%s)
        """, (city, f'%{city}%'))

        row = cursor.fetchone()

        # Get category breakdown
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN average_score >= 9.0 THEN 'luxury'
                    WHEN average_score >= 8.5 THEN 'premium'
                    WHEN average_score >= 8.0 THEN 'mid-range'
                    ELSE 'budget'
                END as category,
                COUNT(DISTINCT hotel_name) as count
            FROM hotel_reviews
            WHERE city = %s OR LOWER(city) LIKE LOWER(%s)
            GROUP BY category
            ORDER BY category
        """, (city, f'%{city}%'))

        categories = {cat: count for cat, count in cursor.fetchall()}

        cursor.close()
        conn.close()

        logger.info(f"📊 Hotel stats for {city}")

        return jsonify({
            'success': True,
            'city': city,
            'stats': {
                'total_hotels': row[0],
                'total_reviews': row[1],
                'average_rating': round(float(row[2]), 1) if row[2] else 0,
                'max_rating': float(row[3]) if row[3] else 0,
                'min_rating': float(row[4]) if row[4] else 0,
                'by_category': categories
            }
        })

    except Exception as e:
        logger.error(f"❌ City stats error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Register blueprint function for flask_app.py
def register_hotels_routes(app):
    """Register hotels blueprint with the Flask app"""
    app.register_blueprint(hotels_bp)
    logger.info("✅ Hotels API routes registered")
