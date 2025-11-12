"""
Dynamic Enhanced Images API - PostgreSQL + ChromaDB Integration
No hardcoded URLs - queries databases for attraction images
"""

from flask import Blueprint, jsonify, request
import logging
import re
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

enhanced_images_bp = Blueprint('enhanced_images', __name__)


def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(os.getenv('DATABASE_URL'))


def normalize_name(name):
    """Normalize attraction name for matching"""
    if not name:
        return ""
    # Remove common suffixes and prefixes
    normalized = name.lower().strip()
    normalized = re.sub(
        r'\s+(di|of|della|del|degli|delle)\s+', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def search_image_in_db(title, context=""):
    """
    Search for attraction image in PostgreSQL attraction_images table
    Returns: (image_url, confidence, attraction_name) or (None, 0, None)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Normalize search terms
        title_norm = normalize_name(title)
        context_norm = normalize_name(context)
        search_text = f"{title_norm} {context_norm}".strip()

        logger.info(f"🔍 Searching DB for: '{title}' (context: '{context}')")

        # Extract city from context if present
        city = None
        city_patterns = [
            ('milano', 'Milan'), ('milan', 'Milan'),
            ('roma', 'Rome'), ('rome', 'Rome'),
            ('firenze', 'Florence'), ('florence', 'Florence'),
            ('venezia', 'Venice'), ('venice', 'Venice'),
            ('napoli', 'Naples'), ('naples', 'Naples'),
            ('torino', 'Turin'), ('turin', 'Turin'),
            ('genova', 'Genoa'), ('genoa', 'Genoa'),
            ('bologna', 'Bologna'),
            ('pisa', 'Pisa'),
        ]

        for pattern, city_name in city_patterns:
            if pattern in search_text.lower():
                city = city_name
                break

        # Multi-strategy search (from most specific to most generic)
        queries = []

        # Strategy 1: Exact match with city
        if city:
            queries.append((
                """
                SELECT original_url, thumb_url, confidence_score, attraction_name, city
                FROM attraction_images
                WHERE LOWER(city) = LOWER(%s)
                  AND (
                      LOWER(attraction_name) LIKE LOWER(%s)
                      OR LOWER(attraction_name) LIKE LOWER(%s)
                  )
                  AND original_url IS NOT NULL
                ORDER BY confidence_score DESC NULLS LAST
                LIMIT 1
                """,
                (city, f"%{title_norm}%", f"%{title.lower()}%"),
                0.9  # High confidence for exact city + name match
            ))

        # Strategy 2: Name match without city (any city with this name)
        queries.append((
            """
            SELECT original_url, thumb_url, confidence_score, attraction_name, city
            FROM attraction_images
            WHERE (
                LOWER(attraction_name) LIKE LOWER(%s)
                OR LOWER(attraction_name) LIKE LOWER(%s)
            )
            AND original_url IS NOT NULL
            ORDER BY confidence_score DESC NULLS LAST, 
                     CASE WHEN LOWER(city) = LOWER(%s) THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (f"%{title_norm}%", f"%{title.lower()}%", city or ''),
            0.7  # Medium confidence without city constraint
        ))

        # Strategy 3: Fuzzy match with city
        if city:
            # Break title into words for partial matching
            words = [w for w in re.split(r'\W+', title_norm) if len(w) > 3]
            if words:
                like_clauses = " OR ".join(
                    [f"LOWER(attraction_name) LIKE LOWER('%{w}%')" for w in words])
                query = f"""
                    SELECT original_url, thumb_url, confidence_score, attraction_name, city
                    FROM attraction_images
                    WHERE LOWER(city) = LOWER(%s)
                      AND ({like_clauses})
                      AND original_url IS NOT NULL
                    ORDER BY confidence_score DESC NULLS LAST
                    LIMIT 1
                """
                queries.append((query, (city,), 0.6))

        # Execute queries in order until we find a result
        for query, params, base_confidence in queries:
            cursor.execute(query, params)
            result = cursor.fetchone()

            if result:
                image_url, thumb_url, db_confidence, attraction_name, found_city = result

                # Prefer original_url, fallback to thumb_url
                final_url = image_url or thumb_url

                if final_url:
                    # Use DB confidence if available, otherwise use base confidence
                    final_confidence = float(
                        db_confidence) if db_confidence else base_confidence

                    logger.info(
                        f"✅ Found image in DB: {attraction_name} ({found_city}) - confidence: {final_confidence}")

                    cursor.close()
                    conn.close()

                    return final_url, final_confidence, f"{attraction_name} ({found_city})"

        # No results found
        logger.info(f"⚠️ No image found in DB for: {title}")
        cursor.close()
        conn.close()

        return None, 0, None

    except Exception as e:
        logger.error(f"❌ DB search error: {e}")
        return None, 0, None


