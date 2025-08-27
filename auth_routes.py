from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template_string, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User
import uuid
import re

# Blueprint per routes di autenticazione
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_db_session():
    """Helper per ottenere sessione database"""
    db = get_db()
    return db.session if db else None

def validate_password(password):
    """Valida password secondo standard di sicurezza"""
    if len(password) < 8:
        return False, "La password deve essere di almeno 8 caratteri"
    if not re.search(r'[A-Z]', password):
        return False, "La password deve contenere almeno una lettera maiuscola"
    if not re.search(r'[a-z]', password):
        return False, "La password deve contenere almeno una lettera minuscola"
    if not re.search(r'\d', password):
        return False, "La password deve contenere almeno un numero"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La password deve contenere almeno un carattere speciale"
    return True, "Password valida"

def validate_email(email):
    """Valida formato email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registrazione nuovo utente"""
    if request.method == 'GET':
        # Mostra form di registrazione
        return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registrazione - Viamigo</title>
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
                <div class="text-center">
                    <h1 class="text-2xl font-bold viamigo-font">Viamigo</h1>
                    <p class="text-xs text-gray-400">Crea il tuo account</p>
                </div>
            </div>
            
            <!-- CONTENUTO FORM -->
            <div class="flex-grow overflow-y-auto p-4">
                <form id="registerForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Nome *</label>
                        <input type="text" name="first_name" required 
                               class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Cognome *</label>
                        <input type="text" name="last_name" required 
                               class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Email *</label>
                        <input type="email" name="email" required 
                               class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Password *</label>
                        <input type="password" name="password" required 
                               class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                        <div class="text-xs text-gray-400 mt-1">
                            Minimo 8 caratteri, con maiuscola, minuscola, numero e carattere speciale
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Conferma Password *</label>
                        <input type="password" name="confirm_password" required 
                               class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Indirizzo (opzionale)</label>
                        <input type="text" name="address" 
                               class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                    </div>
                    
                    <div id="errorMessage" class="hidden text-red-400 text-sm bg-red-900/20 p-3 rounded-lg border border-red-700"></div>
                    
                    <button type="submit" 
                            class="w-full bg-gradient-to-r from-violet-600 to-purple-600 text-white py-3 px-4 rounded-lg hover:from-violet-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-violet-500 font-medium">
                        Crea Account
                    </button>
                    
                    <div class="text-center mt-4">
                        <p class="text-sm text-gray-400">
                            Hai già un account? 
                            <a href="/auth/login" class="text-violet-400 hover:text-violet-300 font-medium">Accedi qui</a>
                        </p>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            // Validazione client-side
            if (data.password !== data.confirm_password) {
                showError('Le password non corrispondono');
                return;
            }
            
            try {
                const response = await fetch('/auth/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showSuccessPopup('Account creato con successo!', '/auth/login');
                } else {
                    showError(result.error || 'Errore durante la registrazione');
                }
            } catch (error) {
                showError('Errore di connessione');
            }
        });
        
        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }

        function showSuccessPopup(message, redirectUrl) {
            const overlay = document.createElement("div");
            overlay.className = "fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50";
            
            const popup = document.createElement("div");
            popup.className = "bg-gray-800 rounded-xl p-6 mx-4 max-w-sm w-full border border-gray-600";
            popup.innerHTML = `
                <div class="text-center">
                    <div class="text-4xl mb-4">✅</div>
                    <h3 class="text-white font-semibold mb-2">${message}</h3>
                    <p class="text-gray-400 text-sm mb-4">Verrai reindirizzato alla pagina di login</p>
                    <button onclick="proceedToLogin()" class="w-full bg-gradient-to-r from-violet-600 to-purple-600 text-white py-2 rounded-lg font-medium hover:from-violet-700 hover:to-purple-700">
                        Continua
                    </button>
                </div>
            `;
            
            overlay.appendChild(popup);
            document.body.appendChild(overlay);
            
            setTimeout(() => { window.location.href = redirectUrl; }, 3000);
            window.proceedToLogin = function() { window.location.href = redirectUrl; };
        }
    </script>
