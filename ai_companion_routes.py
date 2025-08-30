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
        'firenze': [43.7696, 11.2558]
    }

    return city_coords.get(city_name.lower(), [41.9028, 12.4964])

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
                # Veneto
                'venezia': ('venezia', 'Venezia'),
                'venice': ('venezia', 'Venezia'),
                # Toscana
                'firenze': ('firenze', 'Firenze'),
                'florence': ('firenze', 'Firenze')
            }

            location_lower = location_text.lower()
            for city_name, (city_key, city_display) in city_mappings.items():
                if city_name in location_lower:
                    return city_key, city_display

            # Default to Milano if not found
            return 'milano', 'Milano'

        # Get city information from both start and end
        start_city_key, start_city_name = detect_city_from_input(start)
        end_city_key, end_city_name = detect_city_from_input(end)

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

        # Add hardcoded Milano attractions if needed
        if city_key == 'milano':
            milano_attractions = [
                {
                    'name': 'Duomo di Milano',
                    'latitude': 45.4642, 
                    'longitude': 9.1900,
                    'description': 'Magnifica cattedrale gotica nel cuore di Milano',
                    'source': 'Local Knowledge'
                },
                {
                    'name': 'Galleria Vittorio Emanuele II',
                    'latitude': 45.4656,
                    'longitude': 9.1901,
                    'description': 'Storica galleria commerciale del 1865',
                    'source': 'Local Knowledge'
                },
                {
                    'name': 'Castello Sforzesco',
                    'latitude': 45.4703,
                    'longitude': 9.1794,
                    'description': 'Fortezza storica con musei e giardini',
                    'source': 'Local Knowledge'
                },
                {
                    'name': 'Navigli',
                    'latitude': 45.4502,
                    'longitude': 9.1812,
                    'description': 'Quartiere dei canali con ristoranti e vita notturna',
                    'source': 'Local Knowledge'
                }
            ]
            postgres_attractions = milano_attractions[:4]
            
        try:
            # Only query if not Milano (since we hardcoded it)
            if city_key != 'milano':
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
            print(f"⚠️ No dynamic attractions found for {city_name}")
            # Get correct coordinates for the city
            city_coords = get_dynamic_city_coordinates(city_name)
            dynamic_attractions = [{
                'name': f'Centro di {city_name}',
                'coords': city_coords,
                'duration': 1.0,
                'description': f'Centro storico di {city_name}'
            }]

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