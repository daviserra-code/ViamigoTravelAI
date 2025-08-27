from flask import Blueprint, render_template_string, jsonify
from flask_login import login_required, current_user

# Blueprint per routes della dashboard
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principale per utenti autenticati"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Viamigo</title>
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
                    <div class="flex items-center space-x-2">
                        <div class="w-8 h-8 bg-violet-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                            {{ current_user.first_name[0] }}{{ current_user.last_name[0] }}
                        </div>
                        <button onclick="logout()" class="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center">
                            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                        <h2 class="text-lg font-semibold mb-1">Benvenuto, {{ current_user.first_name }}!</h2>
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
                            <h3 class="text-white font-medium text-sm mb-1">Gestisci Profilo</h3>
                            <p class="text-gray-400 text-xs mb-3">Personalizza preferenze</p>
                            <button onclick="window.location.href='/profile'" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">
                                Modifica
                            </button>
                        </div>
                    </div>
                    
                    <!-- Additional Options -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h3 class="text-white font-medium text-sm mb-3">⚙️ Impostazioni Account</h3>
                        <p class="text-gray-400 text-xs mb-3">Gestisci dati personali e sicurezza</p>
                        <button onclick="window.location.href='/account'" class="w-full bg-green-600 text-white py-2 rounded-lg text-sm font-medium">
                            Gestisci Account
                        </button>
                    </div>

                    <!-- Recent Activity -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h3 class="text-white font-medium text-sm mb-3">📈 Attività Recente</h3>
                        <p class="text-gray-400 text-xs text-center py-6">
                            Nessuna attività recente.<br>
                            Inizia pianificando il tuo primo viaggio!
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function logout() {
            try {
                const response = await fetch('/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    window.location.href = '/auth/login';
                } else {
                    alert('Errore durante il logout');
                }
            } catch (error) {
                console.error('Errore:', error);
                alert('Errore di connessione');
            }
        }
    </script>
</body>
</html>
    ''', current_user=current_user)

@dashboard_bp.route('/account')
@login_required
def account_settings():
    """Gestione impostazioni account"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Impostazioni Account - Viamigo</title>
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
                    <div class="flex items-center space-x-3">
                        <a href="/dashboard" class="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-violet-400 hover:text-violet-300">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                            </svg>
                        </a>
                        <div>
                            <h1 class="text-lg font-bold viamigo-font">Account</h1>
                            <p class="text-xs text-gray-400">Impostazioni</p>
                        </div>
                    </div>
                    <div class="w-8 h-8 bg-violet-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                        {{ current_user.first_name[0] }}{{ current_user.last_name[0] }}
                    </div>
                </div>
            </div>

            <!-- CONTENUTO ACCOUNT -->
            <div class="flex-grow overflow-y-auto p-4">
                <div class="space-y-4">
                    <!-- Informazioni Personali -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h2 class="text-white font-medium text-sm mb-4">👤 Informazioni Personali</h2>
                        <form id="profileForm" class="space-y-3">
                            <div class="grid grid-cols-2 gap-3">
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Nome</label>
                                    <input type="text" name="first_name" value="{{ current_user.first_name }}" 
                                           class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Cognome</label>
                                    <input type="text" name="last_name" value="{{ current_user.last_name }}" 
                                           class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-xs font-medium text-gray-300 mb-1">Email</label>
                                <input type="email" name="email" value="{{ current_user.email }}" 
                                       class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                            </div>
                            
                            <div>
                                <label class="block text-xs font-medium text-gray-300 mb-1">Indirizzo (opzionale)</label>
                                <input type="text" name="address" value="{{ current_user.address or '' }}" 
                                       class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                            </div>
                            
                            <div id="profileMessage" class="hidden text-xs"></div>
                            
                            <button type="submit" 
                                    class="w-full bg-violet-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-500">
                                Salva Modifiche
                            </button>
                        </form>
                    </div>

                    <!-- Sicurezza -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h2 class="text-white font-medium text-sm mb-4">🔒 Sicurezza</h2>
                        <form id="passwordForm" class="space-y-3">
                            <div>
                                <label class="block text-xs font-medium text-gray-300 mb-1">Password Attuale</label>
                                <input type="password" name="current_password" 
                                       class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                            </div>
                            
                            <div>
                                <label class="block text-xs font-medium text-gray-300 mb-1">Nuova Password</label>
                                <input type="password" name="new_password" 
                                       class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                                <div class="text-xs text-gray-400 mt-1">
                                    Minimo 8 caratteri, con maiuscola, minuscola, numero e carattere speciale
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-xs font-medium text-gray-300 mb-1">Conferma Nuova Password</label>
                                <input type="password" name="confirm_password" 
                                       class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                            </div>
                            
                            <div id="passwordMessage" class="hidden text-xs"></div>
                            
                            <button type="submit" 
                                    class="w-full bg-red-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500">
                                Cambia Password
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Gestione form profilo
        document.getElementById('profileForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/auth/update_profile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                showMessage('profileMessage', result.message, response.ok ? 'success' : 'error');
                
            } catch (error) {
                showMessage('profileMessage', 'Errore di connessione', 'error');
            }
        });

        // Gestione form password
        document.getElementById('passwordForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            if (data.new_password !== data.confirm_password) {
                showMessage('passwordMessage', 'Le password non corrispondono', 'error');
                return;
            }
            
            try {
                const response = await fetch('/auth/change_password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                showMessage('passwordMessage', result.message, response.ok ? 'success' : 'error');
                
                if (response.ok) {
                    this.reset();
                }
                
            } catch (error) {
                showMessage('passwordMessage', 'Errore di connessione', 'error');
            }
        });

        function showMessage(elementId, message, type) {
            const element = document.getElementById(elementId);
            element.textContent = message;
            if (type === 'success') {
                element.className = 'text-green-400 text-xs bg-green-900/20 p-2 rounded-lg border border-green-700';
            } else {
                element.className = 'text-red-400 text-xs bg-red-900/20 p-2 rounded-lg border border-red-700';
            }
            element.classList.remove('hidden');
            
            setTimeout(() => {
                element.classList.add('hidden');
            }, 5000);
        }
    </script>
</body>
</html>
    ''', current_user=current_user)