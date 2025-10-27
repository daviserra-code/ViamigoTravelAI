"""
Simple Enhanced Images API - Working Version
Fixes the 404 issue with enhanced images
"""

from flask import Blueprint, jsonify, request
import logging
import re

logger = logging.getLogger(__name__)

enhanced_images_bp = Blueprint('enhanced_images', __name__)

# Simple image database for testing
ATTRACTION_IMAGES = {
    # Rome
    'colosseo': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800',  # Colosseum
    'fontana_di_trevi': 'https://images.unsplash.com/photo-1531572753322-ad063cecc140?w=800',  # Trevi Fountain
    'pantheon': 'https://images.unsplash.com/photo-1555992336-03a23c33d7ba?w=800',  # Pantheon Rome
    'piazza_navona': 'https://images.unsplash.com/photo-1560707303-4e980ce876ad?w=800',  # Better Piazza Navona image
    # Milan
    'duomo_milano': 'https://images.unsplash.com/photo-1543832923-44667a44c804?w=800',  # Milan Cathedral
    'castello_sforzesco': 'https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=800',  # Sforza Castle
    'galleria_vittorio_emanuele': 'https://images.unsplash.com/photo-1509715513011-e394f0cb20c4?w=800',  # Galleria in Milan
    'navigli': 'https://images.unsplash.com/photo-1576673177419-2ed30b99e27b?w=800',  # Milan Navigli canals
    # Naples
    'spaccanapoli': 'https://images.unsplash.com/photo-1544737151-6e4b2eb0bb8d?w=800',
    'castel_dell_ovo': 'https://images.unsplash.com/photo-1587022092690-1db5b98c73ac?w=800',
    'piazza_del_plebiscito': 'https://images.unsplash.com/photo-1544737150-6ba4f3b29ed1?w=800',
    'quartieri_spagnoli': 'https://images.unsplash.com/photo-1587022092690-1db5b98c73ac?w=800',
    # Genoa
    'acquario_genova': 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800',
    'palazzo_rosso': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=800',
    'palazzo_bianco': 'https://images.unsplash.com/photo-1565026057447-bc90f80b4a82?w=800',
    'lanterna_genova': 'https://images.unsplash.com/photo-1565026057447-bc90f80b4a82?w=800',
    'via_del_campo': 'https://images.unsplash.com/photo-1585562582810-b6970174c3b6?w=800',
    'centro_storico_genova': 'https://images.unsplash.com/photo-1585562582810-b6970174c3b6?w=800',
    # Florence
    'piazza_della_signoria': 'https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=800',  # Piazza della Signoria
    'uffizi': 'https://images.unsplash.com/photo-1560969184-10fe8719e047?w=800',  # Uffizi Gallery
    'ponte_vecchio': 'https://images.unsplash.com/photo-1557232838-4497d1da2c6b?w=800',  # Ponte Vecchio
    'duomo_firenze': 'https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=800',  # Florence Cathedral
    'palazzo_pitti': 'https://images.unsplash.com/photo-1555992336-03a23c33d7ba?w=800',  # Palazzo Pitti
}


