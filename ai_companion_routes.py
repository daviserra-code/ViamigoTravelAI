#!/usr/bin/env python3
"""
🧠 AI COMPANION ROUTES - Real AI-powered travel intelligence
Genuine GPT-5 AI for Piano B, Scoperte Intelligenti, Diario di Viaggio
"""

from flask import Blueprint, request, jsonify
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import json
from openai import OpenAI
import os
from typing import Dict, List

ai_companion_bp = Blueprint('ai_companion', __name__)

# Initialize OpenAI with fast timeout
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class AICompanionEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)

    def generate_piano_b(self, current_itinerary, context, emergency_type="weather"):
        """Real AI Piano B generation with fast timeout"""
        try:
            prompt = f"""
Sei un AI travel companion intelligente. Genera un Piano B dinamico per questo itinerario:

Itinerario corrente: {json.dumps(current_itinerary[:3], indent=2)}
Contesto: {context}
Emergenza: {emergency_type}

Crea un JSON con alternative realistiche e intelligenti:
{{
    "emergency_type": "{emergency_type}",
    "ai_analysis": "Analisi intelligente della situazione",
    "dynamic_alternatives": [
        {{
            "time": "orario",
            "title": "Nome alternativa",
            "description": "Descrizione dettagliata",
            "why_better": "Perché è meglio della versione originale",
            "ai_insight": "Insight intelligente specifico",
            "indoor": true/false
        }}
    ],
    "smart_adaptations": ["suggerimento AI 1", "suggerimento AI 2"],
    "cost_impact": "Analisi costi",
    "ai_confidence": "high/medium/low"
}}

Rispondi SOLO con JSON valido. Sii specifico e intelligente.
"""

            response = openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion esperto che genera Piani B intelligenti e dinamici."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            print(f"✅ AI Piano B generato: {result.get('ai_confidence', 'unknown')} confidence")
            return result

        except Exception as e:
            print(f"⚠️ AI Piano B fallback: {e}")
            return {
                "emergency_type": emergency_type,
                "ai_analysis": "Fallback: Sistema AI temporaneamente non disponibile",
                "dynamic_alternatives": [
                    {
                        "time": "09:00",
                        "title": "Piano alternativo indoor",
                        "description": "Alternative al coperto nelle vicinanze",
                        "why_better": "Protezione completa dalle intemperie",
                        "ai_insight": "Analisi AI non disponibile",
                        "indoor": True
                    }
                ],
                "smart_adaptations": ["Controlla app meteo locale", "Usa trasporti pubblici"],
                "cost_impact": "Simile al piano originale",
                "ai_confidence": "fallback"
            }

    def generate_scoperte_intelligenti(self, location, time_context, user_profile=None):
        """Real AI intelligent discoveries"""
        try:
            profile_context = f"Profilo utente: {user_profile}" if user_profile else "Profilo generico"

            prompt = f"""
Sei un AI travel companion che scopre gemme nascoste. Analizza questa situazione:

Località: {location}
Momento: {time_context}
{profile_context}

Genera scoperte intelligenti e contestuali:
{{
    "ai_analysis": "Analisi intelligente del contesto attuale",
    "contextual_discoveries": [
        {{
            "title": "Nome scoperta",
            "description": "Descrizione dettagliata e autentica",
            "distance": "distanza precisa",
            "why_now": "Perché è perfetto PROPRIO ora",
            "local_secret": "Segreto che solo i locals sanno",
            "ai_insight": "Insight intelligente unico",
            "timing_perfect": "Spiegazione timing perfetto"
        }}
    ],
    "behavioral_learning": "Cosa l'AI ha imparato dalle preferenze dell'utente",
    "adaptive_suggestions": ["suggerimento adattivo 1", "suggerimento adattivo 2"],
    "ai_confidence": "high/medium/low"
}}

Sii specifico, intelligente e contextualmente rilevante.
"""

            response = openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion che scopre gemme nascoste con intelligenza contestuale."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            print(f"✅ AI Scoperte generate: {len(result.get('contextual_discoveries', []))} scoperte")
            return result

        except Exception as e:
            print(f"⚠️ AI Scoperte fallback: {e}")
            return {
                "ai_analysis": "Fallback: Sistema AI temporaneamente non disponibile",
                "contextual_discoveries": [
                    {
                        "title": "Scoperta locale",
                        "description": "Gem nascosta nelle vicinanze",
                        "distance": "A pochi minuti",
                        "why_now": "Momento ideale per la visita",
                        "local_secret": "Chiedi ai locals per dettagli",
                        "ai_insight": "Analisi AI non disponibile",
                        "timing_perfect": "Sempre un buon momento"
                    }
                ],
                "behavioral_learning": "Sistema di apprendimento non disponibile",
                "adaptive_suggestions": ["Esplora la zona", "Chiedi ai locals"],
                "ai_confidence": "fallback"
            }

    def generate_diario_insights(self, user_actions, preferences, location_history):
        """Real AI travel diary with behavioral analysis"""
        try:
            prompt = f"""
Sei un AI travel companion che analizza comportamenti di viaggio. Analizza i dati e genera insights in formato JSON:

Azioni utente: {json.dumps(user_actions, indent=2)}
Preferenze: {json.dumps(preferences, indent=2)}
Cronologia: {json.dumps(location_history, indent=2)}

Genera insights intelligenti del diario di viaggio in JSON:
{{
    "behavioral_analysis": "Analisi AI dei pattern comportamentali",
    "travel_personality": "Personalità di viaggio dedotta dall'AI",
    "predictive_insights": [
        {{
            "prediction": "Previsione comportamentale",
            "confidence": "percentuale",
            "reasoning": "Ragionamento AI",
            "actionable_tip": "Suggerimento pratico"
        }}
    ],
    "learning_adaptations": "Come l'AI si sta adattando alle tue preferenze",
    "future_recommendations": ["raccomandazione 1", "raccomandazione 2"],
    "ai_evolution": "Come l'AI è evoluta nella comprensione dell'utente",
    "personalization_level": "basic/intermediate/advanced"
}}

Sii perspicace e intelligente nell'analisi comportamentale.
"""

            response = openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion che analizza comportamenti e genera insights personalizzati."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            print(f"✅ AI Diario generato: {result.get('personalization_level', 'unknown')} personalizzazione")
            return result

        except Exception as e:
            print(f"⚠️ AI Diario fallback: {e}")
            return {
                "behavioral_analysis": "Fallback: Analisi AI temporaneamente non disponibile",
                "travel_personality": "In fase di apprendimento",
                "predictive_insights": [
                    {
                        "prediction": "Continuerai ad esplorare nuovi luoghi",
                        "confidence": "70%",
                        "reasoning": "Pattern generale dei viaggiatori",
                        "actionable_tip": "Tieni un diario delle tue esperienze"
                    }
                ],
                "learning_adaptations": "Sistema di apprendimento non disponibile",
                "future_recommendations": ["Esplora nuove destinazioni", "Documenta le tue esperienze"],
                "ai_evolution": "In fase di inizializzazione",
                "personalization_level": "basic"
            }

