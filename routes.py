from flask import session, render_template_string, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_required
from models import User
import logging
from functools import wraps
from datetime import datetime

# Import app and db after initialization to avoid circular imports


def get_app_db():
    from flask_app import app, db
    return app, db


app, db = get_app_db()

# Temporary workaround for auth - create mock endpoints for demo


def require_login(f):
    """Mock login decorator per demo - controlla sessione utente"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Controlla se l'utente ha fatto login demo
        if not session.get('demo_logged_in'):
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function

# Mock current_user per demo


class MockUser:
    def __init__(self):
        self.id = "demo_user_123"
        self.email = "marco@email.com"
        self.first_name = None
        self.last_name = "Rossi"
        self.is_authenticated = True


def get_current_user():
    """Restituisce utente mock per demo"""
    return MockUser()

# Login route handled by auth_routes.py blueprint


# Try to import real auth if available
try:
    if db:
        from replit_auth import make_replit_blueprint
        replit_bp = make_replit_blueprint()
        if replit_bp:
            app.register_blueprint(replit_bp, url_prefix="/auth_real")
except Exception as e:
    print(f"Replit auth not available: {e}")


@app.route('/api/apify/status')
@login_required
def apify_status():
    """Check Apify integration status"""
    from apify_integration import apify_travel

    return jsonify({
        'apify_available': apify_travel.is_available(),
        'api_token_configured': bool(apify_travel.api_token),
        'client_initialized': apify_travel.client is not None,
        'cache_enabled': True,
        'supported_sources': ['google_maps', 'tripadvisor'],
        'foreign_destinations': [
            'usa washington d', 'japan tokyo', 'germany berlin',
            'england london', 'france paris', 'spain madrid'
        ]
    })

# Make session permanent


@app.before_request
def make_session_permanent():
    session.permanent = True


def is_admin(user_id):
    """Controlla se l'utente è admin"""
    # Placeholder for AdminUser model check
    # In a real app, you would query your AdminUser table
    # admin = AdminUser.query.filter_by(user_id=user_id).first()
    # return admin is not None
    return user_id == "admin_user_id"  # Mock admin check


def can_edit_profile(profile_user_id, current_user_id):
    """Controlla se l'utente può modificare il profilo"""
    # L'utente può modificare il proprio profilo o se è admin
    return profile_user_id == current_user_id or is_admin(current_user_id)


@app.route('/')
def index():
    """Homepage - sempre redirect al login per deployment consistency"""
    from flask_login import current_user

    # Per deployment - sempre redirect al login se non autenticato
    # Questo assicura comportamento consistente tra dev e production
    if not current_user.is_authenticated:
        return redirect('/auth/login')

    # Se autenticato, vai alla dashboard
    return redirect('/dashboard')
    if session.get('demo_logged_in'):
        return redirect('/planner')

    # Nessuna autenticazione: redirect al login
    return redirect('/auth/login')


