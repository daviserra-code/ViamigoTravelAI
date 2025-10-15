#!/usr/bin/env python3
"""
⚡ PURE INSTANT ROUTES - True dynamic responses without any AI delays
"""

from flask import Blueprint, request, jsonify
import random

pure_instant_bp = Blueprint('pure_instant', __name__)

# City-specific attractions and restaurants
CITY_DATA = {
    'genova': {
        'coords': [44.4056, 8.9463],
        'attractions': [
            ('Palazzo Rosso', [44.4070, 8.9352]),
            ('Spianata Castelletto', [44.4148, 8.9342]),
            ('Via del Campo', [44.4081, 8.9312]),
            ('Palazzo Bianco', [44.4072, 8.9355]),
            ('Teatro Carlo Felice', [44.4089, 8.9339]),
            ('Cattedrale di San Lorenzo', [44.4075, 8.9322])
        ],
        'restaurants': [
            ('Il Genovese', [44.4065, 8.9345]),
            ('Antica Osteria di Vico Palla', [44.4058, 8.9318]),
            ('Trattoria del Borgo', [44.4072, 8.9330]),
            ('Osteria della Foce', [44.4041, 8.9501]),
            ('Il Giardino di Casana', [44.4099, 8.9364])
        ]
    },
    'new_york': {
        'coords': [40.7589, -73.9851],
        'attractions': [
            ('SoHo Historic District', [40.7230, -73.9987]),
            ('Washington Square Park', [40.7308, -73.9973]),
            ('Brooklyn Bridge', [40.7061, -73.9969]),
            ('High Line Park', [40.7480, -74.0048]),
            ('Central Park', [40.7829, -73.9654]),
            ('Times Square', [40.7580, -73.9855])
        ],
        'restaurants': [
            ("Joe's Pizza", [40.7290, -73.9974]),
            ('Katz\'s Delicatessen', [40.7223, -73.9873]),
            ('The Brass Rail Diner', [40.7260, -73.9965]),
            ('Russ & Daughters', [40.7226, -73.9890]),
            ('Di Fara Pizza', [40.6260, -73.9612])
        ]
    },
    'rome': {
        'coords': [41.9028, 12.4964],
        'attractions': [
            ('Colosseum', [41.8902, 12.4922]),
            ('Trevi Fountain', [41.9009, 12.4833]),
            ('Vatican City', [41.9029, 12.4534]),
            ('Pantheon', [41.8986, 12.4769]),
            ('Spanish Steps', [41.9058, 12.4823])
        ],
        'restaurants': [
            ('Checchino dal 1887', [41.8803, 12.4732]),
            ('Da Enzo al 29', [41.8919, 12.4717]),
            ('Armando al Pantheon', [41.8988, 12.4761]),
            ('Il Sorpasso', [41.9066, 12.4663]),
            ('Metamorfosi', [41.9194, 12.4923])
        ]
    },
    'paris': {
        'coords': [48.8566, 2.3522],
        'attractions': [
            ('Eiffel Tower', [48.8584, 2.2945]),
            ('Louvre Museum', [48.8606, 2.3376]),
            ('Notre-Dame Cathedral', [48.8530, 2.3499]),
            ('Arc de Triomphe', [48.8738, 2.2950]),
            ('Sacré-Cœur', [48.8867, 2.3431])
        ],
        'restaurants': [
            ('Le Comptoir du Relais', [48.8531, 2.3389]),
            ('L\'As du Fallafel', [48.8571, 2.3594]),
            ('Bistrot Paul Bert', [48.8518, 2.3885]),
            ('Le Procope', [48.8530, 2.3389]),
            ('Pierre Hermé', [48.8544, 2.3324])
        ]
    },
    'milan': {
        'coords': [45.4642, 9.1900],
        'attractions': [
            ('Duomo di Milano', [45.4642, 9.1900]),
            ('La Scala Theatre', [45.4677, 9.1898]),
            ('Sforza Castle', [45.4707, 9.1794]),
            ('Navigli District', [45.4502, 9.1793]),
            ('Brera District', [45.4719, 9.1883])
        ],
        'restaurants': [
            ('Osteria di Brera', [45.4719, 9.1883]),
            ('Trattoria Milanese', [45.4654, 9.1859]),
            ('Peck Italian Bar', [45.4657, 9.1906]),
            ('Il Luogo di Aimo e Nadia', [45.4526, 9.1456]),
            ('Ratanà', [45.4821, 9.2005])
        ]
    }
}

