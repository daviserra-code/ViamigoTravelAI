from flask import Blueprint, request, jsonify, send_from_directory
import json
import time
import os
from openai import OpenAI

advanced_bp = Blueprint('advanced', __name__)

@advanced_bp.route('/advanced-features')
def advanced_features_page():
    """Serve the advanced features HTML page"""
    return send_from_directory('static', 'advanced_features.html')

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@advanced_bp.route('/piano_b', methods=['POST'])
def generate_piano_b():
    """Generate intelligent Plan B for current itinerary"""
    try:
        data = request.get_json()
        current_location = data.get('current_location', 'Unknown')
        disruption_type = data.get('disruption_type', 'weather')
        original_plan = data.get('original_plan', [])
        city = data.get('city', 'Milano')

        print(f"🚨 Generating Piano B for {disruption_type} at {current_location}")

        prompt = f"""
        SITUAZIONE EMERGENZA: {disruption_type} a {current_location}, {city}

        Piano originale compromesso:
        {json.dumps(original_plan, indent=2)}

        Genera Piano B intelligente con alternative immediate:
        {{
            "emergency_type": "{disruption_type}",
            "current_location": "{current_location}",
            "immediate_actions": [
                {{
                    "action": "Azione immediata da fare ora",
                    "location": "Dove andare",
                    "time_needed": "5-10 minuti",
                    "why": "Perché questa soluzione funziona"
                }}
            ],
            "alternative_itinerary": [
                {{
                    "time": "Nuovo orario",
                    "title": "Attività alternativa",
                    "description": "Descrizione dettagliata",
                    "indoor": true,
                    "distance_from_current": "200m a piedi",
                    "accessibility": "Informazioni accessibilità"
                }}
            ],
            "cost_impact": "Variazione di costo",
            "real_time_tip": "Consiglio pratico immediato"
        }}

        Rispondi SOLO con JSON valido.
        """

        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Sei un travel expert che gestisce emergenze in tempo reale. Conosci alternative immediate per ogni tipo di disruzione."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=30,
            temperature=0.7
        )

        plan_b = json.loads(response.choices[0].message.content)

        print(f"✅ Piano B generato per {disruption_type}")
        return jsonify({
            "status": "success",
            "plan_b": plan_b,
            "generated_at": time.time()
        })

    except Exception as e:
        print(f"❌ Error generating Piano B: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "fallback_plan": {
                "immediate_actions": [
                    {
                        "action": "Cerca un caffè o centro commerciale nelle vicinanze",
                        "location": "Centro città",
                        "time_needed": "5-10 minuti",
                        "why": "Rifugio sicuro e coperto"
                    }
                ]
            }
        }), 500

@advanced_bp.route('/scoperte_intelligenti', methods=['POST'])
def smart_discoveries():
    """Generate contextualized discoveries based on current location and time"""
    try:
        data = request.get_json()
        current_location = data.get('current_location', 'Milano Centro')
        time_of_day = data.get('time_of_day', 'morning')
        user_interests = data.get('interests', ['culture', 'food'])
        city = data.get('city', 'Milano')

        print(f"🔍 Generating smart discoveries for {current_location} at {time_of_day}")

        prompt = f"""
        POSIZIONE ATTUALE: {current_location}, {city}
        MOMENTO: {time_of_day}
        INTERESSI: {', '.join(user_interests)}

        Genera 3 scoperte intelligenti nelle immediate vicinanze:
        {{
            "current_context": {{
                "location": "{current_location}",
                "optimal_time": "{time_of_day}",
                "weather_consideration": "Considera condizioni attuali"
            }},
            "discoveries": [
                {{
                    "title": "Nome scoperta specifica",
                    "category": "food|culture|shopping|nature|nightlife",
                    "description": "Cosa rende speciale questo posto ADESSO",
                    "distance": "Distanza esatta a piedi",
                    "why_now": "Perché è perfetto proprio in questo momento",
                    "local_secret": "Segreto che solo i locals sanno",
                    "opening_status": "Aperto ora | Apre alle XX:XX",
                    "quick_tip": "Tip pratico immediato",
                    "coordinates": [lat, lon]
                }}
            ],
            "contextual_alert": "Avviso importante per il momento attuale"
        }}

        Basa le scoperte su luoghi REALI e verificabili a {city}.
        """

        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": f"Sei un local expert di {city} che conosce ogni angolo della città e sa cosa è meglio fare in ogni momento della giornata."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=30,
            temperature=0.8
        )

        discoveries = json.loads(response.choices[0].message.content)

        print(f"✅ Smart discoveries generated for {current_location}")
        return jsonify({
            "status": "success",
            "discoveries": discoveries,
            "generated_at": time.time()
        })

    except Exception as e:
        print(f"❌ Error generating discoveries: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "fallback_discoveries": {
                "discoveries": [
                    {
                        "title": f"Esplora il centro di {city}",
                        "category": "culture",
                        "description": "Scopri l'architettura locale",
                        "distance": "Zona pedonale",
                        "why_now": "Sempre interessante",
                        "local_secret": "Osserva i dettagli architettonici"
                    }
                ]
            }
        }), 500