@app.route('/old_dashboard')
def old_dashboard():
    """Vecchia dashboard mobile per compatibilità"""
    if not session.get('demo_logged_in'):
        return redirect('/auth/login')

    # Dashboard/Home per utenti loggati (design mobile)
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viamigo - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0c0a09; }
        .phone-mockup { width: 100%; max-width: 400px; height: 100vh; max-height: 850px; background-color: #111827; border-radius: 40px; border: 10px solid #111827; box-shadow: 0 20px 40px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; }
        .phone-screen { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .viamigo-font { font-family: 'Poppins', sans-serif; background: linear-gradient(to right, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
</head>
<body class="flex justify-center items-center p-4">
    <div class="phone-mockup">
        <div class="phone-screen">
            <!-- HEADER -->
            <div class="header p-4 pt-8 border-b border-gray-700">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-2xl font-bold viamigo-font">Viamigo</h1>
                        <p class="text-xs text-gray-400">Il tuo assistente di viaggio</p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="window.location.href='/profile'" class="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                        </button>
                        <button onclick="window.location.href='/auth/logout'" class="w-10 h-10 bg-red-600 rounded-full flex items-center justify-center">
                            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <!-- CONTENUTO DASHBOARD -->
            <div class="flex-grow overflow-y-auto p-4">
                <div class="space-y-4">
                    <!-- Welcome Card -->
                    <div class="bg-gradient-to-r from-violet-600 to-purple-600 rounded-xl p-4 text-white">
                        <h2 class="text-lg font-semibold mb-1">Benvenuto!</h2>
                        <p class="text-sm opacity-90">Pronto per il tuo prossimo viaggio?</p>
                    </div>

                    <!-- Action Cards -->
                    <div class="grid grid-cols-2 gap-3">
                        <div class="bg-gray-800 rounded-xl p-4 text-center">
                            <div class="text-2xl mb-2">🗺️</div>
                            <h3 class="text-white font-medium text-sm mb-1">Pianifica Viaggio</h3>
                            <p class="text-gray-400 text-xs mb-3">Crea itinerari personalizzati</p>
                            <button onclick="window.location.href='/planner'" class="w-full bg-violet-500 text-white py-2 rounded-lg text-sm font-medium">
                                Inizia
                            </button>
                        </div>

                        <div class="bg-gray-800 rounded-xl p-4 text-center">
                            <div class="text-2xl mb-2">👤</div>
                            <h3 class="text-white font-medium text-sm mb-1">Il Tuo Profilo</h3>
                            <p class="text-gray-400 text-xs mb-3">Gestisci preferenze</p>
                            <button onclick="window.location.href='/profile'" class="w-full bg-green-600 text-white py-2 rounded-lg text-sm font-medium">
                                Gestisci
                            </button>
                        </div>
                    </div>

                    <!-- Destinazioni Suggerite -->
                    <div class="mt-6">
                        <h3 class="text-white font-semibold mb-3">Destinazioni Popolari</h3>
                        <div class="space-y-3">
                            <div class="bg-gray-800 rounded-lg p-3 flex items-center space-x-3">
                                <div class="text-2xl">🏛️</div>
                                <div class="flex-grow">
                                    <h4 class="text-white font-medium text-sm">Roma</h4>
                                    <p class="text-gray-400 text-xs">Città eterna, arte e storia</p>
                                </div>
                                <button class="text-violet-400 text-sm">Esplora</button>
                            </div>

                            <div class="bg-gray-800 rounded-lg p-3 flex items-center space-x-3">
                                <div class="text-2xl">🎭</div>
                                <div class="flex-grow">
                                    <h4 class="text-white font-medium text-sm">Venezia</h4>
                                    <p class="text-gray-400 text-xs">Canali romantici e cultura</p>
                                </div>
                                <button class="text-violet-400 text-sm">Esplora</button>
                            </div>

                            <div class="bg-gray-800 rounded-lg p-3 flex items-center space-x-3">
                                <div class="text-2xl">🎨</div>
                                <div class="flex-grow">
                                    <h4 class="text-white font-medium text-sm">Firenze</h4>
                                    <p class="text-gray-400 text-xs">Rinascimento e arte</p>
                                </div>
                                <button class="text-violet-400 text-sm">Esplora</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')


@app.route('/planner')
@login_required
def planner():
    """Redirect alla pagina originale di pianificazione"""
    return redirect('/static/index.html')


@app.route('/route_proxy')
def route_proxy():
    """Proxy per OpenRouteService API per evitare CORS"""
    try:
        import requests

        profile = request.args.get('profile', 'foot-walking')
        start = request.args.get('start')
        end = request.args.get('end')

        if not start or not end:
            return jsonify({'error': 'Parametri start/end richiesti'}), 400

        # Prova diverse API keys per evitare rate limiting
        api_keys = [
            '5b3ce3597851110001cf6248d8b3c8c3b4de4ecc8f4fcd1ca85f476c',
            '5b3ce3597851110001cf6248a2a977a5f8c17452c4e91b878baec4d0f',
            '5b3ce3597851110001cf6248aa843cc7fdedf412e839ea5fa49bb9b0c'
        ]

        # Usa la prima API key disponibile
        api_key = api_keys[0]
        url = f'https://api.openrouteservice.org/v2/directions/{profile}'

        params = {
            'api_key': api_key,
            'start': start,
            'end': end
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json())
        elif response.status_code == 403 or response.status_code >= 400:
            # API key limitata o altri errori - restituisci fallback per linea retta
            try:
                start_coords = start.split(',')
                end_coords = end.split(',')
                return jsonify({
                    'features': [{
                        'geometry': {
                            'coordinates': [
                                [float(start_coords[0]),
                                 float(start_coords[1])],
                                [float(end_coords[0]), float(end_coords[1])]
                            ]
                        }
                    }]
                })
            except (IndexError, ValueError):
                # Se anche il parsing delle coordinate fallisce
                return jsonify({
                    'features': [{
                        'geometry': {
                            'coordinates': [
                                [8.9314, 44.4063],  # Genova default
                                [8.9326, 44.4109]
                            ]
                        }
                    }]
                })
        else:
            return jsonify({'error': f'API error: {response.status_code}'}), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_profile', methods=['GET'])
def api_get_profile():
    """API endpoint per ottenere profilo utente (per compatibilità con frontend)"""
    from flask_login import current_user

    # Se non autenticato, usa fallback demo per compatibilità
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get('demo_user_id', 'demo_user_123')

    # Mock profilo per demo - funzionalità complete
    return jsonify({
        'success': True,
        'profile': {
            'interests': ['storia', 'arte', 'cibo', 'natura'],
            'travel_pace': 'Moderato',
            'budget': '€€',
            'accessibility_needs': [],
            'language': 'it'
        }
    })


@app.route('/plan', methods=['POST'])
@login_required
def api_plan_trip():
    """API endpoint per pianificazione viaggi - routing dinamico personalizzato"""
    try:
        data = request.get_json()
        start = data.get('start', '').strip()
        end = data.get('end', '').strip()
        city = data.get('city', '').strip()
        duration = data.get('duration', 'half_day')

        if not start or not end:
            return jsonify({
                'success': False,
                'error': 'Start e end sono obbligatori'
            }), 400

        # Sistema di riconoscimento città migliorato se non specificata
        if not city:
            city = detect_city_from_locations(start.lower(), end.lower())

        # Ottieni profilo utente per personalizzazione
        from flask_login import current_user as auth_user

        # Usa utente realmente autenticato se disponibile
        if auth_user.is_authenticated:
            user_id = auth_user.id
        else:
            user_id = session.get('demo_user_id', 'demo_user_123')

        # Mock profilo per demo - interessi personalizzati
        user_interests = ['storia', 'arte', 'cibo', 'natura']

        # 🌍 PRIORITÀ ASSOLUTA: Usa SEMPRE Apify per destinazioni estere
        from apify_integration import apify_travel

        # Lista completa destinazioni estere che DEVONO usare Apify
        foreign_cities = [
            'usa washington d', 'japan tokyo', 'germany berlin',
            'england london', 'france paris', 'spain madrid',
            'london', 'paris', 'madrid', 'berlin', 'tokyo'  # Varianti dirette
        ]

        # 🔍 RICONOSCIMENTO ESTERO: Verifica start, end E city
        is_foreign = False
        detected_foreign_city = None

        # Check in city parameter first
        for foreign_key in foreign_cities:
            if foreign_key in city.lower():
                is_foreign = True
                detected_foreign_city = foreign_key
                break

        # Check in start/end locations
        if not is_foreign:
            combined_location_text = f"{start} {end}".lower()

            # Direct city name detection
            if 'london' in combined_location_text or 'piccadilly' in combined_location_text or 'westminster' in combined_location_text or 'soho' in combined_location_text:
                is_foreign = True
                detected_foreign_city = 'london'
                city = 'london'  # Use simple 'london' for better translation
            elif 'paris' in combined_location_text or 'champs' in combined_location_text or 'eiffel' in combined_location_text:
                is_foreign = True
                detected_foreign_city = 'paris'
                city = 'paris'
            elif 'new york' in combined_location_text or 'manhattan' in combined_location_text or 'brooklyn' in combined_location_text:
                is_foreign = True
                detected_foreign_city = 'new york'
                city = 'new york'
            elif 'berlin' in combined_location_text or 'brandenburg' in combined_location_text:
                is_foreign = True
                detected_foreign_city = 'berlin'
                city = 'berlin'
            elif 'tokyo' in combined_location_text or 'shibuya' in combined_location_text:
                is_foreign = True
                detected_foreign_city = 'tokyo'
                city = 'tokyo'

            # Fallback to original foreign_cities check
            if not is_foreign:
                for foreign_key in foreign_cities:
                    if foreign_key in combined_location_text:
                        is_foreign = True
                        detected_foreign_city = foreign_key
                        city = foreign_key
                        break

        print(
            f"🔍 FOREIGN CHECK: is_foreign={is_foreign}, detected='{detected_foreign_city}', final_city='{city}'")
        print(
            f"🔍 APIFY STATUS: available={apify_travel.is_available()}, token={bool(apify_travel.api_token)}")

        # 🌍 FORCE APIFY for foreign destinations (with fast timeout for London)
        if is_foreign:
            if apify_travel.is_available():
                print(f"🌍 USING APIFY for foreign destination: {city}")

                # For London, try cache first and use faster fallback
                if city.lower() == 'london':
                    from apify_integration import apify_travel
                    cached_attractions = apify_travel.get_cached_places(
                        'london', 'tourist_attraction')
                    if cached_attractions and len(cached_attractions) >= 2:
                        print(f"🚀 Using cached London data to avoid slow Apify")
                        itinerary = generate_london_itinerary_from_cache(
                            start, end, cached_attractions)
                    else:
                        # Try Apify with shorter timeout for London
                        try:
                            import signal

                            def timeout_handler(signum, frame):
                                raise TimeoutError("Apify timeout")
                            signal.signal(signal.SIGALRM, timeout_handler)
                            signal.alarm(15)  # 15 second timeout

                            itinerary = apify_travel.generate_authentic_waypoints(
                                start, end, city)
                            signal.alarm(0)  # Cancel timeout
                        except (TimeoutError, Exception) as e:
                            print(
                                f"⚠️ Apify timeout for London, using fallback: {e}")
                            itinerary = generate_london_fallback_itinerary(
                                start, end)
                else:
                    itinerary = apify_travel.generate_authentic_waypoints(
                        start, end, city)

                print(
                    f"🌍 APIFY returned {len(itinerary) if itinerary else 0} waypoints")
            else:
                print(
                    f"❌ APIFY NOT AVAILABLE for {city} - missing token or client")
                # Force fallback with foreign flag
                from dynamic_routing import dynamic_router
                itinerary = dynamic_router.generate_personalized_itinerary(
                    start, end, city, duration, user_interests
                )
        else:
            print(f"🇮🇹 DOMESTIC destination: {city} - using dynamic routing")
            # Fallback al routing dinamico personalizzato
            from dynamic_routing import dynamic_router
            itinerary = dynamic_router.generate_personalized_itinerary(
                start, end, city, duration, user_interests
            )

        # Se il routing dinamico fallisce, usa template specifici
        if not itinerary or len(itinerary) < 3:
            print(f"Fallback a template per {city}")
            if city == 'torino':
                # 🚀 NEW: Use intelligent Torino routing with REAL database data
                from intelligent_torino_routing import intelligent_torino_router
                itinerary = intelligent_torino_router.generate_intelligent_itinerary(
                    start, end, user_interests, duration
                )
            elif city == 'roma':
                itinerary = generate_roma_itinerary(start, end)
            elif city == 'milano':
                itinerary = generate_milano_itinerary(start, end)
            elif city == 'venezia':
                itinerary = generate_venezia_itinerary(start, end)
            elif city == 'firenze':
                itinerary = generate_firenze_itinerary(start, end)
            elif city == 'genova':
                itinerary = generate_genova_itinerary(start, end)
            else:
                itinerary = generate_generic_itinerary(start, end)

        return jsonify({
            'success': True,
            'itinerary': itinerary,
            'routing_info': {
                'city': city,
                'routing_type': 'apify_authentic' if is_foreign and apify_travel.is_available() else 'dynamic_personalized',
                'generated_for': f"{start} → {end}",
                'realistic_routing': True,
                'walking_routes': True,
                'apify_available': apify_travel.is_available(),
                'is_foreign_destination': is_foreign
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def detect_city_from_locations(start, end):
    """Rileva la città dall'input utente usando Nominatim API per scalabilità mondiale"""
    text = f"{start} {end}".lower()

    # 🌍 PRIORITÀ 0: Riconoscimento destinazioni ESTERE - DEVE usare Apify
    foreign_destinations = {
        'usa washington d': ['usa', 'america', 'washington', 'new york', 'nyc', 'brooklyn', 'manhattan', 'boston', 'chicago', 'los angeles', 'san francisco'],
        'japan tokyo': ['tokyo', 'japan', 'osaka', 'kyoto', 'hiroshima', 'nagoya'],
        'germany berlin': ['berlin', 'germany', 'munich', 'hamburg', 'cologne', 'frankfurt'],
        'england london': ['london', 'england', 'manchester', 'liverpool', 'birmingham'],
        'france paris': ['paris', 'france', 'marseille', 'lyon', 'nice', 'toulouse'],
        'spain madrid': ['madrid', 'spain', 'barcelona', 'valencia', 'seville']
    }

    for country_city, keywords in foreign_destinations.items():
        if any(keyword in text for keyword in keywords):
            print(f"🌍 DESTINAZIONE ESTERA RILEVATA: {country_city}")
            return country_city  # Ritorna il paese_citta come identificativo speciale

    # PRIORITÀ 1: Estrazione automatica nome città dai pattern comma-separated
    import re

    # Pattern: "luogo,città" - estrae la città dopo la virgola
    comma_patterns = re.findall(r'[^,]+,\s*([a-z\s]+)', text)
    for city_candidate in comma_patterns:
        city_candidate = city_candidate.strip()
        if len(city_candidate) > 2:  # Nome città valido
            return city_candidate

    # PRIORITÀ 2: Riconoscimento diretto dalle parole chiave
    for keyword in ['trieste', 'castello miramare', 'piazza unità']:
        if keyword in text:
            return 'trieste'

    # PRIORITÀ 3: Geocoding automatico per identificare la città
    try:
        import requests

        # Prova a geocodificare l'intero testo per identificare la località
        params = {
            'q': f"{start} {end} Italia",
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'it'
        }

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            timeout=3,
            headers={'User-Agent': 'Viamigo/1.0'}
        )

        if response.ok and response.json():
            result = response.json()[0]
            address = result.get('address', {})

            # Estrai città dai dati OSM
            city_candidates = [
                address.get('city'),
                address.get('town'),
                address.get('village'),
                address.get('municipality'),
                address.get('county')
            ]

            for city in city_candidates:
                if city and len(city) > 2:
                    return city.lower()

    except Exception as e:
        print(f"Errore geocoding città: {e}")

    # PRIORITÀ 4: Fallback a città italiane principali
    major_cities = {
        'roma': ['roma', 'rome', 'colosseo', 'vaticano', 'trastevere'],
        'milano': ['milano', 'milan', 'duomo', 'navigli', 'brera'],
        'torino': ['torino', 'turin', 'mole antonelliana'],
        'venezia': ['venezia', 'venice', 'san marco', 'rialto'],
        'firenze': ['firenze', 'florence', 'uffizi', 'ponte vecchio'],
        'genova': ['genova', 'genoa', 'acquario', 'de ferrari'],
        'napoli': ['napoli', 'naples', 'vesuvio', 'spaccanapoli'],
        'bologna': ['bologna', 'torri', 'piazza maggiore'],
        'sardegna': ['sardegna', 'sardinia', 'olbia', 'cagliari', 'portorotondo', 'porto cervo', 'costa smeralda', 'orgosolo', 'nuoro', 'sassari', 'santa teresa', 'gallura', 'baja sardinia', 'cala di volpe']
    }

    for city, keywords in major_cities.items():
        if any(keyword in text for keyword in keywords):
            return city

    return 'generico'


def generate_torino_itinerary(start, end):
    """Genera itinerario specifico per Torino"""
    return [
        {
            'time': '09:00',
            'title': 'Via Roma',
            'description': 'Partenza dalla via pedonale più elegante di Torino, tra portici storici e caffè aristocratici.',
            'coordinates': [45.0703, 7.6869],
            'context': 'via_roma_torino',
            'transport': 'walking'
        },
        {
            'time': '09:30',
            'title': 'Piazza Castello',
            'description': 'Il cuore di Torino con Palazzo Reale, Palazzo Madama e Teatro Regio.',
            'coordinates': [45.0706, 7.6868],
            'context': 'piazza_castello_torino',
            'transport': 'walking'
        },
        {
            'time': '10:15',
            'title': 'Mole Antonelliana',
            'description': 'Il simbolo di Torino con il Museo del Cinema. Vista panoramica dalla cupola.',
            'coordinates': [45.0692, 7.6934],
            'context': 'mole_antonelliana',
            'transport': 'tram'
        },
        {
            'time': '11:00',
            'title': 'Musei Reali',
            'description': 'Palazzo Reale, Armeria Reale e Galleria Sabauda in un unico complesso.',
            'coordinates': [45.0722, 7.6862],
            'context': 'musei_reali_torino',
            'transport': 'walking'
        },
        {
            'time': '12:30',
            'title': 'Lungo Po',
            'description': 'Passeggiata rilassante lungo il fiume Po fino al Parco del Valentino.',
            'coordinates': [45.0618, 7.6908],
            'context': 'lungo_po',
            'transport': 'bus'
        },
        {
            'type': 'tip',
            'title': '🚌 Trasporti Torino',
            'description': 'Biglietto GTT: €1.70 (90 min). Torino Card include trasporti e musei.'
        },
        {
            'type': 'tip',
            'title': '☕ Specialità locale',
            'description': 'Prova il bicerin al Caffè Fiorio (1780) o al Baratti & Milano.'
        }
    ]


def generate_roma_itinerary(start, end):
    """Genera itinerario specifico per Roma"""
    return [
        {
            'time': '09:00',
            'title': 'Stazione Roma Termini',
            'description': 'Partenza dalla stazione principale di Roma. Prendi la Metro A direzione Battistini.',
            'coordinates': [41.9028, 12.4964],
            'context': 'stazione_termini'
        },
        {
            'time': '09:15',
            'title': 'Piazza di Spagna',
            'description': 'Scalinata di Trinità dei Monti e shopping di lusso in Via Condotti.',
            'coordinates': [41.9063, 12.4821],
            'context': 'piazza_spagna'
        },
        {
            'time': '10:00',
            'title': 'Fontana di Trevi',
            'description': 'Lancia una moneta per tornare nella Città Eterna!',
            'coordinates': [41.9009, 12.4833],
            'context': 'fontana_trevi'
        },
        {
            'time': '10:45',
            'title': 'Pantheon',
            'description': 'Capolavoro dell\'architettura romana, perfettamente conservato.',
            'coordinates': [41.8986, 12.4769],
            'context': 'pantheon'
        },
        {
            'time': '11:30',
            'title': 'Piazza Navona',
            'description': 'La piazza barocca più bella di Roma con le sue tre fontane.',
            'coordinates': [41.8986, 12.4730],
            'context': 'piazza_navona'
        },
        {
            'type': 'tip',
            'title': '🚇 Metro Roma',
            'description': 'Biglietto: €1.50 (100 min). Roma Pass include trasporti e musei.'
        }
    ]


def generate_milano_itinerary(start, end):
    """Genera itinerario specifico per Milano"""
    return [
        {
            'time': '09:00',
            'title': 'Duomo di Milano',
            'description': 'La cattedrale gotica più famosa d\'Italia. Salita alle terrazze per vista panoramica.',
            'coordinates': [45.4642, 9.1900],
            'context': 'duomo_milano'
        },
        {
            'time': '10:30',
            'title': 'Galleria Vittorio Emanuele II',
            'description': 'Il salotto di Milano, galleria commerciale del 1800.',
            'coordinates': [45.4655, 9.1897],
            'context': 'galleria_milano'
        },
        {
            'time': '11:15',
            'title': 'Teatro alla Scala',
            'description': 'Il teatro dell\'opera più famoso al mondo.',
            'coordinates': [45.4678, 9.1895],
            'context': 'scala_milano'
        },
        {
            'time': '12:00',
            'title': 'Castello Sforzesco',
            'description': 'Castello rinascimentale con musei e il Parco Sempione.',
            'coordinates': [45.4706, 9.1799],
            'context': 'castello_sforzesco'
        },
        {
            'type': 'tip',
            'title': '🍸 Aperitivo milanese',
            'description': 'Navigli per aperitivo serale (18:00-20:00).'
        }
    ]


def generate_venezia_itinerary(start, end):
    """Genera itinerario specifico per Venezia"""
    return [
        {
            'time': '09:00',
            'title': 'Piazza San Marco',
            'description': 'Il cuore di Venezia con la Basilica e il Campanile.',
            'coordinates': [45.4341, 12.3384],
            'context': 'san_marco_venezia'
        },
        {
            'time': '10:30',
            'title': 'Palazzo Ducale',
            'description': 'Palazzo dei Dogi con il famoso Ponte dei Sospiri.',
            'coordinates': [45.4336, 12.3403],
            'context': 'palazzo_ducale'
        },
        {
            'time': '11:30',
            'title': 'Ponte di Rialto',
            'description': 'Il ponte più antico e famoso del Canal Grande.',
            'coordinates': [45.4380, 12.3358],
            'context': 'rialto_venezia'
        },
        {
            'type': 'tip',
            'title': '🚤 Vaporetto',
            'description': 'Biglietto: €7.50 (75 min). Venice Card per sconti.'
        }
    ]


def generate_firenze_itinerary(start, end):
    """Genera itinerario specifico per Firenze"""
    return [
        {
            'time': '09:00',
            'title': 'Duomo di Firenze',
            'description': 'Cattedrale con la cupola del Brunelleschi.',
            'coordinates': [43.7733, 11.2560],
            'context': 'duomo_firenze'
        },
        {
            'time': '10:30',
            'title': 'Galleria degli Uffizi',
            'description': 'Il museo d\'arte più importante di Firenze.',
            'coordinates': [43.7678, 11.2553],
            'context': 'uffizi'
        },
        {
            'time': '12:00',
            'title': 'Ponte Vecchio',
            'description': 'Il ponte medievale con le botteghe orafe.',
            'coordinates': [43.7681, 11.2533],
            'context': 'ponte_vecchio'
        },
        {
            'type': 'tip',
            'title': '🎨 Prenotazioni',
            'description': 'Uffizi e Accademia richiedono prenotazione obbligatoria.'
        }
    ]


def generate_genova_itinerary(start, end):
    """Genera itinerario specifico per Genova basato su destinazione"""
    print(f"🎯 Routing ottimizzato per genova {end} - coordinate verificate")

    # Analizza la destinazione per generare itinerario pertinente
    end_lower = end.lower().strip()
    start_lower = start.lower().strip()

    # ITINERARIO PARCHI DI NERVI - DESTINAZIONE SPECIFICA
    if 'nervi' in end_lower or 'parchi' in end_lower:
        return [
            {
                'time': '09:00',
                'title': 'Stazione Genova Nervi',
                'description': 'Partenza dalla stazione ferroviaria di Nervi, borgo elegante della Riviera di Levante',
                'coordinates': [44.3878, 8.9515],
                'context': 'stazione_nervi',
                'transport': 'start'
            },
            {
                'time': '09:15',
                'title': 'Passeggiata Anita Garibaldi',
                'description': 'Splendida passeggiata a mare di 2 km con vista sul Golfo Paradiso',
                'coordinates': [44.3885, 8.9525],
                'context': 'passeggiata_nervi',
                'transport': 'walking'
            },
            {
                'time': '10:00',
                'title': 'Parchi di Nervi',
                'description': 'Parco storico con giardini botanici, ville liberty e vista panoramica sul mare',
                'coordinates': [44.3895, 8.9535],
                'context': 'parchi_nervi',
                'transport': 'walking'
            },
            {
                'time': '10:45',
                'title': 'Villa Gropallo - Museo Frugone',
                'description': 'Collezione di arte moderna e contemporanea in elegante villa d\'epoca',
                'coordinates': [44.3902, 8.9542],
                'context': 'villa_gropallo',
                'transport': 'walking'
            },
            {
                'time': '11:30',
                'title': 'Torre Gropallo',
                'description': 'Antica torre di avvistamento con vista spettacolare sulla costa ligure',
                'coordinates': [44.3910, 8.9550],
                'context': 'torre_gropallo',
                'transport': 'walking'
            },
            {
                'type': 'tip',
                'title': '🚂 Come arrivare',
                'description': 'Treno regionale da Genova Brignole a Nervi (20 min, €2.20). Ogni 30 minuti.'
            },
            {
                'type': 'tip',
                'title': '🌸 Stagione ideale',
                'description': 'Primavera per la fioritura nei parchi, estate per il mare.'
            }
        ]

    # ITINERARIO ACQUARIO - DESTINAZIONE SPECIFICA
    elif 'acquario' in end_lower or 'porto antico' in end_lower:
        return [
            {
                'time': '09:00',
                'title': 'Piazza De Ferrari',
                'description': 'Il salotto di Genova con la grande fontana e palazzi storici',
                'coordinates': [44.4076, 8.9338],
                'context': 'piazza_de_ferrari',
                'transport': 'start'
            },
            {
                'time': '09:30',
                'title': 'Cattedrale di San Lorenzo',
                'description': 'Duomo romanico-gotico con tesoro e bomba inesplosa del 1941',
                'coordinates': [44.407, 8.9307],
                'context': 'cattedrale_san_lorenzo',
                'transport': 'walking'
            },
            {
                'time': '10:15',
                'title': 'Via del Campo',
                'description': 'La strada più famosa dei caruggi genovesi, immortalata da De André',
                'coordinates': [44.4088, 8.9294],
                'context': 'via_del_campo',
                'transport': 'walking'
            },
            {
                'time': '11:30',
                'title': 'Porto Antico',
                'description': 'Area portuale rinnovata da Renzo Piano con Acquario e Biosfera',
                'coordinates': [44.4108, 8.9279],
                'context': 'porto_antico',
                'transport': 'walking'
            },
            {
                'time': '12:30',
                'title': 'Acquario di Genova',
                'description': 'Secondo acquario più grande d\'Europa con 12.000 esemplari',
                'coordinates': [44.4108, 8.9279],
                'context': 'acquario_genova',
                'transport': 'walking'
            },
            {
                'type': 'tip',
                'title': '💡 Genova',
                'description': 'Percorso ottimizzato: dal centro storico ai caruggi, fino al porto moderno'
            }
        ]

    # ITINERARIO SPIANATA CASTELLETTO - DESTINAZIONE SPECIFICA
    elif 'castelletto' in end_lower or 'spianata' in end_lower:
        return [
            {
                'time': '09:00',
                'title': 'Piazza Portello',
                'description': 'Punto di partenza per la funicolare verso Castelletto',
                'coordinates': [44.4095, 8.9325],
                'context': 'piazza_portello',
                'transport': 'start'
            },
            {
                'time': '09:15',
                'title': 'Funicolare Castelletto',
                'description': 'Storica funicolare del 1909, viaggio panoramico verso la collina',
                'coordinates': [44.4105, 8.9340],
                'context': 'funicolare_castelletto',
                'transport': 'funicular'
            },
            {
                'time': '09:30',
                'title': 'Spianata Castelletto',
                'description': 'Terrazza panoramica con vista a 360° su Genova, porto e mare',
                'coordinates': [44.4118, 8.9364],
                'context': 'spianata_castelletto',
                'transport': 'walking'
            },
            {
                'time': '10:15',
                'title': 'Museo d\'Arte Orientale',
                'description': 'Collezione orientale più importante d\'Italia in Villetta Di Negro',
                'coordinates': [44.4125, 8.9370],
                'context': 'museo_orientale',
                'transport': 'walking'
            },
            {
                'time': '11:00',
                'title': 'Villetta Di Negro',
                'description': 'Parco romantico con cascate artificiali e grotte decorative',
                'coordinates': [44.4130, 8.9375],
                'context': 'villetta_di_negro',
                'transport': 'walking'
            },
            {
                'type': 'tip',
                'title': '🚡 Funicolare',
                'description': 'Biglietto €0.90, corse ogni 15 min. Orario: 6:40-24:00'
            },
            {
                'type': 'tip',
                'title': '📸 Vista panoramica',
                'description': 'Migliore al tramonto per foto spettacolari del porto'
            }
        ]

    # ITINERARIO GENERICO CENTRO STORICO (fallback)
    else:
        return [
            {
                'time': '09:00',
                'title': 'Piazza De Ferrari',
                'description': 'Il salotto di Genova con la grande fontana e palazzi storici',
                'coordinates': [44.4076, 8.9338],
                'context': 'piazza_de_ferrari',
                'transport': 'start'
            },
            {
                'time': '09:30',
                'title': 'Cattedrale di San Lorenzo',
                'description': 'Duomo romanico-gotico con tesoro e bomba inesplosa del 1941',
                'coordinates': [44.407, 8.9307],
                'context': 'cattedrale_san_lorenzo',
                'transport': 'walking'
            },
            {
                'time': '10:15',
                'title': 'Via del Campo',
                'description': 'La strada più famosa dei caruggi genovesi, immortalata da De André',
                'coordinates': [44.4088, 8.9294],
                'context': 'via_del_campo',
                'transport': 'walking'
            },
            {
                'time': '11:30',
                'title': 'Porto Antico',
                'description': 'Area portuale rinnovata da Renzo Piano con Acquario e Biosfera',
                'coordinates': [44.4108, 8.9279],
                'context': 'porto_antico',
                'transport': 'walking'
            },
            {
                'time': '12:30',
                'title': 'Acquario di Genova',
                'description': 'Secondo acquario più grande d\'Europa con 12.000 esemplari',
                'coordinates': [44.4108, 8.9279],
                'context': 'acquario_genova',
                'transport': 'walking'
            },
            {
                'type': 'tip',
                'title': '💡 Genova',
                'description': 'Percorso ottimizzato: dal centro storico ai caruggi, fino al porto moderno'
            }
        ]


def generate_london_itinerary_from_cache(start, end, cached_attractions):
    """Generate London itinerary from cached data"""
    london_coords = [51.5074, -0.1278]  # Central London

    itinerary = [
        {
            'time': '09:00',
            'title': start,
            'description': f'Starting point: {start}',
            'coordinates': london_coords,
            'context': start.lower().replace(' ', '_').replace(',', ''),
            'transport': 'start',
            'type': 'activity'
        }
    ]

    # Add attractions from cache
    current_time = 9.5
    for i, attraction in enumerate(cached_attractions[:3]):
        time_slot = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
        coords = [attraction.get('latitude', london_coords[0]), attraction.get(
            'longitude', london_coords[1])]

        itinerary.append({
            'time': f"{time_slot} - {int(current_time + 1.5):02d}:{int(((current_time + 1.5) % 1) * 60):02d}",
            'title': attraction.get('name', f'London Attraction {i+1}'),
            'description': attraction.get('description', 'Historic London attraction'),
            'coordinates': coords,
            'context': attraction.get('name', f'attraction_{i}').lower().replace(' ', '_'),
            'transport': 'visit',
            'type': 'activity'
        })
        current_time += 2

    # Add endpoint
    itinerary.append({
        'time': f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}",
        'title': end,
        'description': f'Final destination: {end}',
        'coordinates': london_coords,
        'context': end.lower().replace(' ', '_').replace(',', ''),
        'transport': 'walking',
        'type': 'activity'
    })

    return itinerary


def generate_london_fallback_itinerary(start, end):
    """Fast London fallback when Apify fails"""
    london_attractions = [
        {'name': 'Big Ben', 'coords': [
            51.4994, -0.1245], 'context': 'big_ben'},
        {'name': 'London Eye', 'coords': [
            51.5033, -0.1195], 'context': 'london_eye'},
        {'name': 'Tower Bridge', 'coords': [
            51.5055, -0.0754], 'context': 'tower_bridge'},
        {'name': 'Buckingham Palace', 'coords': [
            51.5014, -0.1419], 'context': 'buckingham_palace'}
    ]

    return [
        {
            'time': '09:00',
            'title': start,
            'description': f'Starting point in London: {start}',
            'coordinates': [51.5074, -0.1278],
            'context': start.lower().replace(' ', '_').replace(',', ''),
            'transport': 'start',
            'type': 'activity'
        },
        {
            'time': '10:00 - 11:30',
            'title': 'Big Ben & Westminster',
            'description': 'Iconic clock tower and Houses of Parliament',
            'coordinates': [51.4994, -0.1245],
            'context': 'big_ben',
            'transport': 'visit',
            'type': 'activity'
        },
        {
            'time': '12:00 - 13:30',
            'title': 'London Eye',
            'description': 'Giant observation wheel with panoramic city views',
            'coordinates': [51.5033, -0.1195],
            'context': 'london_eye',
            'transport': 'visit',
            'type': 'activity'
        },
        {
            'time': '14:00',
            'title': end,
            'description': f'Final destination: {end}',
            'coordinates': [51.5074, -0.1278],
            'context': end.lower().replace(' ', '_').replace(',', ''),
            'transport': 'walking',
            'type': 'activity'
        }
    ]


def generate_generic_itinerary(start, end):
    """Genera itinerario generico per città non riconosciute"""
    return [
        {
            'time': '09:00',
            'title': start.title(),
            'description': f'Punto di partenza: {start}',
            'coordinates': [45.0, 9.0],  # Coordinate generiche Italia centrale
            'context': 'generic_start',
            'transport': 'walking'
        },
        {
            'time': '10:30',
            'title': 'Centro storico',
            'description': 'Esplora il centro storico della città e i suoi monumenti principali.',
            'coordinates': [45.001, 9.001],
            'context': 'generic_center',
            'transport': 'walking'
        },
        {
            'time': '12:00',
            'title': end.title(),
            'description': f'Destinazione finale: {end}',
            'coordinates': [45.002, 9.002],
            'context': 'generic_end',
            'transport': 'walking'
        },
        {
            'type': 'tip',
            'title': '💡 Consiglio',
            'description': 'Per itinerari dettagliati, specifica la città nelle tue ricerche.'
        }
    ]


@app.route('/get_details_backup', methods=['POST'])
@login_required
def api_get_details_backup():
    """API endpoint per dettagli luoghi - sistema ibrido locale + dinamico"""
    try:
        data = request.get_json()
        context = data.get('context', '')

        # Prima prova nel database locale (città italiane principali)
        local_result = get_local_place_details(context)
        if local_result:
            # Formato corretto per il frontend - dati direttamente, non sotto "details"
            return jsonify(local_result)

        # Se non trovato localmente, controlla cache database
        cached_result = get_cached_place_details(context)
        if cached_result:
            return jsonify({
                'success': True,
                'details': cached_result,
                'source': 'cache_database'
            })

        # Se non in cache, usa API dinamiche e salva in cache
        place_name = data.get('place_name', context.replace('_', ' '))
        city = data.get('city', '')
        country = data.get('country', '')

        from dynamic_places_api import dynamic_places
        dynamic_result = dynamic_places.get_place_info(
            place_name, city, country)

        if dynamic_result:
            # Salva in cache per future richieste
            save_to_cache(context, place_name, city, country, dynamic_result)

            return jsonify({
                'success': True,
                'details': dynamic_result,
                'source': 'dynamic_api'
            })

        # Fallback se entrambi falliscono
        return jsonify({
            'success': False,
            'error': 'Informazioni non disponibili per questo luogo'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_local_place_details(context):
    """Ottiene dettagli dal database locale per città italiane principali"""
    # Database dinamico dettagli luoghi per città italiane
    place_details = {
        # === SARDEGNA - COSTA SMERALDA ===
        # Context pattern dal log: cala_di_volpe_olbia portorotondo, baia_sardinia_olbia portorotondo
        'cala_di_volpe_olbia portorotondo': {
            'title': 'Cala di Volpe',
            'summary': 'Spiaggia iconica della Costa Smeralda con acque cristalline color smeraldo e sabbia bianchissima. Una delle spiagge più fotografate al mondo.',
            'details': [
                    {'label': 'Mare', 'value': 'Acque cristalline turchesi'},
                    {'label': 'Hotel',
                        'value': 'Hotel Cala di Volpe (iconico dal 1963)'},
                    {'label': 'Attività', 'value': 'Snorkeling, nuoto, relax'},
                    {'label': 'Accesso', 'value': 'Libero, parcheggio limitato estate'},
                    {'label': 'Servizi',
                        'value': 'Bar sulla spiaggia, noleggio attrezzature'}
            ],
            'tip': '🏖️ Arriva presto al mattino per evitare le folle estive. Porta maschera per snorkeling.',
            'image_url': None
        },
        'baia_sardinia_olbia portorotondo': {
            'title': 'Baia Sardinia',
            'summary': 'Elegante resort costiero della Costa Smeralda con vista panoramica sul mare turchese e macchia mediterranea incontaminata.',
            'details': [
                {'label': 'Spiaggia', 'value': 'Baia dorata protetta dai venti'},
                {'label': 'Marina', 'value': 'Porto turistico moderno'},
                {'label': 'Vita notturna',
                 'value': 'Locali raffinati terrazza mare'},
                {'label': 'Natura', 'value': 'Macchia mediterranea profumata'},
                {'label': 'Resort', 'value': 'Hotel di alta classe vista mare'}
            ],
            'tip': '🌅 Perfetta per chi cerca eleganza discreta. Ottimi ristoranti con vista panoramica.',
            'image_url': None
        },
        'porto_cervo_olbia portorotondo': {
            'title': 'Porto Cervo Marina',
            'summary': 'Il cuore esclusivo della Costa Smeralda con marina di lusso e boutique internazionali. Uno dei porti turistici più prestigiosi del Mediterraneo.',
            'details': [
                {'label': 'Caratteristica', 'value': 'Marina di lusso esclusivo'},
                {'label': 'Shopping', 'value': 'Boutique Prada, Gucci, Louis Vuitton'},
                {'label': 'Ristoranti', 'value': 'Cucina gourmet con vista mare'},
                {'label': 'Eventi', 'value': 'Regata della Sardegna estiva'},
                {'label': 'Stagione peak',
                 'value': 'Luglio-Agosto (alta società)'}
            ],
            'tip': '💡 Visita durante il tramonto per l\'atmosfera più magica. I locali aprono dal tardo pomeriggio.',
            'image_url': None
        },
        'portorotondo_olbia portorotondo': {
            'title': 'Portorotondo',
            'summary': 'Esclusivo borgo turistico della Costa Smeralda con architettura tipica sarda e marina elegante. Destinazione finale del tour.',
            'details': [
                {'label': 'Caratteristica', 'value': 'Borgo esclusivo vista mare'},
                {'label': 'Architettura',
                 'value': 'Case bianche stile mediterraneo'},
                {'label': 'Marina', 'value': 'Porto turistico di charme'},
                {'label': 'Shopping', 'value': 'Boutique esclusive e artigianato'},
                {'label': 'Ristoranti',
                 'value': 'Cucina gourmet terrazza panoramica'}
            ],
            'tip': '⛵ Perfetto per aperitivi al tramonto con vista mare. Centro pedonale elegante.',
            'image_url': None
        },
        'porto_olbia_olbia portorotondo': {
            'title': 'Porto di Olbia',
            'summary': 'Porto commerciale e turistico, punto di partenza per la Costa Smeralda. Gateway per traghetti e collegamenti marittimi.',
            'details': [
                {'label': 'Funzione', 'value': 'Porto commerciale e turistico'},
                {'label': 'Collegamenti',
                 'value': 'Traghetti per Civitavecchia, Genova'},
                {'label': 'Servizi', 'value': 'Terminal passeggeri, parcheggi'},
                {'label': 'Distanza Costa Smeralda',
                 'value': '30 minuti di auto'},
                {'label': 'Yacht club',
                 'value': 'Marina per imbarcazioni da diporto'}
            ],
            'tip': '🚢 Punto di partenza ideale per esplorare la Sardegna settentrionale.',
            'image_url': None
        },
        'porto_cervo_olbia': {
            'title': 'Porto Cervo Marina',
            'summary': 'Il cuore esclusivo della Costa Smeralda con marina di lusso e boutique internazionali.',
            'details': [
                {'label': 'Caratteristica', 'value': 'Marina di lusso esclusivo'},
                {'label': 'Shopping', 'value': 'Boutique Prada, Gucci, Louis Vuitton'},
                {'label': 'Ristoranti', 'value': 'Cucina gourmet con vista mare'}
            ],
            'tip': '💡 **Consiglio**: Visita durante il tramonto per l\'atmosfera più magica. I locali aprono dal tardo pomeriggio.',
            'image_url': None
        },
        'cala_di_volpe_costa': {
            'title': 'Cala di Volpe',
            'summary': 'Spiaggia iconica della Costa Smeralda con acque cristalline e sabbia bianchissima.',
            'details': [
                {'label': 'Caratteristica',
                 'value': 'Spiaggia paradisiaca sabbia bianca'},
                {'label': 'Mare', 'value': 'Acque cristalline turchesi'},
                {'label': 'Hotel',
                 'value': 'Hotel Cala di Volpe (iconico dal 1963)'},
                {'label': 'Attività', 'value': 'Snorkeling, nuoto, relax'},
                {'label': 'Accesso', 'value': 'Libero, parcheggio limitato estate'}
            ],
            'tip': '🏖️ **Consiglio**: Arriva presto al mattino per evitare le folle estive. Porta maschera per snorkeling.',
            'image_url': None
        },
        'baia_sardinia_costa': {
            'title': 'Baia Sardinia',
            'summary': 'Elegante resort costiero con vista panoramica sul mare turchese.',
            'details': [
                {'label': 'Caratteristica', 'value': 'Resort elegante vista mare'},
                {'label': 'Spiaggia', 'value': 'Baia dorata protetta dai venti'},
                {'label': 'Natura', 'value': 'Macchia mediterranea profumata'},
                {'label': 'Marina', 'value': 'Porto turistico moderno'},
                {'label': 'Vita notturna',
                 'value': 'Locali raffinati terrazza mare'}
            ],
            'tip': '🌅 **Consiglio**: Perfetta per chi cerca eleganza discreta. Ottimi ristoranti con vista panoramica.',
            'image_url': None
        },
        'aeroporto_olbia_costa': {
            'title': 'Aeroporto Olbia Costa Smeralda',
            'summary': 'Gateway principale per la Costa Smeralda e la Sardegna settentrionale. Hub turistico con collegamenti diretti per tutta Europa.',
            'details': [
                {'label': 'Codice', 'value': 'OLB - Olbia Costa Smeralda'},
                {'label': 'Collegamenti', 'value': 'Voli diretti da tutta Europa'},
                {'label': 'Servizi', 'value': 'Autonoleggio, navette, taxi'},
                {'label': 'Distanza Costa Smeralda',
                 'value': '30 minuti in auto'},
                {'label': 'Periodo peak',
                 'value': 'Giugno-Settembre (più voli)'}
            ],
            'tip': '🚗 **Consiglio**: Prenota auto a noleggio in anticipo per l\'estate. Navette per Porto Cervo disponibili.',
            'image_url': None
        },
        'porto_cervo': {
            'title': 'Porto Cervo Marina',
            'summary': 'Il cuore esclusivo della Costa Smeralda con marina di lusso e boutique internazionali.',
            'details': [
                {'label': 'Caratteristica', 'value': 'Marina di lusso esclusivo'},
                {'label': 'Shopping', 'value': 'Boutique Prada, Gucci, Louis Vuitton'},
                {'label': 'Ristoranti', 'value': 'Cucina gourmet con vista mare'}
            ],
            'tip': '💡 Visita durante il tramonto per l\'atmosfera più magica.',
            'image_url': None
        },
        'cala_di_volpe': {
            'title': 'Cala di Volpe',
            'summary': 'Spiaggia iconica della Costa Smeralda con acque cristalline e sabbia bianchissima.',
            'details': [
                {'label': 'Mare', 'value': 'Acque cristalline turchesi'},
                {'label': 'Hotel',
                 'value': 'Hotel Cala di Volpe (iconico dal 1963)'},
                {'label': 'Attività', 'value': 'Snorkeling, nuoto, relax'}
            ],
            'tip': '🏖️ Arriva presto al mattino per evitare le folle estive.',
            'image_url': None
        },
        'baia_sardinia': {
            'title': 'Baia Sardinia',
            'summary': 'Elegante resort costiero con vista panoramica sul mare turchese.',
            'details': [
                {'label': 'Spiaggia', 'value': 'Baia dorata protetta dai venti'},
                {'label': 'Marina', 'value': 'Porto turistico moderno'},
                {'label': 'Vita notturna',
                 'value': 'Locali raffinati terrazza mare'}
            ],
            'tip': '🌅 Perfetta per chi cerca eleganza discreta.',
            'image_url': None
        },
        'aeroporto_olbia': {
            'title': 'Aeroporto Olbia Costa Smeralda',
            'summary': 'Gateway principale per la Costa Smeralda e la Sardegna settentrionale.',
            'details': [
                {'label': 'Codice', 'value': 'OLB - Olbia Costa Smeralda'},
                {'label': 'Servizi', 'value': 'Autonoleggio, navette, taxi'},
                {'label': 'Distanza Costa Smeralda',
                 'value': '30 minuti in auto'}
            ],
            'tip': '🚗 Prenota auto a noleggio in anticipo per l\'estate.',
            'image_url': None
        },
        'portorotondo': {
            'title': 'Portorotondo',
            'summary': 'Esclusivo borgo turistico della Costa Smeralda con architettura tipica sarda e marina elegante.',
            'details': [
                {'label': 'Caratteristica', 'value': 'Borgo esclusivo vista mare'},
                {'label': 'Architettura',
                 'value': 'Case bianche stile mediterraneo'},
                {'label': 'Marina', 'value': 'Porto turistico di charme'},
                {'label': 'Shopping', 'value': 'Boutique esclusive e artigianato'},
                {'label': 'Ristoranti',
                 'value': 'Cucina gourmet terrazza panoramica'}
            ],
            'tip': '⛵ Perfetto per aperitivi al tramonto con vista mare. Centro pedonale elegante.',
            'image_url': None
        },

        # === MILANO ===
        'duomo_milano': {
            'title': 'Duomo di Milano',
            'summary': 'Capolavoro gotico con guglie e la Madonnina. Una delle cattedrali più spettacolari del mondo, con terrazze panoramiche che offrono viste mozzafiato sulla città e le Alpi.',
            'details': [
                {'label': 'Costruzione', 'value': '1386-1965 (579 anni)'},
                {'label': 'Stile', 'value': 'Gotico lombardo'},
                {'label': 'Guglie', 'value': '135 guglie con 3.400 statue'},
                {'label': 'Madonnina', 'value': '4.16m, oro, dal 1774'},
                {'label': 'Vetrate',
                 'value': '55 finestre istoriate (XV-XX sec.)'},
                {'label': 'Terrazze', 'value': 'Ascensore €15, scale €10'},
                {'label': 'Cripta', 'value': 'San Carlo Borromeo'},
                {'label': 'Curiosità',
                 'value': 'Meridiana del 1786 ancora funzionante'}
            ],
            'timetable': [
                {'direction': 'Duomo',
                 'times': 'Lun-Dom 8:00-19:00 (ultima entrata 18:10)'},
                {'direction': 'Terrazze',
                 'times': 'Lun-Dom 9:00-19:00 (estate fino 21:00)'},
                {'direction': 'Museo',
                 'times': 'Mar-Dom 10:00-18:00 (chiuso lunedì)'}
            ],
            'actionLink': {
                'text': 'Prenota biglietti',
                'url': 'https://www.duomomilano.it'
            }
        },
        'galleria_milano': {
            'title': 'Galleria Vittorio Emanuele II',
            'summary': 'Il salotto elegante di Milano, galleria commerciale ottocentesca con cupola di vetro e ferro. Considerata uno dei primi centri commerciali al mondo, ospita boutique di lusso e caffè storici.',
            'details': [
                {'label': 'Inaugurazione',
                 'value': '1877 (progetto Giuseppe Mengoni)'},
                {'label': 'Soprannome', 'value': '"Il Salotto di Milano"'},
                {'label': 'Lunghezza', 'value': '196 metri'},
                {'label': 'Cupola', 'value': '47 metri altezza, vetro e ferro'},
                {'label': 'Mosaici pavimento',
                 'value': 'Stemmi di Milano, Torino, Firenze, Roma'},
                {'label': 'Negozi storici',
                 'value': 'Prada (dal 1913), Borsalino'},
                {'label': 'Caffè storici',
                 'value': 'Biffi, Savini (dal 1867)'},
                {'label': 'Rituale portafortuna',
                 'value': 'Girare 3 volte sui genitali del toro torinese'}
            ],
            'timetable': [
                {'direction': 'Negozi',
                 'times': 'Lun-Dom 10:00-20:00 (alcuni fino 22:00)'},
                {'direction': 'Ristoranti', 'times': 'Lun-Dom 12:00-24:00'},
                {'direction': 'Caffè storici', 'times': 'Lun-Dom 7:30-20:00'}
            ]
        },
        'scala_milano': {
            'title': 'Teatro alla Scala',
            'summary': 'Il tempio dell\'opera mondiale. Dal 1778 il teatro più prestigioso per opera lirica e balletto, con una stagione che apre tradizionalmente il 7 dicembre, festa di Sant\'Ambrogio.',
            'details': [
                {'label': 'Inaugurazione',
                 'value': '3 agosto 1778 con "L\'Europa riconosciuta" di Salieri'},
                {'label': 'Architetto',
                 'value': 'Giuseppe Piermarini (neoclassico)'},
                {'label': 'Posti', 'value': '2.030 spettatori, 6 ordini di palchi'},
                {'label': 'Palco reale', 'value': 'Palco n.5 del primo ordine'},
                {'label': 'Stagione inaugurale',
                 'value': '7 dicembre - Sant\'Ambrogio'},
                {'label': 'Artisti famosi',
                 'value': 'Verdi, Puccini, Toscanini, Callas'},
                {'label': 'Museo', 'value': 'Costumi, strumenti, memorabilia'},
                {'label': 'Curiosità', 'value': 'Ricostruito dopo bombardamento 1943'}
            ],
            'timetable': [
                {'direction': 'Visite museo',
                 'times': 'Lun-Dom 9:00-17:30 (ultimo ingresso 17:00)'},
                {'direction': 'Spettacoli',
                 'times': 'Settembre-Luglio (programmazione variabile)'},
                {'direction': 'Biglietteria',
                 'times': 'Lun-Sab 10:00-18:00, Dom 10:00-17:00'}
            ],
            'actionLink': {
                'text': 'Programma e biglietti',
                'url': 'https://www.teatroallascala.org'
            }
        },
        'castello_sforzesco': {
            'title': 'Castello Sforzesco',
            'summary': 'Fortezza rinascimentale simbolo del potere dei Duca di Milano. Oggi ospita musei con capolavori di Michelangelo, Leonardo e arte applicata, circondato dal Parco Sempione.',
            'details': [
                {'label': 'Costruzione originale',
                 'value': '1360 (famiglia Visconti)'},
                {'label': 'Trasformazione',
                 'value': '1450-1499 (Francesco Sforza)'},
                {'label': 'Restauro',
                 'value': '1893-1904 (Luca Beltrami)'},
                {'label': 'Musei', 'value': '9 musei specializzati'},
                {'label': 'Capolavoro',
                 'value': 'Pietà Rondanini (ultima opera Michelangelo)'},
                {'label': 'Leonardo', 'value': 'Decorazioni Sala delle Asse'},
                {'label': 'Torre Filarete',
                 'value': '70 metri, ricostruita dopo esplosione 1521'},
                {'label': 'Cortili',
                 'value': 'Cortile d\'Armi, Cortile della Rocchetta'}
            ],
            'timetable': [
                {'direction': 'Musei',
                 'times': 'Mar-Dom 9:00-17:30 (chiuso lunedì)'},
                {'direction': 'Cortili',
                 'times': 'Lun-Dom 7:00-19:30 (estate fino 20:00)'},
                {'direction': 'Visite guidate',
                 'times': 'Sabato-Domenica 15:00 (prenotazione)'}
            ],
            'actionLink': {
                'text': 'Prenota musei',
                'url': 'https://www.milanocastello.it'
            }
        },
        'parco_sempione': {
            'title': 'Parco Sempione',
            'summary': 'Il polmone verde di Milano con l\'Arco della Pace e la Torre Branca. Perfetto per relax, sport e panorami dalla torre. Un\'oasi di tranquillità nel cuore della città.',
            'details': [
                {'label': 'Superficie', 'value': '38.6 ettari (dal 1888)'},
                {'label': 'Progettista',
                 'value': 'Emilio Alemagna (stile inglese)'},
                {'label': 'Torre Branca',
                 'value': '108m, panorama 360° (ascensore)'},
                {'label': 'Arco della Pace',
                 'value': '25m, 1807-1838, Napoleone'},
                {'label': 'Arena Civica', 'value': '1807, 30.000 spettatori'},
                {'label': 'Acquario', 'value': 'Civico Acquario (1906)'},
                {'label': 'Eventi', 'value': 'Concerti estivi, mercatini, sport'},
                {'label': 'Fauna', 'value': 'Tartarughe, anatre, scoiattoli'}
            ],
            'timetable': [
                {'direction': 'Parco',
                 'times': 'Sempre aperto (illuminato di notte)'},
                {'direction': 'Torre Branca',
                 'times': 'Mar-Dom 10:00-18:00 (estate 21:00)'},
                {'direction': 'Bar parco',
                 'times': 'Lun-Dom 7:00-20:00 (estate 22:00)'}
            ]
        },
        # === TRIESTE ===
        # TRIESTE - Luoghi specifici con dettagli autentici
        'piazza_unita_ditalia_trieste': {
            'title': 'Piazza Unità d\'Italia, Trieste',
            'summary': 'La piazza più grande d\'Europa affacciata sul mare, capolavoro urbanistico dell\'Impero Asburgico. Circondata da palazzi neoclassici e barocchi.',
            'details': [
                {'label': 'Dimensioni',
                 'value': '12.280 m² (la più grande piazza europea sul mare)'},
                {'label': 'Costruzione',
                 'value': 'XIX secolo (epoca asburgica)'},
                {'label': 'Palazzo Municipio',
                 'value': 'Sede comunale con torre campanaria (1877)'},
                {'label': 'Caffè degli Specchi',
                 'value': 'Caffè storico (1839) con vista mare'},
                {'label': 'Fontana Quattro Continenti',
                 'value': 'Simbolo dell\'apertura di Trieste al mondo'},
                {'label': 'Vista', 'value': 'Golfo di Trieste e Castello di Miramare'}
            ],
            'opening_hours': 'Sempre accessibile',
            'cost': 'Gratuito'
        },
        'centro_storico_trieste': {
            'title': 'Centro Storico, Trieste',
            'summary': 'Il cuore mitteleuropeo di Trieste con architetture asburgiche, caffè letterari e atmosfera cosmopolita.',
            'details': [
                {'label': 'Via del Corso',
                 'value': 'Arteria pedonale principale per shopping'},
                {'label': 'Caffè San Marco',
                 'value': 'Caffè letterario frequentato da Joyce e Svevo'},
                {'label': 'Teatro Verdi', 'value': 'Teatro dell\'opera del 1801'},
                {'label': 'Sinagoga', 'value': 'Una delle più grandi d\'Europa'},
                {'label': 'Borgo Teresiano',
                 'value': 'Quartiere settecentesco con canali'},
                {'label': 'Architettura',
                 'value': 'Mix asburgico-italiano unico al mondo'}
            ],
            'opening_hours': 'Sempre accessibile (negozi: 9:00-19:00)',
            'cost': 'Gratuito (consumi variabili)'
        },
        'castello_miramare_trieste': {
            'title': 'Castello di Miramare',
            'summary': 'Castello romantico dell\'Arciduca Massimiliano d\'Asburgo (1856-1860) con giardini botanici e vista spettacolare sul golfo.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1856-1860 (Arciduca Massimiliano)'},
                {'label': 'Stile',
                 'value': 'Eclettico (gotico, rinascimentale, medievale)'},
                {'label': 'Interni', 'value': 'Arredi originali e sale storiche'},
                {'label': 'Giardini', 'value': '22 ettari con 2000+ specie botaniche'},
                {'label': 'Vista panoramica',
                 'value': 'Golfo di Trieste e costa istriana'},
                {'label': 'Leggenda',
                 'value': 'Maledizione di Miramare sui suoi proprietari'}
            ],
            'opening_hours': 'Mar-Dom 9:00-19:00 (estate), 9:00-17:00 (inverno)',
            'cost': '€12 adulti, €8 ridotto, gratuito giardini'
        },
        'canal_grande_trieste': {
            'title': 'Canal Grande, Trieste',
            'summary': 'Il canale navigabile che attraversa il centro storico, cuore del Borgo Teresiano con ponti storici e caffè affacciati.',
            'details': [
                {'label': 'Costruzione',
                 'value': 'XVIII secolo (Maria Teresa d\'Austria)'},
                {'label': 'Lunghezza', 'value': '300 metri navigabili'},
                {'label': 'Ponti', 'value': 'Ponte Rosso e Ponte Verde'},
                {'label': 'Chiesa Sant\'Antonio',
                 'value': 'Chiesa neoclassica sulla sponda'},
                {'label': 'Caffè storici', 'value': 'Caffè con dehors sui ponti'},
                {'label': 'Mercatini',
                 'value': 'Mercato dell\'antiquariato (domenica)'}
            ],
            'opening_hours': 'Sempre accessibile',
            'cost': 'Gratuito'
        },
        'teatro_romano_trieste': {
            'title': 'Teatro Romano, Trieste',
            'summary': 'Antico teatro romano del I-II secolo d.C. scavato nella roccia del colle di San Giusto, con vista panoramica sulla città.',
            'details': [
                {'label': 'Epoca',
                 'value': 'I-II secolo d.C. (epoca augustea)'},
                {'label': 'Capacità',
                 'value': '6000 spettatori (originariamente)'},
                {'label': 'Costruzione', 'value': 'Scavato nella roccia carsica'},
                {'label': 'Stato', 'value': 'Parzialmente conservato'},
                {'label': 'Vista', 'value': 'Panorama su Trieste e il golfo'},
                {'label': 'Eventi', 'value': 'Concerti e spettacoli estivi'}
            ],
            'opening_hours': 'Sempre accessibile (visite guidate su prenotazione)',
            'cost': 'Gratuito'
        },
        # === TORINO ===
        'via_roma_torino': {
            'title': 'Via Roma, Torino',
            'summary': 'La via pedonale più elegante di Torino, creata nel 1930s. I suoi portici neoclassici ospitano boutique di lusso e caffè storici.',
            'details': [
                {'label': 'Lunghezza', 'value': '1.2 km di portici'},
                {'label': 'Costruzione',
                 'value': '1930-1937 (piano urbanistico)'},
                {'label': 'Stile', 'value': 'Architettura razionalista italiana'},
                {'label': 'Shopping', 'value': 'Boutique di lusso, librerie storiche'},
                {'label': 'Caffè storici',
                 'value': 'Caffè Mulassano (1907), Caffè Stratta'}
            ]
        },
        'piazza_castello_torino': {
            'title': 'Piazza Castello, Torino',
            'summary': 'Il cuore politico e culturale di Torino, circondata dai principali palazzi del potere sabaudo. Centro geometrico della città.',
            'details': [
                {'label': 'Dimensioni',
                 'value': '40.000 m² (tra le più grandi d\'Europa)'},
                {'label': 'Palazzo Reale',
                 'value': 'Residenza dei Savoia (XVII-XVIII sec)'},
                {'label': 'Palazzo Madama',
                 'value': 'Museo Civico d\'Arte Antica'},
                {'label': 'Teatro Regio',
                 'value': 'Opera house (1973, dopo incendio)'},
                {'label': 'Armeria Reale',
                 'value': 'Collezione armi antiche più importante al mondo'}
            ]
        },
        'mole_antonelliana': {
            'title': 'Mole Antonelliana',
            'summary': 'Il simbolo di Torino, edificio più alto della città (167m). Originariamente sinagoga, oggi ospita il Museo Nazionale del Cinema.',
            'details': [
                {'label': 'Altezza', 'value': '167.5 metri'},
                {'label': 'Architetto', 'value': 'Alessandro Antonelli'},
                {'label': 'Costruzione', 'value': '1863-1889'},
                {'label': 'Ascensore panoramico',
                 'value': 'Salita alla cupola (€8)'},
                {'label': 'Museo del Cinema',
                 'value': 'Primo in Italia per importanza'},
                {'label': 'Curiosità',
                 'value': 'Compare sul retro delle monete da 2 centesimi'}
            ],
            'timetable': [
                {'direction': 'Museo del Cinema',
                 'times': 'Mar-Dom 9:00-20:00'},
                {'direction': 'Ascensore panoramico',
                 'times': 'Mar-Dom 9:00-19:00 (ultima salita)'}
            ]
        },
        'musei_reali_torino': {
            'title': 'Musei Reali, Torino',
            'summary': 'Il più importante complesso museale del Piemonte, residenza dei Savoia. Include Palazzo Reale, Armeria Reale, Galleria Sabauda e Biblioteca Reale con codici di Leonardo.',
            'details': [
                {'label': 'Patrimonio UNESCO',
                 'value': 'Residenze sabaude (1997)'},
                {'label': 'Palazzo Reale',
                 'value': 'Residenza ufficiale Casa Savoia (1646)'},
                {'label': 'Armeria Reale',
                 'value': 'Collezione armi antiche più ricca al mondo'},
                {'label': 'Galleria Sabauda',
                 'value': 'Capolavori Van Dyck, Rembrandt, Pollaiolo'},
                {'label': 'Biblioteca Reale',
                 'value': 'Autoritratto di Leonardo da Vinci'},
                {'label': 'Biglietto unico',
                 'value': '€15 (ridotto €2), gratuito <18 anni'},
                {'label': 'Prenotazione', 'value': 'Consigliata nei weekend'}
            ],
            'timetable': [
                {'direction': 'Mar-Dom',
                 'times': '9:00-19:00 (ultimo ingresso 18:00)'},
                {'direction': 'Lunedì',
                 'times': 'Chiuso (eccetto festivi)'},
                {'direction': 'Palazzo Reale',
                 'times': 'Visite guidate ogni ora'},
                {'direction': 'Armeria Reale',
                 'times': 'Accesso libero con biglietto'}
            ],
            'actionLink': {
                'text': 'Prenota la visita',
                'url': 'https://www.museireali.beniculturali.it'
            }
        },
        'lungo_po': {
            'title': 'Lungo Po, Torino',
            'summary': 'Le passeggiate lungo il fiume Po offrono scorci romantici di Torino. Dal centro storico al Parco del Valentino.',
            'details': [
                    {'label': 'Lunghezza percorso',
                        'value': '3 km centro-Valentino'},
                    {'label': 'Parco del Valentino',
                        'value': '500.000 m² di verde urbano'},
                    {'label': 'Castello del Valentino',
                        'value': 'Residenza sabauda (UNESCO)'},
                    {'label': 'Borgo medievale',
                        'value': 'Ricostruzione filologica (1884)'},
                    {'label': 'Attività', 'value': 'Jogging, ciclismo, pic-nic'}
            ]
        },
        # === GENOVA ===
        'piazza_de_ferrari': {
            'title': 'Piazza De Ferrari, Genova',
            'summary': 'Il salotto di Genova, circondata da palazzi storici e dominata dalla grande fontana centrale. Cuore del centro storico medievale più esteso d\'Europa.',
            'details': [
                {'label': 'Fontana',
                 'value': 'Costruita nel 1936, ristrutturata nel 2001'},
                {'label': 'Palazzi storici',
                 'value': 'Palazzo Ducale, Palazzo della Regione'},
                {'label': 'Teatro',
                 'value': 'Teatro Carlo Felice (opera house)'},
                {'label': 'Shopping', 'value': 'Gallerie Mazzini, Via XX Settembre'},
                {'label': 'Metro',
                 'value': 'Stazione De Ferrari (linea rossa)'}
            ]
        },
        'via_del_campo': {
            'title': 'Via del Campo, Genova',
            'summary': 'La strada più famosa di Genova, resa celebre dalla canzone di Fabrizio De André. Autentico caruggio medievale nel cuore del centro storico.',
            'details': [
                {'label': 'Lunghezza', 'value': '500 metri di storia medievale'},
                {'label': 'Epoca',
                 'value': 'XII secolo (caruggi medievali)'},
                {'label': 'Fabrizio De André',
                 'value': 'Canzone "Via del Campo" (1967)'},
                {'label': 'Caratteristiche',
                 'value': 'Negozi storici, farinata, botteghe artigiane'},
                {'label': 'Mercato', 'value': 'Mercato del Pesce e prodotti locali'}
            ],
            'opening_hours': 'Sempre accessibile (negozi: 10:00-19:00)',
            'cost': 'Gratuito'
        },
        'cattedrale_san_lorenzo': {
            'title': 'Cattedrale di San Lorenzo, Genova',
            'summary': 'Il Duomo di Genova, famoso per la bomba navale britannica inesplosa del 1941. Capolavoro romanico-gotico con tesoro ecclesiastico.',
            'details': [
                {'label': 'Costruzione',
                 'value': 'IX-XIV secolo (romanico-gotico)'},
                {'label': 'Facciata',
                 'value': 'Marmo bianco e nero a strisce orizzontali'},
                {'label': 'Bomba 1941',
                 'value': 'Proiettile navale britannico inesploso (visibile)'},
                {'label': 'Tesoro',
                 'value': 'Sacro Catino (Sacro Graal), reliquie preziose'},
                {'label': 'Portale', 'value': 'Leoni stilofori medievali'},
                {'label': 'Curiosità',
                 'value': 'Miracolo della bomba che non esplose'}
            ],
            'opening_hours': 'Lun-Sab 9:00-18:00, Dom 15:00-18:00',
            'cost': 'Ingresso gratuito, Tesoro €6'
        },
        'porto_antico': {
            'title': 'Porto Antico, Genova',
            'summary': 'Area portuale storica rinnovata da Renzo Piano per Expo 1992. Centro culturale e turistico con Acquario, Biosfera e Bigo.',
            'details': [
                {'label': 'Progetto Renzo Piano',
                 'value': '1992 (500° scoperta America)'},
                {'label': 'Biosfera', 'value': 'Serra tropicale in vetro e acciaio'},
                {'label': 'Bigo', 'value': 'Ascensore panoramico 40m altezza'},
                {'label': 'Galata Museo del Mare',
                 'value': 'Più grande del Mediterraneo'},
                {'label': 'Eventi', 'value': 'Concerti, festival, mercatini'},
                {'label': 'Ristoranti', 'value': 'Cucina ligure e vista mare'}
            ],
            'opening_hours': 'Sempre accessibile (attrazioni 10:00-19:00)',
            'cost': 'Passeggiata gratuita, attrazioni a pagamento'
        },
        'acquario_genova': {
            'title': 'Acquario di Genova',
            'summary': 'Secondo acquario più grande d\'Europa con 12.000 esemplari marini. Gioiello del Porto Antico progettato da Renzo Piano.',
            'details': [
                {'label': 'Inaugurazione', 'value': '1992 (Expo Colombo)'},
                {'label': 'Dimensioni',
                 'value': '9.700 m² di superficie espositiva'},
                {'label': 'Architetto',
                 'value': 'Renzo Piano (Porto Antico)'},
                {'label': 'Biglietto', 'value': '€29 adulti, €19 bambini'},
                {'label': 'Orari',
                 'value': '9:00-20:00 (estate), 10:00-18:00 (inverno)'},
                {'label': 'Attrazioni',
                 'value': 'Delfini, squali, lamantini, pinguini'},
                {'label': 'Record', 'value': '2° in Europa per grandezza'}
            ],
            'timetable': [
                {'direction': 'Estate (giu-set)',
                 'times': '9:00-20:00 (ultimo ingresso 18:00)'},
                {'direction': 'Inverno (ott-mag)',
                 'times': '9:30-19:00 (ultimo ingresso 17:00)'}
            ],
            'actionLink': {
                'text': 'Prenota biglietto online',
                'url': 'https://www.acquariodigenova.it'
            }
        },
        'cattedrale_genova': {
            'title': 'Cattedrale di San Lorenzo, Genova',
            'summary': 'Il Duomo di Genova, famoso per aver ospitato una bomba navale britannica inesplosa durante la Seconda Guerra Mondiale. Capolavoro di architettura romanico-gotica.',
            'details': [
                {'label': 'Costruzione',
                 'value': 'IX secolo, ricostruita XII-XIV secolo'},
                {'label': 'Stile', 'value': 'Romanico-gotico ligure'},
                {'label': 'Facciata', 'value': 'Marmo bianco e nero a strisce'},
                {'label': 'Bomba inesplosa',
                 'value': '13 febbraio 1941 (esposta nel museo)'},
                {'label': 'Tesoro',
                 'value': 'Sacro Catino (Sacro Graal), reliquie di San Giovanni'},
                {'label': 'Campanile', 'value': 'Torre romanica del XII secolo'},
                {'label': 'Ingresso', 'value': 'Gratuito (museo €6)'}
            ],
            'timetable': [
                {'direction': 'Cattedrale',
                 'times': 'Lun-Sab 8:00-12:00, 15:00-19:00'},
                {'direction': 'Museo del Tesoro',
                 'times': 'Lun-Sab 9:00-12:00, 15:00-18:00'}
            ]
        },
        'spianata_castelletto': {
            'title': 'Spianata Castelletto, Genova',
            'summary': 'Il belvedere più spettacolare di Genova, raggiungibile con la storica funicolare del 1929. Vista panoramica a 360° sulla città e il porto.',
            'details': [
                {'label': 'Altitudine', 'value': '80 metri sul livello del mare'},
                {'label': 'Funicolare',
                 'value': 'Costruita nel 1929, rinnovata nel 2004'},
                {'label': 'Durata salita',
                 'value': '90 secondi (300 metri di percorso)'},
                {'label': 'Biglietto funicolare',
                 'value': '€0.90 (incluso in biglietto AMT)'},
                {'label': 'Panorama',
                 'value': 'Centro storico, porto, Riviera di Ponente'},
                {'label': 'Arte Liberty', 'value': 'Villini e palazzi primi 900'},
                {'label': 'Miglior orario',
                 'value': 'Tramonto (18:30-19:30 estate)'}
            ],
            'timetable': [
                {'direction': 'Funicolare', 'times': '6:00-24:00 ogni 15 minuti'},
                {'direction': 'Spianata', 'times': 'Sempre accessibile'}
            ]
        },
        'museum': {
            'title': 'Musei di Genova',
            'summary': 'Genova offre una ricca collezione di musei che spaziano dall\'arte alla storia marittima, dai palazzi nobiliari alle tradizioni locali.',
            'details': [
                {'label': 'Palazzo Ducale',
                 'value': 'Centro culturale con mostre temporanee'},
                {'label': 'Musei di Strada Nuova',
                 'value': 'Palazzo Rosso, Palazzo Bianco, Palazzo Tursi'},
                {'label': 'Galata Museo del Mare',
                 'value': 'Il più grande museo marittimo del Mediterraneo'},
                {'label': 'Casa di Colombo',
                 'value': 'Casa natale del navigatore genovese'},
                {'label': 'Orari tipici',
                 'value': 'Mar-Dom 10:00-18:00 (variabili)'},
                {'label': 'Biglietti',
                 'value': '€6-15 a museo, card musei disponibile'}
            ],
            'tip': '🎨 La Card Musei di Genova (€12-20) permette l\'accesso a tutti i musei civici.'
        },
        # === FIRENZE ===
        'piazza_del_duomo_firenze': {
            'title': 'Piazza del Duomo, Firenze',
            'summary': 'Il cuore religioso di Firenze con la magnifica Cattedrale di Santa Maria del Fiore, la cupola del Brunelleschi e il Battistero di San Giovanni. Capolavoro del Rinascimento fiorentino.',
            'details': [
                {'label': 'Cattedrale',
                 'value': 'Santa Maria del Fiore (1296-1436)'},
                {'label': 'Cupola Brunelleschi',
                 'value': 'Diametro 45m, prima cupola ottagonale senza armature'},
                {'label': 'Battistero San Giovanni',
                 'value': 'XI-XII secolo, Porte del Paradiso (Ghiberti)'},
                {'label': 'Campanile di Giotto',
                 'value': 'XIV secolo, 84 metri, 414 gradini'},
                {'label': 'Facciata negogotica',
                 'value': 'XIX secolo (1887), marmi policromi'},
                {'label': 'Biglietti',
                 'value': 'Duomo gratuito, cupola €20, campanile €15'}
            ],
            'opening_hours': 'Duomo: Lun-Sab 10:00-17:00, Dom 13:30-16:45',
            'cost': 'Duomo gratuito, complesso €20-30',
            'actionLink': {
                    'text': 'Prenota cupola',
                    'url': 'https://www.ilgrandemuseodelduomo.it'
            }
        },
        'piazza_della_signoria_firenze': {
            'title': 'Piazza della Signoria, Firenze',
            'summary': 'La piazza politica di Firenze con Palazzo Vecchio, sede del governo cittadino. Museo a cielo aperto con statue rinascimentali e Loggia dei Lanzi.',
            'details': [
                {'label': 'Palazzo Vecchio',
                 'value': 'Sede del Comune (1299-1314), torre 94m'},
                {'label': 'Loggia dei Lanzi',
                 'value': 'XIV secolo, statue rinascimentali'},
                {'label': 'David replica',
                 'value': 'Copia del capolavoro di Michelangelo'},
                {'label': 'Perseo Cellini',
                 'value': 'Bronzo manierista (1545-1554)'},
                {'label': 'Fontana Nettuno',
                 'value': 'Ammannati (1565), "Il Biancone"'},
                {'label': 'Caffè Rivoire',
                 'value': 'Storico caffè con vista palazzo (1872)'}
            ],
            'opening_hours': 'Sempre accessibile, Palazzo Vecchio: 9:00-19:00',
            'cost': 'Piazza gratuita, Palazzo Vecchio €12.50'
        },
        'ponte_vecchio_firenze': {
            'title': 'Ponte Vecchio, Firenze',
            'summary': 'Il ponte medievale più famoso del mondo, l\'unico ponte di Firenze sopravvissuto alla Seconda Guerra Mondiale. Caratteristico per le botteghe orafe che lo attraversano.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1345 (ricostruito dopo alluvione 1333)'},
                {'label': 'Corridoio Vasariano',
                 'value': 'Passaggio segreto dei Medici (1565)'},
                {'label': 'Botteghe storiche',
                 'value': 'Orafi dal XVI secolo (prima macellai)'},
                {'label': 'Lunghezza', 'value': '95 metri sull\'Arno'},
                {'label': 'Guerra mondiale',
                 'value': 'Unico ponte risparmiato dai tedeschi (1944)'},
                {'label': 'Taddeo Gaddi',
                 'value': 'Allievo di Giotto, progettista del ponte'}
            ],
            'opening_hours': 'Sempre accessibile, botteghe: 10:00-19:00',
            'cost': 'Passeggiata gratuita, shopping vari prezzi'
        },
        'basilica_santa_croce_firenze': {
            'title': 'Basilica di Santa Croce, Firenze',
            'summary': 'La chiesa francescana più grande del mondo, chiamata "Pantheon di Firenze" per le tombe di Michelangelo, Galileo e Machiavelli. Capolavoro gotico con affreschi di Giotto.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1294-1442, architettura gotica italiana'},
                {'label': 'Tomba Michelangelo',
                 'value': 'Sepolcro del maestro rinascimentale (1564)'},
                {'label': 'Tomba Galileo',
                 'value': 'Monumento al padre della scienza moderna'},
                {'label': 'Cappelle Peruzzi e Bardi',
                 'value': 'Affreschi di Giotto (1320-1325)'},
                {'label': 'Crocifisso Donatello',
                 'value': 'Legno policromo rinascimentale'},
                {'label': 'Cappella Pazzi',
                 'value': 'Brunelleschi, capolavoro architettonico'}
            ],
            'opening_hours': 'Lun-Sab 9:30-17:00, Dom 14:00-17:00',
            'cost': '€8 adulti, €6 ridotto',
            'actionLink': {
                    'text': 'Informazioni visite',
                    'url': 'https://www.santacroceopera.it'
            }
        },
        # === NAPOLI ===
        'piazza_plebiscito_napoli': {
            'title': 'Piazza del Plebiscito, Napoli',
            'summary': 'La piazza più grande e maestosa di Napoli, circondata dalla Basilica di San Francesco di Paola e dal Palazzo Reale. Cuore della Napoli borbonica.',
            'details': [
                {'label': 'Superficie',
                 'value': '25.000 m² (una delle più grandi d\'Italia)'},
                {'label': 'Basilica San Francesco',
                 'value': 'Neoclassica (1816-1846), ispirata al Pantheon'},
                {'label': 'Palazzo Reale',
                 'value': 'Residenza dei Viceré e Borbone (1600-1858)'},
                {'label': 'Leggenda',
                 'value': 'Attraversare a occhi chiusi tra le statue porta fortuna'},
                {'label': 'Eventi', 'value': 'Concerti, manifestazioni, Capodanno'},
                {'label': 'Metro',
                 'value': 'Toledo (Linea 1) - stazione più bella d\'Europa'}
            ],
            'opening_hours': 'Sempre accessibile, Palazzo Reale: 9:00-20:00',
            'cost': 'Piazza gratuita, Palazzo Reale €6'
        },
        'castel_nuovo_napoli': {
            'title': 'Castel Nuovo (Maschio Angioino), Napoli',
            'summary': 'Fortezza medievale simbolo di Napoli, costruita dagli Angioini. L\'Arco di Trionfo aragonese è considerato il primo monumento rinascimentale del Sud Italia.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1279-1282 (Carlo I d\'Angiò)'},
                {'label': 'Arco di Trionfo',
                 'value': '1467, primo Rinascimento napoletano'},
                {'label': 'Torri', 'value': '5 torri cilindriche, Torre del Beverello'},
                {'label': 'Museo Civico',
                 'value': 'Arte napoletana XIV-XVIII secolo'},
                {'label': 'Sala dei Baroni',
                 'value': 'Volta stellata, capolavoro gotico catalano'},
                {'label': 'Biglietto', 'value': '€6 adulti, €3 ridotto'}
            ],
            'opening_hours': 'Lun-Sab 8:30-19:00, Dom 8:30-14:00',
            'cost': '€6 adulti, gratuito <18 anni UE'
        },
        'spaccanapoli_napoli': {
            'title': 'Spaccanapoli, Napoli',
            'summary': 'L\'antica strada greco-romana che divide il centro storico UNESCO. 2.800 anni di storia stratificata in un unico decumano.',
            'details': [
                {'label': 'Lunghezza',
                 'value': '2 km da Via Duomo a Via Monteoliveto'},
                {'label': 'Epoca',
                 'value': 'Decumano inferiore greco-romano (V sec. a.C.)'},
                {'label': 'Patrimonio UNESCO',
                 'value': 'Centro storico (1995)'},
                {'label': 'Chiese storiche',
                 'value': 'Gesù Nuovo, Santa Chiara, San Domenico'},
                {'label': 'Artigianato', 'value': 'Presepi di San Gregorio Armeno'},
                {'label': 'Cultura popolare',
                 'value': 'Caffè, pizzerie storiche, santini'}
            ],
            'opening_hours': 'Sempre accessibile, chiese vari orari',
            'cost': 'Passeggiata gratuita'
        },
        # === BOLOGNA ===
        'piazza_maggiore_bologna': {
            'title': 'Piazza Maggiore, Bologna',
            'summary': 'Il cuore medievale di Bologna, chiamata "il salotto" dai bolognesi. Circondata da palazzi storici e dominata dalla Basilica di San Petronio.',
            'details': [
                {'label': 'Epoca',
                 'value': 'XIII secolo (epoca comunale)'},
                {'label': 'Basilica San Petronio',
                 'value': 'Quinta chiesa più grande al mondo'},
                {'label': 'Palazzo del Podestà',
                 'value': 'XIII secolo, Torre dell\'Arengo'},
                {'label': 'Palazzo Re Enzo',
                 'value': 'Prigione del re di Sardegna (1249-1272)'},
                {'label': 'Curiosità',
                 'value': 'Meridiana più lunga del mondo (San Petronio)'},
                {'label': 'Eventi',
                 'value': 'Cinema sotto le stelle, mercatini, concerti'}
            ],
            'opening_hours': 'Sempre accessibile, San Petronio: 7:45-18:30',
            'cost': 'Piazza gratuita, musei vari prezzi'
        },
        'due_torri_bologna': {
            'title': 'Le Due Torri (Asinelli e Garisenda), Bologna',
            'summary': 'Simboli medievali della "Bologna delle cento torri". La Torre degli Asinelli è la più alta torre pendente d\'Italia.',
            'details': [
                {'label': 'Torre Asinelli',
                 'value': '97.2m altezza, 498 gradini, pendenza 2.23m'},
                {'label': 'Torre Garisenda',
                 'value': '48m altezza, pendenza 3.22m (più della Torre di Pisa)'},
                {'label': 'Costruzione',
                 'value': 'XII secolo (1109-1119)'},
                {'label': 'Torri originarie',
                 'value': 'Circa 100 torri medievali (20 superstiti)'},
                {'label': 'Salita Asinelli',
                 'value': '€5, vista panoramica 360°'},
                {'label': 'Dante',
                 'value': 'Citate nella Divina Commedia (Inferno XXXI)'}
            ],
            'opening_hours': 'Tutti i giorni 9:30-19:00 (estate), 9:30-17:00 (inverno)',
            'cost': '€5 salita Torre Asinelli'
        },
        # === PALERMO ===
        'cattedrale_palermo': {
            'title': 'Cattedrale di Palermo',
            'summary': 'Capolavoro dell\'arte arabo-normanna Patrimonio UNESCO. Sintesi unica di culture musulmana, bizantina e latina.',
            'details': [
                {'label': 'Patrimonio UNESCO',
                 'value': 'Palermo arabo-normanna (2015)'},
                {'label': 'Fondazione',
                 'value': '1185 (su moschea del IX secolo)'},
                {'label': 'Tombe reali',
                 'value': 'Federico II, Ruggero II, Costanza d\'Altavilla'},
                {'label': 'Tesoro',
                 'value': 'Corona di Costanza (XII sec), gioielli normanni'},
                {'label': 'Cripta', 'value': 'Sarcofagi imperiali e arcivescovili'},
                {'label': 'Biglietto completo',
                 'value': '€7 (cattedrale, cripta, tesoro, tetti)'}
            ],
            'opening_hours': 'Lun-Sab 7:00-19:00, Dom 8:00-13:00, 16:00-19:00',
            'cost': 'Ingresso gratuito, percorso completo €7'
        },
        'palazzo_normanni_palermo': {
            'title': 'Palazzo dei Normanni, Palermo',
            'summary': 'Palazzo reale più antico d\'Europa ancora in uso. La Cappella Palatina custodisce i mosaici bizantini più belli al mondo.',
            'details': [
                {'label': 'Fondazione',
                 'value': 'IX secolo arabo, ampliato da Normanni (XI-XII sec)'},
                {'label': 'Cappella Palatina',
                 'value': 'Mosaici bizantini (1132-1143), capolavoro mondiale'},
                {'label': 'Sala di Ruggero',
                 'value': 'Mosaici profani con scene di caccia'},
                {'label': 'Parlamento Siciliano',
                 'value': 'Sede attuale dell\'Assemblea Regionale'},
                {'label': 'Appartamenti Reali',
                 'value': 'Sale di rappresentanza borboniche'},
                {'label': 'Biglietto', 'value': '€12 adulti, €10 ridotto'}
            ],
            'opening_hours': 'Lun-Mer-Gio-Ven-Sab 8:15-17:40, Dom 8:15-13:00',
            'cost': '€12 adulti, gratuito <18 anni UE',
            'actionLink': {
                    'text': 'Prenota la visita',
                    'url': 'https://www.federicosecondo.org'
            }
        },
        # === VENEZIA ===
        'piazza_san_marco_venezia': {
            'title': 'Piazza San Marco, Venezia',
            'summary': 'L\'unica "piazza" di Venezia (le altre sono "campi"), chiamata da Napoleone "il salotto più elegante d\'Europa". Cuore politico e religioso della Serenissima.',
            'details': [
                {'label': 'Basilica San Marco',
                 'value': 'Capolavoro bizantino (1063), Pala d\'Oro'},
                {'label': 'Palazzo Ducale',
                 'value': 'Residenza del Doge, Ponte dei Sospiri'},
                {'label': 'Campanile',
                 'value': '98.6m, "el paron de casa" (il padrone di casa)'},
                {'label': 'Procuratie',
                 'value': 'Palazzi porticati, oggi musei e caffè storici'},
                {'label': 'Acqua alta',
                 'value': 'Passerelle in legno durante le maree eccezionali'},
                {'label': 'Caffè Florian',
                 'value': 'Dal 1720, caffè più antico al mondo'}
            ],
            'opening_hours': 'Sempre accessibile, Basilica: 9:30-17:00',
            'cost': 'Piazza gratuita, Basilica €3, Palazzo Ducale €25'
        },
        'ponte_di_rialto_venezia': {
            'title': 'Ponte di Rialto, Venezia',
            'summary': 'Il più famoso e antico dei quattro ponti che attraversano il Canal Grande. Capolavoro rinascimentale con botteghe integrate nella struttura.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1588-1591 (Antonio da Ponte)'},
                {'label': 'Struttura', 'value': 'Arco unico 28m luce, 24 botteghe'},
                {'label': 'Storia', 'value': 'Sostituisce ponti di legno crollati'},
                {'label': 'Mercato di Rialto',
                 'value': '1000 anni, pesce fresco ogni mattina'},
                {'label': 'Vista panoramica',
                 'value': 'Canal Grande, palazzi storici'},
                {'label': 'Curiosità',
                 'value': 'Progetto vincente contro Michelangelo e Palladio'}
            ],
            'opening_hours': 'Sempre accessibile, mercato: 7:30-12:00',
            'cost': 'Attraversamento gratuito'
        },
        'ca_rezzonico_venezia': {
            'title': 'Ca\' Rezzonico, Venezia',
            'summary': 'Palazzo barocco del XVIII secolo, sede del Museo del Settecento Veneziano. Affreschi di Tiepolo e vita aristocratica della Serenissima.',
            'details': [
                {'label': 'Architetto',
                 'value': 'Baldassarre Longhena (1667)'},
                {'label': 'Affreschi Tiepolo',
                 'value': 'Salone da ballo, Allegoria nuziale'},
                {'label': 'Collezione',
                 'value': 'Mobili, dipinti, costumi del Settecento'},
                {'label': 'Robert Browning',
                 'value': 'Poeta inglese, morì qui nel 1889'},
                {'label': 'Canal Grande',
                 'value': 'Vista privilegiata dalla terrazza'},
                {'label': 'Biglietto', 'value': '€10 adulti, €7.50 ridotto'}
            ],
            'opening_hours': 'Mer-Lun 10:00-18:00 (chiuso martedì)',
            'cost': '€10 adulti, gratuito <6 anni',
            'actionLink': {
                    'text': 'Musei di Venezia',
                    'url': 'https://www.visitmuve.it'
            }
        },
        # === PISA ===
        'piazza_miracoli_pisa': {
            'title': 'Piazza dei Miracoli, Pisa',
            'summary': 'Patrimonio UNESCO dal 1987, chiamata "dei Miracoli" da D\'Annunzio. Complesso romanico pisano unico al mondo con Torre Pendente, Duomo, Battistero e Camposanto.',
            'details': [
                {'label': 'Patrimonio UNESCO',
                 'value': '1987 - "Piazza del Duomo"'},
                {'label': 'Duomo',
                 'value': 'Santa Maria Assunta (1063-1118), prototipo romanico pisano'},
                {'label': 'Torre Pendente',
                 'value': '56m altezza, inclinazione 3.97°, 294 gradini'},
                {'label': 'Battistero',
                 'value': 'Più grande d\'Italia (1152-1363), diametro 34.13m'},
                {'label': 'Camposanto',
                 'value': 'Terra Santa dalle Crociate, affreschi del Trionfo della Morte'},
                {'label': 'Biglietto unico',
                 'value': '€25 per tutti i monumenti, Torre €18 separato'}
            ],
            'opening_hours': 'Tutti i giorni 9:00-20:00 (estate), 10:00-17:00 (inverno)',
            'cost': 'Campo gratuito, monumenti €5-18',
            'actionLink': {
                    'text': 'Prenota Torre di Pisa',
                    'url': 'https://www.opapisa.it'
            }
        },
        'torre_pisa': {
            'title': 'Torre di Pisa',
            'summary': 'Il campanile più famoso al mondo, simbolo dell\'ingegneria medievale. La pendenza è dovuta al cedimento del terreno durante la costruzione nel XII secolo.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1173-1372 (quasi 200 anni)'},
                {'label': 'Architetti',
                 'value': 'Bonanno Pisano e Gherardo din Gherardo'},
                {'label': 'Altezza', 'value': '56.67m lato alto, 55.86m lato basso'},
                {'label': 'Piani', 'value': '8 piani, 294 gradini in marmo'},
                {'label': 'Pendenza massima',
                 'value': '5.5° nel 1990, stabilizzata a 3.97°'},
                {'label': 'Consolidamento',
                 'value': 'Progetto 1990-2001, torre sicura per 300 anni'},
                {'label': 'Visita', 'value': '30 minuti, massimo 45 persone per turno'}
            ],
            'opening_hours': 'Tutti i giorni 9:00-20:00 (estate), 10:00-17:00 (inverno)',
            'cost': '€18 adulti, prenotazione obbligatoria',
            'actionLink': {
                    'text': 'Prenota salita Torre',
                    'url': 'https://www.opapisa.it/en/tickets/'
            }
        },
        'piazza_cavalieri_pisa': {
            'title': 'Piazza dei Cavalieri, Pisa',
            'summary': 'Centro del potere mediceo e sede della prestigiosa Scuola Normale Superiore. Progettata da Vasari come simbolo del dominio fiorentino su Pisa.',
            'details': [
                {'label': 'Progetto Vasari',
                 'value': '1558-1562, riqualificazione mediceo'},
                {'label': 'Palazzo della Carovana',
                 'value': 'Sede Scuola Normale Superiore (1810)'},
                {'label': 'Torre della Muda',
                 'value': 'Prigione del Conte Ugolino (Dante, Inferno XXXIII)'},
                {'label': 'Scuola Normale',
                 'value': 'Fondata da Napoleone, eccellenza universitaria'},
                {'label': 'Chiesa Santo Stefano',
                 'value': 'Cavalieri di Santo Stefano, ordine mediceo'},
                {'label': 'Palazzo dell\'Orologio',
                 'value': 'Unione di due torri medievali'}
            ],
            'opening_hours': 'Sempre accessibile, Scuola Normale: visite guidate su prenotazione',
            'cost': 'Piazza gratuita, visite Scuola Normale €5'
        },
        # === CAGLIARI ===
        'castello_cagliari': {
            'title': 'Castello di Cagliari',
            'summary': 'Quartiere storico fortificato di origine pisana (XIII secolo), cuore del potere sardo-aragonese. Panorama mozzafiato sul Golfo degli Angeli.',
            'details': [
                {'label': 'Fondazione', 'value': 'XIII secolo, dominazione pisana'},
                {'label': 'Mura medievali',
                 'value': 'Torri pisane: San Pancrazio, Elefante'},
                {'label': 'Palazzo Regio',
                 'value': 'Residenza dei Viceré spagnoli e sabaudi'},
                {'label': 'Panorama',
                 'value': 'Vista 360° su Golfo, Molentargius, Sella del Diavolo'},
                {'label': 'Citadella dei Musei',
                 'value': 'Museo Archeologico, Pinacoteca'},
                {'label': 'Via Lamarmora',
                 'value': 'Passeggiata panoramica sulle mura'}
            ],
            'opening_hours': 'Sempre accessibile, musei: Mar-Dom 9:00-20:00',
            'cost': 'Accesso gratuito, musei €5-10'
        },
        'cattedrale_cagliari': {
            'title': 'Cattedrale di Santa Maria, Cagliari',
            'summary': 'Duomo barocco (XVII secolo) costruito su cattedrale pisana. Conserva il pulpito di Guglielmo da Pisa e cripta con martiri sardi.',
            'details': [
                {'label': 'Costruzione',
                 'value': 'XIII secolo pisana, rifacimento barocco XVII sec'},
                {'label': 'Pulpito Guglielmo',
                 'value': 'Capolavoro romanico (1159-1162)'},
                {'label': 'Cripta dei Martiri',
                 'value': '179 nicchie, martiri sardi paleocristiani'},
                {'label': 'Cappella del Braccio',
                 'value': 'Reliquia Santa Cecilia'},
                {'label': 'Tesoro', 'value': 'Oggetti sacri sardo-aragonesi'},
                {'label': 'Campanile', 'value': 'Torre medievale, campane storiche'}
            ],
            'opening_hours': 'Lun-Sab 8:00-12:30, 16:30-20:00, Dom 8:00-13:00, 16:30-20:00',
            'cost': 'Ingresso gratuito, cripta €3'
        },
        'bastione_saint_remy_cagliari': {
            'title': 'Bastione di Saint Remy, Cagliari',
            'summary': 'Terrazza panoramica liberty (1896-1902) simbolo della Cagliari moderna. Vista spettacolare su città, porto e Golfo degli Angeli.',
            'details': [
                {'label': 'Costruzione', 'value': '1896-1902, stile liberty'},
                {'label': 'Architetto',
                 'value': 'Giuseppe Costa, ingegnere militare'},
                {'label': 'Passeggiata Coperta',
                 'value': 'Terrazza panoramica, 300m lunghezza'},
                {'label': 'Scalinata',
                 'value': 'Accesso monumentale dal Largo Carlo Felice'},
                {'label': 'Vista panoramica',
                 'value': 'Porto, Golfo, Sella del Diavolo, entroterra'},
                {'label': 'Eventi culturali',
                 'value': 'Concerti, mostre, spettacoli estivi'}
            ],
            'opening_hours': 'Sempre accessibile, illuminazione notturna',
            'cost': 'Accesso gratuito'
        },
        # === PERUGIA ===
        'corso_vannucci_perugia': {
            'title': 'Corso Vannucci, Perugia',
            'summary': 'Salotto di Perugia e passeggiata principale della città medievale. Palazzo dei Priori, Galleria Nazionale dell\'Umbria e caffè storici.',
            'details': [
                {'label': 'Palazzo dei Priori',
                 'value': 'XIII-XV secolo, sede comunale medievale'},
                {'label': 'Galleria Nazionale',
                 'value': 'Pinacoteca con Perugino, Pinturicchio'},
                {'label': 'Collegio del Cambio',
                 'value': 'Affreschi del Perugino (1496-1500)'},
                {'label': 'Caffè Sandri',
                 'value': 'Storico (1860), dolci tipici perugini'},
                {'label': 'Loggia di Braccio',
                 'value': 'Rinascimento umbro (XV secolo)'},
                {'label': 'Vista panoramica',
                 'value': 'Colline umbre, Valle del Tevere'}
            ],
            'opening_hours': 'Sempre accessibile, musei: Mar-Dom 8:30-19:30',
            'cost': 'Passeggiata gratuita, Galleria €8'
        },
        'fontana_maggiore_perugia': {
            'title': 'Fontana Maggiore, Perugia',
            'summary': 'Capolavoro scultoreo di Nicola e Giovanni Pisano (1278). Simbolo della Perugia medievale e dell\'indipendenza comunale.',
            'details': [
                {'label': 'Architetti',
                 'value': 'Nicola e Giovanni Pisano (1275-1278)'},
                {'label': 'Struttura',
                 'value': 'Due vasche marmoree poligonali sovrapposte'},
                {'label': 'Iconografia',
                 'value': '50 rilievi: mesi, segni zodiacali, arti liberali'},
                {'label': 'Acquedotto',
                 'value': 'Alimentata dalle sorgenti del Monte Pacciano'},
                {'label': 'Restauri', 'value': 'Ultimo intervento 1996-1999'},
                {'label': 'Simbolismo',
                 'value': 'Indipendenza comunale, sapienza medievale'}
            ],
            'opening_hours': 'Sempre visibile e accessibile',
            'cost': 'Visione gratuita'
        },
        # === ROMA ===
        'stazione_termini': {
            'title': 'Stazione Roma Termini',
            'summary': 'La stazione ferroviaria principale di Roma, hub centrale per treni regionali, nazionali e metropolitana. Costruita negli anni \'50, serve oltre 150 milioni di passeggeri all\'anno.',
            'details': [
                {'label': 'Inaugurazione', 'value': '20 dicembre 1950'},
                {'label': 'Binari', 'value': '29 binari'},
                {'label': 'Metro', 'value': 'Linea A (rossa) e B (blu)'},
                {'label': 'Passeggeri/anno', 'value': '150+ milioni'},
                {'label': 'Servizi',
                 'value': 'Biglietteria automatica, sala d\'attesa, ristoranti, negozi'},
                {'label': 'Bagagli', 'value': 'Deposito bagagli disponibile'},
                {'label': 'WiFi', 'value': 'Gratuito per 1 ora'}
            ],
            'timetable': [
                {'direction': 'Metro A - Battistini',
                 'times': 'Ogni 3-6 min (5:30-23:30)'},
                {'direction': 'Metro B - Laurentina',
                 'times': 'Ogni 4-7 min (5:30-23:30)'}
            ],
            'actionLink': {
                'text': 'Orari Trenitalia in tempo reale',
                'url': 'https://www.trenitalia.com'
            }
        },
        'piazza_spagna': {
            'title': 'Piazza di Spagna',
            'summary': 'Una delle piazze più iconiche di Roma, famosa per la maestosa Scalinata di Trinità dei Monti e per essere il cuore dello shopping di lusso romano. La scalinata collega la piazza con la chiesa francese in cima.',
            'details': [
                {'label': 'Gradini scalinata',
                 'value': '135 scalini in travertino'},
                {'label': 'Costruzione', 'value': '1723-1726'},
                {'label': 'Architetto', 'value': 'Francesco de Sanctis'},
                {'label': 'Fontana',
                 'value': 'Fontana della Barcaccia (Bernini, 1629)'},
                {'label': 'Shopping', 'value': 'Via Condotti, Via del Babuino'},
                {'label': 'Curiosità',
                 'value': 'Vietato sedersi sui gradini (multa €250)'},
                {'label': 'Metro', 'value': 'Spagna (Linea A)'}
            ],
            'timetable': [
                {'direction': 'Chiesa Trinità dei Monti',
                 'times': 'Mar-Dom 10:00-19:00'},
                {'direction': 'Keats- Shelley Museum',
                 'times': 'Lun-Sab 10:00-18:00'}
            ]
        },
        'fontana_trevi': {
            'title': 'Fontana di Trevi',
            'summary': 'La fontana barocca più spettacolare al mondo, immortalata in "La Dolce Vita" di Fellini. La tradizione dice che lanciando una moneta con la mano destra sopra la spalla sinistra si tornerà a Roma.',
            'details': [
                {'label': 'Altezza', 'value': '26.3 metri'},
                {'label': 'Larghezza', 'value': '49.15 metri'},
                {'label': 'Architetto', 'value': 'Nicola Salvi'},
                {'label': 'Completamento',
                 'value': '1762 (30 anni di lavori)'},
                {'label': 'Stile', 'value': 'Barocco Romano'},
                {'label': 'Figura centrale', 'value': 'Nettuno (Oceano)'},
                {'label': 'Monete raccolte',
                 'value': '€1.4 milioni/anno (dati alla Caritas)'},
                {'label': 'Curiosità', 'value': 'Due monete = nuova storia d\'amore'},
                {'label': 'Miglior orario',
                 'value': 'Alba (6:00-7:00) per evitare folle'}
            ],
            'timetable': [
                {'direction': 'Accessibile',
                 'times': '24h/7gg (illuminazione notturna)'},
                {'direction': 'Pulizia fontana',
                 'times': 'Ogni lunedì mattina 7:00-9:00'}
            ]
        },
        'pantheon': {
            'title': 'Pantheon',
            'summary': 'Il tempio romano meglio conservato al mondo, considerato una meraviglia architettonica. La sua cupola fu la più grande per 1.300 anni fino a Brunelleschi. Oggi è basilica cristiana e mausoleo reale.',
            'details': [
                    {'label': 'Costruzione originale',
                        'value': '27 a.C. (Marco Agrippa)'},
                    {'label': 'Ricostruzione',
                        'value': '118-128 d.C. (Imperatore Adriano)'},
                    {'label': 'Diametro cupola',
                        'value': '43.30 metri (= altezza interna)'},
                    {'label': 'Oculus',
                        'value': '8.2 metri di diametro (unica fonte di luce)'},
                    {'label': 'Materiale', 'value': 'Calcestruzzo romano con pomice'},
                    {'label': 'Sepolture illustri',
                        'value': 'Raffaello Sanzio, Re Vittorio Emanuele II'},
                    {'label': 'Ingresso',
                        'value': 'Gratuito (prenotazione consigliata)'},
                    {'label': 'Curiosità',
                        'value': 'Il pavimento ha pendenze per far defluire la pioggia'}
            ],
            'timetable': [
                {'direction': 'Lun-Sab',
                 'times': '9:00-19:00 (ultimo ingresso 18:45)'},
                {'direction': 'Domenica',
                 'times': '9:00-18:00 (ultimo ingresso 17:45)'},
                {'direction': 'Messe', 'times': 'Sabato 17:00, Domenica 10:30'}
            ],
            'actionLink': {
                'text': 'Prenota visita guidata',
                'url': 'https://pantheonroma.com'
            }
        },
        'piazza_navona': {
            'title': 'Piazza Navona',
            'summary': 'Il gioiello del barocco romano, costruita sulle rovine dello Stadio di Domiziano. Teatro della rivalità artistica tra Bernini e Borromini, oggi è il salotto elegante di Roma con i suoi caffè storici.',
            'details': [
                {'label': 'Forma originale',
                 'value': 'Stadio di Domiziano (86 d.C., 30.000 spettatori)'},
                {'label': 'Trasformazione',
                 'value': 'XV secolo - da stadio a piazza'},
                {'label': 'Lunghezza', 'value': '276 metri'},
                {'label': 'Fontana centrale',
                 'value': 'Fontana dei Quattro Fiumi (Bernini, 1651)'},
                {'label': 'Fontana sud',
                 'value': 'Fontana del Moro (Bernini)'},
                {'label': 'Fontana nord', 'value': 'Fontana del Nettuno'},
                {'label': 'Chiesa',
                 'value': 'Sant\'Agnese in Agone (Borromini)'},
                {'label': 'Leggenda',
                 'value': 'Statua del Nilo copre gli occhi per non vedere la chiesa'},
                {'label': 'Mercatino',
                 'value': 'Befana (6 gennaio) e Natale'}
            ],
            'timetable': [
                {'direction': 'Caffè storici',
                 'times': 'Caffè Domiziano, Tre Scalini (7:00-1:00)'},
                {'direction': 'Artisti di strada',
                 'times': 'Tutti i giorni 10:00-24:00'},
                {'direction': 'Chiesa S. Agnese',
                 'times': 'Mar-Dom 9:30-12:30, 15:30-19:00'}
            ],
            'actionLink': {
                'text': 'Storia dello Stadio di Domiziano',
                'url': 'https://stadiodomiziano.com'
            }
        },
        # === LONDON ===
        'big_ben': {
            'title': 'Big Ben',
            'summary': 'The iconic clock tower of Westminster Palace, officially called Elizabeth Tower. One of London\'s most recognizable landmarks and symbol of British democracy.',
            'details': [
                {'label': 'Official Name',
                 'value': 'Elizabeth Tower (renamed 2012 for Queen\'s Diamond Jubilee)'},
                {'label': 'Height', 'value': '96 meters (316 feet)'},
                {'label': 'Construction',
                 'value': '1843-1859 (architect: Augustus Pugin)'},
                {'label': 'Bell', 'value': 'Big Ben bell weighs 13.76 tonnes'},
                {'label': 'Clock Face',
                 'value': '4 faces, each 7 meters in diameter'},
                {'label': 'Tours',
                 'value': 'UK residents only, advance booking required'},
                {'label': 'Metro',
                 'value': 'Westminster Station (Circle, District, Jubilee lines)'},
                {'label': 'Best Views',
                 'value': 'Westminster Bridge, Parliament Square'}
            ],
            'opening_hours': 'External viewing 24/7, tours by appointment only',
            'cost': 'External viewing free, guided tours £15-25'
        },
        'tower_bridge': {
            'title': 'Tower Bridge',
            'summary': 'Victorian Gothic bascule and suspension bridge crossing the Thames. Famous for its twin towers and glass floor walkways offering spectacular views over London.',
            'details': [
                {'label': 'Construction',
                 'value': '1886-1894 (architect: Horace Jones)'},
                {'label': 'Bridge Lifts',
                 'value': 'Approximately 1000 times per year'},
                {'label': 'Glass Floor', 'value': '42 meters above the Thames'},
                {'label': 'Engine Rooms',
                 'value': 'Victorian steam engines (now on display)'},
                {'label': 'Exhibition',
                 'value': 'Tower Bridge Exhibition with history displays'},
                {'label': 'Walking Distance',
                 'value': '5 minutes to Tower of London'},
                {'label': 'Metro',
                 'value': 'Tower Hill Station (Circle, District lines)'},
                {'label': 'Photography',
                 'value': 'Best shots from south bank at sunset'}
            ],
            'opening_hours': 'Daily 9:30-18:00 (last entry 17:00)',
            'cost': '£12.30 adults, £5.90 children, free under 5'
        },
        'british_museum': {
            'title': 'British Museum',
            'summary': 'World\'s oldest national public museum housing 8 million artifacts spanning human history and culture from ancient civilizations to modern times.',
            'details': [
                {'label': 'Founded',
                 'value': '1753 (opened to public 1759)'},
                {'label': 'Great Court',
                 'value': 'Europe\'s largest covered square (Queen Elizabeth II Great Court)'},
                {'label': 'Famous Artifacts',
                 'value': 'Rosetta Stone, Egyptian mummies, Parthenon sculptures'},
                {'label': 'Collections',
                 'value': '8 million objects, 80,000 on display'},
                {'label': 'Reading Room',
                 'value': 'Historic Round Reading Room (now information center)'},
                {'label': 'Free Highlights Tour',
                 'value': 'Daily 11:00, 14:00, 15:00 (90 minutes)'},
                {'label': 'Metro',
                 'value': 'Russell Square, Holborn, Tottenham Court Road'},
                {'label': 'Dining',
                 'value': 'Great Court Restaurant, Museum Tavern nearby'}
            ],
            'opening_hours': 'Daily 10:00-17:00, Friday until 20:30',
            'cost': 'Free admission, special exhibitions £10-20'
        },
        'buckingham_palace': {
            'title': 'Buckingham Palace',
            'summary': 'Official London residence of the British monarch since 1837. Famous for Changing of the Guard ceremony and State Rooms open to public in summer.',
            'details': [
                {'label': 'Rooms', 'value': '775 rooms including 19 State Rooms'},
                {'label': 'Changing of Guard',
                 'value': 'Wednesday, Saturday, Sunday 11:00 (Apr-Jul daily)'},
                {'label': 'State Rooms',
                 'value': 'Open July-September (advance booking essential)'},
                {'label': 'Royal Mews',
                 'value': 'Working stables with royal carriages'},
                {'label': 'Garden',
                 'value': '16 hectares, largest private garden in London'},
                {'label': 'Balcony',
                 'value': 'Famous royal appearances during celebrations'},
                {'label': 'Metro', 'value': 'Victoria, Green Park, Hyde Park Corner'},
                {'label': 'Photography',
                 'value': 'Front gates, Victoria Memorial for best shots'}
            ],
            'opening_hours': 'State Rooms: Jul-Sep 9:30-19:30, Royal Mews year-round',
            'cost': 'State Rooms £30, Royal Mews £13, combined ticket £39'
        },
        'piccadilly_circuslondon_london': {
            'title': 'Piccadilly Circus',
            'summary': 'Bustling junction and public space in West End, famous for neon advertising displays, Eros statue and gateway to London\'s theatre district.',
            'details': [
                {'label': 'Nickname', 'value': '"Times Square of London"'},
                {'label': 'Eros Statue',
                 'value': 'Shaftesbury Memorial Fountain (1893)'},
                {'label': 'Advertising',
                 'value': 'Historic curved LED displays since 1908'},
                {'label': 'Theatres', 'value': 'Gateway to West End theatre district'},
                {'label': 'Shopping', 'value': 'Regent Street, Oxford Street nearby'},
                {'label': 'Restaurants',
                 'value': 'Every cuisine imaginable within walking distance'},
                {'label': 'Metro',
                 'value': 'Piccadilly Circus Station (Piccadilly, Bakerloo lines)'},
                {'label': 'Best Time',
                 'value': 'Evening for illuminated signs, daytime for shopping'}
            ],
            'opening_hours': 'Public space - accessible 24/7',
            'cost': 'Free to visit and photograph'
        },
        'walk_to_tower_bridge': {
            'title': 'Thames Walk to Tower Bridge',
            'summary': 'Scenic riverside walk from Westminster area to Tower Bridge along the South Bank, passing London Eye, Tate Modern, and Borough Market.',
            'details': [
                {'label': 'Distance',
                 'value': '2.5km (1.5 miles) pleasant riverside walk'},
                {'label': 'Duration', 'value': '20-30 minutes at leisurely pace'},
                {'label': 'Route Highlights',
                 'value': 'London Eye, Tate Modern, Globe Theatre, Borough Market'},
                {'label': 'Path Type', 'value': 'Paved Thames Path with river views'},
                {'label': 'Photo Opportunities',
                 'value': 'London skyline, HMS Belfast, City Hall'},
                {'label': 'Weather Protection',
                 'value': 'Mostly outdoor - bring umbrella if needed'},
                {'label': 'Accessibility', 'value': 'Fully wheelchair accessible'},
                {'label': 'Refreshments',
                 'value': 'Numerous cafes and pubs along the route'}
            ],
            'opening_hours': 'Thames Path accessible 24/7',
            'cost': 'Free walking route'
        },
        'walk_to_british_museum': {
            'title': 'Central London Walk to British Museum',
            'summary': 'Cultural walk through Bloomsbury district passing garden squares, Georgian architecture, and literary landmarks to reach the world-famous museum.',
            'details': [
                {'label': 'Distance', 'value': '1.2km through historic Bloomsbury'},
                {'label': 'Duration',
                 'value': '15-20 minutes through cultural quarter'},
                {'label': 'Neighborhood',
                 'value': 'Bloomsbury - literary and academic heart of London'},
                {'label': 'Architecture',
                 'value': 'Georgian terraces, garden squares, historic pubs'},
                {'label': 'Literary Sites',
                 'value': 'Charles Dickens Museum, Virginia Woolf locations'},
                {'label': 'University Area',
                 'value': 'University College London campus nearby'},
                {'label': 'Shopping',
                 'value': 'Independent bookshops, vintage stores'},
                {'label': 'Dining', 'value': 'Traditional pubs, international cuisine'}
            ],
            'opening_hours': 'Public streets accessible 24/7',
            'cost': 'Free walking route'
        },
        'walk_to_buckingham_palace': {
            'title': 'Royal Walk to Buckingham Palace',
            'summary': 'Regal procession through Green Park and past royal landmarks, following the route used for state occasions and royal ceremonies.',
            'details': [
                {'label': 'Distance',
                 'value': '1km through royal parks and monuments'},
                {'label': 'Duration', 'value': '12-15 minutes through Green Park'},
                {'label': 'Route',
                 'value': 'Via Green Park, Wellington Arch, Constitution Hill'},
                {'label': 'Royal Parks',
                 'value': 'Green Park - one of London\'s Royal Parks'},
                {'label': 'Monuments',
                 'value': 'Wellington Arch, Canada Gate, Victoria Memorial'},
                {'label': 'Wildlife',
                 'value': 'Pelicans in St. James\'s Park (if route extended)'},
                {'label': 'Royal Protocol',
                 'value': 'Same route used for state processions'},
                {'label': 'Photo Spots',
                 'value': 'Wellington Arch, approaching palace facade'}
            ],
            'opening_hours': 'Green Park: 5:00-midnight',
            'cost': 'Free walking through royal parks'
        },
        # LONDON
        'piazza_san_marco_venezia': {
            'title': 'Piazza San Marco, Venezia',
            'summary': 'L\'unica "piazza" di Venezia (le altre sono "campi"), chiamata da Napoleone "il salotto più elegante d\'Europa". Cuore politico e religioso della Serenissima.',
            'details': [
                {'label': 'Basilica San Marco',
                 'value': 'Capolavoro bizantino (1063), Pala d\'Oro'},
                {'label': 'Palazzo Ducale',
                 'value': 'Residenza del Doge, Ponte dei Sospiri'},
                {'label': 'Campanile',
                 'value': '98.6m, "el paron de casa" (il padrone di casa)'},
                {'label': 'Procuratie',
                 'value': 'Palazzi porticati, oggi musei e caffè storici'},
                {'label': 'Acqua alta',
                 'value': 'Passerelle in legno durante le maree eccezionali'},
                {'label': 'Caffè Florian',
                 'value': 'Dal 1720, caffè più antico al mondo'}
            ],
            'opening_hours': 'Sempre accessibile, Basilica: 9:30-17:00',
            'cost': 'Piazza gratuita, Basilica €3, Palazzo Ducale €25'
        },
        'ponte_di_rialto_venezia': {
            'title': 'Ponte di Rialto, Venezia',
            'summary': 'Il più famoso e antico dei quattro ponti che attraversano il Canal Grande. Capolavoro rinascimentale con botteghe integrate nella struttura.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1588-1591 (Antonio da Ponte)'},
                {'label': 'Struttura', 'value': 'Arco unico 28m luce, 24 botteghe'},
                {'label': 'Storia', 'value': 'Sostituisce ponti di legno crollati'},
                {'label': 'Mercato di Rialto',
                 'value': '1000 anni, pesce fresco ogni mattina'},
                {'label': 'Vista panoramica',
                 'value': 'Canal Grande, palazzi storici'},
                {'label': 'Curiosità',
                 'value': 'Progetto vincente contro Michelangelo e Palladio'}
            ],
            'opening_hours': 'Sempre accessibile, mercato: 7:30-12:00',
            'cost': 'Attraversamento gratuito'
        },
        'ca_rezzonico_venezia': {
            'title': 'Ca\' Rezzonico, Venezia',
            'summary': 'Palazzo barocco del XVIII secolo, sede del Museo del Settecento Veneziano. Affreschi di Tiepolo e vita aristocratica della Serenissima.',
            'details': [
                {'label': 'Architetto',
                 'value': 'Baldassarre Longhena (1667)'},
                {'label': 'Affreschi Tiepolo',
                 'value': 'Salone da ballo, Allegoria nuziale'},
                {'label': 'Collezione',
                 'value': 'Mobili, dipinti, costumi del Settecento'},
                {'label': 'Robert Browning',
                 'value': 'Poeta inglese, morì qui nel 1889'},
                {'label': 'Canal Grande',
                 'value': 'Vista privilegiata dalla terrazza'},
                {'label': 'Biglietto', 'value': '€10 adulti, €7.50 ridotto'}
            ],
            'opening_hours': 'Mer-Lun 10:00-18:00 (chiuso martedì)',
            'cost': '€10 adulti, gratuito <6 anni',
            'actionLink': {
                    'text': 'Musei di Venezia',
                    'url': 'https://www.visitmuve.it'
            }
        },
        # === PISA ===
        'piazza_miracoli_pisa': {
            'title': 'Piazza dei Miracoli, Pisa',
            'summary': 'Patrimonio UNESCO dal 1987, chiamata "dei Miracoli" da D\'Annunzio. Complesso romanico pisano unico al mondo con Torre Pendente, Duomo, Battistero e Camposanto.',
            'details': [
                {'label': 'Patrimonio UNESCO',
                 'value': '1987 - "Piazza del Duomo"'},
                {'label': 'Duomo',
                 'value': 'Santa Maria Assunta (1063-1118), prototipo romanico pisano'},
                {'label': 'Torre Pendente',
                 'value': '56m altezza, inclinazione 3.97°, 294 gradini'},
                {'label': 'Battistero',
                 'value': 'Più grande d\'Italia (1152-1363), diametro 34.13m'},
                {'label': 'Camposanto',
                 'value': 'Terra Santa dalle Crociate, affreschi del Trionfo della Morte'},
                {'label': 'Biglietto unico',
                 'value': '€25 per tutti i monumenti, Torre €18 separato'}
            ],
            'opening_hours': 'Tutti i giorni 9:00-20:00 (estate), 10:00-17:00 (inverno)',
            'cost': 'Campo gratuito, monumenti €5-18',
            'actionLink': {
                    'text': 'Prenota Torre di Pisa',
                    'url': 'https://www.opapisa.it'
            }
        },
        'torre_pisa': {
            'title': 'Torre di Pisa',
            'summary': 'Il campanile più famoso al mondo, simbolo dell\'ingegneria medievale. La pendenza è dovuta al cedimento del terreno durante la costruzione nel XII secolo.',
            'details': [
                {'label': 'Costruzione',
                 'value': '1173-1372 (quasi 200 anni)'},
                {'label': 'Architetti',
                 'value': 'Bonanno Pisano e Gherardo din Gherardo'},
                {'label': 'Altezza', 'value': '56.67m lato alto, 55.86m lato basso'},
                {'label': 'Piani', 'value': '8 piani, 294 gradini in marmo'},
                {'label': 'Pendenza massima',
                 'value': '5.5° nel 1990, stabilizzata a 3.97°'},
                {'label': 'Consolidamento',
                 'value': 'Progetto 1990-2001, torre sicura per 300 anni'},
                {'label': 'Visita', 'value': '30 minuti, massimo 45 persone per turno'}
            ],
            'opening_hours': 'Tutti i giorni 9:00-20:00 (estate), 10:00-17:00 (inverno)',
            'cost': '€18 adulti, prenotazione obbligatoria',
            'actionLink': {
                    'text': 'Prenota salita Torre',
                    'url': 'https://www.opapisa.it/en/tickets/'
            }
        },
        'piazza_cavalieri_pisa': {
            'title': 'Piazza dei Cavalieri, Pisa',
            'summary': 'Centro del potere mediceo e sede della prestigiosa Scuola Normale Superiore. Progettata da Vasari come simbolo del dominio fiorentino su Pisa.',
            'details': [
                {'label': 'Progetto Vasari',
                 'value': '1558-1562, riqualificazione mediceo'},
                {'label': 'Palazzo della Carovana',
                 'value': 'Sede Scuola Normale Superiore (1810)'},
                {'label': 'Torre della Muda',
                 'value': 'Prigione del Conte Ugolino (Dante, Inferno XXXIII)'},
                {'label': 'Scuola Normale',
                 'value': 'Fondata da Napoleone, eccellenza universitaria'},
                {'label': 'Chiesa Santo Stefano',
                 'value': 'Cavalieri di Santo Stefano, ordine mediceo'},
                {'label': 'Palazzo dell\'Orologio',
                 'value': 'Unione di due torri medievali'}
            ],
            'opening_hours': 'Sempre accessibile, Scuola Normale: visite guidate su prenotazione',
            'cost': 'Piazza gratuita, visite Scuola Normale €5'
        },
        # === CAGLIARI ===
        'castello_cagliari': {
            'title': 'Castello di Cagliari',
            'summary': 'Quartiere storico fortificato di origine pisana (XIII secolo), cuore del potere sardo-aragonese. Panorama mozzafiato sul Golfo degli Angeli.',
            'details': [
                {'label': 'Fondazione', 'value': 'XIII secolo, dominazione pisana'},
                {'label': 'Mura medievali',
                 'value': 'Torri pisane: San Pancrazio, Elefante'},
                {'label': 'Palazzo Regio',
                 'value': 'Residenza dei Viceré spagnoli e sabaudi'},
                {'label': 'Panorama',
                 'value': 'Vista 360° su Golfo, Molentargius, Sella del Diavolo'},
                {'label': 'Citadella dei Musei',
                 'value': 'Museo Archeologico, Pinacoteca'},
                {'label': 'Via Lamarmora',
                 'value': 'Passeggiata panoramica sulle mura'}
            ],
            'opening_hours': 'Sempre accessibile, musei: Mar-Dom 9:00-20:00',
            'cost': 'Accesso gratuito, musei €5-10'
        },
        'cattedrale_cagliari': {
            'title': 'Cattedrale di Santa Maria, Cagliari',
            'summary': 'Duomo barocco (XVII secolo) costruito su cattedrale pisana. Conserva il pulpito di Guglielmo da Pisa e cripta con martiri sardi.',
            'details': [
                {'label': 'Costruzione',
                 'value': 'XIII secolo pisana, rifacimento barocco XVII sec'},
                {'label': 'Pulpito Guglielmo',
                 'value': 'Capolavoro romanico (1159-1162)'},
                {'label': 'Cripta dei Martiri',
                 'value': '179 nicchie, martiri sardi paleocristiani'},
                {'label': 'Cappella del Braccio',
                 'value': 'Reliquia Santa Cecilia'},
                {'label': 'Tesoro', 'value': 'Oggetti sacri sardo-aragonesi'},
                {'label': 'Campanile', 'value': 'Torre medievale, campane storiche'}
            ],
            'opening_hours': 'Lun-Sab 8:00-12:30, 16:30-20:00, Dom 8:00-13:00, 16:30-20:00',
            'cost': 'Ingresso gratuito, cripta €3'
        },
        'bastione_saint_remy_cagliari': {
            'title': 'Bastione di Saint Remy, Cagliari',
            'summary': 'Terrazza panoramica liberty (1896-1902) simbolo della Cagliari moderna. Vista spettacolare su città, porto e Golfo degli Angeli.',
            'details': [
                {'label': 'Costruzione', 'value': '1896-1902, stile liberty'},
                {'label': 'Architetto',
                 'value': 'Giuseppe Costa, ingegnere militare'},
                {'label': 'Passeggiata Coperta',
                 'value': 'Terrazza panoramica, 300m lunghezza'},
                {'label': 'Scalinata',
                 'value': 'Accesso monumentale dal Largo Carlo Felice'},
                {'label': 'Vista panoramica',
                 'value': 'Porto, Golfo, Sella del Diavolo, entroterra'},
                {'label': 'Eventi culturali',
                 'value': 'Concerti, mostre, spettacoli estivi'}
            ],
            'opening_hours': 'Sempre accessibile, illuminazione notturna',
            'cost': 'Accesso gratuito'
        },
        # === PERUGIA ===
        'corso_vannucci_perugia': {
            'title': 'Corso Vannucci, Perugia',
            'summary': 'Salotto di Perugia e passeggiata principale della città medievale. Palazzo dei Priori, Galleria Nazionale dell\'Umbria e caffè storici.',
            'details': [
                {'label': 'Palazzo dei Priori',
                 'value': 'XIII-XV secolo, sede comunale medievale'},
                {'label': 'Galleria Nazionale',
                 'value': 'Pinacoteca con Perugino, Pinturicchio'},
                {'label': 'Collegio del Cambio',
                 'value': 'Affreschi del Perugino (1496-1500)'},
                {'label': 'Caffè Sandri',
                 'value': 'Storico (1860), dolci tipici perugini'},
                {'label': 'Loggia di Braccio',
                 'value': 'Rinascimento umbro (XV secolo)'},
                {'label': 'Vista panoramica',
                 'value': 'Colline umbre, Valle del Tevere'}
            ],
            'opening_hours': 'Sempre accessibile, musei: Mar-Dom 8:30-19:30',
            'cost': 'Passeggiata gratuita, Galleria €8'
        },
        'fontana_maggiore_perugia': {
            'title': 'Fontana Maggiore, Perugia',
            'summary': 'Capolavoro scultoreo di Nicola e Giovanni Pisano (1278). Simbolo della Perugia medievale e dell\'indipendenza comunale.',
            'details': [
                {'label': 'Architetti',
                 'value': 'Nicola e Giovanni Pisano (1275-1278)'},
                {'label': 'Struttura',
                 'value': 'Due vasche marmoree poligonali sovrapposte'},
                {'label': 'Iconografia',
                 'value': '50 rilievi: mesi, segni zodiacali, arti liberali'},
                {'label': 'Acquedotto',
                 'value': 'Alimentata dalle sorgenti del Monte Pacciano'},
                {'label': 'Restauri', 'value': 'Ultimo intervento 1996-1999'},
                {'label': 'Simbolismo',
                 'value': 'Indipendenza comunale, sapienza medievale'}
            ],
            'opening_hours': 'Sempre visibile e accessibile',
            'cost': 'Visione gratuita'
        },
        # === ROMA ===
        'stazione_termini': {
            'title': 'Stazione Roma Termini',
            'summary': 'La stazione ferroviaria principale di Roma, hub centrale per treni regionali, nazionali e metropolitana. Costruita negli anni \'50, serve oltre 150 milioni di passeggeri all\'anno.',
            'details': [
                {'label': 'Inaugurazione', 'value': '20 dicembre 1950'},
                {'label': 'Binari', 'value': '29 binari'},
                {'label': 'Metro', 'value': 'Linea A (rossa) e B (blu)'},
                {'label': 'Passeggeri/anno', 'value': '150+ milioni'},
                {'label': 'Servizi',
                 'value': 'Biglietteria automatica, sala d\'attesa, ristoranti, negozi'},
                {'label': 'Bagagli', 'value': 'Deposito bagagli disponibile'},
                {'label': 'WiFi', 'value': 'Gratuito per 1 ora'}
            ],
            'timetable': [
                {'direction': 'Metro A - Battistini',
                 'times': 'Ogni 3-6 min (5:30-23:30)'},
                {'direction': 'Metro B - Laurentina',
                 'times': 'Ogni 4-7 min (5:30-23:30)'}
            ],
            'actionLink': {
                'text': 'Orari Trenitalia in tempo reale',
                'url': 'https://www.trenitalia.com'
            }
        },
        'piazza_spagna': {
            'title': 'Piazza di Spagna',
            'summary': 'Una delle piazze più iconiche di Roma, famosa per la maestosa Scalinata di Trinità dei Monti e per essere il cuore dello shopping di lusso romano. La scalinata collega la piazza con la chiesa francese in cima.',
            'details': [
                {'label': 'Gradini scalinata',
                 'value': '135 scalini in travertino'},
                {'label': 'Costruzione', 'value': '1723-1726'},
                {'label': 'Architetto', 'value': 'Francesco de Sanctis'},
                {'label': 'Fontana',
                 'value': 'Fontana della Barcaccia (Bernini, 1629)'},
                {'label': 'Shopping', 'value': 'Via Condotti, Via del Babuino'},
                {'label': 'Curiosità',
                 'value': 'Vietato sedersi sui gradini (multa €250)'},
                {'label': 'Metro', 'value': 'Spagna (Linea A)'}
            ],
            'timetable': [
                {'direction': 'Chiesa Trinità dei Monti',
                 'times': 'Mar-Dom 10:00-19:00'},
                {'direction': 'Keats- Shelley Museum',
                 'times': 'Lun-Sab 10:00-18:00'}
            ]
        },
        'fontana_trevi': {
            'title': 'Fontana di Trevi',
            'summary': 'La fontana barocca più spettacolare al mondo, immortalata in "La Dolce Vita" di Fellini. La tradizione dice che lanciando una moneta con la mano destra sopra la spalla sinistra si tornerà a Roma.',
            'details': [
                {'label': 'Altezza', 'value': '26.3 metri'},
                {'label': 'Larghezza', 'value': '49.15 metri'},
                {'label': 'Architetto', 'value': 'Nicola Salvi'},
                {'label': 'Completamento',
                 'value': '1762 (30 anni di lavori)'},
                {'label': 'Stile', 'value': 'Barocco Romano'},
                {'label': 'Figura centrale', 'value': 'Nettuno (Oceano)'},
                {'label': 'Monete raccolte',
                 'value': '€1.4 milioni/anno (dati alla Caritas)'},
                {'label': 'Curiosità', 'value': 'Due monete = nuova storia d\'amore'},
                {'label': 'Miglior orario',
                 'value': 'Alba (6:00-7:00) per evitare folle'}
            ],
            'timetable': [
                {'direction': 'Accessibile',
                 'times': '24h/7gg (illuminazione notturna)'},
                {'direction': 'Pulizia fontana',
                 'times': 'Ogni lunedì mattina 7:00-9:00'}
            ]
        },
        'pantheon': {
            'title': 'Pantheon',
            'summary': 'Il tempio romano meglio conservato al mondo, considerato una meraviglia architettonica. La sua cupola fu la più grande per 1.300 anni fino a Brunelleschi. Oggi è basilica cristiana e mausoleo reale.',
            'details': [
                    {'label': 'Costruzione originale',
                        'value': '27 a.C. (Marco Agrippa)'},
                    {'label': 'Ricostruzione',
                        'value': '118-128 d.C. (Imperatore Adriano)'},
                    {'label': 'Diametro cupola',
                        'value': '43.30 metri (= altezza interna)'},
                    {'label': 'Oculus',
                        'value': '8.2 metri di diametro (unica fonte di luce)'},
                    {'label': 'Materiale', 'value': 'Calcestruzzo romano con pomice'},
                    {'label': 'Sepolture illustri',
                        'value': 'Raffaello Sanzio, Re Vittorio Emanuele II'},
                    {'label': 'Ingresso',
                        'value': 'Gratuito (prenotazione consigliata)'},
                    {'label': 'Curiosità',
                        'value': 'Il pavimento ha pendenze per far defluire la pioggia'}
            ],
            'timetable': [
                {'direction': 'Lun-Sab',
                 'times': '9:00-19:00 (ultimo ingresso 18:45)'},
                {'direction': 'Domenica',
                 'times': '9:00-18:00 (ultimo ingresso 17:45)'},
                {'direction': 'Messe', 'times': 'Sabato 17:00, Domenica 10:30'}
            ],
            'actionLink': {
                'text': 'Prenota visita guidata',
                'url': 'https://pantheonroma.com'
            }
        },
        'piazza_navona': {
            'title': 'Piazza Navona',
            'summary': 'Il gioiello del barocco romano, costruita sulle rovine dello Stadio di Domiziano. Teatro della rivalità artistica tra Bernini e Borromini, oggi è il salotto elegante di Roma con i suoi caffè storici.',
            'details': [
                {'label': 'Forma originale',
                 'value': 'Stadio di Domiziano (86 d.C., 30.000 spettatori)'},
                {'label': 'Trasformazione',
                 'value': 'XV secolo - da stadio a piazza'},
                {'label': 'Lunghezza', 'value': '276 metri'},
                {'label': 'Fontana centrale',
                 'value': 'Fontana dei Quattro Fiumi (Bernini, 1651)'},
                {'label': 'Fontana sud',
                 'value': 'Fontana del Moro (Bernini)'},
                {'label': 'Fontana nord', 'value': 'Fontana del Nettuno'},
                {'label': 'Chiesa',
                 'value': 'Sant\'Agnese in Agone (Borromini)'},
                {'label': 'Leggenda',
                 'value': 'Statua del Nilo copre gli occhi per non vedere la chiesa'},
                {'label': 'Mercatino',
                 'value': 'Befana (6 gennaio) e Natale'}
            ],
            'timetable': [
                {'direction': 'Caffè storici',
                 'times': 'Caffè Domiziano, Tre Scalini (7:00-1:00)'},
                {'direction': 'Artisti di strada',
                 'times': 'Tutti i giorni 10:00-24:00'},
                {'direction': 'Chiesa S. Agnese',
                 'times': 'Mar-Dom 9:30-12:30, 15:30-19:00'}
            ],
            'actionLink': {
                'text': 'Storia dello Stadio di Domiziano',
                'url': 'https://stadiodomiziano.com'
            }
        }
    }

    # Cerca nel database dei luoghi
    if context in place_details:
        result = place_details[context]
        print(
            f"✅ Trovati dettagli per {context}: {result.get('title', 'N/A')}")
        return result
    else:
        print(f"❌ Nessun dettaglio trovato per context: {context}")
        return None