def detect_city(location_string):
    """Detect city from location string"""
    location_lower = location_string.lower()
    
    if any(term in location_lower for term in ['genova', 'genoa', 'ferrari', 'acquario', 'spianata', 'palazzo rosso']):
        return 'genova', 'Genova'
    elif any(term in location_lower for term in ['rome', 'roma', 'colosseum', 'vatican', 'trevi']):
        return 'rome', 'Rome'
    elif any(term in location_lower for term in ['paris', 'eiffel', 'louvre', 'champs', 'montmartre']):
        return 'paris', 'Paris'
    elif any(term in location_lower for term in ['milan', 'milano', 'duomo', 'scala', 'navigli']):
        return 'milan', 'Milan'
    elif any(term in location_lower for term in ['london', 'big ben', 'tower bridge', 'westminster']):
        return 'london', 'London'
    elif any(term in location_lower for term in ['new york', 'nyc', 'manhattan', 'brooklyn', 'times square', 'central park']):
        return 'new_york', 'New York'
    else:
        return 'new_york', 'New York'  # Default

def generate_dynamic_details(place_name, place_type, city_name):
    """Generate location-specific authentic details"""
    
    base_details = {
        'new_york': {
            'restaurant': {
                'description': f'{place_name} serves authentic New York cuisine with fresh ingredients and local flavors. Popular among both tourists and locals for its genuine NYC atmosphere.',
                'opening_hours': '11:00-23:00 (Mon-Sun)',
                'price_range': '€€',
                'highlights': ['Authentic NYC flavors', 'Local atmosphere', 'Fresh ingredients'],
                'insider_tip': 'Ask for the daily specials - they feature seasonal local ingredients',
                'best_time': 'Lunch (12-14pm) or early dinner (18-19pm)',
                'emergency_alternatives': ['Local diners nearby', 'Food trucks in the area']
            },
            'attraction': {
                'description': f'{place_name} is an iconic New York attraction showcasing the city\'s rich history and culture. A must-visit destination for understanding authentic NYC character.',
                'opening_hours': '9:00-18:00 (varies seasonally)',
                'price_range': '€€',
                'highlights': ['Historical significance', 'Authentic NYC architecture', 'Cultural importance'],
                'insider_tip': 'Visit during weekdays for a more authentic, less crowded experience',
                'best_time': 'Early morning (9-11am) or late afternoon (16-18pm)',
                'emergency_alternatives': ['Nearby museums', 'Local parks and squares']
            }
        },
        'genova': {
            'restaurant': {
                'description': f'{place_name} serves authentic Ligurian cuisine with fresh pesto, focaccia, and seafood specialties. Experience genuine Genovese culinary traditions.',
                'opening_hours': '12:00-15:00, 19:30-23:00',
                'price_range': '€€',
                'highlights': ['Fresh pesto genovese', 'Local focaccia', 'Mediterranean seafood'],
                'insider_tip': 'Ask for pesto made with Ligurian basilico DOP - the authentic regional variety',
                'best_time': 'Lunch (13-14pm) or dinner (20-21pm) following Ligurian traditions',
                'emergency_alternatives': ['Via del Campo eateries', 'Porto Antico restaurants']
            },
            'attraction': {
                'description': f'{place_name} showcases Genova\'s rich maritime heritage and Renaissance architecture. A key part of understanding this historic port city.',
                'opening_hours': '9:00-18:00 (varies by season)',
                'price_range': '€€',
                'highlights': ['Maritime history', 'Renaissance palaces', 'Panoramic views'],
                'insider_tip': 'Visit early morning for best light and fewer crowds in the historic center',
                'best_time': 'Morning (9-11am) or late afternoon (16-18pm)',
                'emergency_alternatives': ['Palazzo Ducale', 'Musei di Strada Nuova']
            }
        },
        'rome': {
            'restaurant': {
                'description': f'{place_name} offers traditional Roman cuisine prepared with time-honored recipes and local ingredients. A genuine taste of Roman culinary heritage.',
                'opening_hours': '12:00-15:00, 19:00-23:00',
                'price_range': '€€€',
                'highlights': ['Traditional Roman recipes', 'Local ingredients', 'Historic atmosphere'],
                'insider_tip': 'Try the carbonara or cacio e pepe - Roman specialties made authentically here',
                'best_time': 'Lunch (13-14pm) or dinner (20-21pm) following Roman schedule',
                'emergency_alternatives': ['Trastevere restaurants', 'Campo de\' Fiori eateries']
            },
            'attraction': {
                'description': f'{place_name} represents the eternal beauty of Rome, showcasing millennia of history and artistic achievement. An essential part of understanding Roman civilization.',
                'opening_hours': '8:30-19:00 (varies by season)',
                'price_range': '€€€',
                'highlights': ['Ancient Roman history', 'Architectural masterpiece', 'Cultural significance'],
                'insider_tip': 'Book skip-the-line tickets in advance, especially during peak season',
                'best_time': 'Early morning (8:30-10am) or late afternoon to avoid crowds',
                'emergency_alternatives': ['Vatican Museums', 'Capitoline Museums']
            }
        }
    }
    
    # Get city-specific template or default to New York
    city_templates = base_details.get(city_name.lower().replace(' ', '_'), base_details['new_york'])
    template = city_templates.get(place_type, city_templates['attraction'])
    
    return template

