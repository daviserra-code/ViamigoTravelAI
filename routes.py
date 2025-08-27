from flask import session, render_template_string, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from models import User, UserProfile, AdminUser
import logging

# Import app and db after initialization to avoid circular imports
def get_app_db():
    from flask_app import app, db
    return app, db

app, db = get_app_db()

# Temporary workaround for auth - create mock endpoints for demo
def require_login(f):
    """Mock login decorator for demo"""
    return f

@app.route('/auth/login')
def auth_login():
    """Mock login endpoint for demo"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Viamigo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-blue-600 min-h-screen flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg max-w-md w-full mx-4">
            <h2 class="text-2xl font-bold mb-6 text-center">Accesso Temporaneo</h2>
            <p class="text-gray-600 mb-6 text-center">
                L'autenticazione Replit è in configurazione.<br>
                Per ora usa la demo.
            </p>
            <div class="space-y-4">
                <a href="/" class="block w-full bg-blue-600 text-white py-3 rounded text-center">
                    Torna alla Home
                </a>
                <button onclick="history.back()" class="block w-full bg-gray-200 text-gray-700 py-3 rounded text-center">
                    Indietro
                </button>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/auth/logout')
def auth_logout():
    """Mock logout endpoint"""
    return redirect('/')

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
    # Check if user is authenticated (mock for demo)
    user_authenticated = False  # Since Replit auth not working yet
    
    if user_authenticated:
        # Mobile-first home page for logged users
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Viamigo</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                .mobile-container { max-width: 428px; margin: 0 auto; }
                .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            </style>
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="mobile-container bg-white min-h-screen">
                <!-- Header -->
                <div class="gradient-bg text-white p-6 pb-8 rounded-b-3xl">
                    <div class="flex justify-between items-center mb-6">
                        <h1 class="text-2xl font-bold">Viamigo</h1>
                        <div class="w-8 h-8 bg-white bg-opacity-30 rounded-full flex items-center justify-center">
                            <span class="text-sm">👤</span>
                        </div>
                    </div>
                    <div>
                        <h2 class="text-lg mb-1">Ciao, Marco!</h2>
                        <p class="text-blue-100">Pronto per la prossima avventura?</p>
                    </div>
                </div>
                
                <!-- Main Actions -->
                <div class="p-6 -mt-4">
                    <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
                        <h3 class="text-lg font-semibold mb-4">Azioni Rapide</h3>
                        <div class="space-y-3">
                            <a href="/planner" class="flex items-center justify-between p-4 bg-blue-50 rounded-xl">
                                <div class="flex items-center">
                                    <div class="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center mr-3">
                                        <span class="text-white text-lg">🗺️</span>
                                    </div>
                                    <div>
                                        <p class="font-medium">Pianifica Viaggio</p>
                                        <p class="text-sm text-gray-500">Crea nuovo itinerario</p>
                                    </div>
                                </div>
                                <span class="text-blue-500">→</span>
                            </a>
                            
                            <a href="/profile" class="flex items-center justify-between p-4 bg-green-50 rounded-xl">
                                <div class="flex items-center">
                                    <div class="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center mr-3">
                                        <span class="text-white text-lg">⚙️</span>
                                    </div>
                                    <div>
                                        <p class="font-medium">Il Tuo Profilo</p>
                                        <p class="text-sm text-gray-500">Preferenze viaggio</p>
                                    </div>
                                </div>
                                <span class="text-green-500">→</span>
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- Bottom Navigation -->
                <div class="fixed bottom-0 left-1/2 transform -translate-x-1/2 w-full max-w-lg bg-white border-t p-4">
                    <div class="flex justify-around">
                        <button class="flex flex-col items-center p-2 text-blue-500">
                            <span class="text-xl mb-1">🏠</span>
                            <span class="text-xs">Home</span>
                        </button>
                        <button class="flex flex-col items-center p-2 text-gray-400">
                            <span class="text-xl mb-1">🗺️</span>
                            <span class="text-xs">Viaggi</span>
                        </button>
                        <button class="flex flex-col items-center p-2 text-gray-400">
                            <span class="text-xl mb-1">👤</span>
                            <span class="text-xs">Profilo</span>
                        </button>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''')
    else:
        # Mobile-first login page
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Viamigo - Accedi</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                .mobile-container { max-width: 428px; margin: 0 auto; }
                .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            </style>
        </head>
        <body class="gradient-bg min-h-screen flex items-center justify-center p-4">
            <div class="mobile-container w-full">
                <!-- Logo Section -->
                <div class="text-center mb-8">
                    <div class="w-20 h-20 bg-white bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span class="text-3xl">✈️</span>
                    </div>
                    <h1 class="text-4xl font-bold text-white mb-2">Viamigo</h1>
                    <p class="text-blue-100">Il tuo assistente AI per viaggi in Italia</p>
                </div>
                
                <!-- Login Card -->
                <div class="bg-white rounded-3xl p-8 shadow-2xl">
                    <h2 class="text-2xl font-bold text-gray-800 mb-2 text-center">Benvenuto!</h2>
                    <p class="text-gray-600 text-center mb-8">Accedi per iniziare a pianificare</p>
                    
                    <!-- Mock Login Button (Demo) -->
                    <button onclick="mockLogin()" class="w-full bg-blue-600 text-white py-4 rounded-2xl font-semibold text-lg mb-4 shadow-lg">
                        Accedi Demo
                    </button>
                    
                    <!-- Auth Button (Real - currently 404) -->
                    <a href="/auth/login" class="block w-full bg-gray-100 text-gray-700 py-4 rounded-2xl font-semibold text-lg text-center mb-6">
                        Accedi con Replit
                    </a>
                    
                    <div class="text-center">
                        <p class="text-sm text-gray-500">
                            Creando un account accetti i nostri<br>
                            <a href="#" class="text-blue-600">Termini di Servizio</a> e 
                            <a href="#" class="text-blue-600">Privacy Policy</a>
                        </p>
                    </div>
                </div>
                
                <!-- Features Preview -->
                <div class="mt-8 grid grid-cols-3 gap-4 text-center">
                    <div class="text-white">
                        <div class="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center mx-auto mb-2">
                            <span class="text-lg">🎯</span>
                        </div>
                        <p class="text-xs">Personalizzato</p>
                    </div>
                    <div class="text-white">
                        <div class="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center mx-auto mb-2">
                            <span class="text-lg">🤖</span>
                        </div>
                        <p class="text-xs">AI-Powered</p>
                    </div>
                    <div class="text-white">
                        <div class="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center mx-auto mb-2">
                            <span class="text-lg">📍</span>
                        </div>
                        <p class="text-xs">GPS Preciso</p>
                    </div>
                </div>
            </div>
            
            <script>
                function mockLogin() {
                    // Mock login for demo purposes
                    window.location.href = '/demo-dashboard';
                }
            </script>
        </body>
        </html>
        ''')

@app.route('/planner')
def planner():
    """Redirect alla pagina originale di pianificazione"""
    return redirect('/static/index.html')

# === CRUD ROUTES PER USER PROFILE ===

@app.route('/demo-dashboard')
def demo_dashboard():
    """Demo dashboard per mostrare l'app funzionante"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Viamigo - Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .mobile-container { max-width: 428px; margin: 0 auto; }
            .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="mobile-container bg-white min-h-screen">
            <!-- Header -->
            <div class="gradient-bg text-white p-6 pb-8 rounded-b-3xl">
                <div class="flex justify-between items-center mb-6">
                    <h1 class="text-2xl font-bold">Viamigo</h1>
                    <button onclick="showProfileMenu()" class="w-8 h-8 bg-white bg-opacity-30 rounded-full flex items-center justify-center">
                        <span class="text-sm">👤</span>
                    </button>
                </div>
                <div>
                    <h2 class="text-lg mb-1">Ciao, Marco!</h2>
                    <p class="text-blue-100">Hai 2 viaggi pianificati</p>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="p-6 -mt-4">
                <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <h3 class="text-lg font-semibold mb-4">Azioni Rapide</h3>
                    <div class="space-y-3">
                        <a href="/profile" class="flex items-center justify-between p-4 bg-blue-50 rounded-xl">
                            <div class="flex items-center">
                                <div class="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center mr-3">
                                    <span class="text-white text-lg">🗺️</span>
                                </div>
                                <div>
                                    <p class="font-medium">Crea Profilo</p>
                                    <p class="text-sm text-gray-500">Personalizza preferenze</p>
                                </div>
                            </div>
                            <span class="text-blue-500">→</span>
                        </a>
                        
                        <a href="/planner" class="flex items-center justify-between p-4 bg-green-50 rounded-xl">
                            <div class="flex items-center">
                                <div class="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center mr-3">
                                    <span class="text-white text-lg">✨</span>
                                </div>
                                <div>
                                    <p class="font-medium">AI Planner</p>
                                    <p class="text-sm text-gray-500">Pianificatore originale</p>
                                </div>
                            </div>
                            <span class="text-green-500">→</span>
                        </a>
                    </div>
                </div>
                
                <!-- Recent Trips -->
                <div class="bg-white rounded-2xl shadow-lg p-6 mb-20">
                    <h3 class="text-lg font-semibold mb-4">I Tuoi Viaggi</h3>
                    <div class="space-y-3">
                        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                            <div class="flex items-center">
                                <div class="w-10 h-10 bg-orange-100 rounded-xl flex items-center justify-center mr-3">
                                    <span class="text-orange-600 text-lg">🏛️</span>
                                </div>
                                <div>
                                    <p class="font-medium">Roma - 3 giorni</p>
                                    <p class="text-sm text-gray-500">Maggio 2025</p>
                                </div>
                            </div>
                            <span class="text-gray-400">💾</span>
                        </div>
                        
                        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                            <div class="flex items-center">
                                <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center mr-3">
                                    <span class="text-blue-600 text-lg">🏖️</span>
                                </div>
                                <div>
                                    <p class="font-medium">Costiera Amalfitana</p>
                                    <p class="text-sm text-gray-500">Giugno 2025</p>
                                </div>
                            </div>
                            <span class="text-gray-400">💾</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Bottom Navigation -->
            <div class="fixed bottom-0 left-1/2 transform -translate-x-1/2 w-full max-w-lg bg-white border-t p-4">
                <div class="flex justify-around">
                    <button class="flex flex-col items-center p-2 text-blue-500">
                        <span class="text-xl mb-1">🏠</span>
                        <span class="text-xs">Home</span>
                    </button>
                    <button class="flex flex-col items-center p-2 text-gray-400">
                        <span class="text-xl mb-1">🗺️</span>
                        <span class="text-xs">Viaggi</span>
                    </button>
                    <button onclick="window.location.href='/profile'" class="flex flex-col items-center p-2 text-gray-400">
                        <span class="text-xl mb-1">👤</span>
                        <span class="text-xs">Profilo</span>
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            function showProfileMenu() {
                alert('Menu Profilo: Impostazioni, Logout, ecc.');
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/profile')
@require_login
def view_profile():
    """Visualizza e gestisci il profilo utente con UI mobile"""
    # Mock profile data for demo
    profile = None  # UserProfile.query.filter_by(user_id=current_user.id).first()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profilo - Viamigo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .mobile-container { max-width: 428px; margin: 0 auto; }
            .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <div class="mobile-container bg-white min-h-screen">
            <!-- Header -->
            <div class="gradient-bg text-white p-6 pb-8 rounded-b-3xl">
                <div class="flex justify-between items-center mb-6">
                    <button onclick="history.back()" class="w-8 h-8 bg-white bg-opacity-30 rounded-full flex items-center justify-center">
                        <span class="text-sm">←</span>
                    </button>
                    <h1 class="text-xl font-bold">Il Mio Profilo</h1>
                    <button onclick="editProfile()" class="w-8 h-8 bg-white bg-opacity-30 rounded-full flex items-center justify-center">
                        <span class="text-sm">✏️</span>
                    </button>
                </div>
                <div class="text-center">
                    <div class="w-20 h-20 bg-white bg-opacity-30 rounded-full flex items-center justify-center mx-auto mb-3">
                        <span class="text-2xl">👤</span>
                    </div>
                    <h2 class="text-lg font-semibold">Marco Rossi</h2>
                    <p class="text-blue-100">marco@email.com</p>
                </div>
            </div>
            
            <!-- Profile Content -->
            <div class="p-6 -mt-4">
                {% if not profile %}
                <!-- Crea Profilo -->
                <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <div class="text-center">
                        <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <span class="text-2xl">✨</span>
                        </div>
                        <h3 class="text-lg font-semibold mb-2">Personalizza i tuoi viaggi</h3>
                        <p class="text-gray-600 mb-6">Configura le tue preferenze per ricevere consigli su misura</p>
                        <button onclick="createProfile()" class="w-full bg-blue-600 text-white py-4 rounded-xl font-semibold">
                            Crea il Tuo Profilo
                        </button>
                    </div>
                </div>
                {% else %}
                <!-- Profilo Esistente -->
                <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <h3 class="text-lg font-semibold mb-4">Preferenze di Viaggio</h3>
                    
                    <div class="space-y-4">
                        <div>
                            <p class="text-sm text-gray-500 mb-2">I tuoi interessi</p>
                            <div class="flex flex-wrap gap-2">
                                <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">🍝 Cibo</span>
                                <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">🎨 Arte</span>
                                <span class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">🏛️ Storia</span>
                            </div>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <p class="text-sm text-gray-500 mb-1">Ritmo di viaggio</p>
                                <p class="font-medium">🐌 Lento</p>
                            </div>
                            <div>
                                <p class="text-sm text-gray-500 mb-1">Budget</p>
                                <p class="font-medium">💰 €€</p>
                            </div>
                        </div>
                    </div>
                </div>
                {% endif %}
                
                <!-- Settings -->
                <div class="bg-white rounded-2xl shadow-lg p-6 mb-20">
                    <h3 class="text-lg font-semibold mb-4">Impostazioni</h3>
                    
                    <div class="space-y-3">
                        <button onclick="editProfile()" class="flex items-center justify-between w-full p-4 bg-gray-50 rounded-xl">
                            <div class="flex items-center">
                                <span class="text-lg mr-3">✏️</span>
                                <span>Modifica Profilo</span>
                            </div>
                            <span class="text-gray-400">→</span>
                        </button>
                        
                        <button onclick="exportData()" class="flex items-center justify-between w-full p-4 bg-gray-50 rounded-xl">
                            <div class="flex items-center">
                                <span class="text-lg mr-3">📥</span>
                                <span>Esporta Dati</span>
                            </div>
                            <span class="text-gray-400">→</span>
                        </button>
                        
                        <button onclick="deleteProfile()" class="flex items-center justify-between w-full p-4 bg-red-50 rounded-xl text-red-600">
                            <div class="flex items-center">
                                <span class="text-lg mr-3">🗑️</span>
                                <span>Elimina Profilo</span>
                            </div>
                            <span class="text-red-400">→</span>
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Bottom Navigation -->
            <div class="fixed bottom-0 left-1/2 transform -translate-x-1/2 w-full max-w-lg bg-white border-t p-4">
                <div class="flex justify-around">
                    <button onclick="window.location.href='/demo-dashboard'" class="flex flex-col items-center p-2 text-gray-400">
                        <span class="text-xl mb-1">🏠</span>
                        <span class="text-xs">Home</span>
                    </button>
                    <button class="flex flex-col items-center p-2 text-gray-400">
                        <span class="text-xl mb-1">🗺️</span>
                        <span class="text-xs">Viaggi</span>
                    </button>
                    <button class="flex flex-col items-center p-2 text-blue-500">
                        <span class="text-xl mb-1">👤</span>
                        <span class="text-xs">Profilo</span>
                    </button>
                </div>
            </div>
        </div>
        
        <script>
            function createProfile() {
                window.location.href = '/profile/create';
            }
            
            function editProfile() {
                window.location.href = '/profile/edit';
            }
            
            function exportData() {
                alert('Funzionalità di esportazione dati in arrivo!');
            }
            
            function deleteProfile() {
                if (confirm('Sei sicuro di voler eliminare il tuo profilo?')) {
                    alert('Profilo eliminato (demo)');
                }
            }
        </script>
    </body>
    </html>
    ''', profile=profile)

@app.route('/profile/create', methods=['GET', 'POST'])
@require_login
def create_profile():
    """Crea un nuovo profilo utente"""
    # Controlla se esiste già un profilo
    existing_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if existing_profile:
        flash('Hai già un profilo configurato.')
        return redirect(url_for('view_profile'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Crea nuovo profilo
        profile = UserProfile()
        profile.user_id = current_user.id
        
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
    
    # GET request - mostra form
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crea Profilo - Viamigo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/" class="text-xl font-bold">Viamigo</a>
                <a href="/profile" class="bg-blue-500 px-3 py-1 rounded">Torna al Profilo</a>
            </div>
        </nav>
        
        <div class="container mx-auto p-8">
            <div class="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
                <h2 class="text-2xl font-bold mb-6">Crea il Tuo Profilo di Viaggio</h2>
                
                <form method="POST" class="space-y-6">
                    <div>
                        <label class="block font-medium mb-2">I Tuoi Interessi</label>
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {% for interest in ['Cibo', 'Arte', 'Relax', 'Avventura', 'Storia', 'Natura', 'Shopping', 'Nightlife'] %}
                            <label class="flex items-center">
                                <input type="checkbox" name="interests" value="{{ interest }}" class="mr-2">
                                <span>{{ interest }}</span>
                            </label>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div>
                        <label class="block font-medium mb-2">Ritmo di Viaggio</label>
                        <select name="travel_pace" class="w-full border rounded px-3 py-2">
                            <option value="">Seleziona...</option>
                            <option value="Lento">Lento - Mi piace prendermi il mio tempo</option>
                            <option value="Moderato">Moderato - Un buon equilibrio</option>
                            <option value="Veloce">Veloce - Voglio vedere tutto</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block font-medium mb-2">Budget</label>
                        <select name="budget" class="w-full border rounded px-3 py-2">
                            <option value="">Seleziona...</option>
                            <option value="€">€ - Economico</option>
                            <option value="€€">€€ - Medio</option>
                            <option value="€€€">€€€ - Alto</option>
                        </select>
                    </div>
                    
                    <div class="flex space-x-4">
                        <button type="submit" class="bg-green-600 text-white px-6 py-2 rounded">Crea Profilo</button>
                        <a href="/profile" class="bg-gray-500 text-white px-6 py-2 rounded">Annulla</a>
                    </div>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/profile/edit', methods=['GET', 'POST'])
@require_login
def edit_profile():
    """Modifica il profilo dell'utente corrente"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
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
    
    # GET request - mostra form pre-compilato
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Modifica Profilo - Viamigo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/" class="text-xl font-bold">Viamigo</a>
                <a href="/profile" class="bg-blue-500 px-3 py-1 rounded">Torna al Profilo</a>
            </div>
        </nav>
        
        <div class="container mx-auto p-8">
            <div class="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold">Modifica Profilo</h2>
                    <button onclick="deleteProfile()" class="bg-red-600 text-white px-4 py-2 rounded">Elimina Profilo</button>
                </div>
                
                <form method="POST" class="space-y-6">
                    <div>
                        <label class="block font-medium mb-2">I Tuoi Interessi</label>
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {% for interest in ['Cibo', 'Arte', 'Relax', 'Avventura', 'Storia', 'Natura', 'Shopping', 'Nightlife'] %}
                            <label class="flex items-center">
                                <input type="checkbox" name="interests" value="{{ interest }}" 
                                       {% if interest in profile.get_interests() %}checked{% endif %} class="mr-2">
                                <span>{{ interest }}</span>
                            </label>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div>
                        <label class="block font-medium mb-2">Ritmo di Viaggio</label>
                        <select name="travel_pace" class="w-full border rounded px-3 py-2">
                            <option value="">Seleziona...</option>
                            <option value="Lento" {% if profile.travel_pace == 'Lento' %}selected{% endif %}>Lento - Mi piace prendermi il mio tempo</option>
                            <option value="Moderato" {% if profile.travel_pace == 'Moderato' %}selected{% endif %}>Moderato - Un buon equilibrio</option>
                            <option value="Veloce" {% if profile.travel_pace == 'Veloce' %}selected{% endif %}>Veloce - Voglio vedere tutto</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block font-medium mb-2">Budget</label>
                        <select name="budget" class="w-full border rounded px-3 py-2">
                            <option value="">Seleziona...</option>
                            <option value="€" {% if profile.budget == '€' %}selected{% endif %}>€ - Economico</option>
                            <option value="€€" {% if profile.budget == '€€' %}selected{% endif %}>€€ - Medio</option>
                            <option value="€€€" {% if profile.budget == '€€€' %}selected{% endif %}>€€€ - Alto</option>
                        </select>
                    </div>
                    
                    <div class="flex space-x-4">
                        <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded">Salva Modifiche</button>
                        <a href="/profile" class="bg-gray-500 text-white px-6 py-2 rounded">Annulla</a>
                    </div>
                </form>
            </div>
        </div>
        
        <script>
        function deleteProfile() {
            if (confirm('Sei sicuro di voler eliminare il tuo profilo? Questa azione non può essere annullata.')) {
                fetch('/profile/delete', {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Profilo eliminato con successo');
                        window.location.href = '/profile';
                    } else {
                        alert('Errore nell\\'eliminazione del profilo');
                    }
                });
            }
        }
        </script>
    </body>
    </html>
    ''', profile=profile)

@app.route('/profile/delete', methods=['DELETE'])
@require_login
def delete_profile():
    """Elimina il profilo dell'utente corrente"""
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