</body>
</html>
        ''')
    
    elif request.method == 'POST':
        # Processa registrazione
        data = request.get_json()
        db_session = get_db_session()
        
        if not db_session:
            return jsonify({'error': 'Database non disponibile'}), 500
        
        # Validazioni
        required_fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} obbligatorio'}), 400
        
        if data['password'] != data['confirm_password']:
            return jsonify({'error': 'Le password non corrispondono'}), 400
        
        # Validazione email
        if not validate_email(data['email']):
            return jsonify({'error': 'Formato email non valido'}), 400
        
        # Validazione password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Verifica email univoca
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email già registrata'}), 400
        
        try:
            # Crea nuovo utente
            new_user = User(
                id=str(uuid.uuid4()),
                email=data['email'].lower().strip(),
                first_name=data['first_name'].strip(),
                last_name=data['last_name'].strip(),
                address=data.get('address', '').strip() or None
            )
            new_user.set_password(data['password'])
            
            db_session.add(new_user)
            db_session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Account creato con successo',
                'user_id': new_user.id
            }), 201
            
        except Exception as e:
            db_session.rollback()
            return jsonify({'error': f'Errore durante la registrazione: {str(e)}'}), 500

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login utente esistente"""
    if request.method == 'GET':
        # Mostra form di login con header no-cache
        response = make_response(render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Viamigo</title>
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
                <div class="text-center">
                    <h1 class="text-2xl font-bold viamigo-font">Viamigo</h1>
                    <p class="text-xs text-gray-400">Accedi al tuo account</p>
                </div>
            </div>
            
            <!-- CONTENUTO FORM -->
            <div class="flex-grow overflow-y-auto p-4 flex items-center">
                <div class="w-full">
                    <form id="loginForm" class="space-y-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Email</label>
                            <input type="email" name="email" required 
                                   class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Password</label>
                            <input type="password" name="password" required 
                                   class="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                        </div>
                        
                        <div id="errorMessage" class="hidden text-red-400 text-sm bg-red-900/20 p-3 rounded-lg border border-red-700"></div>
                        
                        <button type="submit" 
                                class="w-full bg-gradient-to-r from-violet-600 to-purple-600 text-white py-3 px-4 rounded-lg hover:from-violet-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-violet-500 font-medium">
                            Accedi
                        </button>
                        
                        <div class="text-center mt-6">
                            <p class="text-sm text-gray-400">
                                Non hai un account? 
                                <a href="/auth/register" class="text-violet-400 hover:text-violet-300 font-medium">Registrati qui</a>
                            </p>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    window.location.href = result.redirect || '/dashboard';
                } else {
                    showError(result.error || 'Errore durante il login');
                }
            } catch (error) {
                showError('Errore di connessione');
            }
        });
        
        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
        }
    </script>
</body>
</html>
        '''))
        
        # Aggiungi header no-cache per evitare problemi 304
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    
    elif request.method == 'POST':
        # Processa login
        data = request.get_json()
        db_session = get_db_session()
        
        if not db_session:
            return jsonify({'error': 'Database non disponibile'}), 500
        
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} obbligatorio'}), 400
        
        try:
            user = User.query.filter_by(email=data['email'].lower().strip()).first()
            
            if user and user.check_password(data['password']):
                # Login effettuato con successo - sessione permanente 
                session.permanent = True
                login_user(user, remember=True)
                
                # Determina dove reindirizzare l'utente
                # Se è il primo login (non ha profilo completo), va alla creazione profilo
                # Altrimenti va alla dashboard
                if not user.has_complete_profile():
                    redirect_url = '/create-profile'
                else:
                    redirect_url = '/dashboard'
                
                return jsonify({
                    'success': True,
                    'message': 'Login effettuato con successo',
                    'redirect': redirect_url,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.full_name
                    }
                }), 200
            else:
                return jsonify({'error': 'Email o password non corretti'}), 401
                
        except Exception as e:
            return jsonify({'error': f'Errore durante il login: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout utente"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logout effettuato con successo'}), 200

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Ottieni profilo utente corrente"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'full_name': current_user.full_name,
            'address': current_user.address,
            'profile_image_url': current_user.profile_image_url
        }
    }), 200

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Aggiorna profilo utente"""
    data = request.get_json()
    db_session = get_db_session()
    
    if not db_session:
        return jsonify({'error': 'Database non disponibile'}), 500
    
    try:
        # Aggiorna i campi consentiti
        if 'first_name' in data and data['first_name'].strip():
            current_user.first_name = data['first_name'].strip()
        if 'last_name' in data and data['last_name'].strip():
            current_user.last_name = data['last_name'].strip()
        if 'email' in data and data['email'].strip():
            email = data['email'].lower().strip()
            if validate_email(email):
                # Verifica che l'email non sia già in uso da un altro utente
                existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
                if existing_user:
                    return jsonify({'error': 'Email già in uso'}), 400
                current_user.email = email
            else:
                return jsonify({'error': 'Formato email non valido'}), 400
        if 'address' in data:
            current_user.address = data['address'].strip() or None
        
        db_session.commit()
        return jsonify({'message': 'Profilo aggiornato con successo'}), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': f'Errore durante l\'aggiornamento: {str(e)}'}), 500

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Cambia password utente"""
    data = request.get_json()
    db_session = get_db_session()
    
    if not db_session:
        return jsonify({'error': 'Database non disponibile'}), 500
    
    required_fields = ['current_password', 'new_password', 'confirm_password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} obbligatorio'}), 400
    
    if data['new_password'] != data['confirm_password']:
        return jsonify({'error': 'Le password non corrispondono'}), 400
    
    # Verifica password attuale
    if not current_user.check_password(data['current_password']):
        return jsonify({'error': 'Password attuale non corretta'}), 400
    
    # Validazione nuova password
    is_valid, message = validate_password(data['new_password'])
    if not is_valid:
        return jsonify({'error': message}), 400
    
    try:
        current_user.set_password(data['new_password'])
        db_session.commit()
        return jsonify({'message': 'Password cambiata con successo'}), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({'error': f'Errore durante il cambio password: {str(e)}'}), 500