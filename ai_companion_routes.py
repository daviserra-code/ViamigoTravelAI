#!/usr/bin/env python3
"""
🧠 AI COMPANION ROUTES - Real AI-powered travel intelligence
Genuine AI for Piano B, Scoperte Intelligenti, Diario di Viaggio
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
from api_error_handler import resilient_api_call, with_cache, cache_openai, cache_scrapingdog
from weather_intelligence import weather_intelligence
from crowd_prediction import crowd_predictor
from multi_language_support import multi_language
# RAG integration
from simple_rag_helper import get_city_context_prompt, get_hotel_context_prompt, rag_helper
import requests  # Import requests for making HTTP calls
# 🇮🇹 UNIVERSAL ITALIAN ROUTER!
from intelligent_italian_routing import italian_router

ai_companion_bp = Blueprint('ai_companion', __name__)

# Initialize OpenAI with fast timeout
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
openai_api_key = os.environ.get("OPENAI_API_KEY")  # Ensure this is available


class AICompanionEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.db_url = os.getenv('DATABASE_URL')

    def _query_attractions_from_db(self, city_name: str, city_key: str, limit: int = 6) -> List[Dict]:
        """
        🚀 DYNAMIC DATABASE QUERY - Query PostgreSQL for REAL attractions
        Queries both comprehensive_attractions and place_cache tables
        """
        import psycopg2
        import json as json_module

        attractions = []

        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Priority 1: Query place_cache (best curated data)
            print(f"📊 Querying place_cache for {city_name}...")
            cursor.execute("""
                SELECT place_name, city, place_data, cache_key
                FROM place_cache
                WHERE LOWER(city) = LOWER(%s)
                ORDER BY priority_level DESC, access_count DESC
                LIMIT %s
            """, (city_name, limit))

            place_cache_results = cursor.fetchall()

            for row in place_cache_results:
                place_name, city, place_data_json, cache_key = row
                place_data = json_module.loads(
                    place_data_json) if place_data_json else {}

                lat = place_data.get('lat') or place_data.get('latitude')
                lng = place_data.get('lon') or place_data.get(
                    'lng') or place_data.get('longitude')

                print(
                    f"🔍 DEBUG place_cache: {place_name} - lat:{lat}, lng:{lng}, keys:{list(place_data.keys())[:5]}")

                attractions.append({
                    'name': place_data.get('name', place_name),
                    'latitude': lat,
                    'longitude': lng,
                    'description': place_data.get('description', f'{place_name} a {city_name}'),
                    'image_url': place_data.get('image_url'),
                    'source': 'PostgreSQL place_cache'
                })

            # Priority 2: If insufficient data, query comprehensive_attractions
            if len(attractions) < limit:
                print(
                    f"📊 Querying comprehensive_attractions for {city_name}...")
                cursor.execute("""
                    SELECT name, city, category, description, latitude, longitude, image_url
                    FROM comprehensive_attractions
                    WHERE LOWER(city) = LOWER(%s)
                      AND latitude IS NOT NULL
                      AND longitude IS NOT NULL
                    ORDER BY CASE 
                        WHEN image_url IS NOT NULL THEN 1 
                        ELSE 2 
                    END,
                    RANDOM()
                    LIMIT %s
                """, (city_name, limit - len(attractions)))

                db_results = cursor.fetchall()

                for row in db_results:
                    name, city, category, description, lat, lng, image_url = row
                    attractions.append({
                        'name': name,
                        'latitude': lat,
                        'longitude': lng,
                        'description': description or f'{name} a {city_name}',
                        'image_url': image_url,
                        'source': 'PostgreSQL comprehensive_attractions'
                    })

            cursor.close()
            conn.close()

            print(
                f"✅ Found {len(attractions)} attractions from database for {city_name}")
            return attractions

        except Exception as e:
            print(f"❌ Database query error for {city_name}: {e}")
            return []

    def _query_restaurants_from_db(self, city_name: str, city_key: str, limit: int = 3) -> List[Dict]:
        """
        🚀 DYNAMIC DATABASE QUERY - Query PostgreSQL for REAL restaurants
        Queries both comprehensive_attractions and place_cache tables
        """
        import psycopg2
        import json as json_module

        restaurants = []

        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # Priority 1: Query place_cache for restaurants
            print(f"📊 Querying place_cache for restaurants in {city_name}...")
            cursor.execute("""
                SELECT place_name, city, place_data, cache_key
                FROM place_cache
                WHERE LOWER(city) = LOWER(%s)
                  AND (place_data::jsonb->>'type' = 'restaurant' 
                       OR cache_key LIKE '%restaurant%')
                ORDER BY priority_level DESC, access_count DESC
                LIMIT %s
            """, (city_name, limit))

            place_cache_results = cursor.fetchall()

            for row in place_cache_results:
                place_name, city, place_data_json, cache_key = row
                place_data = json_module.loads(
                    place_data_json) if place_data_json else {}

                restaurants.append({
                    'name': place_data.get('name', place_name),
                    'latitude': place_data.get('lat') or place_data.get('latitude'),
                    'longitude': place_data.get('lon') or place_data.get('lng') or place_data.get('longitude'),
                    'description': place_data.get('description', f'Ristorante a {city_name}'),
                    'image_url': place_data.get('image_url'),
                    'source': 'PostgreSQL place_cache'
                })

            # Priority 2: If insufficient, query comprehensive_attractions for food places
            if len(restaurants) < limit:
                print(
                    f"📊 Querying comprehensive_attractions for restaurants in {city_name}...")
                cursor.execute("""
                    SELECT name, city, category, description, latitude, longitude, image_url
                    FROM comprehensive_attractions
                    WHERE LOWER(city) = LOWER(%s)
                      AND (category ILIKE '%restaurant%' OR category ILIKE '%food%' OR category ILIKE '%cafe%')
                      AND latitude IS NOT NULL
                      AND longitude IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (city_name, limit - len(restaurants)))

                db_results = cursor.fetchall()

                for row in db_results:
                    name, city, category, description, lat, lng, image_url = row
                    restaurants.append({
                        'name': name,
                        'latitude': lat,
                        'longitude': lng,
                        'description': description or f'Ristorante a {city_name}',
                        'image_url': image_url,
                        'source': 'PostgreSQL comprehensive_attractions'
                    })

            cursor.close()
            conn.close()

            print(
                f"✅ Found {len(restaurants)} restaurants from database for {city_name}")
            return restaurants

        except Exception as e:
            print(f"❌ Database query error for {city_name}: {e}")
            return []

    def generate_piano_b(self, current_itinerary, context, emergency_type="weather"):
        """Real AI Piano B generation with fast timeout"""
        try:
            # Extract city from context to avoid hallucination
            city_name = None
            context_lower = context.lower() if context else ""

            # Check context first
            if 'milano' in context_lower or 'milan' in context_lower or 'duomo milano' in context_lower:
                city_name = "Milan"
            # Bergamo detection - CRITICAL: Add before Genoa!
            elif any(term in context_lower for term in ['bergamo', 'città alta', 'citta alta', 'venetian walls']):
                city_name = "Bergamo"
            # Torino detection - PRIORITIZE before Roma to avoid "via roma" confusion
            elif any(term in context_lower for term in ['torino', 'turin', 'mole antonelliana',
                                                        '_torino', ',torino']):
                city_name = "Torino"
            # Roma detection - check for city context, not just substring
            elif (('roma,' in context_lower or ',roma' in context_lower or
                   'rome' in context_lower or 'colosseo' in context_lower or
                   'vaticano' in context_lower) and
                  'torino' not in context_lower and 'milano' not in context_lower):
                city_name = "Rome"
            elif 'london' in context_lower or 'piccadilly' in context_lower or 'westminster' in context_lower:
                city_name = "London"
            elif 'paris' in context_lower or 'eiffel' in context_lower:
                city_name = "Paris"
            elif 'venezia' in context_lower or 'venice' in context_lower:
                city_name = "Venice"
            elif 'genova' in context_lower or 'genoa' in context_lower:
                city_name = "Genova"

            # Then check itinerary
            if not city_name and current_itinerary and len(current_itinerary) > 0:
                first_stop = current_itinerary[0].get('title', '').lower()
                if any(term in first_stop for term in ['milano', 'milan', 'duomo']):
                    city_name = "Milan"
                elif any(term in first_stop for term in ['bergamo', 'città alta', 'citta alta']):
                    city_name = "Bergamo"
                elif any(term in first_stop for term in ['torino', 'turin', 'mole antonelliana']):
                    city_name = "Torino"
                elif any(term in first_stop for term in ['london', 'piccadilly', 'westminster']):
                    city_name = "London"
                elif any(term in first_stop for term in ['paris', 'eiffel']):
                    city_name = "Paris"
                # Roma - avoid "via roma" substring match
                elif (any(term in first_stop for term in ['colosseo', 'vaticano', 'fontana di trevi']) or
                      ('roma,' in first_stop or ',roma' in first_stop or 'rome' in first_stop)):
                    city_name = "Rome"
                elif any(term in first_stop for term in ['genova', 'genoa', 'piazza de ferrari']):
                    city_name = "Genova"
                elif any(term in first_stop for term in ['venezia', 'venice', 'rialto']):
                    city_name = "Venice"

            # If still no city, refuse to hallucinate
            if not city_name:
                print(f"⚠️ NO CITY DETECTED - refusing to hallucinate")
                return {
                    "emergency_type": emergency_type,
                    "ai_analysis": "Unable to determine city - please specify location",
                    "dynamic_alternatives": [],
                    "smart_adaptations": ["Specify the city for better recommendations"],
                    "cost_impact": "Unknown",
                    "ai_confidence": "error"
                }

            # 🧠 RAG INTEGRATION: Get real place data from PostgreSQL cache
            real_context = get_city_context_prompt(
                city_name, ["restaurant", "tourist_attraction", "cafe", "museum"])

            # 🏨 PATH C: Add hotel context with rich reviews
            hotel_context = get_hotel_context_prompt(
                city_name, min_score=8.0, limit=3)

            # 🎯 EXTRACT CURRENT STOPS to exclude from alternatives
            current_stop_names = []
            if current_itinerary and len(current_itinerary) > 0:
                for stop in current_itinerary:
                    # Extract stop name from different possible fields
                    stop_name = stop.get('title') or stop.get(
                        'name') or stop.get('place', '')
                    if stop_name:
                        current_stop_names.append(stop_name.strip())

            stops_to_exclude = ', '.join(
                current_stop_names) if current_stop_names else "nessuna"

            print(f"🧠 RAG: Injected {city_name} context into Piano B prompt")
            print(f"🏨 PATH C: Added hotel reviews for {city_name}")
            print(f"🚫 EXCLUDING current stops: {stops_to_exclude}")

            prompt = f"""
Sei un AI travel companion intelligente per {city_name}. Genera un Piano B dinamico per questo itinerario:

Città: {city_name}
Itinerario corrente: {json.dumps(current_itinerary[:3], indent=2)}
Contesto: {context}
Emergenza: {emergency_type}

🚫 CRITICO: L'itinerario corrente include già questi posti: {stops_to_exclude}

{real_context}

{hotel_context}

REGOLE CRITICHE:
1. Tutte le alternative devono essere SOLO E ESCLUSIVAMENTE per {city_name}.
2. NON suggerire MAI questi posti già nell'itinerario: {stops_to_exclude}
3. NON menzionare MAI attrazioni di altre città.
4. Suggerisci ALTERNATIVE DIVERSE dai posti già visitati.
5. Sii specifico: indica nomi esatti di luoghi a {city_name}.

Verifica OGNI suggerimento:
- È davvero a {city_name}? ✓
- È DIVERSO da {stops_to_exclude}? ✓

Crea un JSON con alternative realistiche e intelligenti SOLO per {city_name}:
{{
    "emergency_type": "{emergency_type}",
    "ai_analysis": "Analisi intelligente della situazione",
    "dynamic_alternatives": [
        {{
            "time": "orario",
            "title": "Nome alternativa DIVERSA da quelle attuali",
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

Rispondi SOLO con JSON valido. Sii specifico per {city_name} e EVITA {stops_to_exclude}.
"""

            response = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion esperto che genera Piani B intelligenti e dinamici."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            print(
                f"✅ AI Piano B generato: {result.get('ai_confidence', 'unknown')} confidence")
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
            # Extract city from location to prevent cross-city hallucinations
            location_lower = location.lower() if location else ""
            city_name = None

            if any(term in location_lower for term in ['milano', 'milan', 'duomo', 'navigli']):
                city_name = "Milan"
            # Bergamo detection - CRITICAL: Add before Genoa!
            elif any(term in location_lower for term in ['bergamo', 'città alta', 'citta alta', 'venetian walls']):
                city_name = "Bergamo"
            # Torino detection - PRIORITIZE before Roma
            elif any(term in location_lower for term in ['torino', 'turin', 'mole antonelliana', '_torino', ',torino']):
                city_name = "Torino"
            # Roma detection - avoid "via roma" substring match
            elif (any(term in location_lower for term in ['colosseo', 'vaticano', 'fontana di trevi']) or
                  ('roma,' in location_lower or ',roma' in location_lower or 'rome' in location_lower)):
                city_name = "Rome"
            elif any(term in location_lower for term in ['london', 'piccadilly', 'westminster']):
                city_name = "London"
            elif any(term in location_lower for term in ['paris', 'eiffel', 'louvre']):
                city_name = "Paris"
            elif any(term in location_lower for term in ['venezia', 'venice', 'rialto', 'san marco']):
                city_name = "Venice"
            elif any(term in location_lower for term in ['genova', 'genoa', 'acquario', 'piazza de ferrari']):
                city_name = "Genova"

            if not city_name:
                print(f"⚠️ NO CITY IN LOCATION - refusing to hallucinate")
                return {
                    "ai_analysis": "Unable to determine city from location",
                    "contextual_discoveries": [],
                    "behavioral_learning": "Please specify city for personalized discoveries",
                    "adaptive_suggestions": ["Provide more specific location"],
                    "ai_confidence": "error"
                }

            profile_context = f"Profilo utente: {user_profile}" if user_profile else "Profilo generico"

            # 🧠 RAG INTEGRATION: Get real place data from PostgreSQL cache
            real_context = get_city_context_prompt(
                city_name, ["restaurant", "tourist_attraction", "cafe", "museum"])

            # 🏨 PATH C: Add hotel context with rich reviews
            hotel_context = get_hotel_context_prompt(
                city_name, min_score=8.0, limit=3)

            print(f"🧠 RAG: Injected {city_name} context into Scoperte prompt")
            print(f"🏨 PATH C: Added hotel reviews for {city_name}")

            prompt = f"""
Sei un AI travel companion che scopre gemme nascoste. Analizza questa situazione:

Località: {location}
Città: {city_name}
Momento: {time_context}
{profile_context}

{real_context}

{hotel_context}

REGOLA CRITICA: Tutte le scoperte devono essere SOLO E ESCLUSIVAMENTE a {city_name}.
NON suggerire MAI luoghi di altre città.
NON menzionare Genova se parliamo di Milano.
NON menzionare Milano se parliamo di Genova.
NON menzionare Roma se parliamo di altre città.

Verifica che OGNI scoperta sia davvero a {city_name} prima di includerla.

Genera scoperte intelligenti e contestuali PER {city_name}:
{{
    "ai_analysis": "Analisi intelligente del contesto attuale a {city_name}",
    "contextual_discoveries": [
        {{
            "title": "Nome scoperta a {city_name}",
            "description": "Descrizione dettagliata e autentica",
            "distance": "distanza precisa",
            "why_now": "Perché è perfetto PROPRIO ora",
            "local_secret": "Segreto che solo i locals di {city_name} sanno",
            "ai_insight": "Insight intelligente unico",
            "timing_perfect": "Spiegazione timing perfetto"
        }}
    ],
    "behavioral_learning": "Cosa l'AI ha imparato dalle preferenze dell'utente",
    "adaptive_suggestions": ["suggerimento adattivo 1", "suggerimento adattivo 2"],
    "ai_confidence": "high/medium/low"
}}

Sii specifico per {city_name}, intelligente e contextualmente rilevante. NO CROSS-CITY HALLUCINATIONS.
"""

            response = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion che scopre gemme nascoste con intelligenza contestuale."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            print(
                f"✅ AI Scoperte generate: {len(result.get('contextual_discoveries', []))} scoperte")
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
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Sei un AI travel companion che analizza comportamenti e genera insights personalizzati."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30
            )

            result = json.loads(response.choices[0].message.content)
            print(
                f"✅ AI Diario generato: {result.get('personalization_level', 'unknown')} personalizzazione")
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


