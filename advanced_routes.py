from simple_rag_helper import rag_helper
from openai import OpenAI
from flask import Blueprint, request, jsonify, send_from_directory
import json
import time
import os
import dotenv
dotenv.load_dotenv()

advanced_bp = Blueprint('advanced', __name__)


@advanced_bp.route('/advanced-features')
def advanced_features_page():
    """Serve the advanced features HTML page"""
    return send_from_directory('static', 'advanced_features.html')


@advanced_bp.route('/api/get_city_attractions')
def get_city_attractions():
    """Get dynamic attractions for a city using RAG + PostgreSQL + ChromaDB"""
    try:
        city = request.args.get('city', 'Milano')
        location = request.args.get('location', '')

        print(f"🎯 API: Getting attractions for {city} (location: {location})")

        # Use RAG to get real place data from PostgreSQL
        city_context = rag_helper.get_city_context(
            city,
            categories=['tourist_attraction', 'museum', 'monument']
        )

        attractions = []

        # Convert PostgreSQL data to timeline format
        for category, data in city_context.get('categories', {}).items():
            places = data.get('places', [])

            for i, place in enumerate(places[:3]):  # Top 3 per category
                name = place.get('name', place.get(
                    'title', 'Attrazione locale'))

                # Generate contextual description using ChatGPT + RAG data
                description = generate_attraction_description(place, city)

                # Create timeline entry
                time_slots = [
                    '14:30 - 16:30 (2 ore)', '16:45 - 17:30 (45 min)', '17:30 - 18:30 (1 ora)']

                attractions.append({
                    'time': time_slots[min(len(attractions), 2)],
                    'title': name,
                    'description': description,
                    'category': category,
                    'source': 'rag_postgresql'
                })

                if len(attractions) >= 3:  # Limit to 3 attractions
                    break

            if len(attractions) >= 3:
                break

        # Fallback to default if no RAG data
        if not attractions:
            attractions = get_fallback_attractions(city)

        return jsonify({
            'success': True,
            'city': city,
            'attractions': attractions,
            'source': 'rag_postgresql' if city_context.get('total_places', 0) > 0 else 'fallback',
            'total_places_in_db': city_context.get('total_places', 0)
        })

    except Exception as e:
        print(f"❌ Error getting attractions for {city}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'attractions': get_fallback_attractions(city),
            'source': 'error_fallback'
        })


def generate_attraction_description(place_data: dict, city: str) -> str:
    """Generate contextual description using ChatGPT + real place data"""
    try:
        name = place_data.get('name', place_data.get('title', 'Attrazione'))

        # Extract real data from place_data
        description = place_data.get('description', '')
        category = place_data.get('category', place_data.get('type', ''))

        # Use ChatGPT for rich descriptions with real context
        prompt = f"""
        Crea una descrizione coinvolgente (max 80 caratteri) per questa attrazione di {city}:
        
        Nome: {name}
        Categoria: {category}
        Descrizione originale: {description}
        
        Deve essere informativa, coinvolgente e adatta per un itinerario turistico.
        Rispondi solo con la descrizione, senza virgolette o prefissi.
        """

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7
        )

        generated_description = response.choices[0].message.content.strip()
        return generated_description[:120]  # Ensure max length

    except Exception as e:
        # Fallback to original description
        return place_data.get('description', f'Attrazione storica di {city}.')[:120]


