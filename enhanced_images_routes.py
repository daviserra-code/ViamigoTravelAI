"""
Enhanced Images API Routes for ViamigoTravelAI
Provides improved image classification and retrieval
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

enhanced_images_bp = Blueprint('enhanced_images', __name__)

# Try to import the real service, fallback to mock for testing
try:
    from enhanced_image_service import get_enhanced_attraction_image, classify_attraction_enhanced
    logger.info("Using real enhanced image service")
except ImportError:
    try:
        from mock_enhanced_image_service import get_enhanced_attraction_image, classify_attraction_enhanced
        logger.info("Using mock enhanced image service for testing")
    except ImportError:
        logger.error("No enhanced image service available")

        def get_enhanced_attraction_image(city, attraction, fallback=None):
            return {'url': 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=400', 'confidence': 0.3}

        def classify_attraction_enhanced(title, context):
            return 'Italia', 'Generic', 0.3


@enhanced_images_bp.route('/api/images/enhanced/<city>/<attraction>', methods=['GET'])
def get_enhanced_image(city, attraction):
    """Get enhanced image for a specific attraction"""
    try:
        fallback_url = request.args.get('fallback')

        image_data = get_enhanced_attraction_image(
            city, attraction, fallback_url)

        return jsonify({
            'success': True,
            'image': image_data,
            'city': city,
            'attraction': attraction
        })

    except Exception as e:
        logger.error(f"Error getting enhanced image: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_images_bp.route('/api/images/classify', methods=['POST'])
def classify_attraction():
    """Classify attraction from title and context"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        context = data.get('context', '')

        city, attraction, confidence = classify_attraction_enhanced(
            title, context)

        # Get image for classified attraction
        image_data = get_enhanced_attraction_image(city, attraction)

        return jsonify({
            'success': True,
            'classification': {
                'city': city,
                'attraction': attraction,
                'confidence': confidence
            },
            'image': image_data
        })

    except Exception as e:
        logger.error(f"Error classifying attraction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_images_bp.route('/api/images/batch', methods=['POST'])
def get_batch_images():
    """Get images for multiple attractions at once"""
    try:
        data = request.get_json()
        attractions = data.get('attractions', [])

        results = []
        for item in attractions:
            title = item.get('title', '')
            context = item.get('context', '')

            # Classify attraction
            city, attraction, confidence = classify_attraction_enhanced(
                title, context)

            # Get image
            image_data = get_enhanced_attraction_image(city, attraction)

            results.append({
                'original_title': title,
                'classified_attraction': attraction,
                'city': city,
                'confidence': confidence,
                'image': image_data
            })

        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })

    except Exception as e:
        logger.error(f"Error processing batch images: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
