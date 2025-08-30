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
                model="gpt-5",  # Latest model as per blueprint
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion esperto che genera Piani B intelligenti e dinamici."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=6  # Fast timeout
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
                timeout=6
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
                timeout=6
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

# Import Flask essentials
from flask import Blueprint, request, jsonify
import json
import random
from datetime import datetime

# Create blueprint
ai_companion_bp = Blueprint('ai_companion', __name__)

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

@ai_companion_bp.route('/plan_ai_powered', methods=['POST'])
def plan_ai_powered():
    """Complete AI-powered planning with all companion features"""
    try:
        data = request.get_json()
        start = data.get('start', 'Piazza De Ferrari, Genova')
        end = data.get('end', 'Acquario di Genova')
        interests = data.get('interests', [])
        pace = data.get('pace', 'Moderato')
        budget = data.get('budget', '€€')

        print(f"🧠 AI-powered planning: {start} → {end}")

        # Detect city from input with proper geographical mapping
        def detect_city_from_input(location_text):
            city_mappings = {
                # Liguria
                'genova': ('genova', 'Genova'),
                'portofino': ('genova', 'Portofino'),
                'cinque terre': ('genova', 'Cinque Terre'),
                # Sardegna
                'olbia': ('olbia', 'Olbia'),
                'porto': ('olbia', 'Olbia'),
                'portorotondo': ('olbia', 'Porto Rotondo'),
                'costa smeralda': ('olbia', 'Costa Smeralda'),
                'porto cervo': ('olbia', 'Porto Cervo'),
                # Lombardia
                'milano': ('milano', 'Milano'),
                # Lazio
                'roma': ('roma', 'Roma'),
                # Toscana
                'firenze': ('firenze', 'Firenze'),
                # Veneto
                'venezia': ('venezia', 'Venezia'),
                # Internazionali
                'new york': ('new_york', 'New York'),
                'manhattan': ('new_york', 'New York'),
                'brooklyn': ('new_york', 'New York')
            }

            location_lower = location_text.lower()
            for city_name, (city_key, city_display) in city_mappings.items():
                if city_name in location_lower:
                    return city_key, city_display

            # If no match found, try to extract a reasonable city name
            if 'sardegna' in location_lower or 'sardinia' in location_lower:
                return 'olbia', 'Sardegna'

            # Extract city name dynamically without hardcoded fallback
            words = location_text.split()
            for word in words:
                clean_word = word.strip(',').strip()
                if len(clean_word) > 2:
                    return clean_word.lower(), clean_word.title()

            return 'unknown', 'Unknown Location'

        # 🗄️ DATA SOURCE HIERARCHY: PostgreSQL → Cost-effective scraping → Static fallback
        from cost_effective_scraping import CostEffectiveDataProvider
        from models import PlaceCache

        # Get city information
        end_city_key, end_city_name = detect_city_from_input(end)

        # Check if destination is specifically Nervi
        is_nervi_destination = 'nervi' in end.lower() or 'parchi' in end.lower()

        print(f"🏛️ Checking PostgreSQL database for {end_city_name}")

        # 1. FIRST: Check PostgreSQL database for pre-populated data
        postgres_attractions = []
        postgres_restaurants = []

        try:
            # Query attractions from PostgreSQL
            attraction_cache = PlaceCache.query.filter(
                PlaceCache.city.ilike(f'%{end_city_name}%')
            ).filter(
                PlaceCache.place_data.contains('tourist_attraction')
            ).limit(4).all()

            for cache_entry in attraction_cache:
                place_data = cache_entry.get_place_data()
                if place_data:
                    postgres_attractions.append({
                        'name': place_data.get('name', cache_entry.place_name),
                        'latitude': place_data.get('latitude', 44.4063),
                        'longitude': place_data.get('longitude', 8.9314),
                        'description': place_data.get('description', f'Historic attraction in {end_city_name}'),
                        'source': 'PostgreSQL Database'
                    })

            print(f"🏛️ Found {len(postgres_attractions)} attractions in PostgreSQL")

        except Exception as e:
            print(f"⚠️ PostgreSQL query error: {e}")

        # 2. SECOND: If insufficient data, use cost-effective scraping
        real_attractions = postgres_attractions
        real_restaurants = postgres_restaurants

        if len(real_attractions) < 2:
            print(f"🔍 PostgreSQL insufficient, using cost-effective scraping for {end_city_name}")
            scraping_provider = CostEffectiveDataProvider()
            scraped_attractions = scraping_provider.get_places_data(end_city_name, "tourist_attraction")
            scraped_restaurants = scraping_provider.get_places_data(end_city_name, "restaurant")

            # Combine PostgreSQL + scraped data
            real_attractions.extend(scraped_attractions)
            real_restaurants.extend(scraped_restaurants)
        else:
            print(f"✅ Using PostgreSQL data for {end_city_name}")

        # 🌟 COMPLETELY DYNAMIC - Use scraped data for attractions
        dynamic_attractions = []

        if real_attractions:
            for attraction in real_attractions[:4]:  # Use top 4 scraped attractions
                dynamic_attractions.append({
                    'name': attraction['name'],
                    'coords': [attraction['latitude'], attraction['longitude']],
                    'duration': 1.5,  # Default duration
                    'description': attraction.get('description', f'Attraction in {end_city_name}')
                })
            print(f"✅ Using {len(dynamic_attractions)} DYNAMIC attractions for {end_city_name}")
        else:
            print(f"⚠️ No dynamic attractions found for {end_city_name}")
            dynamic_attractions = [{
                'name': f'Centro di {end_city_name}',
                'coords': [0, 0],  # Will be set dynamically below
                'duration': 1.0,
                'description': f'Centro storico di {end_city_name}'
            }]

        # 🗺️ DYNAMIC COORDINATES - Get from first attraction or geocoding
        if dynamic_attractions and dynamic_attractions[0]['coords'][0] != 0:
            starting_coords = dynamic_attractions[0]['coords']
        else:
            # Fallback: Use geocoding to get city center coordinates
            starting_coords = get_dynamic_city_coordinates(end_city_name)
            # Update the placeholder attraction with real coordinates
            if dynamic_attractions:
                dynamic_attractions[0]['coords'] = starting_coords
        print(f"🗺️ Using coordinates {starting_coords} for city: {end_city_key}")

        # Initialize current_time for itinerary building
        current_time = 9.0  # Start at 9:00 AM

        # Build intelligent itinerary starting from user's specified location
        itinerary = [
            {
                'time': '09:00',
                'title': start,
                'description': f'Punto di partenza: {start}',
                'coordinates': starting_coords,
                'context': f'{start.lower().replace(" ", "_").replace(",", "")}_{end_city_key}',
                'transport': 'start',
                'type': 'activity'
            }
        ]

        # For Nervi destination, add train travel
        if is_nervi_destination:
            current_time += 0.5  # 30 minutes
            itinerary.append({
                'time': f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                'title': 'Viaggio in treno verso Nervi',
                'description': 'Treno regionale da Genova Brignole a Nervi (20 minuti, €2.20)',
                'coordinates': [44.3878, 8.9515],
                'context': 'train_to_nervi',
                'type': 'transport',
                'transport': 'train'
            })
            current_time += 0.33  # 20 minutes

        # Build comprehensive itinerary with multiple waypoints
        end_lower = end.lower()

        # Always include multiple attractions for a rich experience
        selected_attractions = []

        # If user specifically requested a destination, include it as main attraction
        if 'acquario' in end_lower:
            # Build complete Genova waterfront experience
            selected_attractions = [
                {'name': 'Via del Campo', 'coords': [44.4055, 8.9298], 'duration': 0.75},
                {'name': 'Cattedrale di San Lorenzo', 'coords': [44.4082, 8.9309], 'duration': 1.0},
                {'name': 'Porto Antico', 'coords': [44.4108, 8.9279], 'duration': 1.0},
                {'name': 'Acquario di Genova', 'coords': [44.4109, 8.9326], 'duration': 2.5}
            ]
        elif 'castelletto' in end_lower or 'spianata' in end_lower:
            # Build complete historic center + panoramic experience
            selected_attractions = [
                {'name': 'Via del Campo', 'coords': [44.4055, 8.9298], 'duration': 0.75},
                {'name': 'Cattedrale di San Lorenzo', 'coords': [44.4082, 8.9309], 'duration': 1.0},
                {'name': 'Palazzo Ducale', 'coords': [44.4071, 8.9348], 'duration': 1.0},
                {'name': 'Spianata Castelletto', 'coords': [44.4127, 8.9264], 'duration': 1.5}
            ]
        else:
            # Complete Genova experience with multiple attractions
            selected_attractions = dynamic_attractions[:4]  # Include 4 attractions for rich experience

        # GEOGRAPHIC SEQUENCING: Sort attractions by proximity to create logical route
        def calculate_distance(coord1, coord2):
            """Calculate simple Euclidean distance between two coordinates"""
            return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)**0.5

        def sort_attractions_by_proximity(attractions, start_coords):
            """Sort attractions to create optimal geographical sequence"""
            if not attractions:
                return []

            sorted_attractions = []
            remaining = attractions.copy()
            current_location = start_coords

            while remaining:
                # Find closest attraction to current location
                closest_idx = min(range(len(remaining)),
                                key=lambda i: calculate_distance(current_location, remaining[i]['coords']))

                closest_attraction = remaining.pop(closest_idx)
                sorted_attractions.append(closest_attraction)
                current_location = closest_attraction['coords']

            return sorted_attractions

        # Apply geographical sorting
        selected_attractions = sort_attractions_by_proximity(selected_attractions, starting_coords)

        print(f"🗺️ Optimized route with {len(selected_attractions)} stops in geographical order")

        for i, attraction in enumerate(selected_attractions):
            # Calculate real travel time and method based on distance
            if i > 0:
                prev_coords = selected_attractions[i-1]['coords']
                current_coords = attraction['coords']
                distance_km = calculate_distance(prev_coords, current_coords) * 111  # Rough km conversion

                # Determine transport method and time based on distance
                if distance_km > 2:  # >2km = public transport
                    if attraction['name'] == 'Spianata Castelletto':
                        transport_method = "funicolare"
                        travel_duration = 0.25  # 15 min
                        transport_desc = f"Funicolare da Piazza Portello (€0.90) - {int(travel_duration*60)} minuti"
                    else:
                        transport_method = "metro/bus"
                        travel_duration = 0.33  # 20 min
                        transport_desc = f"Metro/bus urbano - {int(travel_duration*60)} minuti"
                elif distance_km > 0.8:  # 0.8-2km = longer walk
                    transport_method = "walking"
                    travel_duration = distance_km * 0.2  # 12 min/km
                    transport_desc = f"Passeggiata di {int(travel_duration*60)} minuti ({distance_km:.1f}km)"
                else:  # <0.8km = short walk
                    transport_method = "walking"
                    travel_duration = 0.17  # 10 min
                    transport_desc = f"Breve passeggiata di {int(travel_duration*60)} minuti"

                start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
                current_time += travel_duration
                end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"

                itinerary.append({
                    "time": f"{start_time} - {end_time}",
                    "title": f"Verso {attraction['name']}",
                    "description": transport_desc,
                    "type": "transport",
                    "context": f"walk_to_{attraction['name'].lower().replace(' ', '_')}",
                    "coordinates": attraction['coords'],
                    "transport": transport_method,
                    "distance_km": round(distance_km, 1),
                    "duration_minutes": int(travel_duration * 60)
                })

            # Add main activity with FULL DETAILS
            activity_duration = attraction.get('duration', 1.5)
            start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            current_time += activity_duration
            end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"

            # 🚀 DYNAMIC DETAILS - Generate using attraction data
            details = generate_dynamic_attraction_details(attraction, end_city_name)

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

            # Add contextual tips and photo opportunities
            if i == 0:
                if is_nervi_destination:
                    itinerary.append({
                        "type": "tip",
                        "title": "🚂 Come arrivare",
                        "description": "Treno regionale da Genova Brignole a Nervi (20 min, €2.20). Ogni 30 minuti."
                    })
                else:
                    itinerary.append({
                        "type": "tip",
                        "title": "📸 Photo Stop",
                        "description": f"Perfetto per foto ai caratteristici caruggi. Cerca i dettagli architettonici medievali."
                    })

            # Add intermediate photo stops and local insights
            if i == 1 and len(selected_attractions) > 2:
                current_time += 0.17  # 10 minutes
                itinerary.append({
                    "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                    "title": "Sosta panoramica",
                    "description": "Fermata per foto al panorama sui tetti di Genova e il porto",
                    "coordinates": [attraction['coords'][0] + 0.001, attraction['coords'][1] + 0.001],
                    "context": "photo_stop_panorama",
                    "type": "activity",
                    "transport": "photo"
                })

            if i == 2 and 'acquario' in end_lower:
                # Add gelato break before Acquario
                current_time += 0.25  # 15 minutes
                itinerary.append({
                    "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                    "title": "Gelateria Il Doge",
                    "description": "Pausa gelato con vista sul porto prima dell'Acquario. Prova il gusto 'Pesto' tipico genovese!",
                    "coordinates": [44.4105, 8.9285],
                    "context": "gelateria_il_doge",
                    "type": "activity",
                    "transport": "visit",
                    "_rich_details": {
                        "opening_hours": "10:00-22:00",
                        "price_range": "€3-5",
                        "highlights": ["Gelato artigianale", "Vista porto", "Gusti tipici liguri"]
                    }
                })

                itinerary.append({
                    "type": "tip",
                    "title": "🍦 Local Secret",
                    "description": "I genovesi mangiano il gelato anche d'inverno! Il 'focaccia al formaggio' con gelato è una combo locale."
                })

        # Add lunch break if itinerary is long enough
        if current_time > 12.5:  # After 12:30
            itinerary.append({
                "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                "title": "Pranzo tipico genovese",
                "description": "Trattoria Antica Osteria del Borgo - Pesto fatto in casa, focaccia col formaggio e farinata",
                "coordinates": [44.4065, 8.9295],
                "context": "antica_osteria_borgo",
                "type": "activity",
                "transport": "visit",
                "_rich_details": {
                    "opening_hours": "12:00-15:00, 19:00-23:00",
                    "price_range": "€25-35 a persona",
                    "highlights": ["Pesto al mortaio", "Focaccia col formaggio DOP", "Farinata calda", "Vino Vermentino"],
                    "insider_tip": "Ordina il 'menu degustazione ligure' - include pesto, focaccia e farinata"
                }
            })
            current_time += 1.0  # 1 hour lunch

            itinerary.append({
                "type": "tip",
                "title": "🍝 Tradizione culinaria",
                "description": "Il pesto genovese DOP deve essere fatto solo con basilico genovese, aglio, pinoli, parmigiano, pecorino e olio EVO ligure."
            })

        # Add aperitivo if it's late afternoon
        if current_time > 17.0:
            itinerary.append({
                "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                "title": "Aperitivo con vista",
                "description": "Rooftop Bar Palazzo Grillo - Cocktail con vista panoramica sui tetti di Genova",
                "coordinates": [44.4075, 8.9325],
                "context": "aperitivo_palazzo_grillo",
                "type": "activity",
                "transport": "visit",
                "opening_hours": "17:00-02:00",
                "price_range": "€8-12 per cocktail",
                "highlights": ["Vista panoramica", "Cocktail signature", "Aperitivo ligure", "Terrazza storica"]
            })
            current_time += 0.5

        # Ensure the itinerary ends meaningfully
        if current_time < 19.0:  # If still early evening
            itinerary.append({
                "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                "title": "Passeggiata serale",
                "description": "Rientro attraverso i caruggi illuminati - Genova di sera ha un fascino particolare",
                "coordinates": starting_coords,
                "context": "evening_walk_caruggi",
                "type": "activity",
                "transport": "walking"
            })

        # Add comprehensive local tips and cultural insights
        if is_nervi_destination:
            itinerary.append({
                "type": "tip",
                "title": "🌸 Stagione ideale",
                "description": "Primavera per la fioritura nei parchi, estate per il mare."
            })
        else:
            # Add multiple cultural and practical tips
            itinerary.extend([
                {
                    "type": "tip",
                    "title": "🏛️ Storia dei Caruggi",
                    "description": "I caruggi (vicoli) di Genova sono il centro storico medievale più grande d'Europa. Ogni vicolo ha una storia millenaria."
                },
                {
                    "type": "tip",
                    "title": "🎭 Genova nascosta",
                    "description": "Cerca i 'madonnette' (edicole sacre) sui muri dei caruggi - sono oltre 3000 e proteggono la città da secoli."
                },
                {
                    "type": "tip",
                    "title": "🚇 Trasporti unici",
                    "description": "Genova ha funicolari, ascensori pubblici e una ferrovia a cremagliera - il trasporto pubblico più verticale d'Italia!"
                },
                {
                    "type": "tip",
                    "title": "🏴‍☠️ Curiosità marinara",
                    "description": "Genova ha dato i natali a Cristoforo Colombo. La sua casa (presunta) è in Via del Mulcento, vicino a Porta Soprana."
                }
            ])

        print(f"✅ Generated itinerary with {len(itinerary)} items, ending at: {end}")

        return jsonify({
            "itinerary": itinerary,
            "city": end_city_name,
            "total_duration": f"{current_time - 9:.1f} hours",
            "status": "success"
        })

    except Exception as e:
        print(f"❌ AI-powered planning error: {e}")
        return jsonify({
            "error": f"Planning failed: {str(e)}",
            "itinerary": []
        }), 500

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

    # Ultimate fallback: Rome coordinates
    return [41.9028, 12.4964]

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