def classify_attraction_simple(title, context=""):
    """Simple attraction classification"""
    text = f"{title} {context}".lower()

    # Italian cities - CHECK CONTEXT FIRST for better accuracy
    if any(city in text for city in ['firenze', 'florence']):
        city = 'Firenze'
    elif any(city in text for city in ['roma', 'rome']):
        city = 'Roma'
    elif any(city in text for city in ['milano', 'milan']):
        city = 'Milano'
    elif any(city in text for city in ['napoli', 'naples']):
        city = 'Napoli'
    elif any(city in text for city in ['genova', 'genoa']):
        city = 'Genova'
    else:
        city = 'Italia'

    # Extract attraction
    attraction = 'Generic'
    confidence = 0.5

    # Known attractions
    if 'colosseo' in text or 'colosseum' in text:
        attraction = 'Colosseo'
        confidence = 0.9
    elif 'trevi' in text or 'fontana' in text:
        attraction = 'Fontana di Trevi'
        confidence = 0.9
    elif 'pantheon' in text:
        attraction = 'Pantheon'
        confidence = 0.9
    elif 'navona' in text:
        attraction = 'Piazza Navona'
        confidence = 0.9
    # Florence attractions
    elif 'signoria' in text:
        attraction = 'Piazza della Signoria'
        confidence = 0.9
    elif 'uffizi' in text:
        attraction = 'Galleria degli Uffizi'
        confidence = 0.9
    elif 'ponte vecchio' in text or 'pontevecchio' in text:
        attraction = 'Ponte Vecchio'
        confidence = 0.9
    elif 'duomo' in text and 'firenze' in text:
        attraction = 'Duomo di Firenze'
        confidence = 0.9
    elif 'palazzo pitti' in text or 'palazzopitti' in text:
        attraction = 'Palazzo Pitti'
        confidence = 0.9
    # Milan attractions
    elif 'duomo' in text and 'milano' in text:
        attraction = 'Duomo di Milano'
        confidence = 0.9
    elif 'castello' in text or 'sforzesco' in text:
        attraction = 'Castello Sforzesco'
        confidence = 0.9
    elif 'galleria' in text:
        attraction = 'Galleria Vittorio Emanuele II'
        confidence = 0.9
    elif 'navigli' in text:
        attraction = 'Navigli'
        confidence = 0.9
    # Naples attractions
    elif 'spaccanapoli' in text:
        attraction = 'Spaccanapoli'
        confidence = 0.9
    elif 'castel' in text and 'ovo' in text:
        attraction = 'Castel dell\'Ovo'
        confidence = 0.9
    elif 'plebiscito' in text:
        attraction = 'Piazza del Plebiscito'
        confidence = 0.9
    elif 'spagnoli' in text:
        attraction = 'Quartieri Spagnoli'
        confidence = 0.9
    elif 'acquario' in text:
        attraction = 'Acquario di Genova'
        confidence = 0.9
    elif 'palazzo rosso' in text:
        attraction = 'Palazzo Rosso'
        confidence = 0.9
    elif 'palazzo bianco' in text:
        attraction = 'Palazzo Bianco'
        confidence = 0.9
    elif 'lanterna' in text:
        attraction = 'Lanterna di Genova'
        confidence = 0.9
    elif 'via del campo' in text:
        attraction = 'Via del Campo'
        confidence = 0.8
    elif city == 'Genova':
        attraction = 'Centro Storico di Genova'
        confidence = 0.7

    return city, attraction, confidence


def get_image_for_attraction(attraction):
    """Get image URL for attraction"""
    # Normalize attraction name for lookup
    lookup_key = attraction.lower()
    lookup_key = re.sub(r'[^\w\s]', '', lookup_key)  # Remove punctuation
    lookup_key = lookup_key.replace(' ', '_')
    lookup_key = lookup_key.replace('di_', '').replace(
        'del_', '').replace('della_', '')

    return ATTRACTION_IMAGES.get(lookup_key, 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=800')


@enhanced_images_bp.route('/api/images/classify', methods=['POST'])
def classify_attraction():
    """Classify attraction from title and context using intelligent multi-stage approach"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        title = data.get('title', '')
        context = data.get('context', '')

        logger.info(f"🔍 Classifying: '{title}' with context: '{context}'")

        # First try simple classification for fast results
        city, attraction, confidence = classify_attraction_simple(
            title, context)

        # If confidence is low, use intelligent classifier
        if confidence < 0.8:
            try:
                from intelligent_image_classifier import classify_image_intelligent
                intelligent_result = classify_image_intelligent(title, context)

                if intelligent_result.get('success') and intelligent_result.get('classification', {}).get('confidence', 0) > confidence:
                    # Use intelligent result if better
                    classification = intelligent_result['classification']
                    city = classification.get('city', city)
                    attraction = classification.get('attraction', attraction)
                    confidence = classification.get('confidence', confidence)
                    image_url = intelligent_result.get(
                        'image_url', get_image_for_attraction(attraction))
                else:
                    image_url = get_image_for_attraction(attraction)
            except Exception as e:
                logger.warning(
                    f"⚠️ Intelligent classifier failed, using simple: {e}")
                image_url = get_image_for_attraction(attraction)
        else:
            image_url = get_image_for_attraction(attraction)

        result = {
            'success': True,
            'classification': {
                'city': city,
                'attraction': attraction,
                'confidence': confidence
            },
            'image': {
                'url': image_url,
                'confidence': confidence
            }
        }

        logger.info(
            f"✅ Classification result: {city} -> {attraction} (confidence: {confidence})")
        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Error classifying attraction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_images_bp.route('/api/images/batch', methods=['POST'])
def get_batch_images():
    """Get images for multiple attractions at once"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        attractions = data.get('attractions', [])
        results = []

        for item in attractions:
            title = item.get('title', '')
            context = item.get('context', '')

            city, attraction, confidence = classify_attraction_simple(
                title, context)
            image_url = get_image_for_attraction(attraction)

            results.append({
                'original_title': title,
                'classified_attraction': attraction,
                'city': city,
                'confidence': confidence,
                'image': {
                    'url': image_url,
                    'confidence': confidence
                }
            })

        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })

    except Exception as e:
        logger.error(f"❌ Error processing batch images: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@enhanced_images_bp.route('/api/images/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    return jsonify({
        'success': True,
        'message': 'Enhanced Images API is working!',
        'available_endpoints': [
            '/api/images/classify',
            '/api/images/batch',
            '/api/images/test'
        ]
    })