@pure_instant_bp.route('/plan_pure', methods=['POST'])
def plan_pure():
    """Pure instant planning with true dynamic content"""
    try:
        data = request.get_json()
        start = data.get('start', 'Fifth Avenue')
        end = data.get('end', 'Cornelia Street')
        
        print(f"🚀 Pure instant planning: {start} → {end}")
        
        # Detect city from both start and end locations
        start_city_key, start_city_name = detect_city(start)
        end_city_key, end_city_name = detect_city(end)
        
        # Use end city as primary destination
        city_key = end_city_key
        city_name = end_city_name
        
        # Get city data or default to NYC
        city_info = CITY_DATA.get(city_key, CITY_DATA['new_york'])
        base_coords = city_info['coords']
        
        # Build dynamic itinerary
        itinerary = [
            {
                'time': '09:00',
                'title': f'{start.title()}',
                'description': f'Starting point: {start}',
                'coordinates': base_coords,
                'context': f'{start.lower().replace(" ", "_")}_{city_key}',
                'transport': 'start'
            }
        ]
        
        # Select random attractions and restaurants for variety
        attractions = random.sample(city_info['attractions'], min(3, len(city_info['attractions'])))
        restaurants = random.sample(city_info['restaurants'], min(2, len(city_info['restaurants'])))
        
        times = ['10:00', '12:30', '14:30', '15:30', '17:00']
        place_index = 0
        
        # Add first attraction
        if attractions:
            place_name, coords = attractions[0]
            details = generate_dynamic_details(place_name, 'attraction', city_name)
            itinerary.append({
                'time': times[place_index],
                'title': place_name,
                'description': details['description'],
                'coordinates': coords,
                'context': f'attraction_{city_key}',
                'transport': 'walking',
                **details
            })
            place_index += 1
        
        # Add first restaurant
        if restaurants:
            place_name, coords = restaurants[0]
            details = generate_dynamic_details(place_name, 'restaurant', city_name)
            itinerary.append({
                'time': times[place_index],
                'title': place_name,
                'description': details['description'],
                'coordinates': coords,
                'context': f'restaurant_{city_key}',
                'transport': 'walking',
                **details
            })
            place_index += 1
        
        # Add remaining attractions
        for i in range(1, min(3, len(attractions))):
            if place_index < len(times):
                place_name, coords = attractions[i]
                details = generate_dynamic_details(place_name, 'attraction', city_name)
                itinerary.append({
                    'time': times[place_index],
                    'title': place_name,
                    'description': details['description'],
                    'coordinates': coords,
                    'context': f'attraction{i+1}_{city_key}',
                    'transport': 'walking',
                    **details
                })
                place_index += 1
        
        # Add second restaurant if available
        if len(restaurants) > 1 and place_index < len(times):
            place_name, coords = restaurants[1]
            details = generate_dynamic_details(place_name, 'restaurant', city_name)
            itinerary.append({
                'time': times[place_index],
                'title': place_name,
                'description': details['description'],
                'coordinates': coords,
                'context': f'restaurant2_{city_key}',
                'transport': 'walking',
                **details
            })
        
        # End destination
        itinerary.append({
            'time': '18:30',
            'title': f'{end.title()}',
            'description': f'Final destination: {end}',
            'coordinates': base_coords,
            'context': f'{end.lower().replace(" ", "_")}_{city_key}',
            'transport': 'walking'
        })
        
        # Add contextual tip
        itinerary.append({
            'type': 'tip',
            'title': f'💡 {city_name}',
            'description': f'Authentic {city_name} experience with local attractions and cuisine'
        })
        
        # City-specific Plan B
        plan_b_data = {
            'emergency_type': 'rain',
            'alternative_plan': [
                {
                    'time': '09:00',
                    'title': f'{city_name} Indoor Market',
                    'description': f'Covered market with local food and shopping',
                    'why_better': 'Complete protection from weather',
                    'indoor': True
                },
                {
                    'time': '11:00',
                    'title': f'{city_name} Museum District',
                    'description': f'World-class museums and galleries',
                    'why_better': 'Cultural enrichment while staying dry',
                    'indoor': True
                }
            ],
            'smart_tips': [f'Use {city_name} public transport', 'Check local weather apps'],
            'cost_impact': 'Similar to original plan'
        }
        
        itinerary.append({
            'type': 'emergency_plan',
            'title': '🌧️ Piano B',
            'description': 'Indoor alternatives for bad weather',
            'coordinates': base_coords,
            'plan_b_data': plan_b_data
        })
        
        # Dynamic discoveries
        discoveries = [
            {
                'title': f'Hidden {city_name} Gem',
                'description': f'Local secret spot known only to {city_name} residents',
                'distance': '5 minutes walk',
                'why_now': 'Perfect timing for authentic local experience',
                'local_secret': f'Ask locals about the best times to visit this {city_name} treasure'
            },
            {
                'title': f'{city_name} Local Market',
                'description': f'Authentic market where {city_name} locals shop daily',
                'distance': '3 minutes walk',
                'why_now': 'Morning is when freshest products arrive',
                'local_secret': 'Try the local specialties recommended by vendors'
            }
        ]
        
        itinerary.append({
            'type': 'smart_discovery',
            'title': '🔍 Scoperte Local',
            'description': f'Hidden gems in {city_name}',
            'coordinates': base_coords,
            'discoveries': discoveries
        })
        
        print(f"✅ Pure instant response generated for {city_name}")
        
        return jsonify({
            'itinerary': itinerary,
            'city': city_name,
            'total_duration': '9.5 hours',
            'transport_cost': f'{city_name} public transport recommended',
            'status': 'pure_instant_success'
        })
        
    except Exception as e:
        print(f"❌ Error in pure instant planning: {e}")
        return jsonify({'error': f'Pure instant planning error: {str(e)}'}), 500