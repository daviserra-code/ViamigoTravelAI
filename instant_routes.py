#!/usr/bin/env python3
"""
⚡ INSTANT ROUTES - Zero timeout, pure cache-based responses
"""

from flask import Blueprint, request, jsonify
from smart_ai_cache import get_cached_ai_details, get_cached_plan_b, get_cached_discoveries

instant_bp = Blueprint('instant', __name__)

@instant_bp.route('/plan_instant', methods=['POST'])
def plan_instant():
    """Instant planning without any OpenAI calls"""
    try:
        data = request.get_json()
        start = data.get('start', 'Fifth Avenue')
        end = data.get('end', 'Cornelia Street')
        
        # NYC coordinates
        nyc_coords = [40.7589, -73.9851]
        
        # Build instant itinerary
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
        
        # Add SoHo with full details
        soho_details = get_cached_ai_details('SoHo', 'attraction')
        itinerary.append({
            'time': '10:00',
            'title': 'SoHo',
            'description': soho_details['description'],
            'coordinates': [40.7230, -73.9987],
            'context': 'attraction_new_york',
            'transport': 'walking',
            'opening_hours': soho_details['opening_hours'],
            'price_range': soho_details['price_range'],
            'highlights': soho_details['highlights'],
            'insider_tip': soho_details['insider_tip'],
            'best_time': soho_details['best_time'],
            'emergency_alternatives': soho_details['emergency_alternatives']
        })
        
        # Add The Brass Rail with full details
        brass_rail_details = get_cached_ai_details('The Brass Rail', 'restaurant')
        itinerary.append({
            'time': '12:30',
            'title': 'The Brass Rail',
            'description': brass_rail_details['description'],
            'coordinates': [40.7260, -73.9965],
            'context': 'restaurant_new_york',
            'transport': 'walking',
            'opening_hours': brass_rail_details['opening_hours'],
            'price_range': brass_rail_details['price_range'],
            'highlights': brass_rail_details['highlights'],
            'insider_tip': brass_rail_details['insider_tip'],
            'emergency_alternatives': brass_rail_details['emergency_alternatives']
        })
        
        # Add South Street Seaport
        seaport_details = get_cached_ai_details('South Street Seaport', 'attraction')
        itinerary.append({
            'time': '14:30',
            'title': 'South Street Seaport',
            'description': seaport_details['description'],
            'coordinates': [40.7057, -74.0029],
            'context': 'attraction2_new_york',
            'transport': 'walking',
            'opening_hours': seaport_details['opening_hours'],
            'price_range': seaport_details['price_range'],
            'highlights': seaport_details['highlights'],
            'insider_tip': seaport_details['insider_tip'],
            'best_time': seaport_details['best_time']
        })
        
        # Add Washington Square Park
        wsq_details = get_cached_ai_details('Washington Square Park', 'attraction')
        itinerary.append({
            'time': '15:30',
            'title': 'Washington Square Park',
            'description': wsq_details['description'],
            'coordinates': [40.7308, -73.9973],
            'context': 'attraction3_new_york',
            'transport': 'walking',
            'opening_hours': wsq_details['opening_hours'],
            'price_range': wsq_details['price_range'],
            'highlights': wsq_details['highlights'],
            'insider_tip': wsq_details['insider_tip'],
            'best_time': wsq_details['best_time']
        })
        
        # Add Joe's Pizza
        joes_details = get_cached_ai_details("Joe's Pizza", 'restaurant')
        itinerary.append({
            'time': '17:00',
            'title': "Joe's Pizza",
            'description': joes_details['description'],
            'coordinates': [40.7290, -73.9974],
            'context': 'restaurant2_new_york',
            'transport': 'walking',
            'opening_hours': joes_details['opening_hours'],
            'price_range': joes_details['price_range'],
            'highlights': joes_details['highlights'],
            'insider_tip': joes_details['insider_tip'],
            'emergency_alternatives': joes_details['emergency_alternatives']
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
            'description': 'Authentic walking tour with instant AI-powered details and local insights'
        })
        
        # Add Plan B
        plan_b = get_cached_plan_b('new york')
        itinerary.append({
            'type': 'emergency_plan',
            'title': '🌧️ Piano B',
            'description': 'Alternative al coperto se piove',
            'coordinates': nyc_coords,
            'plan_b_data': plan_b
        })
        
        # Add discoveries
        discoveries = get_cached_discoveries('new york')
        itinerary.append({
            'type': 'smart_discovery',
            'title': '🔍 Scoperte Local',
            'description': 'Gemme nascoste nelle vicinanze',
            'coordinates': nyc_coords,
            'discoveries': discoveries
        })
        
        return jsonify({
            'itinerary': itinerary,
            'city': 'New York',
            'total_duration': '9.5 hours',
            'transport_cost': '$0 (walking only)',
            'status': 'instant_success'
        })
        
    except Exception as e:
        print(f"Error in instant planning: {e}")
        return jsonify({'error': f'Instant planning error: {str(e)}'}), 500