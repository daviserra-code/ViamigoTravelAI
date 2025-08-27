from flask import session, render_template_string, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from models import User, UserProfile, AdminUser
import logging
from functools import wraps

# Import app and db after initialization to avoid circular imports
def get_app_db():
    from flask_app import app, db
    return app, db

app, db = get_app_db()

# Temporary workaround for auth - create mock endpoints for demo
def require_login(f):
    """Mock login decorator for demo - simula utente autenticato"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Per demo, simula sempre un utente loggato con ID fisso
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

@app.route('/auth/login')
def auth_login():
    """Login page con design di Gemini integrato"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viamigo - Login</title>
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
            <!-- PAGINA LOGIN -->
            <div class="flex-grow flex flex-col justify-center items-center p-8">
                <div class="text-center mb-12">
                    <svg class="w-20 h-20 self-center mx-auto" viewBox="0 0 100 100">
                        <defs>
                            <linearGradient id="g-login" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#8b5cf6"/>
                                <stop offset="100%" stop-color="#a78bfa"/>
                            </linearGradient>
                        </defs>
                        <path d="M20 80 C 30 40, 70 40, 80 80 L 50 20 Z" fill="url(#g-login)"/>
                    </svg>
                    <h1 class="text-5xl font-bold self-end mt-4 viamigo-font">Viamigo</h1>
                    <p class="text-gray-400 mt-2">Il tuo compagno di viaggio intelligente.</p>
                </div>
                
                <form id="login-form" class="w-full space-y-4" onsubmit="handleLogin(event)">
                    <input type="email" name="email" placeholder="Email" 
                           class="w-full bg-gray-800 text-white p-4 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-violet-500">
                    <input type="password" name="password" placeholder="Password" 
                           class="w-full bg-gray-800 text-white p-4 rounded-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-violet-500">
                    <button type="submit" class="w-full font-bold py-4 rounded-xl text-lg bg-violet-500 text-white hover:bg-violet-600 transition-colors">
                        Accedi
                    </button>
                </form>
                
                <div class="text-center mt-6 space-y-3">
                    <a href="#" class="text-sm text-gray-400 hover:text-white block">Password dimenticata?</a>
                    <div class="border-t border-gray-700 pt-4">
                        <p class="text-sm text-gray-400 mb-3">Demo per sviluppo:</p>
                        <button onclick="demoLogin()" class="w-full font-semibold py-3 rounded-xl text-sm bg-gray-700 text-white hover:bg-gray-600 transition-colors">
                            Accesso Demo
                        </button>
                    </div>
                    <div class="mt-4">
                        <a href="/" class="text-sm text-violet-400 hover:text-violet-300">← Torna alla Home</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function handleLogin(event) {
            event.preventDefault();
            const email = event.target.email.value;
            const password = event.target.password.value;
            
            if (!email || !password) {
                alert('Inserisci email e password');
                return;
            }
            
            // In futuro qui implementeremo l'autenticazione reale con Replit Auth
            alert('Funzionalità di login in sviluppo. Usa "Accesso Demo" per ora.');
        }
        
        function demoLogin() {
            // Redirect al profilo per demo
            window.location.href = '/profile';
        }
    </script>
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
        # Home page per utenti loggati (mantiene UI originale)
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Viamigo - Home</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50 min-h-screen">
            <nav class="bg-blue-600 text-white p-4">
                <div class="container mx-auto flex justify-between items-center">
                    <h1 class="text-xl font-bold">Viamigo</h1>
                    <div class="space-x-4">
                        <span>Ciao, Marco</span>
                        <a href="/profile" class="bg-blue-500 px-3 py-1 rounded">Profilo</a>
                        <a href="/auth/logout" class="bg-red-500 px-3 py-1 rounded">Logout</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mx-auto p-8">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-2xl font-bold mb-4">Benvenuto in Viamigo!</h2>
                    <p class="text-gray-600 mb-6">Il tuo assistente AI per viaggi personalizzati in Italia.</p>
                    
                    <div class="grid md:grid-cols-2 gap-6">
                        <div class="border rounded-lg p-4">
                            <h3 class="font-semibold mb-2">Pianifica Viaggio</h3>
                            <p class="text-sm text-gray-600 mb-4">Crea itinerari personalizzati</p>
                            <a href="/planner" class="bg-blue-600 text-white px-4 py-2 rounded">Inizia</a>
                        </div>
                        
                        <div class="border rounded-lg p-4">
                            <h3 class="font-semibold mb-2">Il Tuo Profilo</h3>
                            <p class="text-sm text-gray-600 mb-4">Gestisci preferenze di viaggio</p>
                            <a href="/profile" class="bg-green-600 text-white px-4 py-2 rounded">Gestisci</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        ''')
    else:
        # Landing page originale con logo e UI esistente
        return redirect('/static/index.html')

@app.route('/planner')
def planner():
    """Redirect alla pagina originale di pianificazione"""
    return redirect('/static/index.html')

# === CRUD ROUTES PER USER PROFILE ===

@app.route('/demo-dashboard')  
def demo_dashboard():
    """Demo di accesso per mostrare l'integrazione profilo"""
    return redirect('/profile')

@app.route('/profile')
@require_login
def view_profile():
    """Visualizza il profilo dell'utente - design mobile uniforme a Viamigo"""
    profile = None  # UserProfile.query.filter_by(user_id=current_user.id).first()
    
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
                    <h3 class="text-white text-xl font-semibold">Marco Rossi</h3>
                    <p class="text-gray-400 text-sm">marco@email.com</p>
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
    ''', profile=profile)

@app.route('/profile/create', methods=['GET', 'POST'])
@require_login
def create_profile():
    """Crea un nuovo profilo utente"""
    current_user = get_current_user()  # Usa mock user
    
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
    current_user = get_current_user()  # Usa mock user
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