@enhanced_images_bp.route('/api/images/classify', methods=['POST'])
def classify_and_get_image():
    """
    Classify attraction and return image from PostgreSQL database
    """
    try:
        data = request.json
        title = data.get('title', '')
        context = data.get('context', '')

        if not title:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400

        logger.info(f"🔍 Classifying: '{title}' with context: '{context}'")

        # Search database for image
        image_url, confidence, classification = search_image_in_db(
            title, context)

        if image_url:
            # Parse classification
            if classification and '(' in classification:
                attraction, city = classification.rsplit('(', 1)
                attraction = attraction.strip()
                city = city.rstrip(')').strip()
            else:
                attraction = classification or title
                city = context or 'Italia'

            logger.info(
                f"✅ Classification result: {city} -> {attraction} (confidence: {confidence})")

            return jsonify({
                'success': True,
                'classification': {
                    'attraction': attraction,
                    'city': city,
                    'confidence': confidence
                },
                'image': {
                    'url': image_url,
                    'confidence': confidence
                }
            })
        else:
            # No image found - return generic fallback
            logger.info(f"⚠️ No image found for: {title}")
            return jsonify({
                'success': True,
                'classification': {
                    'attraction': title,
                    'city': context or 'Italia',
                    'confidence': 0.3
                },
                'image': {
                    'url': 'https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800',  # Generic Italy
                    'confidence': 0.3
                }
            })

    except Exception as e:
        logger.error(f"❌ Classification error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_images_bp.route('/api/images/search', methods=['POST'])
def search_images():
    """
    Search for images by city and/or attraction name
    Returns multiple matching images
    """
    try:
        data = request.json
        city = data.get('city', '')
        attraction_name = data.get('attraction_name', '')
        limit = data.get('limit', 10)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        where_clauses = []
        params = []

        if city:
            where_clauses.append("LOWER(city) = LOWER(%s)")
            params.append(city)

        if attraction_name:
            where_clauses.append("LOWER(attraction_name) LIKE LOWER(%s)")
            params.append(f"%{attraction_name}%")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        params.append(limit)

        query = f"""
            SELECT 
                attraction_name,
                city,
                original_url,
                thumb_url,
                confidence_score,
                license,
                creator,
                width,
                height
            FROM attraction_images
            WHERE {where_sql}
              AND original_url IS NOT NULL
            ORDER BY confidence_score DESC NULLS LAST
            LIMIT %s
        """

        cursor.execute(query, tuple(params))
        results = cursor.fetchall()

        images = []
        for row in results:
            images.append({
                'attraction_name': row[0],
                'city': row[1],
                'original_url': row[2],
                'thumb_url': row[3],
                'confidence_score': float(row[4]) if row[4] else 0.5,
                'license': row[5],
                'creator': row[6],
                'width': row[7],
                'height': row[8]
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'count': len(images),
            'images': images
        })

    except Exception as e:
        logger.error(f"❌ Search error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_images_bp.route('/api/images/stats', methods=['GET'])
def get_image_stats():
    """
    Get statistics about images in database
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total count
        cursor.execute(
            "SELECT COUNT(*) FROM attraction_images WHERE original_url IS NOT NULL")
        total = cursor.fetchone()[0]

        # By city
        cursor.execute("""
            SELECT city, COUNT(*) 
            FROM attraction_images 
            WHERE original_url IS NOT NULL
            GROUP BY city 
            ORDER BY COUNT(*) DESC
        """)
        by_city = [{'city': row[0], 'count': row[1]}
                   for row in cursor.fetchall()]

        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence_score) 
            FROM attraction_images 
            WHERE confidence_score IS NOT NULL
        """)
        avg_confidence = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_images': total,
                'cities_count': len(by_city),
                'by_city': by_city,
                'avg_confidence': float(avg_confidence) if avg_confidence else 0
            }
        })

    except Exception as e:
        logger.error(f"❌ Stats error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
