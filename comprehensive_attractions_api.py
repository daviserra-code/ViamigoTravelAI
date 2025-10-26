#!/usr/bin/env python3
"""
Enhanced API routes for comprehensive attractions data
Integrates OSM + Wikidata + Commons data with ViamigoTravelAI
"""
from flask import Blueprint, jsonify, request
import psycopg2
import os
from typing import Dict, List, Optional
import json

comprehensive_attractions_bp = Blueprint('comprehensive_attractions', __name__)


def get_db_connection():
    """Get database connection"""
    db_url = os.getenv('DATABASE_URL') or os.getenv('NEON_POSTGRES_POOLED_URL')
    return psycopg2.connect(db_url)


@comprehensive_attractions_bp.route('/api/attractions/comprehensive/stats', methods=['GET'])
def get_comprehensive_stats():
    """Get comprehensive statistics about the attractions dataset"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Overall stats
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_attractions,
                        COUNT(DISTINCT city) as cities_count,
                        COUNT(*) FILTER (WHERE has_image = true) as with_images,
                        COUNT(*) FILTER (WHERE wikidata_id IS NOT NULL) as with_wikidata,
                        COUNT(*) FILTER (WHERE source_commons = true) as from_commons,
                        AVG(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as coord_coverage
                    FROM comprehensive_attractions
                """)

                overall_stats = cur.fetchone()

                # Stats by city
                cur.execute("""
                    SELECT 
                        city,
                        COUNT(*) as total_count,
                        COUNT(*) FILTER (WHERE has_image = true) as with_images,
                        COUNT(*) FILTER (WHERE wikidata_id IS NOT NULL) as with_wikidata,
                        COUNT(DISTINCT category) as unique_categories
                    FROM comprehensive_attractions
                    GROUP BY city
                    ORDER BY total_count DESC
                """)

                city_stats = cur.fetchall()

                # Stats by category
                cur.execute("""
                    SELECT 
                        category,
                        attraction_type,
                        COUNT(*) as count,
                        COUNT(*) FILTER (WHERE has_image = true) as with_images
                    FROM comprehensive_attractions
                    GROUP BY category, attraction_type
                    ORDER BY count DESC
                    LIMIT 20
                """)

                category_stats = cur.fetchall()

                return jsonify({
                    'overall': {
                        'total_attractions': overall_stats[0],
                        'cities_count': overall_stats[1],
                        'with_images': overall_stats[2],
                        'with_wikidata': overall_stats[3],
                        'from_commons': overall_stats[4],
                        'coordinate_coverage': float(overall_stats[5] or 0)
                    },
                    'by_city': [
                        {
                            'city': row[0],
                            'total_count': row[1],
                            'with_images': row[2],
                            'with_wikidata': row[3],
                            'unique_categories': row[4]
                        }
                        for row in city_stats
                    ],
                    'by_category': [
                        {
                            'category': row[0],
                            'attraction_type': row[1],
                            'count': row[2],
                            'with_images': row[3]
                        }
                        for row in category_stats
                    ]
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@comprehensive_attractions_bp.route('/api/attractions/comprehensive/search', methods=['GET'])
def search_comprehensive_attractions():
    """Search comprehensive attractions with various filters"""
    try:
        # Parse query parameters
        city = request.args.get('city')
        category = request.args.get('category')
        has_image = request.args.get('has_image', '').lower() == 'true'
        has_wikidata = request.args.get('has_wikidata', '').lower() == 'true'
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
        search_term = request.args.get('search', '')
        query_param = request.args.get('query', '')  # Main search parameter

        # City mapping for regions stored in database
        city_region_mapping = {
            'milano': 'Lombardia',
            'milan': 'Lombardia',
            'torino': 'Piemonte',
            'turin': 'Piemonte',
            'florence': 'Toscana',
            'firenze': 'Toscana'
        }

        # Build query
        conditions = []
        params = []

        # Handle main query parameter (for searches like "Duomo Milano")
        if query_param:
            query_lower = query_param.lower()

            # Check if query contains city names that need region mapping
            mapped_city = None
            for city_name, region in city_region_mapping.items():
                if city_name in query_lower:
                    mapped_city = region
                    break

            if mapped_city:
                # Search in the mapped region
                conditions.append(
                    "(city ILIKE %s AND (name ILIKE %s OR description ILIKE %s))")
                params.extend(
                    [f"%{mapped_city}%", f"%{query_param}%", f"%{query_param}%"])
            else:
                # Regular search across all attractions
                conditions.append(
                    "(name ILIKE %s OR description ILIKE %s OR city ILIKE %s)")
                params.extend(
                    [f"%{query_param}%", f"%{query_param}%", f"%{query_param}%"])

        if city:
            # Apply city mapping if needed
            city_mapped = city_region_mapping.get(city.lower(), city)
            conditions.append("city ILIKE %s")
            params.append(f"%{city_mapped}%")

        if category:
            conditions.append("category ILIKE %s")
            params.append(f"%{category}%")

        if has_image:
            conditions.append("has_image = true")

        if has_wikidata:
            conditions.append("wikidata_id IS NOT NULL")

        if search_term:
            conditions.append("(name ILIKE %s OR description ILIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        where_clause = "WHERE " + \
            " AND ".join(conditions) if conditions else ""

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get attractions
                query = f"""
                    SELECT 
                        id, city, name, description, category, attraction_type,
                        latitude, longitude, osm_id, wikidata_id, wikipedia_url,
                        has_image, thumb_url, image_license, image_creator,
                        source_osm, source_wikidata, source_commons,
                        created_at
                    FROM comprehensive_attractions
                    {where_clause}
                    ORDER BY 
                        CASE WHEN has_image THEN 0 ELSE 1 END,
                        CASE WHEN wikidata_id IS NOT NULL THEN 0 ELSE 1 END,
                        name
                    LIMIT %s OFFSET %s
                """

                params.extend([limit, offset])
                cur.execute(query, params)
                attractions = cur.fetchall()

                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM comprehensive_attractions {where_clause}
                """
                cur.execute(count_query, params[:-2])  # Exclude limit/offset
                total_count = cur.fetchone()[0]

                return jsonify({
                    'attractions': [
                        {
                            'id': row[0],
                            'city': row[1],
                            'name': row[2],
                            'description': row[3],
                            'category': row[4],
                            'attraction_type': row[5],
                            'coordinates': {
                                'lat': float(row[6]) if row[6] else None,
                                'lon': float(row[7]) if row[7] else None
                            },
                            'osm_id': row[8],
                            'wikidata_id': row[9],
                            'wikipedia_url': row[10],
                            'has_image': row[11],
                            'thumb_url': row[12],
                            'image_license': row[13],
                            'image_creator': row[14],
                            'sources': {
                                'osm': row[15],
                                'wikidata': row[16],
                                'commons': row[17]
                            },
                            'created_at': row[18].isoformat() if row[18] else None
                        }
                        for row in attractions
                    ],
                    'pagination': {
                        'total': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_more': offset + limit < total_count
                    },
                    'filters_applied': {
                        'city': city,
                        'category': category,
                        'has_image': has_image,
                        'has_wikidata': has_wikidata,
                        'search_term': search_term
                    }
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@comprehensive_attractions_bp.route('/api/attractions/comprehensive/<int:attraction_id>', methods=['GET'])
def get_attraction_details(attraction_id):
    """Get detailed information about a specific attraction"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get attraction details
                cur.execute("""
                    SELECT 
                        id, city, name, raw_name, description, category, attraction_type,
                        latitude, longitude, osm_id, osm_type, osm_tags,
                        wikidata_id, wikipedia_url, has_image, image_url, thumb_url, original_url,
                        image_creator, image_license, image_attribution,
                        source_osm, source_wikidata, source_commons,
                        created_at, updated_at
                    FROM comprehensive_attractions
                    WHERE id = %s
                """, (attraction_id,))

                attraction = cur.fetchone()
                if not attraction:
                    return jsonify({'error': 'Attraction not found'}), 404

                # Get related images from attraction_images table
                cur.execute("""
                    SELECT 
                        id, file_size, confidence_score, 
                        original_title, content_url, license, creator, attribution,
                        created_at
                    FROM attraction_images
                    WHERE osm_id = %s OR wikidata_id = %s
                    ORDER BY confidence_score DESC
                    LIMIT 5
                """, (attraction[8], attraction[12]))  # osm_id, wikidata_id

                related_images = cur.fetchall()

                return jsonify({
                    'attraction': {
                        'id': attraction[0],
                        'city': attraction[1],
                        'name': attraction[2],
                        'raw_name': attraction[3],
                        'description': attraction[4],
                        'category': attraction[5],
                        'attraction_type': attraction[6],
                        'coordinates': {
                            'lat': float(attraction[7]) if attraction[7] else None,
                            'lon': float(attraction[8]) if attraction[8] else None
                        },
                        'osm': {
                            'id': attraction[9],
                            'type': attraction[10],
                            'tags': json.loads(attraction[11]) if attraction[11] else {}
                        },
                        'external_links': {
                            'wikidata_id': attraction[12],
                            'wikipedia_url': attraction[13]
                        },
                        'image': {
                            'has_image': attraction[14],
                            'image_url': attraction[15],
                            'thumb_url': attraction[16],
                            'original_url': attraction[17],
                            'creator': attraction[18],
                            'license': attraction[19],
                            'attribution': attraction[20]
                        },
                        'sources': {
                            'osm': attraction[21],
                            'wikidata': attraction[22],
                            'commons': attraction[23]
                        },
                        'metadata': {
                            'created_at': attraction[24].isoformat() if attraction[24] else None,
                            'updated_at': attraction[25].isoformat() if attraction[25] else None
                        }
                    },
                    'related_images': [
                        {
                            'id': img[0],
                            'file_size': img[1],
                            'confidence_score': float(img[2]) if img[2] else None,
                            'title': img[3],
                            'url': img[4],
                            'license': img[5],
                            'creator': img[6],
                            'attribution': img[7],
                            'created_at': img[8].isoformat() if img[8] else None
                        }
                        for img in related_images
                    ]
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@comprehensive_attractions_bp.route('/api/attractions/comprehensive/categories', methods=['GET'])
def get_attraction_categories():
    """Get list of all attraction categories and types"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        category,
                        attraction_type,
                        COUNT(*) as count,
                        COUNT(*) FILTER (WHERE has_image = true) as with_images
                    FROM comprehensive_attractions
                    GROUP BY category, attraction_type
                    ORDER BY count DESC
                """)

                categories = cur.fetchall()

                return jsonify({
                    'categories': [
                        {
                            'category': row[0],
                            'attraction_type': row[1],
                            'count': row[2],
                            'with_images': row[3]
                        }
                        for row in categories
                    ]
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@comprehensive_attractions_bp.route('/api/attractions/comprehensive/nearby', methods=['GET'])
def find_nearby_attractions():
    """Find attractions near given coordinates"""
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius_km = float(request.args.get('radius', 1.0))
        limit = min(int(request.args.get('limit', 20)), 100)

        if not lat or not lon:
            return jsonify({'error': 'lat and lon parameters required'}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Use Haversine formula for distance calculation
                cur.execute("""
                    SELECT 
                        id, city, name, description, category, attraction_type,
                        latitude, longitude, has_image, thumb_url, wikidata_id,
                        (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) 
                         * cos(radians(longitude) - radians(%s)) 
                         + sin(radians(%s)) * sin(radians(latitude)))) as distance_km
                    FROM comprehensive_attractions
                    WHERE latitude IS NOT NULL 
                      AND longitude IS NOT NULL
                    HAVING distance_km <= %s
                    ORDER BY distance_km
                    LIMIT %s
                """, (lat, lon, lat, radius_km, limit))

                nearby = cur.fetchall()

                return jsonify({
                    'nearby_attractions': [
                        {
                            'id': row[0],
                            'city': row[1],
                            'name': row[2],
                            'description': row[3],
                            'category': row[4],
                            'attraction_type': row[5],
                            'coordinates': {
                                'lat': float(row[6]),
                                'lon': float(row[7])
                            },
                            'has_image': row[8],
                            'thumb_url': row[9],
                            'wikidata_id': row[10],
                            'distance_km': round(float(row[11]), 2)
                        }
                        for row in nearby
                    ],
                    'search_params': {
                        'center': {'lat': lat, 'lon': lon},
                        'radius_km': radius_km,
                        'found_count': len(nearby)
                    }
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@comprehensive_attractions_bp.route('/api/attractions/comprehensive/city/<city>', methods=['GET'])
def get_city_attractions_comprehensive(city):
    """Get attractions for a specific city with enhanced results for famous places"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Special handling for famous attractions that might be missing
                famous_attractions = {
                    'roma': ['pantheon', 'colosseo', 'colosseum', 'trevi', 'vaticano'],
                    'milano': ['duomo', 'scala', 'castello sforzesco', 'navigli'],
                    'firenze': ['duomo', 'ponte vecchio', 'uffizi', 'palazzo pitti'],
                    'venezia': ['san marco', 'palazzo ducale', 'rialto', 'murano'],
                    'napoli': ['vesuvio', 'pompei', 'castel dell\'ovo', 'spaccanapoli'],
                    'genova': ['acquario', 'palazzo rosso', 'palazzo bianco', 'cattedrale', 'via del campo', 'spianata castelletto', 'lanterna']
                }

                city_lower = city.lower()

                # Build query with preference for famous attractions
                query = """
                    SELECT 
                        id, city, name, description, category, attraction_type,
                        latitude, longitude, osm_id, wikidata_id, wikipedia_url,
                        has_image, thumb_url, image_license, image_creator,
                        source_osm, source_wikidata, source_commons,
                        created_at,
                        CASE 
                """

                # Add scoring for famous attractions
                params = [f"%{city}%"]
                if city_lower in famous_attractions:
                    for i, famous in enumerate(famous_attractions[city_lower]):
                        query += f" WHEN LOWER(name) LIKE %s THEN {len(famous_attractions[city_lower]) - i}"
                        params.append(f"%{famous}%")

                query += """
                            ELSE 0 
                        END as fame_score
                    FROM comprehensive_attractions
                    WHERE city ILIKE %s
                    ORDER BY 
                        fame_score DESC,
                        CASE WHEN has_image THEN 0 ELSE 1 END,
                        CASE WHEN wikidata_id IS NOT NULL THEN 0 ELSE 1 END,
                        name
                    LIMIT 50
                """

                params.append(f"%{city}%")
                cur.execute(query, params)
                attractions = cur.fetchall()

                results = []
                for row in attractions:
                    attraction = {
                        'id': row[0],
                        'city': row[1],
                        'name': row[2],
                        'description': row[3] or f"Important attraction in {city}",
                        'category': row[4],
                        'attraction_type': row[5],
                        'coordinates': {
                            'lat': float(row[6]) if row[6] else None,
                            'lon': float(row[7]) if row[7] else None
                        },
                        'osm_id': row[8],
                        'wikidata_id': row[9],
                        'wikipedia_url': row[10],
                        'has_image': row[11],
                        'thumb_url': row[12],
                        'image_license': row[13],
                        'image_creator': row[14],
                        'sources': {
                            'osm': row[15],
                            'wikidata': row[16],
                            'commons': row[17]
                        },
                        'fame_score': row[19] if len(row) > 19 else 0,
                        'created_at': row[18].isoformat() if row[18] else None
                    }
                    results.append(attraction)

                return jsonify({
                    'city': city,
                    'attractions': results,
                    'total_count': len(results),
                    'with_images': len([a for a in results if a['has_image']]),
                    'famous_found': len([a for a in results if a.get('fame_score', 0) > 0]),
                    'success': True
                })

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
