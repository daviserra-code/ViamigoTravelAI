#!/usr/bin/env python3
"""
⚡ LIGHTNING ROUTES - Instant response with background AI processing
Returns cached data immediately, then enriches with real AI in background
"""

from flask import Blueprint, request, jsonify
import threading
import time
from smart_ai_cache import get_cached_ai_details, get_cached_plan_b, get_cached_discoveries

lightning_bp = Blueprint('lightning', __name__)

# In-memory store for enhanced content
enhanced_store = {}

def background_ai_enhancement(itinerary_id, places, city):
    """Background thread to enhance content with real AI"""
    try:
        from intelligent_content_generator import IntelligentContentGenerator
        ai_generator = IntelligentContentGenerator()
        
        # Process each place with AI
        for i, place in enumerate(places):
            if 'title' in place and place.get('type') != 'tip':
                try:
                    place_type = 'restaurant' if 'restaurant' in place.get('context', '') else 'attraction'
                    ai_details = ai_generator.enrich_place_details(place['title'], city, place_type)
                    
                    # Store enhanced details
                    enhanced_store[f"{itinerary_id}_{i}"] = ai_details
                    print(f"✅ AI enhanced: {place['title']}")
                except Exception as e:
                    print(f"⚠️ AI enhancement failed for {place['title']}: {e}")
        
        # Generate AI features
        try:
            discoveries = ai_generator.generate_smart_discoveries("Fifth Avenue", city, "morning")
            plan_b = ai_generator.generate_emergency_plan_b(places, city, "rain")
            
            enhanced_store[f"{itinerary_id}_discoveries"] = discoveries
            enhanced_store[f"{itinerary_id}_plan_b"] = plan_b
            print("✅ AI features generated in background")
        except Exception as e:
            print(f"⚠️ Background AI features failed: {e}")
            
    except Exception as e:
        print(f"⚠️ Background AI processing failed: {e}")

@lightning_bp.route('/plan_lightning', methods=['POST'])
def plan_lightning():
    """Lightning fast planning with background AI enhancement"""
    try:
        data = request.get_json()
        start = data.get('start', 'Fifth Avenue')
        end = data.get('end', 'Cornelia Street')
        
        # Generate unique itinerary ID
        itinerary_id = f"{int(time.time() * 1000)}"
        
        # NYC coordinates
        nyc_coords = [40.7589, -73.9851]
        
        # Build instant itinerary with cached AI details
        itinerary = [
            {
                'time': '09:00',
                'title': f'{start.title()}',
                'description': f'Starting point: {start}',
                'coordinates': nyc_coords,
                'context': f'{start.lower().replace(" ", "_")}_new_york',
                'transport': 'start'
            }
        ]
        
        # Add places with cached AI details
        places_data = [
            ('SoHo', [40.7230, -73.9987], 'attraction'),
            ('The Brass Rail', [40.7260, -73.9965], 'restaurant'),
            ('South Street Seaport', [40.7057, -74.0029], 'attraction'),
            ('Washington Square Park', [40.7308, -73.9973], 'attraction'),
            ("Joe's Pizza", [40.7290, -73.9974], 'restaurant')
        ]
        
        times = ['10:00', '12:30', '14:30', '15:30', '17:00']
        
        for i, (place_name, coords, place_type) in enumerate(places_data):
            details = get_cached_ai_details(place_name, place_type)
            itinerary.append({
                'time': times[i],
                'title': place_name,
                'description': details['description'],
                'coordinates': coords,
                'context': f'{place_type}_new_york',
                'transport': 'walking',
                'opening_hours': details['opening_hours'],
                'price_range': details['price_range'],
                'highlights': details['highlights'],
                'insider_tip': details['insider_tip'],
                'best_time': details.get('best_time', 'Any time'),
                'emergency_alternatives': details.get('emergency_alternatives', [])
            })
        
        # End destination
        itinerary.append({
            'time': '18:30',
            'title': f'{end.title()}',
            'description': f'Final destination: {end}',
            'coordinates': [40.7282, -74.0007],
            'context': f'{end.lower().replace(" ", "_")}_new_york',
            'transport': 'walking'
        })
        
        # Add tip
        itinerary.append({
            'type': 'tip',
            'title': '💡 New York City',
            'description': 'Authentic walking tour with instant cached AI details, being enhanced in background'
        })
        
        # Add cached Plan B and discoveries
        plan_b = get_cached_plan_b('new york')
        discoveries = get_cached_discoveries('new york')
        
        itinerary.extend([
            {
                'type': 'emergency_plan',
                'title': '🌧️ Piano B',
                'description': 'Alternative al coperto se piove',
                'coordinates': nyc_coords,
                'plan_b_data': plan_b
            },
            {
                'type': 'smart_discovery',
                'title': '🔍 Scoperte Local',
                'description': 'Gemme nascoste nelle vicinanze',
                'coordinates': nyc_coords,
                'discoveries': discoveries
            }
        ])
        
        # Start background AI enhancement
        threading.Thread(
            target=background_ai_enhancement,
            args=(itinerary_id, itinerary, 'new york'),
            daemon=True
        ).start()
        
        print(f"⚡ Lightning response sent, background AI processing started for {itinerary_id}")
        
        return jsonify({
            'itinerary': itinerary,
            'city': 'New York',
            'total_duration': '9.5 hours',
            'transport_cost': '$0 (walking only)',
            'status': 'lightning_success',
            'itinerary_id': itinerary_id,
            'enhancement_status': 'processing'
        })
        
    except Exception as e:
        print(f"Error in lightning planning: {e}")
        return jsonify({'error': f'Lightning planning error: {str(e)}'}), 500

@lightning_bp.route('/get_enhancements/<itinerary_id>', methods=['GET'])
def get_enhancements(itinerary_id):
    """Get AI enhancements for an itinerary"""
    try:
        enhancements = {}
        for key, value in enhanced_store.items():
            if key.startswith(itinerary_id):
                enhancements[key] = value
        
        return jsonify({
            'enhancements': enhancements,
            'status': 'ready' if enhancements else 'processing'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500