def get_fallback_attractions(city: str) -> list:
    """Fallback attractions when RAG data is not available"""
    fallback_data = {
        'bergamo': [
            {'time': '14:30 - 16:30 (2 ore)', 'title': 'Basilica di Santa Maria Maggiore',
             'description': 'Capolavoro romanico-gotico con incredibili intarsi lignei.'},
            {'time': '16:45 - 17:30 (45 min)', 'title': 'Cappella Colleoni',
             'description': 'Gioiello del Rinascimento progettato da Amadeo.'},
            {'time': '17:30 - 18:30 (1 ora)', 'title': 'Città Alta',
             'description': 'Passeggiata tra le mura veneziane patrimonio UNESCO.'}
        ],
        'milano': [
            {'time': '14:30 - 16:30 (2 ore)', 'title': 'Duomo di Milano',
             'description': 'Magnifica cattedrale gotica. Terrazza panoramica inclusa.'},
            {'time': '16:45 - 17:30 (45 min)', 'title': 'Galleria Vittorio Emanuele II',
             'description': 'Storica galleria commerciale del 1865, il salotto di Milano.'},
            {'time': '17:30 - 18:30 (1 ora)', 'title': 'Castello Sforzesco',
             'description': 'Fortezza storica con musei e giardini.'}
        ]
    }

    return fallback_data.get(city.lower(), [
        {'time': '14:30 - 16:30 (2 ore)', 'title': f'Centro storico di {city}',
         'description': f'Esplora il cuore di {city} con i suoi monumenti principali.'},
        {'time': '16:45 - 17:30 (45 min)', 'title': f'Musei di {city}',
         'description': f'Visita i principali musei e attrazioni culturali.'},
        {'time': '17:30 - 18:30 (1 ora)', 'title': f'Passeggiata a {city}',
         'description': f'Rilassante passeggiata per le vie caratteristiche.'}
    ])


# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# RAG integration for dynamic attractions


@advanced_bp.route('/piano_b', methods=['POST'])
def generate_piano_b():
    """Generate intelligent Plan B for current itinerary"""
    try:
        data = request.get_json()
        current_location = data.get('current_location', 'Unknown')
        disruption_type = data.get('disruption_type', 'weather')
        original_plan = data.get('original_plan', [])
        city = data.get('city', 'Milano')

        print(
            f"🚨 Generating Piano B for {disruption_type} at {current_location}")

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

        print(
            f"🔍 Generating smart discoveries for {current_location} at {time_of_day}")

        prompt = f"""
        POSIZIONE ATTUALE: {current_location}, {city}
        MOMENTO: {time_of_day}
        INTERESSI: {', '.join(user_interests)}

        Genera 3 scoperte intelligenti nelle immediate vicinanze in formato JSON:
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
        Rispondi SOLO con JSON valido, nessun altro testo.
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

        print(
            f"📖 Generating AI diary for {len(visited_places)} places in {city}")

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
        city = data.get('city', '')  # City context for local searches

        print(
            f"🗺️ Planning route: {start} to {end} via {transport_mode} in {city}")

        # 🌍 DESTINAZIONI ESTERE - Usa Apify per dati autentici
        foreign_destinations = {
            'usa washington d': {'country': 'USA', 'center': [38.9072, -77.0369]},
            'japan tokyo': {'country': 'Japan', 'center': [35.6762, 139.6503]},
            'germany berlin': {'country': 'Germany', 'center': [52.5200, 13.4050]},
            'england london': {'country': 'UK', 'center': [51.5074, -0.1278]},
            # Add direct London mapping
            'london': {'country': 'UK', 'center': [51.5074, -0.1278]},
            'france paris': {'country': 'France', 'center': [48.8566, 2.3522]},
            'spain madrid': {'country': 'Spain', 'center': [40.4168, -3.7038]}
        }

        # Mock function to simulate city detection
        def detect_city_advanced(start_loc, end_loc):
            print(
                f"Simulating city detection for: start='{start_loc}', end='{end_loc}'")
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
                # Fallback to provided city or default
                return city if city else 'milano centro'

        # 🔍 Auto-detect city for foreign destinations
        detected_city = detect_city_advanced(start, end)

        # 🇬🇧 SPECIAL: Force London detection
        if any('london' in loc.lower() for loc in [start, end]) or 'london' in detected_city.lower():
            detected_city = 'london'
            print(
                f"🇬🇧 FORCED London detection from: start='{start}', end='{end}'")

        # Map detected cities to foreign destinations
        if detected_city in foreign_destinations:
            destination_info = foreign_destinations[detected_city]
            country = destination_info['country']
            center_coords = destination_info['center']

            print(
                f"🌍 Detected foreign destination: {detected_city} ({country}). Using Apify simulation.")
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
            print(
                f"🏠 Detected local destination or city context: {city or detected_city}. Using local data.")
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
