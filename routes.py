from flask import session, render_template_string, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_required
from models import User, UserProfile, AdminUser
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
        self.first_name = "Marco"
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

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

def is_admin(user_id):
    """Controlla se l'utente è admin"""
    admin = AdminUser.query.filter_by(user_id=user_id).first()
    return admin is not None

def can_edit_profile(profile_user_id, current_user_id):
    """Controlla se l'utente può modificare il profilo"""
    # L'utente può modificare il proprio profilo o se è admin
    return profile_user_id == current_user_id or is_admin(current_user_id)

@app.route('/')
def index():
    """Homepage - redirect basato su stato autenticazione"""
    from flask_login import current_user
    
    # Se l'utente è autenticato con Flask-Login, va alla dashboard
    if current_user.is_authenticated:
        return redirect('/dashboard')
    
    # Altrimenti controlla il fallback demo per compatibilità
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
                        <h2 class="text-lg font-semibold mb-1">Benvenuto, Marco!</h2>
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
@require_login
def planner():
    """Redirect alla pagina originale di pianificazione"""
    return redirect('/static/index.html')

@app.route('/get_profile', methods=['GET'])
def api_get_profile():
    """API endpoint per ottenere profilo utente (per compatibilità con frontend)"""
    from flask_login import current_user
    
    # Se non autenticato, usa fallback demo per compatibilità
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = session.get('demo_user_id', 'demo_user_123')
    
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    if profile:
        return jsonify({
            'success': True,
            'profile': {
                'interests': profile.interests.split(',') if profile.interests else [],
                'travel_pace': profile.travel_pace,
                'budget': profile.budget
            }
        })
    else:
        return jsonify({
            'success': False,
            'profile': {
                'interests': [],
                'travel_pace': 'Moderato',
                'budget': '€€'
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
            
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        user_interests = profile.interests.split(',') if profile and profile.interests else []
        
        # Prova prima il routing dinamico personalizzato
        from dynamic_routing import dynamic_router
        itinerary = dynamic_router.generate_personalized_itinerary(
            start, end, city, duration, user_interests
        )
        
        # Se il routing dinamico fallisce, usa template specifici
        if not itinerary or len(itinerary) < 3:
            print(f"Fallback a template per {city}")
            if city == 'torino':
                itinerary = generate_torino_itinerary(start, end)
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
                'routing_type': 'dynamic_personalized',
                'generated_for': f"{start} → {end}",
                'realistic_routing': True,
                'walking_routes': True
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
        'bologna': ['bologna', 'torri', 'piazza maggiore']
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
    """Genera itinerario specifico per Genova"""
    return [
        {
            'time': '09:00',
            'title': 'Piazza De Ferrari',
            'description': 'Il cuore di Genova con la famosa fontana. Punto di partenza per esplorare il centro storico.',
            'coordinates': [44.4071, 8.9348],
            'context': 'piazza_de_ferrari',
            'transport': 'walking'
        },
        {
            'time': '09:20',
            'title': 'Via del Campo',
            'description': 'La strada più famosa di Genova, cantata da De André. Caruggi medievali autentici.',
            'coordinates': [44.4076, 8.9290],
            'context': 'via_del_campo',
            'transport': 'walking'
        },
        {
            'time': '10:00',
            'title': 'Cattedrale di San Lorenzo',
            'description': 'Duomo di Genova con la famosa bomba inesplosa della Seconda Guerra Mondiale.',
            'coordinates': [44.4076, 8.9321],
            'context': 'cattedrale_genova',
            'transport': 'walking'
        },
        {
            'time': '10:45',
            'title': 'Spianata Castelletto',
            'description': 'Vista panoramica mozzafiato su Genova. Salita con funicolare storica.',
            'coordinates': [44.4118, 8.9364],
            'context': 'spianata_castelletto',
            'transport': 'funicular'
        },
        {
            'time': '11:30',
            'title': 'Acquario di Genova',
            'description': 'Secondo acquario più grande d\'Europa. Metro linea rossa fino a San Giorgio.',
            'coordinates': [44.4109, 8.9326],
            'context': 'acquario_genova',
            'transport': 'metro'
        },
        {
            'type': 'tip',
            'title': '🚇 Trasporti Genova',
            'description': 'Metro AMT: €1.50 (100 min). Funicolare Castelletto: €0.90. Biglietto giornaliero: €4.50.'
        },
        {
            'type': 'tip',
            'title': '🍝 Specialità locale',
            'description': 'Prova il pesto genovese autentico da Il Genovese o prenditi una farinata in Via del Campo.'
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

@app.route('/get_details', methods=['POST'])
@require_login
def api_get_details():
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
        dynamic_result = dynamic_places.get_place_info(place_name, city, country)
        
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
            # === MILANO ===
            'duomo_milano': {
                'title': 'Duomo di Milano',
                'summary': 'Capolavoro gotico con guglie e la Madonnina. Una delle cattedrali più spettacolari del mondo, con terrazze panoramiche che offrono viste mozzafiato sulla città e le Alpi.',
                'details': [
                    {'label': 'Costruzione', 'value': '1386-1965 (579 anni)'},
                    {'label': 'Stile', 'value': 'Gotico lombardo'},
                    {'label': 'Guglie', 'value': '135 guglie con 3.400 statue'},
                    {'label': 'Madonnina', 'value': '4.16m, oro, dal 1774'},
                    {'label': 'Vetrate', 'value': '55 finestre istoriate (XV-XX sec.)'},
                    {'label': 'Terrazze', 'value': 'Ascensore €15, scale €10'},
                    {'label': 'Cripta', 'value': 'San Carlo Borromeo'},
                    {'label': 'Curiosità', 'value': 'Meridiana del 1786 ancora funzionante'}
                ],
                'timetable': [
                    {'direction': 'Duomo', 'times': 'Lun-Dom 8:00-19:00 (ultima entrata 18:10)'},
                    {'direction': 'Terrazze', 'times': 'Lun-Dom 9:00-19:00 (estate fino 21:00)'},
                    {'direction': 'Museo', 'times': 'Mar-Dom 10:00-18:00 (chiuso lunedì)'}
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
                    {'label': 'Inaugurazione', 'value': '1877 (progetto Giuseppe Mengoni)'},
                    {'label': 'Soprannome', 'value': '"Il Salotto di Milano"'},
                    {'label': 'Lunghezza', 'value': '196 metri'},
                    {'label': 'Cupola', 'value': '47 metri altezza, vetro e ferro'},
                    {'label': 'Mosaici pavimento', 'value': 'Stemmi di Milano, Torino, Firenze, Roma'},
                    {'label': 'Negozi storici', 'value': 'Prada (dal 1913), Borsalino'},
                    {'label': 'Caffè storici', 'value': 'Biffi, Savini (dal 1867)'},
                    {'label': 'Rituale portafortuna', 'value': 'Girare 3 volte sui genitali del toro torinese'}
                ],
                'timetable': [
                    {'direction': 'Negozi', 'times': 'Lun-Dom 10:00-20:00 (alcuni fino 22:00)'},
                    {'direction': 'Ristoranti', 'times': 'Lun-Dom 12:00-24:00'},
                    {'direction': 'Caffè storici', 'times': 'Lun-Dom 7:30-20:00'}
                ]
            },
            'scala_milano': {
                'title': 'Teatro alla Scala',
                'summary': 'Il tempio dell\'opera mondiale. Dal 1778 il teatro più prestigioso per opera lirica e balletto, con una stagione che apre tradizionalmente il 7 dicembre, festa di Sant\'Ambrogio.',
                'details': [
                    {'label': 'Inaugurazione', 'value': '3 agosto 1778 con "L\'Europa riconosciuta" di Salieri'},
                    {'label': 'Architetto', 'value': 'Giuseppe Piermarini (neoclassico)'},
                    {'label': 'Posti', 'value': '2.030 spettatori, 6 ordini di palchi'},
                    {'label': 'Palco reale', 'value': 'Palco n.5 del primo ordine'},
                    {'label': 'Stagione inaugurale', 'value': '7 dicembre - Sant\'Ambrogio'},
                    {'label': 'Artisti famosi', 'value': 'Verdi, Puccini, Toscanini, Callas'},
                    {'label': 'Museo', 'value': 'Costumi, strumenti, memorabilia'},
                    {'label': 'Curiosità', 'value': 'Ricostruito dopo bombardamento 1943'}
                ],
                'timetable': [
                    {'direction': 'Visite museo', 'times': 'Lun-Dom 9:00-17:30 (ultimo ingresso 17:00)'},
                    {'direction': 'Spettacoli', 'times': 'Settembre-Luglio (programmazione variabile)'},
                    {'direction': 'Biglietteria', 'times': 'Lun-Sab 10:00-18:00, Dom 10:00-17:00'}
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
                    {'label': 'Costruzione originale', 'value': '1360 (famiglia Visconti)'},
                    {'label': 'Trasformazione', 'value': '1450-1499 (Francesco Sforza)'},
                    {'label': 'Restauro', 'value': '1893-1904 (Luca Beltrami)'},
                    {'label': 'Musei', 'value': '9 musei specializzati'},
                    {'label': 'Capolavoro', 'value': 'Pietà Rondanini (ultima opera Michelangelo)'},
                    {'label': 'Leonardo', 'value': 'Decorazioni Sala delle Asse'},
                    {'label': 'Torre Filarete', 'value': '70 metri, ricostruita dopo esplosione 1521'},
                    {'label': 'Cortili', 'value': 'Cortile d\'Armi, Cortile della Rocchetta'}
                ],
                'timetable': [
                    {'direction': 'Musei', 'times': 'Mar-Dom 9:00-17:30 (chiuso lunedì)'},
                    {'direction': 'Cortili', 'times': 'Lun-Dom 7:00-19:30 (estate fino 20:00)'},
                    {'direction': 'Visite guidate', 'times': 'Sabato-Domenica 15:00 (prenotazione)'}
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
                    {'label': 'Progettista', 'value': 'Emilio Alemagna (stile inglese)'},
                    {'label': 'Torre Branca', 'value': '108m, panorama 360° (ascensore)'},
                    {'label': 'Arco della Pace', 'value': '25m, 1807-1838, Napoleone'},
                    {'label': 'Arena Civica', 'value': '1807, 30.000 spettatori'},
                    {'label': 'Acquario', 'value': 'Civico Acquario (1906)'},
                    {'label': 'Eventi', 'value': 'Concerti estivi, mercatini, sport'},
                    {'label': 'Fauna', 'value': 'Tartarughe, anatre, scoiattoli'}
                ],
                'timetable': [
                    {'direction': 'Parco', 'times': 'Sempre aperto (illuminato di notte)'},
                    {'direction': 'Torre Branca', 'times': 'Mar-Dom 10:00-18:00 (estate 21:00)'},
                    {'direction': 'Bar parco', 'times': 'Lun-Dom 7:00-20:00 (estate 22:00)'}
                ]
            },
            # === TRIESTE ===
            # TRIESTE - Luoghi specifici con dettagli autentici
            'piazza_unita_ditalia_trieste': {
                'title': 'Piazza Unità d\'Italia, Trieste',
                'summary': 'La piazza più grande d\'Europa affacciata sul mare, capolavoro urbanistico dell\'Impero Asburgico. Circondata da palazzi neoclassici e barocchi.',
                'details': [
                    {'label': 'Dimensioni', 'value': '12.280 m² (la più grande piazza europea sul mare)'},
                    {'label': 'Costruzione', 'value': 'XIX secolo (epoca asburgica)'},
                    {'label': 'Palazzo Municipio', 'value': 'Sede comunale con torre campanaria (1877)'},
                    {'label': 'Caffè degli Specchi', 'value': 'Caffè storico (1839) con vista mare'},
                    {'label': 'Fontana Quattro Continenti', 'value': 'Simbolo dell\'apertura di Trieste al mondo'},
                    {'label': 'Vista', 'value': 'Golfo di Trieste e Castello di Miramare'}
                ],
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            },
            'centro_storico_trieste': {
                'title': 'Centro Storico, Trieste',
                'summary': 'Il cuore mitteleuropeo di Trieste con architetture asburgiche, caffè letterari e atmosfera cosmopolita.',
                'details': [
                    {'label': 'Via del Corso', 'value': 'Arteria pedonale principale per shopping'},
                    {'label': 'Caffè San Marco', 'value': 'Caffè letterario frequentato da Joyce e Svevo'},
                    {'label': 'Teatro Verdi', 'value': 'Teatro dell\'opera del 1801'},
                    {'label': 'Sinagoga', 'value': 'Una delle più grandi d\'Europa'},
                    {'label': 'Borgo Teresiano', 'value': 'Quartiere settecentesco con canali'},
                    {'label': 'Architettura', 'value': 'Mix asburgico-italiano unico al mondo'}
                ],
                'opening_hours': 'Sempre accessibile (negozi: 9:00-19:00)',
                'cost': 'Gratuito (consumi variabili)'
            },
            'castello_miramare_trieste': {
                'title': 'Castello di Miramare',
                'summary': 'Castello romantico dell\'Arciduca Massimiliano d\'Asburgo (1856-1860) con giardini botanici e vista spettacolare sul golfo.',
                'details': [
                    {'label': 'Costruzione', 'value': '1856-1860 (Arciduca Massimiliano)'},
                    {'label': 'Stile', 'value': 'Eclettico (gotico, rinascimentale, medievale)'},
                    {'label': 'Interni', 'value': 'Arredi originali e sale storiche'},
                    {'label': 'Giardini', 'value': '22 ettari con 2000+ specie botaniche'},
                    {'label': 'Vista panoramica', 'value': 'Golfo di Trieste e costa istriana'},
                    {'label': 'Leggenda', 'value': 'Maledizione di Miramare sui suoi proprietari'}
                ],
                'opening_hours': 'Mar-Dom 9:00-19:00 (estate), 9:00-17:00 (inverno)',
                'cost': '€12 adulti, €8 ridotto, gratuito giardini'
            },
            'canal_grande_trieste': {
                'title': 'Canal Grande, Trieste',
                'summary': 'Il canale navigabile che attraversa il centro storico, cuore del Borgo Teresiano con ponti storici e caffè affacciati.',
                'details': [
                    {'label': 'Costruzione', 'value': 'XVIII secolo (Maria Teresa d\'Austria)'},
                    {'label': 'Lunghezza', 'value': '300 metri navigabili'},
                    {'label': 'Ponti', 'value': 'Ponte Rosso e Ponte Verde'},
                    {'label': 'Chiesa Sant\'Antonio', 'value': 'Chiesa neoclassica sulla sponda'},
                    {'label': 'Caffè storici', 'value': 'Caffè con dehors sui ponti'},
                    {'label': 'Mercatini', 'value': 'Mercato dell\'antiquariato (domenica)'}
                ],
                'opening_hours': 'Sempre accessibile',
                'cost': 'Gratuito'
            },
            'teatro_romano_trieste': {
                'title': 'Teatro Romano, Trieste',
                'summary': 'Antico teatro romano del I-II secolo d.C. scavato nella roccia del colle di San Giusto, con vista panoramica sulla città.',
                'details': [
                    {'label': 'Epoca', 'value': 'I-II secolo d.C. (epoca augustea)'},
                    {'label': 'Capacità', 'value': '6000 spettatori (originariamente)'},
                    {'label': 'Costruzione', 'value': 'Scavato nella roccia carsica'},
                    {'label': 'Stato', 'value': 'Parzialmente conservato'},
                    {'label': 'Vista', 'value': 'Panorama su Trieste e il golfo'},
                    {'label': 'Eventi', 'value': 'Concerti e spettacoli estivi'}
                ],
                'opening_hours': 'Sempre accessibile (visite guidate su prenotazione)',
                'cost': 'Gratuito'
            },
            # TORINO
            'via_roma_torino': {
                'title': 'Via Roma, Torino',
                'summary': 'La via pedonale più elegante di Torino, creata nel 1930s. I suoi portici neoclassici ospitano boutique di lusso e caffè storici.',
                'details': [
                    {'label': 'Lunghezza', 'value': '1.2 km di portici'},
                    {'label': 'Costruzione', 'value': '1930-1937 (piano urbanistico)'},
                    {'label': 'Stile', 'value': 'Architettura razionalista italiana'},
                    {'label': 'Shopping', 'value': 'Boutique di lusso, librerie storiche'},
                    {'label': 'Caffè storici', 'value': 'Caffè Mulassano (1907), Caffè Stratta'}
                ]
            },
            'piazza_castello_torino': {
                'title': 'Piazza Castello, Torino',
                'summary': 'Il cuore politico e culturale di Torino, circondata dai principali palazzi del potere sabaudo. Centro geometrico della città.',
                'details': [
                    {'label': 'Dimensioni', 'value': '40.000 m² (tra le più grandi d\'Europa)'},
                    {'label': 'Palazzo Reale', 'value': 'Residenza dei Savoia (XVII-XVIII sec)'},
                    {'label': 'Palazzo Madama', 'value': 'Museo Civico d\'Arte Antica'},
                    {'label': 'Teatro Regio', 'value': 'Opera house (1973, dopo incendio)'},
                    {'label': 'Armeria Reale', 'value': 'Collezione armi antiche più importante al mondo'}
                ]
            },
            'mole_antonelliana': {
                'title': 'Mole Antonelliana',
                'summary': 'Il simbolo di Torino, edificio più alto della città (167m). Originariamente sinagoga, oggi ospita il Museo Nazionale del Cinema.',
                'details': [
                    {'label': 'Altezza', 'value': '167.5 metri'},
                    {'label': 'Architetto', 'value': 'Alessandro Antonelli'},
                    {'label': 'Costruzione', 'value': '1863-1889'},
                    {'label': 'Ascensore panoramico', 'value': 'Salita alla cupola (€8)'},
                    {'label': 'Museo del Cinema', 'value': 'Primo in Italia per importanza'},
                    {'label': 'Curiosità', 'value': 'Compare sul retro delle monete da 2 centesimi'}
                ],
                'timetable': [
                    {'direction': 'Museo del Cinema', 'times': 'Mar-Dom 9:00-20:00'},
                    {'direction': 'Ascensore panoramico', 'times': 'Mar-Dom 9:00-19:00 (ultima salita)'}
                ]
            },
            'musei_reali_torino': {
                'title': 'Musei Reali, Torino',
                'summary': 'Il più importante complesso museale del Piemonte, residenza dei Savoia. Include Palazzo Reale, Armeria Reale, Galleria Sabauda e Biblioteca Reale con codici di Leonardo.',
                'details': [
                    {'label': 'Patrimonio UNESCO', 'value': 'Residenze sabaude (1997)'},
                    {'label': 'Palazzo Reale', 'value': 'Residenza ufficiale Casa Savoia (1646)'},
                    {'label': 'Armeria Reale', 'value': 'Collezione armi antiche più ricca al mondo'},
                    {'label': 'Galleria Sabauda', 'value': 'Capolavori Van Dyck, Rembrandt, Pollaiolo'},
                    {'label': 'Biblioteca Reale', 'value': 'Autoritratto di Leonardo da Vinci'},
                    {'label': 'Biglietto unico', 'value': '€15 (ridotto €2), gratuito <18 anni'},
                    {'label': 'Prenotazione', 'value': 'Consigliata nei weekend'}
                ],
                'timetable': [
                    {'direction': 'Mar-Dom', 'times': '9:00-19:00 (ultimo ingresso 18:00)'},
                    {'direction': 'Lunedì', 'times': 'Chiuso (eccetto festivi)'},
                    {'direction': 'Palazzo Reale', 'times': 'Visite guidate ogni ora'},
                    {'direction': 'Armeria Reale', 'times': 'Accesso libero con biglietto'}
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
                    {'label': 'Lunghezza percorso', 'value': '3 km centro-Valentino'},
                    {'label': 'Parco del Valentino', 'value': '500.000 m² di verde urbano'},
                    {'label': 'Castello del Valentino', 'value': 'Residenza sabauda (UNESCO)'},
                    {'label': 'Borgo medievale', 'value': 'Ricostruzione filologica (1884)'},
                    {'label': 'Attività', 'value': 'Jogging, ciclismo, pic-nic'}
                ]
            },
            # GENOVA
            'piazza_de_ferrari': {
                'title': 'Piazza De Ferrari, Genova',
                'summary': 'Il salotto di Genova, circondata da palazzi storici e dominata dalla grande fontana centrale. Cuore del centro storico medievale più esteso d\'Europa.',
                'details': [
                    {'label': 'Fontana', 'value': 'Costruita nel 1936, ristrutturata nel 2001'},
                    {'label': 'Palazzi storici', 'value': 'Palazzo Ducale, Palazzo della Regione'},
                    {'label': 'Teatro', 'value': 'Teatro Carlo Felice (opera house)'},
                    {'label': 'Shopping', 'value': 'Gallerie Mazzini, Via XX Settembre'},
                    {'label': 'Metro', 'value': 'Stazione De Ferrari (linea rossa)'}
                ]
            },
            'via_del_campo': {
                'title': 'Via del Campo, Genova',
                'summary': 'La strada più famosa di Genova, resa celebre dalla canzone di Fabrizio De André. Autentico caruggio medievale nel cuore del centro storico.',
                'details': [
                    {'label': 'Lunghezza', 'value': '500 metri di storia medievale'},
                    {'label': 'Epoca', 'value': 'XII secolo (caruggi medievali)'},
                    {'label': 'Fabrizio De André', 'value': 'Canzone "Via del Campo" (1967)'},
                    {'label': 'Caratteristiche', 'value': 'Negozi storici, farinata, botteghe artigiane'},
                    {'label': 'Mercato', 'value': 'Mercato del Pesce e prodotti locali'}
                ],
                'opening_hours': 'Sempre accessibile (negozi: 10:00-19:00)',
                'cost': 'Gratuito'
            },
            'cattedrale_san_lorenzo': {
                'title': 'Cattedrale di San Lorenzo, Genova',
                'summary': 'Il Duomo di Genova, famoso per la bomba navale britannica inesplosa del 1941. Capolavoro romanico-gotico con tesoro ecclesiastico.',
                'details': [
                    {'label': 'Costruzione', 'value': 'IX-XIV secolo (romanico-gotico)'},
                    {'label': 'Facciata', 'value': 'Marmo bianco e nero a strisce orizzontali'},
                    {'label': 'Bomba 1941', 'value': 'Proiettile navale britannico inesploso (visibile)'},
                    {'label': 'Tesoro', 'value': 'Santo Graal leggendario, reliquie preziose'},
                    {'label': 'Portale', 'value': 'Leoni stilofori medievali'},
                    {'label': 'Curiosità', 'value': 'Miracolo della bomba che non esplose'}
                ],
                'opening_hours': 'Lun-Sab 9:00-18:00, Dom 15:00-18:00',
                'cost': 'Ingresso gratuito, Tesoro €6'
            },
            'porto_antico': {
                'title': 'Porto Antico, Genova',
                'summary': 'Area portuale storica rinnovata da Renzo Piano per Expo 1992. Centro culturale e turistico con Acquario, Biosfera e Bigo.',
                'details': [
                    {'label': 'Progetto Renzo Piano', 'value': '1992 (500° scoperta America)'},
                    {'label': 'Biosfera', 'value': 'Serra tropicale in vetro e acciaio'},
                    {'label': 'Bigo', 'value': 'Ascensore panoramico 40m altezza'},
                    {'label': 'Galata Museo del Mare', 'value': 'Più grande del Mediterraneo'},
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
                    {'label': 'Dimensioni', 'value': '10.000 m², 70 vasche, 6M litri'},
                    {'label': 'Specie', 'value': '12.000 esemplari, 600 specie'},
                    {'label': 'Highlights', 'value': 'Delfini, squali, lamantini, pinguini'},
                    {'label': 'Percorso', 'value': '2.5 ore dalla Liguria ai tropici'},
                    {'label': 'Novità 2024', 'value': 'Padiglione Cetacei, mondo coralli'}
                ],
                'opening_hours': 'Tutti i giorni 9:00-20:00 (estate), 10:00-18:00 (inverno)',
                'cost': '€29 adulti, €19 bambini 4-12 anni'
            },
            'cattedrale_genova': {
                'title': 'Cattedrale di San Lorenzo, Genova',
                'summary': 'Il Duomo di Genova, famoso per aver ospitato una bomba navale britannica inesplosa durante la Seconda Guerra Mondiale. Capolavoro di architettura romanico-gotica.',
                'details': [
                    {'label': 'Costruzione', 'value': 'IX secolo, ricostruita XII-XIV secolo'},
                    {'label': 'Stile', 'value': 'Romanico-gotico ligure'},
                    {'label': 'Facciata', 'value': 'Marmo bianco e nero a strisce'},
                    {'label': 'Bomba inesplosa', 'value': '13 febbraio 1941 (esposta nel museo)'},
                    {'label': 'Tesoro', 'value': 'Sacro Catino (Sacro Graal), reliquie di San Giovanni'},
                    {'label': 'Campanile', 'value': 'Torre romanica del XII secolo'},
                    {'label': 'Ingresso', 'value': 'Gratuito (museo €6)'}
                ],
                'timetable': [
                    {'direction': 'Cattedrale', 'times': 'Lun-Sab 8:00-12:00, 15:00-19:00'},
                    {'direction': 'Museo del Tesoro', 'times': 'Lun-Sab 9:00-12:00, 15:00-18:00'}
                ]
            },
            'spianata_castelletto': {
                'title': 'Spianata Castelletto, Genova',
                'summary': 'Il belvedere più spettacolare di Genova, raggiungibile con la storica funicolare del 1929. Vista panoramica a 360° sulla città e il porto.',
                'details': [
                    {'label': 'Altitudine', 'value': '80 metri sul livello del mare'},
                    {'label': 'Funicolare', 'value': 'Costruita nel 1929, rinnovata nel 2004'},
                    {'label': 'Durata salita', 'value': '90 secondi (300 metri di percorso)'},
                    {'label': 'Biglietto funicolare', 'value': '€0.90 (incluso in biglietto AMT)'},
                    {'label': 'Panorama', 'value': 'Centro storico, porto, Riviera di Ponente'},
                    {'label': 'Arte Liberty', 'value': 'Villini e palazzi primi 900'},
                    {'label': 'Miglior orario', 'value': 'Tramonto (18:30-19:30 estate)'}
                ],
                'timetable': [
                    {'direction': 'Funicolare', 'times': '6:00-24:00 ogni 15 minuti'},
                    {'direction': 'Spianata', 'times': 'Sempre accessibile'}
                ]
            },
            'acquario_genova': {
                'title': 'Acquario di Genova',
                'summary': 'Il secondo acquario più grande d\'Europa, nel Porto Antico progettato da Renzo Piano. Casa di 12.000 esemplari di 600 specie diverse.',
                'details': [
                    {'label': 'Dimensioni', 'value': '9.700 m² di superficie espositiva'},
                    {'label': 'Apertura', 'value': '1992 (Expo Colombo 500 anni)'},
                    {'label': 'Architetto', 'value': 'Renzo Piano (Porto Antico)'},
                    {'label': 'Biglietto', 'value': '€29 adulti, €19 bambini'},
                    {'label': 'Orari', 'value': '9:00-20:00 (estate), 9:30-19:00 (inverno)'},
                    {'label': 'Attrazioni', 'value': 'Delfini, squali, lamantini, pinguini'},
                    {'label': 'Record', 'value': '2° in Europa per grandezza'}
                ],
                'timetable': [
                    {'direction': 'Estate (giu-set)', 'times': '9:00-20:00 (ultimo ingresso 18:00)'},
                    {'direction': 'Inverno (ott-mag)', 'times': '9:30-19:00 (ultimo ingresso 17:00)'}
                ],
                'actionLink': {
                    'text': 'Prenota biglietto online',
                    'url': 'https://www.acquariodigenova.it'
                }
            },
            # FIRENZE
            'piazza_del_duomo_firenze': {
                'title': 'Piazza del Duomo, Firenze',
                'summary': 'Il cuore religioso di Firenze con la magnifica Cattedrale di Santa Maria del Fiore, la cupola del Brunelleschi e il Battistero di San Giovanni. Capolavoro del Rinascimento fiorentino.',
                'details': [
                    {'label': 'Cattedrale', 'value': 'Santa Maria del Fiore (1296-1436)'},
                    {'label': 'Cupola Brunelleschi', 'value': 'Diametro 45m, prima cupola ottagonale senza armature'},
                    {'label': 'Battistero San Giovanni', 'value': 'XI-XII secolo, Porte del Paradiso (Ghiberti)'},
                    {'label': 'Campanile di Giotto', 'value': 'XIV secolo, 84 metri, 414 gradini'},
                    {'label': 'Facciata negogotica', 'value': 'XIX secolo (1887), marmi policromi'},
                    {'label': 'Biglietti', 'value': 'Duomo gratuito, cupola €20, campanile €15'}
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
                    {'label': 'Palazzo Vecchio', 'value': 'Sede del Comune (1299-1314), torre 94m'},
                    {'label': 'Loggia dei Lanzi', 'value': 'XIV secolo, statue rinascimentali'},
                    {'label': 'David replica', 'value': 'Copia del capolavoro di Michelangelo'},
                    {'label': 'Perseo Cellini', 'value': 'Bronzo manierista (1545-1554)'},
                    {'label': 'Fontana Nettuno', 'value': 'Ammannati (1565), "Il Biancone"'},
                    {'label': 'Caffè Rivoire', 'value': 'Storico caffè con vista palazzo (1872)'}
                ],
                'opening_hours': 'Sempre accessibile, Palazzo Vecchio: 9:00-19:00',
                'cost': 'Piazza gratuita, Palazzo Vecchio €12.50'
            },
            'ponte_vecchio_firenze': {
                'title': 'Ponte Vecchio, Firenze',
                'summary': 'Il ponte medievale più famoso del mondo, l\'unico ponte di Firenze sopravvissuto alla Seconda Guerra Mondiale. Caratteristico per le botteghe orafe che lo attraversano.',
                'details': [
                    {'label': 'Costruzione', 'value': '1345 (ricostruito dopo alluvione 1333)'},
                    {'label': 'Corridoio Vasariano', 'value': 'Passaggio segreto dei Medici (1565)'},
                    {'label': 'Botteghe storiche', 'value': 'Orafi dal XVI secolo (prima macellai)'},
                    {'label': 'Lunghezza', 'value': '95 metri sull\'Arno'},
                    {'label': 'Guerra mondiale', 'value': 'Unico ponte risparmiato dai tedeschi (1944)'},
                    {'label': 'Taddeo Gaddi', 'value': 'Allievo di Giotto, progettista del ponte'}
                ],
                'opening_hours': 'Sempre accessibile, botteghe: 10:00-19:00',
                'cost': 'Passeggiata gratuita, shopping vari prezzi'
            },
            'basilica_santa_croce_firenze': {
                'title': 'Basilica di Santa Croce, Firenze',
                'summary': 'La chiesa francescana più grande del mondo, chiamata "Pantheon di Firenze" per le tombe di Michelangelo, Galileo e Machiavelli. Capolavoro gotico con affreschi di Giotto.',
                'details': [
                    {'label': 'Costruzione', 'value': '1294-1442, architettura gotica italiana'},
                    {'label': 'Tomba Michelangelo', 'value': 'Sepolcro del maestro rinascimentale (1564)'},
                    {'label': 'Tomba Galileo', 'value': 'Monumento al padre della scienza moderna'},
                    {'label': 'Cappelle Peruzzi e Bardi', 'value': 'Affreschi di Giotto (1320-1325)'},
                    {'label': 'Crocifisso Donatello', 'value': 'Legno policromo rinascimentale'},
                    {'label': 'Cappella Pazzi', 'value': 'Brunelleschi, capolavoro architettonico'}
                ],
                'opening_hours': 'Lun-Sab 9:30-17:00, Dom 14:00-17:00',
                'cost': '€8 adulti, €6 ridotto',
                'actionLink': {
                    'text': 'Informazioni visite',
                    'url': 'https://www.santacroceopera.it'
                }
            },
            'stazione_termini': {
                'title': 'Stazione Roma Termini',
                'summary': 'La stazione ferroviaria principale di Roma, hub centrale per treni regionali, nazionali e metropolitana. Costruita negli anni \'50, serve oltre 150 milioni di passeggeri all\'anno.',
                'details': [
                    {'label': 'Inaugurazione', 'value': '20 dicembre 1950'},
                    {'label': 'Binari', 'value': '29 binari'},
                    {'label': 'Metro', 'value': 'Linea A (rossa) e B (blu)'},
                    {'label': 'Passeggeri/anno', 'value': '150+ milioni'},
                    {'label': 'Servizi', 'value': 'Biglietteria automatica, sala d\'attesa, ristoranti, negozi'},
                    {'label': 'Bagagli', 'value': 'Deposito bagagli disponibile'},
                    {'label': 'WiFi', 'value': 'Gratuito per 1 ora'}
                ],
                'timetable': [
                    {'direction': 'Metro A - Battistini', 'times': 'Ogni 3-6 min (5:30-23:30)'},
                    {'direction': 'Metro B - Laurentina', 'times': 'Ogni 4-7 min (5:30-23:30)'}
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
                    {'label': 'Gradini scalinata', 'value': '135 scalini in travertino'},
                    {'label': 'Costruzione', 'value': '1723-1726'},
                    {'label': 'Architetto', 'value': 'Francesco de Sanctis'},
                    {'label': 'Fontana', 'value': 'Fontana della Barcaccia (Bernini, 1629)'},
                    {'label': 'Shopping', 'value': 'Via Condotti, Via del Babuino'},
                    {'label': 'Curiosità', 'value': 'Vietato sedersi sui gradini (multa €250)'},
                    {'label': 'Metro', 'value': 'Spagna (Linea A)'}
                ],
                'timetable': [
                    {'direction': 'Chiesa Trinità dei Monti', 'times': 'Mar-Dom 10:00-19:00'},
                    {'direction': 'Keats-Shelley Museum', 'times': 'Lun-Sab 10:00-18:00'}
                ]
            },
            'fontana_trevi': {
                'title': 'Fontana di Trevi',
                'summary': 'La fontana barocca più spettacolare al mondo, immortalata in "La Dolce Vita" di Fellini. La tradizione dice che lanciando una moneta con la mano destra sopra la spalla sinistra si tornerà a Roma.',
                'details': [
                    {'label': 'Altezza', 'value': '26.3 metri'},
                    {'label': 'Larghezza', 'value': '49.15 metri'},
                    {'label': 'Architetto', 'value': 'Nicola Salvi'},
                    {'label': 'Completamento', 'value': '1762 (30 anni di lavori)'},
                    {'label': 'Stile', 'value': 'Barocco Romano'},
                    {'label': 'Figura centrale', 'value': 'Nettuno (Oceano)'},
                    {'label': 'Monete raccolte', 'value': '€1.4 milioni/anno (dati alla Caritas)'},
                    {'label': 'Curiosità', 'value': 'Due monete = nuova storia d\'amore'},
                    {'label': 'Miglior orario', 'value': 'Alba (6:00-7:00) per evitare folle'}
                ],
                'timetable': [
                    {'direction': 'Accessibile', 'times': '24h/7gg (illuminazione notturna)'},
                    {'direction': 'Pulizia fontana', 'times': 'Ogni lunedì mattina 7:00-9:00'}
                ]
            },
            'pantheon': {
                'title': 'Pantheon',
                'summary': 'Il tempio romano meglio conservato al mondo, considerato una meraviglia architettonica. La sua cupola fu la più grande per 1.300 anni fino a Brunelleschi. Oggi è basilica cristiana e mausoleo reale.',
                'details': [
                    {'label': 'Costruzione originale', 'value': '27 a.C. (Marco Agrippa)'},
                    {'label': 'Ricostruzione', 'value': '118-128 d.C. (Imperatore Adriano)'},
                    {'label': 'Diametro cupola', 'value': '43.30 metri (= altezza interna)'},
                    {'label': 'Oculus', 'value': '8.2 metri di diametro (unica fonte di luce)'},
                    {'label': 'Materiale', 'value': 'Calcestruzzo romano con pomice'},
                    {'label': 'Sepolture illustri', 'value': 'Raffaello Sanzio, Re Vittorio Emanuele II'},
                    {'label': 'Ingresso', 'value': 'Gratuito (prenotazione consigliata)'},
                    {'label': 'Curiosità', 'value': 'Il pavimento ha pendenze per far defluire la pioggia'}
                ],
                'timetable': [
                    {'direction': 'Lun-Sab', 'times': '9:00-19:00 (ultimo ingresso 18:45)'},
                    {'direction': 'Domenica', 'times': '9:00-18:00 (ultimo ingresso 17:45)'},
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
                    {'label': 'Forma originale', 'value': 'Stadio di Domiziano (86 d.C., 30.000 spettatori)'},
                    {'label': 'Trasformazione', 'value': 'XV secolo - da stadio a piazza'},
                    {'label': 'Lunghezza', 'value': '276 metri'},
                    {'label': 'Fontana centrale', 'value': 'Fontana dei Quattro Fiumi (Bernini, 1651)'},
                    {'label': 'Fontana sud', 'value': 'Fontana del Moro (Bernini)'},
                    {'label': 'Fontana nord', 'value': 'Fontana del Nettuno'},
                    {'label': 'Chiesa', 'value': 'Sant\'Agnese in Agone (Borromini)'},
                    {'label': 'Leggenda', 'value': 'Statua del Nilo copre gli occhi per non vedere la chiesa'},
                    {'label': 'Mercatino', 'value': 'Befana (6 gennaio) e Natale'}
                ],
                'timetable': [
                    {'direction': 'Caffè storici', 'times': 'Caffè Domiziano, Tre Scalini (7:00-1:00)'},
                    {'direction': 'Artisti di strada', 'times': 'Tutti i giorni 10:00-24:00'},
                    {'direction': 'Chiesa S. Agnese', 'times': 'Mar-Dom 9:30-12:30, 15:30-19:00'}
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
        print(f"✅ Trovati dettagli per {context}: {result.get('title', 'N/A')}")
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
@require_login
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
        
    profile = UserProfile.query.filter_by(user_id=auth_user.id).first()
    
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
                <div class="flex flex-col items-center mb-8">
                    <div class="w-20 h-20 bg-gray-700 rounded-full flex items-center justify-center mb-3 border-2 border-violet-500">
                        <span class="text-2xl">👤</span>
                    </div>
                    <h3 class="text-white text-xl font-semibold">{{ auth_user.first_name }} {{ auth_user.last_name }}</h3>
                    <p class="text-gray-400 text-sm">{{ auth_user.email }}</p>
                </div>

                {% if not profile %}
                <!-- Nuovo Profilo -->
                <div class="bg-gray-800 rounded-xl p-6 mb-6 border border-gray-700">
                    <div class="text-center">
                        <div class="w-16 h-16 bg-violet-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                            <span class="text-2xl">✨</span>
                        </div>
                        <h3 class="text-white text-lg font-semibold mb-2">Personalizza i tuoi viaggi</h3>
                        <p class="text-gray-400 mb-6 text-sm">Configura le tue preferenze per ricevere consigli su misura</p>
                        <button onclick="window.location.href='/profile/create'" class="w-full bg-violet-500 text-white py-3 rounded-xl font-semibold">
                            Crea il Tuo Profilo
                        </button>
                    </div>
                </div>
                {% else %}
                <!-- Profilo Esistente -->
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
                {% endif %}

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
    ''', profile=profile, auth_user=auth_user)

@app.route('/profile/create', methods=['GET', 'POST'])
@require_login
def create_profile():
    """Crea un nuovo profilo utente"""
    from flask_login import current_user as auth_user
    
    # Usa utente realmente autenticato
    if not auth_user.is_authenticated:
        return redirect('/auth/login')
    
    # Controlla se esiste già un profilo (commentato per permettere test)
    # existing_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    # if existing_profile:
    #     return redirect(url_for('view_profile'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Controlla se esiste già un profilo
        existing_profile = UserProfile.query.filter_by(user_id=auth_user.id).first()
        
        if existing_profile:
            # Aggiorna il profilo esistente invece di crearne uno nuovo
            profile = existing_profile
            
            # Gestisce interessi
            interests = data.get('interests', [])
            if isinstance(interests, str):
                interests = [i.strip() for i in interests.split(',') if i.strip()]
            profile.set_interests(interests)
            
            profile.travel_pace = data.get('travel_pace')
            profile.budget = data.get('budget')
            profile.updated_at = datetime.now()
        else:
            # Crea nuovo profilo
            profile = UserProfile()
            profile.user_id = auth_user.id
            
            # Gestisce interessi
            interests = data.get('interests', [])
            if isinstance(interests, str):
                interests = [i.strip() for i in interests.split(',') if i.strip()]
            profile.set_interests(interests)
            
            profile.travel_pace = data.get('travel_pace')
            profile.budget = data.get('budget')
            
            db.session.add(profile)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Profilo creato con successo',
                'profile': profile.to_dict()
            })
        else:
            flash('Profilo creato con successo!')
            return redirect(url_for('view_profile'))
    
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
@require_login
def edit_profile():
    """Modifica il profilo dell'utente corrente"""
    from flask_login import current_user as auth_user
    
    # Usa utente realmente autenticato
    if not auth_user.is_authenticated:
        return redirect('/auth/login')
        
    profile = UserProfile.query.filter_by(user_id=auth_user.id).first()
    if not profile:
        flash('Devi prima creare un profilo.')
        return redirect(url_for('create_profile'))
    
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
@require_login
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
@require_login
def get_profile_api():
    """API per ottenere il profilo dell'utente corrente"""
    current_user = get_current_user()  # Usa mock user
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({'profile': None})
    
    return jsonify({'profile': profile.to_dict()})

@app.route('/api/profile', methods=['POST'])
@require_login
def create_profile_api():
    """API per creare un profilo"""
    return create_profile()

@app.route('/api/profile', methods=['PUT'])
@require_login
def update_profile_api():
    """API per aggiornare un profilo"""
    return edit_profile()

@app.route('/api/profile', methods=['DELETE'])
@require_login
def delete_profile_api():
    """API per eliminare un profilo"""
    return delete_profile()

# === ADMIN ROUTES (per funzionalità future) ===

@app.route('/admin/profiles')
@require_login
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)