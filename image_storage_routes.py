"""
Image Storage Routes for ViamigoTravelAI
Serves stored attraction images from PostgreSQL with online fallback
"""
from flask import Blueprint, request, jsonify, Response
import psycopg2
import os
import logging
import requests
from io import BytesIO

# Create blueprint for image routes
image_routes_bp = Blueprint('image_routes', __name__)

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using DATABASE_URL"""
    try:
        # Read DATABASE_URL from environment or .env file
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            # Try reading from .env file
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith('DATABASE_URL='):
                            db_url = line.strip().split('=', 1)[1].strip('"\'')
                            break

        if not db_url:
            logger.error("DATABASE_URL not found")
            return None

        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


@image_routes_bp.route('/api/images/attraction/<int:image_id>')
def serve_attraction_image(image_id):
    """Serve stored attraction image by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        with conn.cursor() as cur:
            cur.execute("""
                SELECT img_bytes, mime_type, attraction_name, city
                FROM attraction_images 
                WHERE id = %s
            """, (image_id,))

            result = cur.fetchone()
            if not result:
                return jsonify({'error': 'Image not found'}), 404

            img_bytes, mime_type, name, city = result

        conn.close()

        return Response(
            img_bytes,
            mimetype=mime_type or 'image/jpeg',
            headers={
                'Content-Disposition': f'inline; filename="{name}_{city}.jpg"',
                'Cache-Control': 'public, max-age=86400'  # Cache for 24 hours
            }
        )

    except Exception as e:
        logger.error(f"Error serving image {image_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@image_routes_bp.route('/api/images/search')
def search_attraction_images():
    """Search for stored attraction images by city or attraction name"""
    try:
        city = request.args.get('city', '').strip()
        attraction = request.args.get('attraction', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)

        if not city and not attraction:
            return jsonify({'error': 'Provide city or attraction parameter'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        # Build query based on parameters
        where_conditions = []
        params = []

        if city:
            where_conditions.append("LOWER(city) = LOWER(%s)")
            params.append(city)

        if attraction:
            where_conditions.append("LOWER(attraction_name) ILIKE LOWER(%s)")
            params.append(f"%{attraction}%")

        where_clause = " AND ".join(where_conditions)
        params.append(limit)

        query = f"""
            SELECT id, city, attraction_name, attraction_qid,
                   original_url, thumb_url, mime_type,
                   width, height, LENGTH(img_bytes) as size_bytes
            FROM attraction_images 
            WHERE {where_clause}
            ORDER BY city, attraction_name
            LIMIT %s
        """

        with conn.cursor() as cur:
            cur.execute(query, params)
            results = cur.fetchall()

        conn.close()

        images = []
        for row in results:
            image_id, city, name, qid, orig_url, thumb_url, mime, width, height, size = row
            images.append({
                'id': image_id,
                'city': city,
                'attraction_name': name,
                'attraction_qid': qid,
                'local_url': f'/api/images/attraction/{image_id}',
                'original_url': orig_url,
                'thumb_url': thumb_url,
                'mime_type': mime,
                'width': width,
                'height': height,
                'size_bytes': size
            })

        return jsonify({
            'images': images,
            'count': len(images),
            'query': {'city': city, 'attraction': attraction}
        })

    except Exception as e:
        logger.error(f"Error searching images: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@image_routes_bp.route('/api/images/stats')
def get_image_stats():
    """Get statistics about stored images"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        with conn.cursor() as cur:
            # Get city statistics
            cur.execute("""
                SELECT city, COUNT(*) as count, 
                       SUM(LENGTH(img_bytes)) as total_bytes,
                       AVG(LENGTH(img_bytes)) as avg_bytes
                FROM attraction_images 
                GROUP BY city 
                ORDER BY count DESC
            """)
            city_stats = cur.fetchall()

            # Get overall statistics
            cur.execute("""
                SELECT COUNT(*) as total_images,
                       COUNT(DISTINCT city) as cities_count,
                       SUM(LENGTH(img_bytes)) as total_size,
                       AVG(LENGTH(img_bytes)) as avg_size
                FROM attraction_images
            """)
            overall = cur.fetchone()

        conn.close()

        return jsonify({
            'overall': {
                'total_images': overall[0],
                'cities_count': overall[1],
                'total_size_bytes': overall[2],
                'total_size_mb': round(overall[2] / 1024 / 1024, 2) if overall[2] else 0,
                'avg_size_bytes': round(overall[3]) if overall[3] else 0
            },
            'by_city': [
                {
                    'city': city,
                    'image_count': count,
                    'total_bytes': total_bytes,
                    'avg_bytes': round(avg_bytes)
                }
                for city, count, total_bytes, avg_bytes in city_stats
            ]
        })

    except Exception as e:
        logger.error(f"Error getting image stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500
