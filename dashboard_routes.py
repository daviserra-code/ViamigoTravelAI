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
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-bold text-violet-600">Viamigo</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2">
                        <div class="w-8 h-8 bg-violet-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                            {{ current_user.first_name[0] }}{{ current_user.last_name[0] }}
                        </div>
                        <span class="text-sm font-medium text-gray-700">{{ current_user.full_name }}</span>
                    </div>
                    <button onclick="logout()" class="text-sm text-gray-500 hover:text-gray-700">
                        Logout
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
            <div class="mb-8">
                <h2 class="text-2xl font-bold text-gray-900 mb-2">
                    Benvenuto, {{ current_user.first_name }}!
                </h2>
                <p class="text-gray-600">
                    Inizia a pianificare il tuo prossimo viaggio con Viamigo
                </p>
            </div>

            <!-- Action Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- Piano Viaggio -->
                <div class="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 bg-violet-100 rounded-lg flex items-center justify-center mb-4">
                        <svg class="w-6 h-6 text-violet-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Pianifica Viaggio</h3>
                    <p class="text-gray-600 mb-4">Crea il tuo itinerario personalizzato con mappe interattive</p>
                    <a href="/planner" class="inline-flex items-center px-4 py-2 bg-violet-600 text-white text-sm font-medium rounded-md hover:bg-violet-700">
                        Inizia
                    </a>
                </div>

                <!-- Profilo -->
                <div class="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Gestisci Profilo</h3>
                    <p class="text-gray-600 mb-4">Personalizza le tue preferenze di viaggio</p>
                    <a href="/profile" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700">
                        Modifica
                    </a>
                </div>

                <!-- Account -->
                <div class="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
                    <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                        <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Impostazioni Account</h3>
                    <p class="text-gray-600 mb-4">Gestisci i tuoi dati personali e la sicurezza</p>
                    <a href="/account" class="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700">
                        Gestisci
                    </a>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="mt-8">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Attività Recente</h3>
                <div class="bg-white rounded-lg shadow-sm border p-6">
                    <p class="text-gray-500 text-center py-8">
                        Nessuna attività recente. Inizia pianificando il tuo primo viaggio!
                    </p>
                </div>
            </div>
        </div>
    </main>

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
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center space-x-4">
                    <a href="/dashboard" class="text-violet-600 hover:text-violet-700">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                        </svg>
                    </a>
                    <h1 class="text-xl font-bold text-violet-600">Impostazioni Account</h1>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 bg-violet-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {{ current_user.first_name[0] }}{{ current_user.last_name[0] }}
                    </div>
                    <span class="text-sm font-medium text-gray-700">{{ current_user.full_name }}</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
            <!-- Informazioni Personali -->
            <div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">Informazioni Personali</h2>
                <form id="profileForm" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                            <input type="text" name="first_name" value="{{ current_user.first_name }}" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Cognome</label>
                            <input type="text" name="last_name" value="{{ current_user.last_name }}" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                        <input type="email" name="email" value="{{ current_user.email }}" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Indirizzo (opzionale)</label>
                        <input type="text" name="address" value="{{ current_user.address or '' }}" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                    </div>
                    
                    <div id="profileMessage" class="hidden"></div>
                    
                    <button type="submit" 
                            class="bg-violet-600 text-white px-4 py-2 rounded-md hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-500">
                        Salva Modifiche
                    </button>
                </form>
            </div>

            <!-- Sicurezza -->
            <div class="bg-white rounded-lg shadow-sm border p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">Sicurezza</h2>
                <form id="passwordForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Password Attuale</label>
                        <input type="password" name="current_password" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Nuova Password</label>
                        <input type="password" name="new_password" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                        <div class="text-xs text-gray-500 mt-1">
                            Minimo 8 caratteri, con maiuscola, minuscola, numero e carattere speciale
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Conferma Nuova Password</label>
                        <input type="password" name="confirm_password" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-violet-500">
                    </div>
                    
                    <div id="passwordMessage" class="hidden"></div>
                    
                    <button type="submit" 
                            class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500">
                        Cambia Password
                    </button>
                </form>
            </div>
        </div>
    </main>

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
            element.className = type === 'success' ? 'text-green-600 text-sm' : 'text-red-600 text-sm';
            element.classList.remove('hidden');
            
            setTimeout(() => {
                element.classList.add('hidden');
            }, 5000);
        }
    </script>
</body>
</html>
    ''', current_user=current_user)