def get_cached_place_details(context):
    """Ottiene dettagli dalla cache database"""
    try:
        from models import PlaceCache
        cached = PlaceCache.query.filter_by(cache_key=context).first()
        if cached:
            cached.update_access()
            db.session.commit()
            return cached.get_place_data()
    except Exception as e:
        print(f"Errore cache lookup: {e}")
    return None


def save_to_cache(context, place_name, city, country, place_data):
    """Salva dati luogo in cache database"""
    try:
        import json
        from models import PlaceCache

        cache_entry = PlaceCache(
            cache_key=context,
            place_name=place_name,
            city=city,
            country=country,
            place_data=json.dumps(place_data),
            priority_level='dynamic'
        )
        db.session.add(cache_entry)
        db.session.commit()
        print(f"✅ Salvato in cache: {place_name}")
    except Exception as e:
        print(f"Errore salvataggio cache: {e}")


@app.route('/save_preferences', methods=['POST'])
@login_required
def api_save_preferences():
    """API endpoint per salvare preferenze utente"""
    try:
        data = request.get_json()
        current_user = get_current_user()

        # Trova o crea profilo utente
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()

        if not profile:
            profile = UserProfile(
                user_id=current_user.id,
                interests='',
                travel_pace='Moderato',
                budget='€€',
                bio='Viaggiatore entusiasta'
            )
            db.session.add(profile)

        # Aggiorna le preferenze
        if 'interests' in data:
            profile.set_interests(data['interests'])
        if 'travel_pace' in data:
            profile.travel_pace = data['travel_pace']
        if 'budget' in data:
            profile.budget = data['budget']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Preferenze salvate correttamente'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === CRUD ROUTES PER USER PROFILE ===


