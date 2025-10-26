from flask import Blueprint, render_template_string, jsonify
from flask_login import login_required, current_user

# Blueprint per routes della dashboard
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    print(
        f"[DEBUG] Dashboard access: current_user.is_authenticated={getattr(current_user, 'is_authenticated', None)}, current_user.email={getattr(current_user, 'email', None)}")
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
                            {% if current_user.first_name and current_user.last_name %}
                                {{ current_user.first_name[0] }}{{ current_user.last_name[0] }}
                            {% elif current_user.email %}
                                {{ current_user.email[0].upper() }}
                            {% else %}
                                U
                            {% endif %}
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
                        <h2 class="text-lg font-semibold mb-1">
                            Benvenuto{% if current_user.first_name %}, {{ current_user.first_name }}{% elif current_user.email %}, {{ current_user.email.split('@')[0] }}{% endif %}!
                        </h2>
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
                    
                    <!-- NUOVA CARD: Compagno di Viaggio Intelligente -->
                    <div class="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl p-4 text-center">
                        <div class="text-2xl mb-2">🧠</div>
                        <h3 class="text-white font-medium text-sm mb-1">Compagno AI</h3>
                        <p class="text-gray-200 text-xs mb-3">Piano B, Scoperte, Diario</p>
                        <button onclick="window.location.href='/advanced-features'" class="w-full bg-white text-emerald-600 py-2 rounded-lg text-sm font-medium">
                            🚀 Prova Ora
                        </button>
                    </div>

                    <!-- Additional Options -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h3 class="text-white font-medium text-sm mb-3">⚙️ Impostazioni Account</h3>
                        <p class="text-gray-400 text-xs mb-3">Gestisci dati personali e sicurezza</p>
                        <button onclick="window.location.href='/account'" class="w-full bg-green-600 text-white py-2 rounded-lg text-sm font-medium">
                            Gestisci Account
                        </button>
                    </div>

                    <!-- Route History & Photo Gallery -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h3 class="text-white font-medium text-sm mb-3">🗺️ Cronologia Itinerari</h3>
                        <div id="route-history" class="space-y-3">
                            <!-- Route history will be populated here -->
                        </div>
                        <button onclick="viewAllRoutes()" class="w-full mt-3 bg-purple-600 text-white py-2 rounded-lg text-sm font-medium">
                            Visualizza Tutti gli Itinerari
                        </button>
                    </div>

                    <!-- Photo Gallery -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h3 class="text-white font-medium text-sm mb-3">📸 Galleria Viaggi</h3>
                        <div id="photo-gallery" class="grid grid-cols-3 gap-2 mb-3">
                            <!-- Photo gallery will be populated here -->
                        </div>
                        <button onclick="openPhotoGallery()" class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium">
                            Esplora Galleria Completa
                        </button>
                    </div>

                    <!-- Recent Activity -->
                    <div class="bg-gray-800 rounded-xl p-4">
                        <h3 class="text-white font-medium text-sm mb-3">📈 Attività Recente</h3>
                        <div id="recent-activity">
                            <p class="text-gray-400 text-xs text-center py-6">
                                Nessuna attività recente.<br>
                                Inizia pianificando il tuo primo viaggio!
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Load dashboard data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadRouteHistory();
            loadPhotoGallery();
            loadRecentActivity();
        });

        // Load route history from localStorage and server
        async function loadRouteHistory() {
            const routeHistoryContainer = document.getElementById('route-history');
            
            try {
                // First try to load from localStorage for immediate feedback
                const localRoutes = JSON.parse(localStorage.getItem('viamigo_route_history') || '[]');
                
                if (localRoutes.length > 0) {
                    displayRouteHistory(localRoutes.slice(0, 3)); // Show last 3 routes
                } else {
                    routeHistoryContainer.innerHTML = `
                        <p class="text-gray-400 text-xs text-center py-4">
                            Nessun itinerario salvato.<br>
                            Crea il tuo primo itinerario!
                        </p>
                    `;
                }
            } catch (error) {
                console.error('Error loading route history:', error);
                routeHistoryContainer.innerHTML = `
                    <p class="text-gray-400 text-xs text-center py-4">
                        Errore nel caricamento degli itinerari.
                    </p>
                `;
            }
        }

        // Display route history items
        function displayRouteHistory(routes) {
            const container = document.getElementById('route-history');
            container.innerHTML = '';
            
            routes.forEach((route, index) => {
                const routeItem = document.createElement('div');
                routeItem.className = 'bg-gray-700 rounded-lg p-3 border border-gray-600';
                routeItem.innerHTML = `
                    <div class="flex items-center justify-between">
                        <div class="flex-grow">
                            <h4 class="text-white text-sm font-medium">${route.title || 'Itinerario'}</h4>
                            <p class="text-gray-400 text-xs">${route.city || 'Città non specificata'} • ${formatDate(route.date)}</p>
                            <p class="text-gray-500 text-xs mt-1">${route.stops || 0} tappe</p>
                        </div>
                        <button onclick="reopenRoute('${route.id}')" class="bg-emerald-600 text-white px-3 py-1 rounded text-xs hover:bg-emerald-700">
                            Riapri
                        </button>
                    </div>
                `;
                container.appendChild(routeItem);
            });
        }

        // Load photo gallery with travel destination images
        function loadPhotoGallery() {
            const galleryContainer = document.getElementById('photo-gallery');
            
            // Sample travel photos from popular Italian destinations
            const samplePhotos = [
                { src: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=120&h=120&fit=crop', alt: 'Roma - Colosseo', link: 'https://unsplash.com/photos/rome-colosseum' },
                { src: 'https://images.unsplash.com/photo-1601985843082-5e1ecdf71b71?w=120&h=120&fit=crop', alt: 'Firenze - Duomo', link: 'https://unsplash.com/photos/florence-duomo' },
                { src: 'https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=120&h=120&fit=crop', alt: 'Venezia - San Marco', link: 'https://unsplash.com/photos/venice-san-marco' },
                { src: 'https://images.unsplash.com/photo-1543832923-44667a5ab6ea?w=120&h=120&fit=crop', alt: 'Milano - Duomo', link: 'https://unsplash.com/photos/milan-duomo' },
                { src: 'https://images.unsplash.com/photo-1555758292-972ddd980eb2?w=120&h=120&fit=crop', alt: 'Napoli - Centro', link: 'https://unsplash.com/photos/naples' },
                { src: 'https://images.unsplash.com/photo-1513581166391-887ba0ad7c1b?w=120&h=120&fit=crop', alt: 'Genova - Porto', link: 'https://unsplash.com/photos/genoa' }
            ];
            
            galleryContainer.innerHTML = '';
            samplePhotos.slice(0, 6).forEach(photo => {
                const photoItem = document.createElement('div');
                photoItem.className = 'aspect-square rounded-lg overflow-hidden bg-gray-700 cursor-pointer hover:scale-105 transition-transform';
                photoItem.innerHTML = `
                    <img src="${photo.src}" alt="${photo.alt}" class="w-full h-full object-cover" 
                         onclick="openExternalLink('${photo.link}')"
                         onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold\\'>Foto</div>'">
                `;
                galleryContainer.appendChild(photoItem);
            });
        }

        // Load recent activity
        async function loadRecentActivity() {
            const activityContainer = document.getElementById('recent-activity');
            
            try {
                // Try to get recent activity from localStorage
                const recentRoutes = JSON.parse(localStorage.getItem('viamigo_route_history') || '[]');
                const recentSearches = JSON.parse(localStorage.getItem('viamigo_recent_searches') || '[]');
                
                if (recentRoutes.length > 0 || recentSearches.length > 0) {
                    let activityHTML = '<div class="space-y-2">';
                    
                    // Show most recent route
                    if (recentRoutes.length > 0) {
                        const lastRoute = recentRoutes[0];
                        activityHTML += `
                            <div class="text-xs text-gray-400">
                                ✅ Ultimo itinerario: <span class="text-white">${lastRoute.city}</span>
                                <span class="text-gray-500">(${formatDate(lastRoute.date)})</span>
                            </div>
                        `;
                    }
                    
                    // Show recent searches
                    if (recentSearches.length > 0) {
                        const lastSearch = recentSearches[0];
                        activityHTML += `
                            <div class="text-xs text-gray-400">
                                🔍 Ultima ricerca: <span class="text-white">${lastSearch}</span>
                            </div>
                        `;
                    }
                    
                    activityHTML += '</div>';
                    activityContainer.innerHTML = activityHTML;
                } else {
                    activityContainer.innerHTML = `
                        <p class="text-gray-400 text-xs text-center py-6">
                            Nessuna attività recente.<br>
                            Inizia pianificando il tuo primo viaggio!
                        </p>
                    `;
                }
            } catch (error) {
                console.error('Error loading recent activity:', error);
            }
        }

        // Helper function to format dates
        function formatDate(dateString) {
            if (!dateString) return 'Data non disponibile';
            try {
                const date = new Date(dateString);
                return date.toLocaleDateString('it-IT', { 
                    day: 'numeric', 
                    month: 'short',
                    year: 'numeric'
                });
            } catch (error) {
                return 'Data non valida';
            }
        }

        // View all routes (opens full route history page)
        function viewAllRoutes() {
            // For now, redirect to planner with a special parameter
            window.location.href = '/planner?view=history';
        }

        // Open photo gallery in full view
        function openPhotoGallery() {
            // Create modal for photo gallery
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4';
            modal.innerHTML = `
                <div class="bg-gray-800 rounded-xl p-6 max-w-md w-full max-h-[80vh] overflow-y-auto">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-white font-bold text-lg">🏛️ Galleria Destinazioni Italiane</h3>
                        <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-white">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        <div class="aspect-square rounded-lg overflow-hidden bg-gray-700 cursor-pointer" onclick="openExternalLink('https://unsplash.com/photos/rome-colosseum')">
                            <img src="https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=200&h=200&fit=crop" alt="Roma - Colosseo" class="w-full h-full object-cover">
                        </div>
                        <div class="aspect-square rounded-lg overflow-hidden bg-gray-700 cursor-pointer" onclick="openExternalLink('https://unsplash.com/photos/florence-duomo')">
                            <img src="https://images.unsplash.com/photo-1601985843082-5e1ecdf71b71?w=200&h=200&fit=crop" alt="Firenze - Duomo" class="w-full h-full object-cover">
                        </div>
                        <div class="aspect-square rounded-lg overflow-hidden bg-gray-700 cursor-pointer" onclick="openExternalLink('https://unsplash.com/photos/venice-san-marco')">
                            <img src="https://images.unsplash.com/photo-1523906921802-b5d2d899e93b?w=200&h=200&fit=crop" alt="Venezia - San Marco" class="w-full h-full object-cover">
                        </div>
                        <div class="aspect-square rounded-lg overflow-hidden bg-gray-700 cursor-pointer" onclick="openExternalLink('https://unsplash.com/photos/milan-duomo')">
                            <img src="https://images.unsplash.com/photo-1543832923-44667a5ab6ea?w=200&h=200&fit=crop" alt="Milano - Duomo" class="w-full h-full object-cover">
                        </div>
                    </div>
                    <p class="text-gray-400 text-xs text-center mb-4">
                        Esplora le bellezze d'Italia. Clicca sulle immagini per vederle a grandezza reale.
                    </p>
                    <button onclick="window.location.href='/planner'" class="w-full bg-emerald-600 text-white py-2 rounded-lg text-sm font-medium">
                        Pianifica un Viaggio
                    </button>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Open external link in new tab
        function openExternalLink(url) {
            window.open(url, '_blank', 'noopener,noreferrer');
        }

        // Reopen a saved route
        function reopenRoute(routeId) {
            if (!routeId) {
                window.location.href = '/planner';
                return;
            }
            
            try {
                const routes = JSON.parse(localStorage.getItem('viamigo_route_history') || '[]');
                const route = routes.find(r => r.id === routeId);
                
                if (route) {
                    // Store the route data for the planner to pick up
                    localStorage.setItem('viamigo_restore_route', JSON.stringify(route));
                    window.location.href = '/planner?restore=' + routeId;
                } else {
                    window.location.href = '/planner';
                }
            } catch (error) {
                console.error('Error reopening route:', error);
                window.location.href = '/planner';
            }
        }

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