@ai_companion_bp.route('/ai/piano_b', methods=['POST'])
@resilient_api_call('openai', timeout=60, fallback_data={
    'alternative_plans': [
        {
            'title': 'Piano Rilassante',
            'description': 'Itinerario con meno camminate e più comfort',
            'stops': ['Caffè panoramico', 'Museo con visita guidata', 'Ristorante tradizionale'],
            'estimated_time': '4 ore',
            'estimated_cost': '€50-70'
        }
    ]
})
def ai_piano_b():
    """Generate intelligent Plan B suggestions"""
    try:
        data = request.get_json()
        current_plan = data.get('current_plan', [])
        city = data.get('city', 'Milano')

        print(
            f"🧠 Generating Piano B for {city} with {len(current_plan)} current stops")

        prompt = f"""
        PIANO B INTELLIGENTE - {city}

        Piano attuale:
        {json.dumps(current_plan, indent=2)}

        Genera 3 alternative creative per questo itinerario:
        1. PIANO RILASSANTE: Meno camminate, più comfort
        2. PIANO AVVENTUROSO: Luoghi nascosti e esperienze uniche
        3. PIANO EXPRESS: Massima efficienza, highlights principali

        Per ogni piano includi:
        - Titolo piano
        - 3-4 tappe specifiche con orari
        - Perché è migliore del piano originale
        - Costo stimato
        - Tempo totale

        Rispondi in JSON valido con array "alternative_plans".
        """

        # Use OpenAI client directly (works within Flask context)
        response = openai_client.chat.completions.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=2000,
            temperature=0.8,
            timeout=60
        )

        # Extract and parse the response
        if response.choices:
            content = response.choices[0].message.content
            # The content is expected to be a JSON string
            return jsonify(json.loads(content))
        else:
            # Handle cases where the response structure is unexpected
            return jsonify({'error': 'Unexpected response structure from OpenAI'}), 500

    except requests.exceptions.Timeout:
        print("⚠️ OpenAI API call timed out.")
        # The resilient_api_call decorator will handle this and return fallback_data
        raise  # Re-raise to let the decorator catch it
    except requests.exceptions.RequestException as e:
        print(f"⚠️ OpenAI API request failed: {e}")
        # The resilient_api_call decorator will handle this
        raise
    except Exception as e:
        print(f"❌ An unexpected error occurred in ai_piano_b: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@ai_companion_bp.route('/ai/scoperte', methods=['POST'])
@resilient_api_call('openai', timeout=60, fallback_data={
    'discoveries': [
        {
            'type': 'Gemma Nascosta',
            'name': 'Cortile storico nascosto',
            'description': 'Un angolo segreto della città',
            'why_special': 'Raramente visitato dai turisti',
            'cost': 'Gratuito'
        }
    ]
})
def ai_scoperte():
    """Generate intelligent discoveries using ChromaDB + real database"""
    try:
        data = request.get_json()
        user_interests = data.get('interests', ['arte', 'cibo'])
        city = data.get('city', 'Milano')
        current_location = data.get('current_location', '')

        print(
            f"🔍 Generating discoveries for {city} based on interests: {user_interests}")

        # 🎯 GET REAL CONTEXT FROM CHROMADB
        real_context = ""
        try:
            city_context = get_city_context_prompt(city, limit=5)
            if city_context:
                real_context = f"\n\n🗺️ CONTESTO REALE {city.upper()} (da ChromaDB):\n{city_context}\n"
                print(f"✅ ChromaDB context loaded for {city}")
            else:
                print(f"⚠️ No ChromaDB context for {city}")
        except Exception as e:
            print(f"⚠️ ChromaDB query failed: {e}")

        # 🎯 GET REAL ATTRACTIONS FROM DATABASE
        real_attractions = []
        try:
            import psycopg2
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cur = conn.cursor()

            # Query for unique, interesting places
            cur.execute("""
                SELECT DISTINCT name, category, description
                FROM comprehensive_attractions
                WHERE LOWER(city) = LOWER(%s)
                  AND description IS NOT NULL
                  AND description != ''
                ORDER BY RANDOM()
                LIMIT 10
            """, (city,))

            results = cur.fetchall()
            for name, category, desc in results:
                real_attractions.append(f"- {name}: {desc[:100]}")

            conn.close()

            if real_attractions:
                real_context += f"\n\n🏛️ ATTRAZIONI REALI {city.upper()}:\n" + "\n".join(
                    real_attractions[:8])
                print(
                    f"✅ Found {len(real_attractions)} real attractions for {city}")
        except Exception as e:
            print(f"⚠️ Database query failed: {e}")

        prompt = f"""
        SCOPERTE INTELLIGENTI - {city}

        Interessi utente: {', '.join(user_interests)}
        Posizione attuale: {current_location}
        {real_context}

        🎯 REGOLE CRITICHE:
        1. USA SOLO luoghi REALI menzionati nel contesto sopra
        2. NON inventare nomi di posti - VERIFICA che esistano nel contesto
        3. Ogni scoperta deve essere UNICA e SPECIFICA per {city}
        4. Se il contesto menziona un posto, USA IL NOME ESATTO
        5. NON ripetere scoperte generiche

        Trova 5 scoperte autentiche:
        1. GEMMA NASCOSTA: Luogo poco turistico ma affascinante (USA NOME REALE dal contesto)
        2. ESPERIENZA LOCALE: Attività che fanno solo i locals (SPECIFICA per {city})
        3. CURIOSITÀ STORICA: Fatto interessante VERIFICABILE (dal contesto ChromaDB)
        4. FOTO PERFETTA: Spot Instagram poco conosciuto (NOME REALE)
        5. ASSAGGIO AUTENTICO: Cibo/drink tipico di {city} (NON generico)

        Per ogni scoperta includi:
        - Nome ESATTO (dal contesto reale)
        - Descrizione (max 100 caratteri)
        - Perché è speciale
        - Come raggiungerla
        - Costo/gratuito
        - Orario migliore

        VERIFICA: Ogni nome deve apparire nel contesto reale sopra!
        
        Rispondi in JSON valido con array "discoveries".
        """

        # Use OpenAI client directly (Flask context safe)
        response = openai_client.chat.completions.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1500,
            temperature=0.9,
            timeout=60
        )

        if response.choices:
            content = response.choices[0].message.content
            return jsonify(json.loads(content))
        else:
            return jsonify({'error': 'Unexpected response structure from OpenAI'}), 500

    except requests.exceptions.Timeout:
        print("⚠️ OpenAI API call timed out.")
        raise
    except requests.exceptions.RequestException as e:
        print(f"⚠️ OpenAI API request failed: {e}")
        raise
    except Exception as e:
        print(f"❌ An unexpected error occurred in ai_scoperte: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500


@ai_companion_bp.route('/ai_piano_b', methods=['POST'])
def ai_piano_b_deprecated():
    """Generate real AI Piano B (deprecated, use /ai/piano_b)"""
    # This route is kept for backward compatibility but should ideally be removed or updated
    # to redirect to the new endpoint. For now, it just calls the new endpoint.
    return ai_piano_b()


@ai_companion_bp.route('/ai_scoperte', methods=['POST'])
def ai_scoperte_deprecated():
    """Generate real AI intelligent discoveries (deprecated, use /ai/scoperte)"""
    # This route is kept for backward compatibility but should ideally be removed or updated
    # to redirect to the new endpoint. For now, it just calls the new endpoint.
    return ai_scoperte()


@ai_companion_bp.route('/ai_diario', methods=['POST'])
def ai_diario():
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
        'bergamo': [45.6983, 9.6773],
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

            response = requests.get(url, params=params, timeout=3, headers={
                                    'User-Agent': 'Viamigo/1.0'})
            if response.ok and response.json():
                data = response.json()[0]
                coords = [float(data['lat']), float(data['lon'])]
                print(
                    f"🗺️ Found coordinates for {city_name} in {country}: {coords}")
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
            model="gpt-4-turbo",
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
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a travel expert who knows authentic local attractions."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        attractions_data = json.loads(response.choices[0].message.content)

        # Handle different response formats from OpenAI
        if isinstance(attractions_data, dict):
            if 'attractions' in attractions_data:
                attractions_list = attractions_data['attractions']
            elif 'places' in attractions_data:
                attractions_list = attractions_data['places']
            else:
                # Single attraction in dict format
                attractions_list = [attractions_data]
        elif isinstance(attractions_data, list):
            attractions_list = attractions_data
        else:
            print(
                f"⚠️ Unexpected AI response format: {type(attractions_data)}")
            attractions_list = []

        # Convert to our format
        dynamic_attractions = []
        for i, attr in enumerate(attractions_list[:4]):
            if isinstance(attr, dict):
                # Safely extract coordinates with fallbacks
                lat = attr.get('latitude', attr.get(
                    'lat', coords[0] + (i * 0.01)))
                lng = attr.get('longitude', attr.get(
                    'lng', coords[1] + (i * 0.01)))

                try:
                    lat = float(lat)
                    lng = float(lng)
                except (ValueError, TypeError):
                    lat = coords[0] + (i * 0.01)
                    lng = coords[1] + (i * 0.01)

                dynamic_attractions.append({
                    'name': attr.get('name', f'Attrazione {city_name} {i+1}'),
                    'coords': [lat, lng],
                    'duration': attr.get('duration', 1.5),
                    'description': attr.get('description', f'Attrazione autentica di {city_name}')
                })
            else:
                print(f"⚠️ Skipping invalid attraction data: {attr}")

        print(
            f"✅ AI generated {len(dynamic_attractions)} attractions for {city_name}")
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

        # 🇮🇹 ITALIAN CITIES: Use intelligent database-driven router for ALL Italian cities
        italian_cities = {
            'milano': 'Milano', 'milan': 'Milano',
            'roma': 'Roma', 'rome': 'Roma',
            'torino': 'Torino', 'turin': 'Torino',
            'venezia': 'Venezia', 'venice': 'Venezia',
            'firenze': 'Firenze', 'florence': 'Firenze',
            'napoli': 'Napoli', 'naples': 'Napoli',
            'bologna': 'Bologna',
            'genova': 'Genova', 'genoa': 'Genova',
            'palermo': 'Palermo',
            'catania': 'Catania',
            'bari': 'Bari',
            'verona': 'Verona',
            'padova': 'Padova', 'padua': 'Padova',
            'trieste': 'Trieste',
        }

        # Detect Italian city
        combined_text = (start + ' ' + end).lower()
        detected_city = None
        for key, city_name in italian_cities.items():
            if key in combined_text:
                detected_city = city_name
                break

        if detected_city:
            print(
                f"✅ Detected ITALIAN CITY: {detected_city} - using IntelligentItalianRouter")
            itinerary = italian_router.generate_intelligent_itinerary(
                start=start,
                end=end,
                city_name=detected_city,
                interests=interests,
                duration="full_day" if pace == "Lento" else "half_day"
            )
            return jsonify({
                "itinerary": itinerary,
                "city": detected_city,
                "total_duration": f"{len(itinerary) * 1.5:.1f} hours",
                "status": "success",
                "router": "intelligent_italian"
            })

        # Detect city from input with proper geographical mapping
        def detect_city_from_input(location_text):
            city_mappings = {
                # Lombardia
                'milano': ('milano', 'Milano'),
                'milan': ('milano', 'Milano'),
                'duomo milano': ('milano', 'Milano'),
                'buenos aires': ('milano', 'Milano'),
                'bergamo': ('bergamo', 'Bergamo'),
                'città alta': ('bergamo', 'Bergamo'),
                'citta alta': ('bergamo', 'Bergamo'),
                # Piemonte
                'torino': ('torino', 'Torino'),
                'turin': ('torino', 'Torino'),
                'mole antonelliana': ('torino', 'Torino'),
                # Liguria
                'genova': ('genova', 'Genova'),
                'genoa': ('genova', 'Genova'),
                'portofino': ('portofino', 'Portofino'),
                'cinque terre': ('cinqueterre', 'Cinque Terre'),
                # Lazio - MUST check for context to avoid "via roma" match
                'colosseo': ('roma', 'Roma'),
                'colosseum': ('roma', 'Roma'),
                'vaticano': ('roma', 'Roma'),
                'fontana di trevi': ('roma', 'Roma'),
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

            # PRIORITY 1: Check for explicit city suffix (e.g., ",torino" or "_torino")
            # NOTE: Exclude 'roma' here because it matches "via roma" street names
            import re
            city_suffix_match = re.search(
                r'[,_\s](torino|milano|bergamo|genova|portofino|cinqueterre|venezia|firenze|napoli|palermo|catania|taormina|siracusa|olbia|portorotondo|portocervo|costasmeralda|santeodoro|golfoaranci|london)\b', location_lower)
            if city_suffix_match:
                city_found = city_suffix_match.group(1)
                city_mappings_reverse = {
                    'torino': ('torino', 'Torino'),
                    'milano': ('milano', 'Milano'),
                    'bergamo': ('bergamo', 'Bergamo'),
                    'genova': ('genova', 'Genova'),
                    'portofino': ('portofino', 'Portofino'),
                    'cinqueterre': ('cinqueterre', 'Cinque Terre'),
                    'venezia': ('venezia', 'Venezia'),
                    'firenze': ('firenze', 'Firenze'),
                    'napoli': ('napoli', 'Napoli'),
                    'palermo': ('palermo', 'Palermo'),
                    'catania': ('catania', 'Catania'),
                    'taormina': ('taormina', 'Taormina'),
                    'siracusa': ('siracusa', 'Siracusa'),
                    'olbia': ('olbia', 'Olbia'),
                    'portorotondo': ('portorotondo', 'Porto Rotondo'),
                    'portocervo': ('portocervo', 'Porto Cervo'),
                    'costasmeralda': ('costasmeralda', 'Costa Smeralda'),
                    'santeodoro': ('santeodoro', 'San Teodoro'),
                    'golfoaranci': ('golfoaranci', 'Golfo Aranci'),
                    'london': ('london', 'London')
                }
                if city_found in city_mappings_reverse:
                    return city_mappings_reverse[city_found]

            # PRIORITY 1.5: Special check for Roma with strict comma/underscore boundary
            # Only match if ",roma" or "_roma" (not "via roma" which would have space)
            roma_match = re.search(r'[,_](roma|rome)\b', location_lower)
            if roma_match:
                return ('roma', 'Roma')

            # PRIORITY 2: Check landmark patterns (but not "roma" alone to avoid "via roma")
            for city_name, (city_key, city_display) in city_mappings.items():
                if city_name in location_lower:
                    # Skip generic "roma" or "rome" if we detect torino/milano/etc context
                    if city_name in ['roma', 'rome']:
                        if any(ctx in location_lower for ctx in ['torino', 'milano', 'genova', 'via roma']):
                            continue  # Skip Roma detection if other city context present
                    return city_key, city_display

            # Dynamic city extraction from comma-separated format
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

        # Initialize data sources
        postgres_attractions = []
        postgres_restaurants = []
        attractions = []
        restaurants = []

        # 🌍 FOREIGN DESTINATION CHECK - FORCE APIFY
        foreign_patterns = [
            'london', 'england', 'uk', 'britain', 'big ben', 'tower bridge',
            'paris', 'france', 'berlin', 'germany', 'madrid', 'spain',
            'new york', 'usa', 'america', 'manhattan', 'brooklyn'
        ]

        is_foreign = any(pattern in start.lower() or pattern in end.lower()
                         for pattern in foreign_patterns)

        combined_text_for_foreign_check = start.lower() + " " + end.lower()
        is_foreign = any(
            pattern in combined_text_for_foreign_check for pattern in foreign_patterns)

        if is_foreign:
            print(
                f"🌍 FOREIGN destination detected: {city_name} - FORCING Apify")

            # FORCE Apify for foreign destinations - don't check PostgreSQL first
            from apify_integration import apify_travel
            if apify_travel.is_available():
                print(f"🌍 FORCING Apify usage for {city_name}")
                try:
                    apify_attractions = apify_travel.get_authentic_places(
                        city_name, ['tourist_attraction'])
                    apify_restaurants = apify_travel.get_authentic_places(city_name, [
                                                                          'restaurant'])

                    if apify_attractions and 'tourist_attraction' in apify_attractions and apify_attractions['tourist_attraction']:
                        print(
                            f"✅ Apify returned {len(apify_attractions['tourist_attraction'])} attractions for {city_name}")
                        attractions = apify_attractions['tourist_attraction'][:4]

                    if apify_restaurants and 'restaurant' in apify_restaurants and apify_restaurants['restaurant']:
                        print(
                            f"✅ Apify returned {len(apify_restaurants['restaurant'])} restaurants for {city_name}")
                        restaurants = apify_restaurants['restaurant'][:2]

                    if attractions and restaurants:
                        print(f"🌍 SUCCESS: Using Apify data for {city_name}")
                        # Skip PostgreSQL entirely for foreign destinations
                        postgres_attractions = []
                        postgres_restaurants = []
                    else:
                        print(
                            f"⚠️ Apify returned insufficient data for {city_name}")

                except Exception as e:
                    print(f"❌ Apify error for {city_name}: {e}")
            else:
                print(f"❌ Apify not available for {city_name}")

            # Only check PostgreSQL if Apify completely failed
            if not attractions or not restaurants:
                print(
                    f"⚠️ Apify insufficient for {city_name}, checking PostgreSQL as fallback...")
                # Fallback to PostgreSQL check
                try:
                    # Get all places for this city and filter by type in Python
                    all_city_places = PlaceCache.query.filter(
                        PlaceCache.city.ilike(f'%{city_name}%')
                    ).all()

                    # Filter attractions
                    for cache_entry in all_city_places:
                        place_data = cache_entry.get_place_data()
                        if place_data and place_data.get('type') == 'attraction':
                            postgres_attractions.append({
                                'name': place_data.get('name', cache_entry.place_name),
                                'latitude': place_data.get('latitude', 45.4642),
                                'longitude': place_data.get('longitude', 9.1900),
                                'description': place_data.get('description', f'Historic attraction in {city_name}'),
                                'source': 'PostgreSQL Database'
                            })
                            if len(postgres_attractions) >= 4:
                                break

                    print(
                        f"🏛️ Found {len(postgres_attractions)} attractions in PostgreSQL")

                    # Filter restaurants
                    for cache_entry in all_city_places:
                        place_data = cache_entry.get_place_data()
                        if place_data and place_data.get('type') == 'restaurant':
                            postgres_restaurants.append({
                                'name': place_data.get('name', cache_entry.place_name),
                                'latitude': place_data.get('latitude', 45.4642),
                                'longitude': place_data.get('longitude', 9.1900),
                                'description': place_data.get('description', f'Restaurant in {city_name}'),
                                'source': 'PostgreSQL Database'
                            })
                            if len(postgres_restaurants) >= 2:
                                break

                    print(
                        f"🏛️ Found {len(postgres_restaurants)} restaurants in PostgreSQL")

                except Exception as e:
                    print(f"⚠️ PostgreSQL query error: {e}")

                # Combine PostgreSQL data if Apify failed
                attractions.extend(postgres_attractions)
                restaurants.extend(postgres_restaurants)

            if not attractions or not restaurants:
                print(
                    f"⚠️ Insufficient data from Apify and PostgreSQL for {city_name}. Using AI generation as last resort.")
                dynamic_attractions_ai = generate_ai_attractions_for_city(
                    city_name, city_key)
                # Use AI generated as fallback
                attractions.extend(dynamic_attractions_ai)
                # No restaurants from AI in this fallback scenario

        else:  # Not a foreign destination, proceed with standard logic
            print(
                f"🏛️ Domestic destination: {city_name}. Querying PostgreSQL database...")

            # 🚀 DYNAMIC DATABASE QUERY - NO HARDCODED DATA!
            # Query comprehensive_attractions table for REAL data
            postgres_attractions = ai_engine._query_attractions_from_db(
                city_name, city_key)

            if postgres_attractions:
                print(
                    f"✅ Found {len(postgres_attractions)} attractions from database for {city_name}")
            else:
                print(f"⚠️ No attractions found in database for {city_name}")

            # Query restaurants from database too
            postgres_restaurants = ai_engine._query_restaurants_from_db(
                city_name, city_key)

            if postgres_restaurants:
                print(
                    f"✅ Found {len(postgres_restaurants)} restaurants from database for {city_name}")
            else:
                print(f"⚠️ No restaurants found in database for {city_name}")

            # If insufficient data from database, use cost-effective scraping
            real_attractions = postgres_attractions
            real_restaurants = postgres_restaurants

            if len(real_attractions) < 2:
                print(
                    f"🔍 PostgreSQL insufficient, using cost-effective scraping for {city_name}")
                scraping_provider = CostEffectiveDataProvider()
                scraped_attractions = scraping_provider.get_places_data(
                    city_name, "tourist_attraction")
                scraped_restaurants = scraping_provider.get_places_data(
                    city_name, "restaurant")

                # Combine PostgreSQL + scraped data
                real_attractions.extend(scraped_attractions)
                real_restaurants.extend(scraped_restaurants)

                # ⚡ PERFORMANCE: Apify fallback DISABLED for speed
                # Apify takes 60-70s per call = terrible UX
                # Instead: Use fast OSM/Geoapify data immediately
                # If quality is poor, user can retry and cache will warm up
                # Alternative: Trigger Apify in background thread (future enhancement)

                # OLD SLOW CODE (commented out):
                # if len(real_attractions) < 3:
                #     apify_attractions = apify_travel.get_authentic_places(city_name, ['tourist_attraction'])
                #     # This blocks for 60-70 seconds! ❌

                # NEW FAST APPROACH: Accept OSM data for instant response
                print(
                    f"⚡ Using fast scraped data for {city_name} ({len(real_attractions)} attractions, {len(real_restaurants)} restaurants)")
            else:
                print(f"✅ Using PostgreSQL data for {city_name}")

            attractions.extend(real_attractions[:4])
            restaurants.extend(real_restaurants[:2])

        # Build dynamic attractions list for the CORRECT city
        dynamic_attractions = []

        if attractions:
            for attraction in attractions:
                # Handle both dict and list formats safely
                if isinstance(attraction, dict):
                    name = attraction.get('name', 'Unknown Attraction')
                    lat = attraction.get('latitude', 0)
                    lng = attraction.get('longitude', 0)
                    duration = attraction.get('duration', 1.5)
                    description = attraction.get(
                        'description', f'Attraction in {city_name}')

                    # Ensure coordinates are valid numbers
                    try:
                        lat = float(lat) if lat is not None else 0
                        lng = float(lng) if lng is not None else 0
                    except (ValueError, TypeError):
                        lat = lng = 0

                    dynamic_attractions.append({
                        'name': name,
                        'coords': [lat, lng],
                        'duration': duration,
                        'description': description
                    })
                else:
                    print(
                        f"⚠️ Skipping invalid attraction format: {attraction}")
            print(
                f"✅ Using {len(dynamic_attractions)} DYNAMIC attractions for {city_name}")
        else:
            print(
                f"⚠️ No attractions found/generated for {city_name}, using AI generation as a last resort.")
            # Use AI to generate authentic attractions for any city
            dynamic_attractions = generate_ai_attractions_for_city(
                city_name, city_key)

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
        city_key_clean = city_name.lower().replace(' ', '_')
        for i, attraction in enumerate(dynamic_attractions[:4]):
            # Calculate travel time and method based on distance
            travel_duration = 0.33  # 20 minutes between attractions
            if i > 0:
                current_time += travel_duration
                attraction_name_walk = attraction['name'].lower().replace(
                    ' ', '_')
                itinerary.append({
                    "time": f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
                    "title": f"Verso {attraction['name']}",
                    "description": f"Breve passeggiata di 15-20 minuti attraverso {city_name}",
                    "type": "transport",
                    # NOW INCLUDES CITY!
                    "context": f"walk_to_{attraction_name_walk}_{city_key_clean}",
                    "coordinates": attraction['coords'],
                    "transport": "walking"
                })

            # Add main activity with FULL DETAILS
            activity_duration = attraction.get('duration', 1.5)
            start_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
            current_time += activity_duration
            end_time = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"

            # Generate dynamic details using attraction data
            details = generate_dynamic_attraction_details(
                attraction, city_name)

            # Use rich description from details
            description = details['description']

            # Generate context with city suffix to prevent cross-city hallucinations
            attraction_name_clean = attraction['name'].lower().replace(' ', '_').replace('di_', '').replace(
                'del_', '').replace('di', '').replace('del', '').replace('__', '_').strip('_')
            city_key_clean = city_name.lower().replace(' ', '_')
            context_with_city = f"{attraction_name_clean}_{city_key_clean}"

            itinerary.append({
                "time": f"{start_time} - {end_time}",
                "title": attraction['name'],
                "description": description,
                "type": "activity",
                "context": context_with_city,  # NOW INCLUDES CITY SUFFIX!
                "coordinates": attraction['coords'],
                "transport": "visit",
            })

            # 🚫 REMOVE AI DETAILS GENERATION TO PREVENT HALLUCINATION
            # Only add minimal details to prevent errors
            attraction['_rich_details'] = {
                'source': 'apify' if is_foreign else 'database',
                'city': city_name,
                'verified': True
            }
            print(f"✅ Minimal details added for {attraction['name']}")

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

        print(
            f"✅ Generated itinerary with {len(itinerary)} items for {city_name}")

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


# ============= NEW INTELLIGENT FEATURES =============

@ai_companion_bp.route('/weather_intelligence', methods=['POST'])
def get_weather_intelligence():
    """Get weather-aware intelligence for trip planning"""
    try:
        data = request.get_json()
        lat = data.get('latitude', 45.4642)  # Default Milan
        lon = data.get('longitude', 9.1900)
        language = data.get('language', 'it')

        # Get current weather
        weather = weather_intelligence.get_current_weather(lat, lon)

        # Analyze conditions
        severity, trigger_plan_b, reasons = weather_intelligence.analyze_weather_conditions(
            weather)

        # Get forecast
        forecast = weather_intelligence.get_forecast(lat, lon, hours=24)

        # Get weather-appropriate suggestions
        suggestions = weather_intelligence.suggest_weather_appropriate_activities(
            weather,
            data.get('activity_type', 'general')
        )

        # Translate if needed
        if language != 'en':
            weather['description'] = multi_language.translate(
                weather['description'], language, 'en')
            reasons = [multi_language.translate(
                r, language, 'en') for r in reasons]

            # Translate suggestions
            for key in suggestions:
                if isinstance(suggestions[key], list):
                    suggestions[key] = [multi_language.translate(
                        s, language, 'en') for s in suggestions[key]]

        response = {
            'current_weather': weather,
            'severity': severity,
            'trigger_plan_b': trigger_plan_b,
            'reasons': reasons,
            'forecast': forecast[:8],  # Next 24 hours
            'suggestions': suggestions,
            'timestamp': weather['timestamp']
        }

        # Auto-trigger Plan B if severe weather
        if trigger_plan_b:
            print(
                f"⚠️ Weather Alert: Auto-triggering Plan B due to {severity} weather")
            response['plan_b_auto_triggered'] = True
            response['plan_b_reason'] = f"Weather conditions: {', '.join(reasons)}"

        return jsonify(response)

    except Exception as e:
        print(f"❌ Weather intelligence error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_companion_bp.route('/crowd_prediction', methods=['POST'])
def predict_crowds():
    """Predict crowd levels for attractions"""
    try:
        data = request.get_json()
        places = data.get('places', [])
        language = data.get('language', 'it')
        optimize_itinerary = data.get('optimize', False)

        predictions = []

        for place in places:
            # Predict crowd level
            prediction = crowd_predictor.predict_crowd_level(
                place.get('name', 'Unknown'),
                place.get('type', 'general'),
                None  # Current time by default
            )

            # Get AI insights if available
            if place.get('name') and place.get('city'):
                ai_insights = crowd_predictor.get_ai_crowd_insights(
                    place['name'],
                    place['city']
                )
                if ai_insights:
                    prediction['ai_insights'] = ai_insights

            # Translate if needed
            if language != 'en':
                prediction['description'] = multi_language.translate(
                    prediction['description'],
                    language,
                    'en'
                )
                prediction['recommendations'] = [
                    multi_language.translate(r, language, 'en')
                    for r in prediction['recommendations']
                ]

            predictions.append(prediction)

        response = {
            'predictions': predictions,
            'overall_recommendation': None
        }

        # Optimize itinerary if requested
        if optimize_itinerary and len(places) > 1:
            from datetime import datetime
            optimized = crowd_predictor.generate_crowd_aware_itinerary(
                places,
                datetime.now()
            )
            response['optimized_itinerary'] = optimized
            response['overall_recommendation'] = "Itinerary optimized to avoid crowds"

            if language != 'it':
                response['overall_recommendation'] = multi_language.translate(
                    response['overall_recommendation'],
                    language,
                    'it'
                )

        return jsonify(response)

    except Exception as e:
        print(f"❌ Crowd prediction error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_companion_bp.route('/translate', methods=['POST'])
def translate_content():
    """Translate content to user's preferred language"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        target_language = data.get('target_language', 'en')
        source_language = data.get('source_language', None)
        content_type = data.get('content_type', 'text')  # text, itinerary, ui

        # Auto-detect source language if not provided
        if not source_language:
            source_language = multi_language.detect_language(content)

        result = {}

        if content_type == 'text':
            # Simple text translation
            result['translated'] = multi_language.translate(
                content,
                target_language,
                source_language
            )

        elif content_type == 'itinerary':
            # Translate full itinerary
            result['translated'] = multi_language.translate_itinerary(
                content,  # Should be a list of itinerary items
                target_language
            )

        elif content_type == 'ui':
            # Get UI strings in target language
            result['ui_strings'] = multi_language.localize_ui(target_language)
            result['tips'] = multi_language.get_language_specific_tips(
                data.get('city', 'general'),
                target_language
            )

        result['source_language'] = source_language
        result['target_language'] = target_language
        result['language_info'] = multi_language.supported_languages.get(
            target_language)

        return jsonify(result)

    except Exception as e:
        print(f"❌ Translation error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_companion_bp.route('/intelligent_planning', methods=['POST'])
def intelligent_trip_planning():
    """Combined intelligent planning with weather, crowds, and language support"""
    try:
        data = request.get_json()
        city = data.get('city', 'Milano')
        lat = data.get('latitude', 45.4642)
        lon = data.get('longitude', 9.1900)
        language = data.get('language', 'it')
        preferences = data.get('preferences', {})

        print(f"🧠 Intelligent planning for {city} in {language}")

        # Get weather intelligence
        weather = weather_intelligence.get_current_weather(lat, lon)
        weather_severity, trigger_plan_b, weather_reasons = weather_intelligence.analyze_weather_conditions(
            weather)

        # Get basic itinerary (reuse existing logic)
        # This would normally call your existing itinerary generation

        response = {
            'city': city,
            'language': language,
            'intelligence': {
                'weather': {
                    'current': weather,
                    'severity': weather_severity,
                    'auto_plan_b': trigger_plan_b,
                    'reasons': weather_reasons
                },
                'crowd_optimization': True,
                'language_support': True
            },
            'recommendations': []
        }

        # Add weather-based recommendations
        if trigger_plan_b:
            response['recommendations'].append({
                'type': 'weather',
                'priority': 'high',
                'message': multi_language.translate(
                    f"Weather alert: {weather_severity}. Indoor activities recommended.",
                    language,
                    'en'
                ),
                'action': 'activate_plan_b'
            })

        # Add crowd recommendations
        from datetime import datetime
        hour = datetime.now().hour
        if hour in [11, 12, 14, 15, 16]:  # Peak hours
            response['recommendations'].append({
                'type': 'crowd',
                'priority': 'medium',
                'message': multi_language.translate(
                    "Peak hours detected. Consider visiting less popular attractions first.",
                    language,
                    'en'
                ),
                'action': 'optimize_order'
            })

        # Add language-specific tips
        tips = multi_language.get_language_specific_tips(city, language)
        response['local_tips'] = tips

        return jsonify(response)

    except Exception as e:
        print(f"❌ Intelligent planning error: {e}")
        return jsonify({'error': str(e)}), 500