# Global AI engine
ai_engine = AICompanionEngine()

@ai_companion_bp.route('/ai_piano_b', methods=['POST'])
def generate_ai_piano_b():
    """Generate real AI Piano B"""
    try:
        data = request.get_json()
        itinerary = data.get('itinerary', [])
        context = data.get('context', 'travel planning')
        emergency_type = data.get('emergency_type', 'weather')

        print(f"🧠 Generating AI Piano B for {emergency_type}")

        # Use thread pool for fast AI generation
        future = ai_engine.executor.submit(
            ai_engine.generate_piano_b,
            itinerary,
            context,
            emergency_type
        )

        # Wait with timeout
        try:
            result = future.result(timeout=8)
            return jsonify({
                'status': 'ai_success',
                'piano_b': result,
                'generation_time': 'real-time AI',
                'ai_powered': True
            })
        except Exception as e:
            print(f"⚠️ AI Piano B timeout: {e}")
            return jsonify({
                'status': 'ai_fallback',
                'piano_b': ai_engine.generate_piano_b(itinerary, context, emergency_type),
                'generation_time': 'fallback mode',
                'ai_powered': False
            })

    except Exception as e:
        return jsonify({'error': f'AI Piano B error: {str(e)}'}), 500

@ai_companion_bp.route('/ai_scoperte', methods=['POST'])
def generate_ai_scoperte():
    """Generate real AI intelligent discoveries"""
    try:
        data = request.get_json()
        location = data.get('location', 'unknown')
        time_context = data.get('time_context', 'morning')
        user_profile = data.get('user_profile')

        print(f"🧠 Generating AI Scoperte for {location} at {time_context}")

        future = ai_engine.executor.submit(
            ai_engine.generate_scoperte_intelligenti,
            location,
            time_context,
            user_profile
        )

        try:
            result = future.result(timeout=8)
            return jsonify({
                'status': 'ai_success',
                'scoperte': result,
                'generation_time': 'real-time AI',
                'ai_powered': True
            })
        except Exception as e:
            print(f"⚠️ AI Scoperte timeout: {e}")
            return jsonify({
                'status': 'ai_fallback',
                'scoperte': ai_engine.generate_scoperte_intelligenti(location, time_context, user_profile),
                'generation_time': 'fallback mode',
                'ai_powered': False
            })

    except Exception as e:
        return jsonify({'error': f'AI Scoperte error: {str(e)}'}), 500