@advanced_bp.route('/diario_ai', methods=['POST'])
def ai_diary():
    """Generate personalized travel diary insights"""
    try:
        data = request.get_json()
        visited_places = data.get('visited_places', [])
        current_mood = data.get('mood', 'curious')
        travel_style = data.get('travel_style', 'explorer')
        city = data.get('city', 'Milano')

        print(f"📖 Generating AI diary for {len(visited_places)} places in {city}")

        prompt = f"""
        DIARIO DI VIAGGIO PERSONALE - {city}

        Luoghi visitati oggi:
        {json.dumps(visited_places, indent=2)}

        Stato d'animo: {current_mood}
        Stile di viaggio: {travel_style}

        Crea un diario di viaggio personalizzato:
        {{
            "diary_entry": {{
                "title": "Titolo poetico della giornata",
                "narrative": "Racconto fluido e personale dell'esperienza",
                "highlights": [
                    {{
                        "moment": "Momento specifico",
                        "emotion": "Emozione provata",
                        "detail": "Dettaglio che rimarrà nella memoria"
                    }}
                ],
                "personal_growth": "Cosa ho imparato oggi",
                "tomorrow_inspiration": "Cosa voglio esplorare domani",
                "hidden_gems_discovered": ["Scoperta inaspettata 1", "Scoperta 2"],
                "local_connections": "Interazioni con locals o culture locali",
                "sensory_memories": {{
                    "taste": "Sapore che ricorderò",
                    "sound": "Suono caratteristico",
                    "sight": "Immagine più bella",
                    "feeling": "Sensazione fisica del momento"
                }}
            }},
            "travel_wisdom": "Lezione di viaggio per il futuro",
            "gratitude_note": "Cosa apprezzo di più di oggi"
        }}

        Rendi il diario personale, emotivo e memorabile.
        """

        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": f"Sei un travel writer esperto che crea diari di viaggio personali e toccanti. Trasformi le esperienze in ricordi indimenticabili."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            timeout=30,
            temperature=0.9
        )

        diary = json.loads(response.choices[0].message.content)

        print(f"✅ AI diary generated for {city}")
        return jsonify({
            "status": "success",
            "diary": diary,
            "generated_at": time.time()
        })

    except Exception as e:
        print(f"❌ Error generating diary: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "fallback_diary": {
                "diary_entry": {
                    "title": f"Giornata di scoperte a {city}",
                    "narrative": f"Oggi ho esplorato {city} scoprendo luoghi interessanti e vivendo momenti unici.",
                    "highlights": [
                        {
                            "moment": "Passeggiata nel centro",
                            "emotion": "Curiosità",
                            "detail": "L'atmosfera autentica della città"
                        }
                    ]
                }
            }
        }), 500

