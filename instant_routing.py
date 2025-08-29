#!/usr/bin/env python3
"""
🚀 INSTANT ROUTING - Zero AI delays, instant responses
Backup system for when OpenAI is slow/timing out
"""

def get_instant_nyc_itinerary(start: str, end: str) -> dict:
    """Returns instant NYC itinerary without any AI calls"""
    
    itinerary = [
        {
            'time': '09:00',
            'title': f'{start.title()}',
            'description': f'Starting point: {start}',
            'coordinates': [40.7589, -73.9851],  # NYC center
            'context': f'{start.lower().replace(" ", "_")}_new_york',
            'transport': 'start'
        },
        {
            'time': '10:00', 
            'title': 'SoHo District',
            'description': 'Historic neighborhood with cast-iron architecture, boutique shopping, and art galleries. Perfect for morning exploration.',
            'coordinates': [40.7230, -73.9987],
            'context': 'attraction_new_york',
            'transport': 'walking',
            'highlights': ['Cast-iron buildings', 'Art galleries', 'Designer boutiques'],
            'best_time': 'Morning 9-11am for fewer crowds'
        },
        {
            'time': '12:30',
            'title': 'The Brass Rail',
            'description': 'Classic NYC diner serving authentic American comfort food since 1936. Famous for burgers and milkshakes.',
            'coordinates': [40.7260, -73.9965],
            'context': 'restaurant_new_york', 
            'transport': 'walking',
            'price_range': '€€',
            'insider_tip': 'Try the classic burger and ask for extra pickles'
        },
        {
            'time': '14:30',
            'title': 'Washington Square Park',
            'description': 'Iconic park with the famous arch, street performers, and NYU campus. Great for people watching.',
            'coordinates': [40.7308, -73.9973],
            'context': 'attraction2_new_york',
            'transport': 'walking'
        },
        {
            'time': '16:00',
            'title': f'{end.title()}',
            'description': f'Final destination: {end}',
            'coordinates': [40.7282, -74.0007],  # Cornelia Street area
            'context': f'{end.lower().replace(" ", "_")}_new_york',
            'transport': 'walking'
        },
        {
            'type': 'tip',
            'title': '💡 New York City',
            'description': 'Authentic walking tour through historic neighborhoods with local insights'
        }
    ]
    
    # Add Piano B
    plan_b = {
        "emergency_type": "rain",
        "alternative_plan": [
            {
                "time": "09:00",
                "title": "Chelsea Market",
                "description": "Historic indoor market with 35+ food vendors and shops",
                "why_better": "Completely covered, full day of activities",
                "indoor": True
            },
            {
                "time": "12:00",
                "title": "Westfield World Trade Center",
                "description": "Underground shopping complex with restaurants",
                "why_better": "Connected to subway, climate controlled",
                "indoor": True
            }
        ],
        "smart_tips": ["Use subway for covered transport", "Many buildings connect underground"],
        "cost_impact": "Similar to original plan"
    }
    
    # Add discoveries
    smart_discoveries = [
        {
            "title": "Hidden Speakeasy Entry",
            "description": "Secret entrance behind bookshelf at Housing Works Bookstore",
            "distance": "2 minutes walk",
            "why_now": "Less crowded during afternoon hours",
            "local_secret": "Ask for 'The Library' at the back"
        },
        {
            "title": "Rooftop Garden View",
            "description": "Free access to High Line park section with city views",
            "distance": "5 minutes walk",
            "why_now": "Perfect lighting for photos right now", 
            "local_secret": "Best views are at the Gansevoort entrance"
        }
    ]
    
    return {
        'itinerary': itinerary,
        'plan_b': plan_b,
        'smart_discoveries': smart_discoveries,
        'city': 'New York',
        'total_duration': '7 hours',
        'transport_cost': '$0 (walking only)'
    }

def get_instant_itinerary(start: str, end: str, city: str) -> dict:
    """Get instant itinerary for any city without AI delays"""
    
    if 'new york' in city.lower():
        return get_instant_nyc_itinerary(start, end)
    
    # Generic city itinerary
    return {
        'itinerary': [
            {
                'time': '09:00',
                'title': f'{start.title()}',
                'description': f'Starting point: {start}',
                'coordinates': [44.4056, 8.9463],  # Default coords
                'context': f'{start.lower().replace(" ", "_")}_{city.lower()}',
                'transport': 'start'
            },
            {
                'time': '10:00',
                'title': f'Historic Center {city.title()}',
                'description': f'Explore the main attractions and historic sites of {city}',
                'coordinates': [44.4066, 8.9473],
                'context': f'attraction_{city.lower()}',
                'transport': 'walking'
            },
            {
                'time': '16:00',
                'title': f'{end.title()}',
                'description': f'Final destination: {end}',
                'coordinates': [44.4076, 8.9483],
                'context': f'{end.lower().replace(" ", "_")}_{city.lower()}',
                'transport': 'walking'
            }
        ],
        'plan_b': {"emergency_type": "rain", "alternative_plan": []},
        'smart_discoveries': [],
        'city': city.title(),
        'total_duration': '7 hours'
    }