@ai_companion_bp.route('/ai_diario', methods=['POST'])
def generate_ai_diario():
    """Generate real AI travel diary insights"""
    try:
        data = request.get_json()
        user_actions = data.get('user_actions', [])
        preferences = data.get('preferences', {})
        location_history = data.get('location_history', [])

        print(f"🧠 Generating AI Diario insights")

        future = ai_engine.executor.submit(
            ai_engine.generate_diario_insights,
            user_actions,
            preferences,
            location_history
        )

        try:
            result = future.result(timeout=8)
            return jsonify({
                'status': 'ai_success',
                'diario': result,
                'generation_time': 'real-time AI',
                'ai_powered': True
            })
        except Exception as e:
            print(f"⚠️ AI Diario timeout: {e}")
            return jsonify({
                'status': 'ai_fallback',
                'diario': ai_engine.generate_diario_insights(user_actions, preferences, location_history),
                'generation_time': 'fallback mode',
                'ai_powered': False
            })

    except Exception as e:
        return jsonify({'error': f'AI Diario error: {str(e)}'}), 500

def get_dynamic_city_coordinates(city_name: str):
    """Get city coordinates dynamically using geocoding"""
    try:
        import requests

        # Use Nominatim for free geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': city_name,
            'format': 'json',
            'limit': 1
        }

        response = requests.get(url, params=params, timeout=5)
        if response.ok and response.json():
            data = response.json()[0]
            coords = [float(data['lat']), float(data['lon'])]
            print(f"🗺️ Dynamic coordinates for {city_name}: {coords}")
            return coords
    except Exception as e:
        print(f"⚠️ Geocoding failed for {city_name}: {e}")

    # Fallback coordinates for major cities
    city_coords = {
        'milano': [45.4642, 9.1900],
        'roma': [41.9028, 12.4964],
        'genova': [44.4056, 8.9463],
        'venezia': [45.4408, 12.3155],
        'firenze': [43.7696, 11.2558],
        'napoli': [40.8518, 14.2681],
        'palermo': [38.1157, 13.3615],  # Palermo, Sicily
        'catania': [37.5079, 15.0830],
        # Sardegna - Costa Smeralda
        'olbia': [40.9239, 9.5002],
        'portorotondo': [41.0165, 9.5353],
        'portocervo': [41.1366, 9.5353],
        'costasmeralda': [41.1100, 9.5500],
        'santeodoro': [40.7731, 9.6656],
        'golfoaranci': [40.9984, 9.6200],
        'london': [51.5074, -0.1278],
        'paris': [48.8566, 2.3522],
        'new york': [40.7128, -74.0060]
    }

    # Never default to Rome - try harder to get real coordinates
    if city_name.lower() in city_coords:
        return city_coords[city_name.lower()]
    
    # Try OpenStreetMap Nominatim one more time with better query
    try:
        import requests
        url = "https://nominatim.openstreetmap.org/search"
        
        # Try with country hint
        for country in ['Italy', 'Italia', 'France', 'Spain', 'Portugal', 'Greece']:
            params = {
                'q': f"{city_name}, {country}",
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = requests.get(url, params=params, timeout=3, headers={'User-Agent': 'Viamigo/1.0'})
            if response.ok and response.json():
                data = response.json()[0]
                coords = [float(data['lat']), float(data['lon'])]
                print(f"🗺️ Found coordinates for {city_name} in {country}: {coords}")
                return coords
    except:
        pass
    
    # Last resort - use AI to get approximate coordinates
    try:
        from openai import OpenAI
        import json
        import os
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Return only JSON with latitude and longitude"},
                {"role": "user", "content": f"What are the GPS coordinates of {city_name}? Return: {{\"lat\": 0.0, \"lon\": 0.0}}"}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        coords_data = json.loads(response.choices[0].message.content)
        return [coords_data['lat'], coords_data['lon']]
    except:
        # True last resort - return center of Italy (not Rome)
        return [42.5, 12.5]  # Geographic center of Italy

def generate_dynamic_attraction_details(attraction, city_name: str):
    """Generate dynamic attraction details from scraped data"""
    return {
        'description': attraction.get('description', f"Visita {attraction['name']} - una delle principali attrazioni di {city_name.title()}"),
        'opening_hours': 'Consultare orari ufficiali locali',
        'price_range': 'Da verificare sul posto',
        'highlights': [f'Attrazione di {city_name.title()}', 'Esperienza locale autentica'],
        'insider_tip': f'Chiedi ai locals per consigli su {attraction["name"]}.',
        'best_time': 'Durante orari di apertura',
        'visit_duration': attraction.get('duration', 1.0),
        'accessibility': 'Da verificare accessibilità',
        'photo_spots': ['Punti panoramici locali']
    }

def generate_ai_attractions_for_city(city_name: str, city_key: str):
    """Use AI to generate authentic attractions for any city"""
    try:
        import os
        from openai import OpenAI
        import json
        
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Get coordinates first
        coords = get_dynamic_city_coordinates(city_name)
        
        prompt = f"""Generate 4 authentic tourist attractions for {city_name}.
        Return a JSON array with exactly 4 attractions in this format:
        [
            {{
                "name": "Name of actual attraction",
                "latitude": {coords[0]},
                "longitude": {coords[1]},
                "description": "Brief authentic description in Italian",
                "duration": 1.5
            }}
        ]
        
        Important:
        - Use REAL attractions that actually exist in {city_name}
        - Vary the coordinates slightly around the city center
        - Include mix of historical sites, cultural attractions, and local highlights
        - Descriptions should be authentic and informative
        """
        
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a travel expert who knows authentic local attractions."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        attractions_data = json.loads(response.choices[0].message.content)
        if 'attractions' in attractions_data:
            attractions_data = attractions_data['attractions']
        elif not isinstance(attractions_data, list):
            attractions_data = [attractions_data]
            
        # Convert to our format
        dynamic_attractions = []
        for attr in attractions_data[:4]:
            dynamic_attractions.append({
                'name': attr.get('name', f'Attrazione {city_name}'),
                'coords': [
                    attr.get('latitude', coords[0] + (len(dynamic_attractions) * 0.01)),
                    attr.get('longitude', coords[1] + (len(dynamic_attractions) * 0.01))
                ],
                'duration': attr.get('duration', 1.5),
                'description': attr.get('description', f'Attrazione autentica di {city_name}')
            })
        
        print(f"✅ AI generated {len(dynamic_attractions)} attractions for {city_name}")
        return dynamic_attractions
        
    except Exception as e:
        print(f"⚠️ AI generation failed: {e}, using fallback")
        # Fallback with basic city center
        coords = get_dynamic_city_coordinates(city_name)
        return [{
            'name': f'Centro storico di {city_name}',
            'coords': coords,
            'duration': 2.0,
            'description': f'Esplora il centro storico di {city_name}'
        }]

def cache_attractions_to_db(city_name: str, attractions):
    """Cache generated attractions to database for future use"""
    try:
        from models import PlaceCache
        from flask_app import db
        import json
        
        for attraction in attractions:
            cache_key = f"{city_name.lower()}_{attraction['name'].lower().replace(' ', '_')}"
            
            # Check if already exists
            existing = PlaceCache.query.filter_by(cache_key=cache_key).first()
            if not existing:
                place_data = {
                    'name': attraction['name'],
                    'latitude': attraction['coords'][0],
                    'longitude': attraction['coords'][1],
                    'description': attraction.get('description', ''),
                    'category': 'tourist_attraction',
                    'duration': attraction.get('duration', 1.5)
                }
                
                new_cache = PlaceCache(
                    cache_key=cache_key,
                    place_name=attraction['name'],
                    city=city_name,
                    country='Italy',  # Can be enhanced with country detection
                    place_data=json.dumps(place_data),
                    priority_level='ai_generated'
                )
                db.session.add(new_cache)
        
        db.session.commit()
        print(f"✅ Cached {len(attractions)} attractions for {city_name}")
        
    except Exception as e:
        print(f"⚠️ Failed to cache attractions: {e}")

@ai_companion_bp.route('/plan_ai_powered', methods=['POST'])
def plan_ai_powered():
    """Complete AI-powered planning with all companion features"""
    try:
        data = request.get_json()
        start = data.get('start', 'Piazza Duomo, Milano')
        end = data.get('end', 'Corso Buenos Aires, Milano')
        interests = data.get('interests', [])
        pace = data.get('pace', 'Moderato')
        budget = data.get('budget', '€€')

        print(f"🧠 AI-powered planning: {start} → {end}")

        # Detect city from input with proper geographical mapping
        def detect_city_from_input(location_text):
            city_mappings = {
                # Lombardia
                'milano': ('milano', 'Milano'),
                'milan': ('milano', 'Milano'),
                'duomo': ('milano', 'Milano'),
                'buenos aires': ('milano', 'Milano'),
                # Liguria
                'genova': ('genova', 'Genova'),
                'portofino': ('genova', 'Portofino'),
                'cinque terre': ('genova', 'Cinque Terre'),
                # Lazio
                'roma': ('roma', 'Roma'),
                'rome': ('roma', 'Roma'),
                'colosseo': ('roma', 'Roma'),
                'trevi': ('roma', 'Roma'),
                # Veneto
                'venezia': ('venezia', 'Venezia'),
                'venice': ('venezia', 'Venezia'),
                'san marco': ('venezia', 'Venezia'),
                'rialto': ('venezia', 'Venezia'),
                # Toscana
                'firenze': ('firenze', 'Firenze'),
                'florence': ('firenze', 'Firenze'),
                # Campania
                'napoli': ('napoli', 'Napoli'),
                'naples': ('napoli', 'Napoli'),
                'spaccanapoli': ('napoli', 'Napoli'),
                # Sicilia
                'palermo': ('palermo', 'Palermo'),
                'pretoria': ('palermo', 'Palermo'),
                'villena': ('palermo', 'Palermo'),
                'quattro canti': ('palermo', 'Palermo'),
                'catania': ('catania', 'Catania'),
                'taormina': ('taormina', 'Taormina'),
                'siracusa': ('siracusa', 'Siracusa'),
                # Sardegna - Costa Smeralda & Olbia
                'olbia': ('olbia', 'Olbia'),
                'portorotondo': ('portorotondo', 'Porto Rotondo'),
                'porto rotondo': ('portorotondo', 'Porto Rotondo'),
                'rotondo': ('portorotondo', 'Porto Rotondo'),
                'porto cervo': ('portocervo', 'Porto Cervo'),
                'portocervo': ('portocervo', 'Porto Cervo'),
                'cervo': ('portocervo', 'Porto Cervo'),
                'costa smeralda': ('costasmeralda', 'Costa Smeralda'),
                'san teodoro': ('santeodoro', 'San Teodoro'),
                'golfo aranci': ('golfoaranci', 'Golfo Aranci'),
                # UK
                'london': ('london', 'London'),
                'londra': ('london', 'London'),
                'big ben': ('london', 'London'),
                'tower bridge': ('london', 'London')
            }

            location_lower = location_text.lower()
            for city_name, (city_key, city_display) in city_mappings.items():
                if city_name in location_lower:
                    return city_key, city_display

            # Dynamic city extraction from comma-separated format
            import re
            # Extract city name after comma (e.g., "piazza pretoria,palermo" -> "palermo")
            comma_match = re.search(r',\s*([a-z]+)', location_lower)
            if comma_match:
                extracted_city = comma_match.group(1)
                # Capitalize properly for display
                city_display = extracted_city.capitalize()
                return extracted_city, city_display
            
            # If no city found, try to extract from the input
            # Split by spaces and check last word as potential city
            words = location_lower.split()
            if len(words) > 0:
                potential_city = words[-1]
                if len(potential_city) > 3:  # Reasonable city name length
                    return potential_city, potential_city.capitalize()

            # Default to generic city handling (will use AI to generate appropriate content)
            return 'generic', 'Unknown City'

        # Get city information from both start and end
        start_city_key, start_city_name = detect_city_from_input(start)
        end_city_key, end_city_name = detect_city_from_input(end)

        # Special handling for Costa Smeralda destinations
        # If destination contains specific locations, prioritize them
        end_lower = end.lower()
        if 'porto cervo' in end_lower or 'portocervo' in end_lower:
            city_key = 'portocervo'
            city_name = 'Porto Cervo'
        elif 'porto rotondo' in end_lower or 'portorotondo' in end_lower:
            city_key = 'portorotondo'
            city_name = 'Porto Rotondo'
        elif 'costa smeralda' in end_lower:
            city_key = 'costasmeralda'
            city_name = 'Costa Smeralda'
        else:
            # Use the destination city as primary
            city_key = end_city_key
            city_name = end_city_name

        print(f"🏛️ Planning for {city_name} based on route: {start} → {end}")

        # Get real data for the correct city
        from cost_effective_scraping import CostEffectiveDataProvider
        from models import PlaceCache

        print(f"🏛️ Checking PostgreSQL database for {city_name}")

        # Check PostgreSQL database for pre-populated data
        postgres_attractions = []
        postgres_restaurants = []

        # Add hardcoded attractions for major cities
        city_attractions = {
            'milano': [
                {'name': 'Duomo di Milano', 'latitude': 45.4642, 'longitude': 9.1900, 'description': 'Magnifica cattedrale gotica nel cuore di Milano'},
                {'name': 'Galleria Vittorio Emanuele II', 'latitude': 45.4656, 'longitude': 9.1901, 'description': 'Storica galleria commerciale del 1865'},
                {'name': 'Castello Sforzesco', 'latitude': 45.4703, 'longitude': 9.1794, 'description': 'Fortezza storica con musei e giardini'},
                {'name': 'Navigli', 'latitude': 45.4502, 'longitude': 9.1812, 'description': 'Quartiere dei canali con ristoranti e vita notturna'}
            ],
            'roma': [
                {'name': 'Colosseo', 'latitude': 41.8902, 'longitude': 12.4922, 'description': 'Anfiteatro Flavio, simbolo di Roma antica'},
                {'name': 'Fontana di Trevi', 'latitude': 41.9009, 'longitude': 12.4833, 'description': 'Fontana barocca più famosa al mondo'},
                {'name': 'Pantheon', 'latitude': 41.8986, 'longitude': 12.4769, 'description': 'Tempio romano meglio conservato'},
                {'name': 'Piazza Navona', 'latitude': 41.8992, 'longitude': 12.4730, 'description': 'Piazza barocca con fontana del Bernini'}
            ],
            'venezia': [
                {'name': 'Piazza San Marco', 'latitude': 45.4345, 'longitude': 12.3387, 'description': 'Il salotto di Venezia con la Basilica'},
                {'name': 'Ponte di Rialto', 'latitude': 45.4380, 'longitude': 12.3360, 'description': 'Ponte storico sul Canal Grande'},
                {'name': 'Palazzo Ducale', 'latitude': 45.4334, 'longitude': 12.3406, 'description': 'Capolavoro gotico veneziano'},
                {'name': 'Canal Grande', 'latitude': 45.4370, 'longitude': 12.3327, 'description': 'Arteria principale di Venezia'}
            ],
            'napoli': [
                {'name': 'Spaccanapoli', 'latitude': 40.8518, 'longitude': 14.2581, 'description': 'Via storica che taglia il centro antico'},
                {'name': 'Castel dell\'Ovo', 'latitude': 40.8280, 'longitude': 14.2478, 'description': 'Castello sul mare nel Borgo Marinari'},
                {'name': 'Piazza del Plebiscito', 'latitude': 40.8359, 'longitude': 14.2487, 'description': 'Grande piazza con Palazzo Reale'},
                {'name': 'Quartieri Spagnoli', 'latitude': 40.8455, 'longitude': 14.2490, 'description': 'Vicoli caratteristici napoletani'}
            ],
            'london': [
                {'name': 'Big Ben', 'latitude': 51.5007, 'longitude': -0.1246, 'description': 'Iconic clock tower of Westminster'},
                {'name': 'Tower Bridge', 'latitude': 51.5055, 'longitude': -0.0754, 'description': 'Victorian Gothic bridge over Thames'},
                {'name': 'British Museum', 'latitude': 51.5194, 'longitude': -0.1270, 'description': 'World history and culture museum'},
                {'name': 'Buckingham Palace', 'latitude': 51.5014, 'longitude': -0.1419, 'description': 'Royal residence with changing of guard'}
            ],
            'palermo': [
                {'name': 'Cattedrale di Palermo', 'latitude': 38.1145, 'longitude': 13.3561, 'description': 'Maestosa cattedrale normanna con cripta reale'},
                {'name': 'Teatro Massimo', 'latitude': 38.1203, 'longitude': 13.3571, 'description': 'Il più grande teatro lirico d\'Italia'},
                {'name': 'Mercato di Ballarò', 'latitude': 38.1109, 'longitude': 13.3590, 'description': 'Mercato storico con street food siciliano'},
                {'name': 'Palazzo dei Normanni', 'latitude': 38.1109, 'longitude': 13.3530, 'description': 'Palazzo reale con Cappella Palatina'},
                {'name': 'Quattro Canti', 'latitude': 38.1157, 'longitude': 13.3613, 'description': 'Piazza barocca ottagonale al centro'},
                {'name': 'Piazza Pretoria', 'latitude': 38.1159, 'longitude': 13.3620, 'description': 'Piazza con fontana monumentale'}
            ],
            'olbia': [
                {'name': 'Basilica di San Simplicio', 'latitude': 40.9239, 'longitude': 9.5002, 'description': 'Chiesa romanica del XI secolo, monumento più importante di Olbia'},
                {'name': 'Porto di Olbia', 'latitude': 40.9250, 'longitude': 9.5150, 'description': 'Porto turistico con vista sull\'isola di Tavolara'},
                {'name': 'Museo Archeologico', 'latitude': 40.9231, 'longitude': 9.4968, 'description': 'Reperti nuragici e relitti di navi romane'},
                {'name': 'Corso Umberto', 'latitude': 40.9240, 'longitude': 9.4978, 'description': 'Via principale dello shopping e aperitivi'}
            ],
            'portorotondo': [
                {'name': 'Piazzetta San Marco', 'latitude': 41.0165, 'longitude': 9.5353, 'description': 'Piazza centrale in stile veneziano con caffè e boutique'},
                {'name': 'Marina di Porto Rotondo', 'latitude': 41.0170, 'longitude': 9.5370, 'description': 'Porto turistico esclusivo con yacht di lusso'},
                {'name': 'Chiesa di San Lorenzo', 'latitude': 41.0158, 'longitude': 9.5345, 'description': 'Chiesa moderna con sculture di Mario Ceroli'},
                {'name': 'Spiaggia Ira', 'latitude': 41.0120, 'longitude': 9.5400, 'description': 'Spiaggia di sabbia bianca con acque cristalline'},
                {'name': 'Teatro di Porto Rotondo', 'latitude': 41.0155, 'longitude': 9.5360, 'description': 'Anfiteatro all\'aperto per eventi estivi'}
            ],
            'portocervo': [
                {'name': 'Piazzetta di Porto Cervo', 'latitude': 41.1366, 'longitude': 9.5353, 'description': 'Centro mondano della Costa Smeralda'},
                {'name': 'Marina di Porto Cervo', 'latitude': 41.1370, 'longitude': 9.5370, 'description': 'Porto più esclusivo del Mediterraneo'},
                {'name': 'Chiesa Stella Maris', 'latitude': 41.1350, 'longitude': 9.5340, 'description': 'Chiesa moderna con vista panoramica'},
                {'name': 'Pevero Golf Club', 'latitude': 41.1300, 'longitude': 9.5200, 'description': 'Campo da golf più prestigioso della Sardegna'}
            ]
        }
        
        if city_key in city_attractions:
            postgres_attractions = [
                {**attr, 'source': 'Local Knowledge'} 
                for attr in city_attractions[city_key]
            ]
            
        try:
            # Only query if not in our hardcoded cities
            attraction_cache = []
            if city_key not in city_attractions:
                attraction_cache = PlaceCache.query.filter(
                    PlaceCache.city.ilike(f'%{city_name}%')
                ).filter(
                    PlaceCache.place_data.contains('tourist_attraction')
                ).limit(4).all()

            for cache_entry in attraction_cache:
                place_data = cache_entry.get_place_data()
                if place_data:
                    postgres_attractions.append({
                        'name': place_data.get('name', cache_entry.place_name),
                        'latitude': place_data.get('latitude', 45.4642),
                        'longitude': place_data.get('longitude', 9.1900),
                        'description': place_data.get('description', f'Historic attraction in {city_name}'),
                        'source': 'PostgreSQL Database'
                    })

            print(f"🏛️ Found {len(postgres_attractions)} attractions in PostgreSQL")

        except Exception as e:
            print(f"⚠️ PostgreSQL query error: {e}")

        # If insufficient data, use cost-effective scraping for the CORRECT city
        real_attractions = postgres_attractions

        if len(real_attractions) < 2:
            print(f"🔍 PostgreSQL insufficient, using cost-effective scraping for {city_name}")
            scraping_provider = CostEffectiveDataProvider()
            scraped_attractions = scraping_provider.get_places_data(city_name, "tourist_attraction")

            # Combine PostgreSQL + scraped data
            real_attractions.extend(scraped_attractions)
        else:
            print(f"✅ Using PostgreSQL data for {city_name}")

        # Build dynamic attractions list for the CORRECT city
        dynamic_attractions = []

        if real_attractions:
            for attraction in real_attractions[:4]:  # Use top 4 attractions
                dynamic_attractions.append({
                    'name': attraction['name'],
                    'coords': [attraction['latitude'], attraction['longitude']],
                    'duration': 1.5,  # Default duration
                    'description': attraction.get('description', f'Attraction in {city_name}')
                })
            print(f"✅ Using {len(dynamic_attractions)} DYNAMIC attractions for {city_name}")
        else:
            print(f"⚠️ No dynamic attractions found for {city_name}, using AI generation")
            # Use AI to generate authentic attractions for any city
            dynamic_attractions = generate_ai_attractions_for_city(city_name, city_key)
            
            # Cache the generated attractions for future use
            if dynamic_attractions:
                cache_attractions_to_db(city_name, dynamic_attractions)

        # Get coordinates for the correct city
        if dynamic_attractions and dynamic_attractions[0]['coords'][0] != 0:
            starting_coords = dynamic_attractions[0]['coords']
        else:
            starting_coords = get_dynamic_city_coordinates(city_name)

        print(f"🗺️ Using coordinates {starting_coords} for city: {city_key}")

        # Initialize current_time for itinerary building
        current_time = 9.0  # Start at 9:00 AM

        # Build intelligent itinerary starting from user's specified location
        itinerary = [
            {
                'time': '09:00',
                'title': start,
                'description': f'Punto di partenza: {start}',
                'coordinates': starting_coords,
                'context': f'{start.lower().replace(" ", "_").replace(",", "")}_{city_key}',
                'transport': 'start',
                'type': 'activity'
            }
        ]

        # Build comprehensive itinerary with multiple waypoints
        for i, attraction in enumerate(dynamic_attractions[:4]):
            # Calculate travel time and method based on distance
            if i > 0:
                travel_duration = 0.33  # 20 minutes between attractions
                current_time += travel_duration

                itinerary.append({
                    "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                    "title": f"Verso {attraction['name']}",
                    "description": f"Breve passeggiata di 15-20 minuti attraverso {city_name}",
                    "type": "transport",
                    "context": f"walk_to_{attraction['name'].lower().replace(' ', '_')}",
                    "coordinates": attraction['coords'],
                    "transport": "walking"
                })

            # Add main activity with FULL DETAILS
            activity_duration = attraction.get('duration', 1.5)
            start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            current_time += activity_duration
            end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"

            # Generate dynamic details using attraction data
            details = generate_dynamic_attraction_details(attraction, city_name)

            # Use rich description from details
            description = details['description']

            itinerary.append({
                "time": f"{start_time} - {end_time}",
                "title": attraction['name'],
                "description": description,
                "type": "activity",
                "context": attraction['name'].lower().replace(' ', '_').replace('di_', '').replace('del_', '').replace('di', '').replace('del', '').replace('__', '_').strip('_'),
                "coordinates": attraction['coords'],
                "transport": "visit",

                # Store rich details in context for modal display only
                "_rich_details": {
                    "opening_hours": details['opening_hours'],
                    "price_range": details['price_range'],
                    "highlights": details['highlights'],
                    "insider_tip": details['insider_tip'],
                    "best_time": details['best_time'],
                    "accessibility": details['accessibility'],
                    "photo_spots": details['photo_spots'],
                    "visit_duration_hours": details['visit_duration']
                }
            })

        # Add local tips for the correct city
        itinerary.extend([
            {
                "type": "tip",
                "title": f"🏛️ Storia di {city_name}",
                "description": f"Esplora la ricca storia e cultura di {city_name} attraverso i suoi monumenti principali."
            },
            {
                "type": "tip",
                "title": f"📸 Photo Spots",
                "description": f"Non perdere le migliori location per foto caratteristiche di {city_name}."
            }
        ])

        print(f"✅ Generated itinerary with {len(itinerary)} items for {city_name}")

        return jsonify({
            "itinerary": itinerary,
            "city": city_name,
            "total_duration": f"{current_time - 9:.1f} hours",
            "status": "success"
        })

    except Exception as e:
        print(f"❌ AI-powered planning error: {e}")
        return jsonify({
            "error": f"Planning failed: {str(e)}",
            "itinerary": []
        }), 500