@advanced_bp.route('/plan_route_advanced', methods=['POST'])
def plan_route_advanced():
    """
    Plans a route between two points, incorporating external APIs for foreign destinations
    and local data for domestic ones.
    """
    try:
        data = request.get_json()
        start = data.get('start', '')
        end = data.get('end', '')
        transport_mode = data.get('transport_mode', 'driving')
        city = data.get('city', '') # City context for local searches

        print(f"🗺️ Planning route: {start} to {end} via {transport_mode} in {city}")

        # 🌍 DESTINAZIONI ESTERE - Usa Apify per dati autentici
        foreign_destinations = {
            'usa washington d': {'country': 'USA', 'center': [38.9072, -77.0369]},
            'japan tokyo': {'country': 'Japan', 'center': [35.6762, 139.6503]},
            'germany berlin': {'country': 'Germany', 'center': [52.5200, 13.4050]},
            'england london': {'country': 'UK', 'center': [51.5074, -0.1278]},
            'london': {'country': 'UK', 'center': [51.5074, -0.1278]},  # Add direct London mapping
            'france paris': {'country': 'France', 'center': [48.8566, 2.3522]},
            'spain madrid': {'country': 'Spain', 'center': [40.4168, -3.7038]}
        }

        # Mock function to simulate city detection
        def detect_city_advanced(start_loc, end_loc):
            print(f"Simulating city detection for: start='{start_loc}', end='{end_loc}'")
            # In a real scenario, this would involve more sophisticated geocoding or API calls.
            # For this example, we'll make some basic assumptions.
            if 'london' in start_loc.lower() or 'london' in end_loc.lower():
                return 'london'
            elif 'paris' in start_loc.lower() or 'paris' in end_loc.lower():
                return 'france paris'
            elif 'madrid' in start_loc.lower() or 'madrid' in end_loc.lower():
                return 'spain madrid'
            elif 'berlin' in start_loc.lower() or 'berlin' in end_loc.lower():
                return 'germany berlin'
            elif 'tokyo' in start_loc.lower() or 'tokyo' in end_loc.lower():
                return 'japan tokyo'
            elif 'washington' in start_loc.lower() or 'washington' in end_loc.lower():
                return 'usa washington d'
            else:
                return city if city else 'milano centro' # Fallback to provided city or default

        # 🔍 Auto-detect city for foreign destinations
        detected_city = detect_city_advanced(start, end)

        # 🇬🇧 SPECIAL: Force London detection
        if any('london' in loc.lower() for loc in [start, end]) or 'london' in detected_city.lower():
            detected_city = 'london'
            print(f"🇬🇧 FORCED London detection from: start='{start}', end='{end}'")

        # Map detected cities to foreign destinations
        if detected_city in foreign_destinations:
            destination_info = foreign_destinations[detected_city]
            country = destination_info['country']
            center_coords = destination_info['center']

            print(f"🌍 Detected foreign destination: {detected_city} ({country}). Using Apify simulation.")
            # In a real application, you would call an Apify scraper here.
            # For now, we'll return mock data.
            return jsonify({
                "status": "success",
                "route_details": {
                    "type": "foreign",
                    "destination_country": country,
                    "message": f"Using Apify data for {detected_city}. Route planning will use its coordinates.",
                    "coordinates": center_coords,
                    "start_location": start,
                    "end_location": end,
                    "transport_mode": transport_mode,
                    "estimated_time": "1-2 hours (Simulated)"
                }
            })
        else:
            # Use local data or routing service for domestic destinations
            print(f"🏠 Detected local destination or city context: {city or detected_city}. Using local data.")
            # Here you would integrate with a local routing service or use local place data.
            # For example, if 'city' is 'Milano', you might query a local database for points of interest.
            return jsonify({
                "status": "success",
                "route_details": {
                    "type": "local",
                    "message": f"Route planning within {city or detected_city}. Using local data.",
                    "start_location": start,
                    "end_location": end,
                    "transport_mode": transport_mode,
                    "estimated_time": "30-60 minutes (Simulated)"
                }
            })

    except Exception as e:
        print(f"❌ Error planning route: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "fallback_route": {
                "message": "Could not plan route. Please try again or use manual navigation."
            }
        }), 500

print("🚀 Advanced Routes caricato - Piano B, Scoperte Intelligenti, Diario AI attivi!")