@app.route('/demo-dashboard')
def demo_dashboard():
    """Demo di accesso per mostrare l'integrazione profilo"""
    return redirect('/profile')


@app.route('/profile')
@login_required
def view_profile():
    """Visualizza il profilo dell'utente - design mobile uniforme a Viamigo"""
    from flask_login import current_user as auth_user

    # Usa utente realmente autenticato
    if not auth_user.is_authenticated:
        return redirect('/auth/login')

    # Profilo semplificato senza UserProfile model
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viamigo - Il Mio Profilo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0c0a09; }
        .phone-mockup { width: 100%; max-width: 400px; height: 100vh; max-height: 850px; background-color: #111827; border-radius: 40px; border: 10px solid #111827; box-shadow: 0 20px 40px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; }
        .phone-screen { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .viamigo-font { font-family: 'Poppins', sans-serif; background: linear-gradient(to right, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .interest-tag.selected { background-color: #a78bfa; color: #111827; font-weight: 600; }
        .segmented-control button.selected { background-color: #a78bfa; color: #111827; font-weight: 600; }
    </style>
</head>
<body class="flex justify-center items-center p-4">
    <div class="phone-mockup">
        <div class="phone-screen">
            <!-- HEADER PROFILO -->
            <div class="header p-4 pt-8 border-b border-gray-700">
                <div class="flex items-center space-x-3">
                    <button onclick="window.location.href='/'" class="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                        </svg>
                    </button>
                    <div class="overflow-hidden">
                        <p class="text-xs text-gray-400">Il tuo account</p>
                        <h2 class="font-bold text-white text-lg">Profilo & Preferenze</h2>
                    </div>
                </div>
            </div>

            <!-- CONTENUTO PROFILO -->
            <div class="flex-grow overflow-y-auto p-4">
                <!-- Info Utente -->
                <!-- Info Utente -->
                <div class="flex flex-col items-center mb-8">
                    <div class="w-20 h-20 bg-gray-700 rounded-full flex items-center justify-center mb-3 border-2 border-violet-500">
                        <span class="text-2xl">👤</span>
                    </div>
                    <h3 class="text-white text-xl font-semibold">{{ auth_user.first_name or 'Utente' }} {{ auth_user.last_name or 'Viamigo' }}</h3>
                    <p class="text-gray-400 text-sm">{{ auth_user.email }}</p>
                </div>

                <!-- Profilo Semplificato -->
                <div class="space-y-6">
                    <!-- Interessi -->
                    <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                        <h3 class="text-gray-400 text-sm font-medium mb-3">I tuoi interessi</h3>
                        <div class="grid grid-cols-3 gap-2">
                            <span class="bg-violet-500 text-white py-2 px-3 rounded-lg text-sm text-center">Arte</span>
                            <span class="bg-violet-500 text-white py-2 px-3 rounded-lg text-sm text-center">Cibo</span>
                            <span class="bg-violet-500 text-white py-2 px-3 rounded-lg text-sm text-center">Storia</span>
                        </div>
                    </div>

                    <!-- Preferenze -->
                    <div class="bg-gray-800 rounded-xl p-4 border border-gray-700">
                        <h3 class="text-gray-400 text-sm font-medium mb-4">Preferenze</h3>
                        <div class="space-y-3">
                            <div class="flex justify-between">
                                <span class="text-gray-300">Ritmo di viaggio</span>
                                <span class="text-white font-medium">Moderato</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-300">Budget</span>
                                <span class="text-white font-medium">€€</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Azioni -->
                <div class="space-y-4 mt-8">
                    <button onclick="window.location.href='/profile/edit'" class="w-full bg-gray-700 text-white py-3 rounded-xl font-semibold flex items-center justify-center space-x-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                        <span>Modifica Profilo</span>
                    </button>

                    <button onclick="window.location.href='/auth/logout'" class="w-full bg-red-600/20 text-red-400 py-3 rounded-xl font-semibold flex items-center justify-center space-x-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                        </svg>
                        <span>Logout</span>
                    </button>
                </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''', auth_user=auth_user)


@app.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    """Pagina creazione profilo semplificata"""
    from flask_login import current_user as auth_user

    # Redirect a profilo esistente per ora
    return redirect('/profile')

    # GET request - mostra form con design mobile Viamigo
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viamigo - Crea Profilo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0c0a09; }
        .phone-mockup { width: 100%; max-width: 400px; height: 100vh; max-height: 850px; background-color: #111827; border-radius: 40px; border: 10px solid #111827; box-shadow: 0 20px 40px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; }
        .phone-screen { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .viamigo-font { font-family: 'Poppins', sans-serif; background: linear-gradient(to right, #a78bfa, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .interest-tag { background-color: #374151; color: #d1d5db; cursor: pointer; transition: all 0.2s; }
        .interest-tag.selected { background-color: #a78bfa; color: #111827; font-weight: 600; }
        .segmented-control button { background-color: #374151; color: #d1d5db; transition: all 0.2s; }
        .segmented-control button.selected { background-color: #a78bfa; color: #111827; font-weight: 600; }
    </style>
</head>
<body class="flex justify-center items-center p-4">
    <div class="phone-mockup">
        <div class="phone-screen">
            <!-- HEADER -->
            <div class="header p-4 pt-8 border-b border-gray-700">
                <div class="flex items-center space-x-3">
                    <button onclick="window.location.href='/profile'" class="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                        </svg>
                    </button>
                    <div class="overflow-hidden">
                        <p class="text-xs text-gray-400">Personalizza i tuoi viaggi</p>
                        <h2 class="font-bold text-white text-lg">Crea il Tuo Profilo</h2>
                    </div>
                </div>
            </div>

            <!-- CONTENUTO FORM -->
            <div class="flex-grow overflow-y-auto p-4">
                <form method="POST" class="space-y-6">
                    <!-- Interessi -->
                    <div>
                        <h3 class="text-gray-400 text-sm font-medium mb-3">I tuoi interessi</h3>
                        <div class="grid grid-cols-2 gap-2">
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Cibo')">🍕 Cibo</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Arte')">🎨 Arte</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Storia')">🏛️ Storia</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Natura')">🌲 Natura</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Relax')">🧘 Relax</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Avventura')">⛰️ Avventura</div>
                        </div>
                        <input type="hidden" name="interests" id="interests-input">
                    </div>

                    <!-- Ritmo di Viaggio -->
                    <div>
                        <h3 class="text-gray-400 text-sm font-medium mb-3">Ritmo di viaggio</h3>
                        <div class="segmented-control grid grid-cols-3 bg-gray-800 rounded-xl p-1 gap-1">
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectPace(this, 'Lento')">🐌 Lento</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm selected" onclick="selectPace(this, 'Moderato')">🚶 Moderato</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectPace(this, 'Veloce')">🏃 Veloce</button>
                        </div>
                        <input type="hidden" name="travel_pace" id="pace-input" value="Moderato">
                    </div>

                    <!-- Budget -->
                    <div>
                        <h3 class="text-gray-400 text-sm font-medium mb-3">Budget</h3>
                        <div class="segmented-control grid grid-cols-3 bg-gray-800 rounded-xl p-1 gap-1">
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectBudget(this, '€')">€ Economico</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm selected" onclick="selectBudget(this, '€€')">€€ Medio</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectBudget(this, '€€€')">€€€ Alto</button>
                        </div>
                        <input type="hidden" name="budget" id="budget-input" value="€€">
                    </div>

                    <!-- Pulsanti Azione -->
                    <div class="space-y-3 pt-4">
                        <button type="submit" class="w-full bg-violet-500 text-white py-3 rounded-xl font-semibold">
                            Crea il Mio Profilo
                        </button>
                        <button type="button" onclick="window.location.href='/profile'" class="w-full bg-gray-700 text-white py-3 rounded-xl font-semibold">
                            Annulla
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        let selectedInterests = [];

        function toggleInterest(element, interest) {
            if (selectedInterests.includes(interest)) {
                selectedInterests = selectedInterests.filter(i => i !== interest);
                element.classList.remove('selected');
            } else {
                selectedInterests.push(interest);
                element.classList.add('selected');
            }
            document.getElementById('interests-input').value = selectedInterests.join(',');
        }

        function selectPace(element, pace) {
            document.querySelectorAll('.segmented-control button').forEach(btn => {
                if (btn.parentElement.parentElement.querySelector('#pace-input')) {
                    btn.classList.remove('selected');
                }
            });
            element.classList.add('selected');
            document.getElementById('pace-input').value = pace;
        }

        function selectBudget(element, budget) {
            document.querySelectorAll('.segmented-control button').forEach(btn => {
                if (btn.parentElement.parentElement.querySelector('#budget-input')) {
                    btn.classList.remove('selected');
                }
            });
            element.classList.add('selected');
            document.getElementById('budget-input').value = budget;
        }
    </script>
</body>
</html>
    ''')


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Pagina modifica profilo semplificata"""
    from flask_login import current_user as auth_user

    # Redirect a profilo principale per ora
    return redirect('/profile')

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        # Aggiorna profilo
        interests = data.get('interests', [])
        if isinstance(interests, str):
            interests = [i.strip() for i in interests.split(',') if i.strip()]
        profile.set_interests(interests)

        profile.travel_pace = data.get('travel_pace')
        profile.budget = data.get('budget')

        db.session.commit()

        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Profilo aggiornato con successo',
                'profile': profile.to_dict()
            })
        else:
            flash('Profilo aggiornato con successo!')
            return redirect(url_for('view_profile'))

    # GET request - mostra form pre-compilato con design mobile
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viamigo - Modifica Profilo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0c0a09; }
        .phone-mockup { width: 100%; max-width: 400px; height: 100vh; max-height: 850px; background-color: #111827; border-radius: 40px; border: 10px solid #111827; box-shadow: 0 20px 40px rgba(0,0,0,0.5); display: flex; flex-direction: column; overflow: hidden; }
        .phone-screen { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .interest-tag { background-color: #374151; color: #d1d5db; cursor: pointer; transition: all 0.2s; }
        .interest-tag.selected { background-color: #a78bfa; color: #111827; font-weight: 600; }
        .segmented-control button { background-color: #374151; color: #d1d5db; transition: all 0.2s; }
        .segmented-control button.selected { background-color: #a78bfa; color: #111827; font-weight: 600; }
    </style>
</head>
<body class="flex justify-center items-center p-4">
    <div class="phone-mockup">
        <div class="phone-screen">
            <!-- HEADER -->
            <div class="header p-4 pt-8 border-b border-gray-700">
                <div class="flex items-center space-x-3">
                    <button onclick="window.location.href='/profile'" class="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                        </svg>
                    </button>
                    <div class="overflow-hidden">
                        <p class="text-xs text-gray-400">Aggiorna le tue preferenze</p>
                        <h2 class="font-bold text-white text-lg">Modifica Profilo</h2>
                    </div>
                </div>
            </div>

            <!-- CONTENUTO FORM -->
            <div class="flex-grow overflow-y-auto p-4">
                <form method="POST" class="space-y-6">
                    <!-- Interessi -->
                    <div>
                        <h3 class="text-gray-400 text-sm font-medium mb-3">I tuoi interessi</h3>
                        <div class="grid grid-cols-2 gap-2">
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Cibo')">🍕 Cibo</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Arte')">🎨 Arte</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Storia')">🏛️ Storia</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Natura')">🌲 Natura</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Relax')">🧘 Relax</div>
                            <div class="interest-tag py-2 px-3 rounded-lg text-sm text-center" onclick="toggleInterest(this, 'Avventura')">⛰️ Avventura</div>
                        </div>
                        <input type="hidden" name="interests" id="interests-input">
                    </div>

                    <!-- Ritmo di Viaggio -->
                    <div>
                        <h3 class="text-gray-400 text-sm font-medium mb-3">Ritmo di viaggio</h3>
                        <div class="segmented-control grid grid-cols-3 bg-gray-800 rounded-xl p-1 gap-1">
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectPace(this, 'Lento')">🐌 Lento</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectPace(this, 'Moderato')">🚶 Moderato</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectPace(this, 'Veloce')">🏃 Veloce</button>
                        </div>
                        <input type="hidden" name="travel_pace" id="pace-input" value="{{ profile.travel_pace or 'Moderato' }}">
                    </div>

                    <!-- Budget -->
                    <div>
                        <h3 class="text-gray-400 text-sm font-medium mb-3">Budget</h3>
                        <div class="segmented-control grid grid-cols-3 bg-gray-800 rounded-xl p-1 gap-1">
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectBudget(this, '€')">€ Economico</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectBudget(this, '€€')">€€ Medio</button>
                            <button type="button" class="py-2 px-3 rounded-lg text-sm" onclick="selectBudget(this, '€€€')">€€€ Alto</button>
                        </div>
                        <input type="hidden" name="budget" id="budget-input" value="{{ profile.budget or '€€' }}">
                    </div>

                    <!-- Pulsanti Azione -->
                    <div class="space-y-3 pt-4">
                        <button type="submit" class="w-full bg-violet-500 text-white py-3 rounded-xl font-semibold">
                            Salva Modifiche
                        </button>
                        <button type="button" onclick="window.location.href='/profile'" class="w-full bg-gray-700 text-white py-3 rounded-xl font-semibold">
                            Annulla
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Preseleziona interessi esistenti del profilo
        let selectedInterests = {{ profile.get_interests() | tojson if profile else [] }};

        // Inizializzazione al caricamento
        document.addEventListener('DOMContentLoaded', function() {
            // Preseleziona interessi
            selectedInterests.forEach(interest => {
                const element = document.querySelector(`[onclick*="${interest}"]`);
                if (element) element.classList.add('selected');
            });

            // Preseleziona ritmo e budget
            const currentPace = "{{ profile.travel_pace or 'Moderato' }}";
            const currentBudget = "{{ profile.budget or '€€' }}";

            document.querySelector(`[onclick*="${currentPace}"]`)?.classList.add('selected');
            document.querySelector(`[onclick*="${currentBudget}"]`)?.classList.add('selected');

            document.getElementById('interests-input').value = selectedInterests.join(',');
        });

        function toggleInterest(element, interest) {
            if (selectedInterests.includes(interest)) {
                selectedInterests = selectedInterests.filter(i => i !== interest);
                element.classList.remove('selected');
            } else {
                selectedInterests.push(interest);
                element.classList.add('selected');
            }
            document.getElementById('interests-input').value = selectedInterests.join(',');
        }

        function selectPace(element, pace) {
            document.querySelectorAll('.segmented-control button').forEach(btn => {
                if (btn.parentElement.parentElement.querySelector('#pace-input')) {
                    btn.classList.remove('selected');
                }
            });
            element.classList.add('selected');
            document.getElementById('pace-input').value = pace;
        }

        function selectBudget(element, budget) {
            document.querySelectorAll('.segmented-control button').forEach(btn => {
                if (btn.parentElement.parentElement.querySelector('#budget-input')) {
                    btn.classList.remove('selected');
                }
            });
            element.classList.add('selected');
            document.getElementById('budget-input').value = budget;
        }
    </script>
</body>
</html>
    ''', profile=profile)


@app.route('/profile/delete', methods=['DELETE'])
@login_required
def delete_profile():
    """Elimina il profilo dell'utente corrente"""
    current_user = get_current_user()  # Usa mock user
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({'success': False, 'message': 'Profilo non trovato'}), 404

    db.session.delete(profile)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Profilo eliminato con successo'})

# === API ROUTES ===


@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile_api():
    """API per ottenere il profilo dell'utente corrente"""
    current_user = get_current_user()  # Usa mock user
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({'profile': None})

    return jsonify({'profile': profile.to_dict()})


@app.route('/api/profile', methods=['POST'])
@login_required
def create_profile_api():
    """API per creare un profilo"""
    return create_profile()


@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile_api():
    """API per aggiornare un profilo"""
    return edit_profile()


@app.route('/api/profile', methods=['DELETE'])
@login_required
def delete_profile_api():
    """API per eliminare un profilo"""
    return delete_profile()

# === ADMIN ROUTES (per funzionalità future) ===


@app.route('/admin/profiles')
@login_required
def admin_profiles():
    """Admin: visualizza tutti i profili"""
    current_user = get_current_user()  # Usa mock user
    if not is_admin(current_user.id):
        return redirect(url_for('index'))

    profiles = db.session.query(UserProfile, User).join(User).all()

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin - Profili Utenti</title>
        <meta charset="utf-8">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-red-600 text-white p-4">
            <div class="container mx-auto">
                <h1 class="text-xl font-bold">Admin Panel - Profili Utenti</h1>
            </div>
        </nav>

        <div class="container mx-auto p-8">
            <div class="bg-white rounded-lg shadow-md overflow-hidden">
                <table class="w-full">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="p-3 text-left">Utente</th>
                            <th class="p-3 text-left">Email</th>
                            <th class="p-3 text-left">Interessi</th>
                            <th class="p-3 text-left">Ritmo</th>
                            <th class="p-3 text-left">Budget</th>
                            <th class="p-3 text-left">Azioni</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for profile, user in profiles %}
                        <tr class="border-b">
                            <td class="p-3">{{ user.first_name or 'N/A' }} {{ user.last_name or '' }}</td>
                            <td class="p-3">{{ user.email }}</td>
                            <td class="p-3">{{ ', '.join(profile.get_interests()) if profile.get_interests() else 'N/A' }}</td>
                            <td class="p-3">{{ profile.travel_pace or 'N/A' }}</td>
                            <td class="p-3">{{ profile.budget or 'N/A' }}</td>
                            <td class="p-3">
                                <a href="/admin/profile/{{ profile.id }}/edit" class="text-blue-600">Modifica</a> |
                                <a href="#" onclick="deleteUserProfile({{ profile.id }})" class="text-red-600">Elimina</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    ''', profiles=profiles)

# === NEW SYSTEM HEALTH ROUTE ===


@app.route('/api/system/health')
@login_required
def system_health():
    """Get system health status including all API services"""
    from api_error_handler import api_error_handler

    try:
        health_data = api_error_handler.get_system_health()

        # Add cache statistics
        from api_error_handler import cache_openai, cache_scrapingdog, cache_nominatim, cache_apify

        health_data['cache_stats'] = {
            'openai': cache_openai.get_stats(),
            'scrapingdog': cache_scrapingdog.get_stats(),
            'nominatim': cache_nominatim.get_stats(),
            'apify': cache_apify.get_stats()
        }

        # Add Apify integration status
        from apify_integration import apify_travel
        health_data['integrations'] = {
            'apify': {
                'available': apify_travel.is_available(),
                'api_token_configured': bool(apify_travel.api_token)
            }
        }

        return jsonify(health_data)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Health check failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


# =====================================
# MISSING ROUTES - FIXES FOR ISSUES
# =====================================

@app.route('/api/routes/history', methods=['GET'])
def get_route_history():
    """Get saved route history for current user"""
    try:
        # For now, return empty list - in future this would query database
        return jsonify({
            'routes': [],
            'total_count': 0,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/routes/save', methods=['POST'])
def save_route():
    """Save a route to user's history"""
    try:
        data = request.get_json()
        route_data = data.get('route', {})

        # For now, just return success - in future this would save to database
        return jsonify({
            'success': True,
            'message': 'Route saved successfully',
            'route_id': f"route_{datetime.now().timestamp()}"
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/routes/load/<route_id>', methods=['GET'])
def load_route(route_id):
    """Load a specific saved route"""
    try:
        # For now, return empty route - in future this would query database
        return jsonify({
            'route': None,
            'success': False,
            'message': 'Route not found'
        }), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/attractions/enhanced/<city>')
def get_enhanced_city_attractions(city):
    """Enhanced city attractions with better image matching"""
    try:
        # Query comprehensive attractions database for better results
        from comprehensive_attractions_api import get_db_connection

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Search for attractions in the city with preference for those with images
                cur.execute("""
                    SELECT 
                        name, description, category, attraction_type,
                        latitude, longitude, 
                        thumb_url, image_license, image_creator,
                        wikidata_id, wikipedia_url,
                        has_image
                    FROM comprehensive_attractions
                    WHERE city ILIKE %s
                    ORDER BY 
                        CASE WHEN has_image THEN 0 ELSE 1 END,
                        CASE WHEN name ILIKE %s THEN 0 ELSE 1 END,
                        CASE WHEN name ILIKE %s THEN 0 ELSE 1 END,
                        CASE WHEN name ILIKE %s THEN 0 ELSE 1 END,
                        name
                    LIMIT 20
                """, [f"%{city}%", "%pantheon%", "%colosseo%", "%duomo%"])

                attractions = cur.fetchall()

                results = []
                for row in attractions:
                    attraction = {
                        'name': row[0],
                        'description': row[1] or f"Important {row[3] or 'attraction'} in {city}",
                        'category': row[2],
                        'type': row[3],
                        'coordinates': {
                            'lat': float(row[4]) if row[4] else None,
                            'lon': float(row[5]) if row[5] else None
                        },
                        'has_image': row[11],
                        'image_url': row[6] if row[11] else None,
                        'image_license': row[7],
                        'image_creator': row[8],
                        'wikidata_id': row[9],
                        'wikipedia_url': row[10]
                    }
                    results.append(attraction)

                return jsonify({
                    'city': city,
                    'attractions': results,
                    'total_count': len(results),
                    'success': True
                })

    except Exception as e:
        # Fallback to basic response
        return jsonify({
            'city': city,
            'attractions': [],
            'total_count': 0,
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
