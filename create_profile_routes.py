from flask import Blueprint, request, jsonify, render_template_string
from flask_login import login_required, current_user
from models import UserProfile
from auth_routes import get_db_session
import uuid

create_profile_bp = Blueprint('create_profile', __name__)

@create_profile_bp.route('/create-profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    """Creazione profilo di viaggio per nuovi utenti"""
    
    if request.method == 'GET':
        # Mostra form di creazione profilo
        return render_template_string('''
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crea il tuo Profilo - Viamigo</title>
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
                    <p class="text-xs text-gray-400">Crea il tuo profilo di viaggio</p>
                </div>
            </div>
            
            <!-- CONTENUTO PROFILO -->
            <div class="flex-grow overflow-y-auto p-4">
                <div class="space-y-4">
                    <div class="text-center mb-6">
                        <h2 class="text-lg font-semibold text-white mb-2">Benvenuto, {{ current_user.first_name }}!</h2>
                        <p class="text-sm text-gray-400">Personalizza il tuo profilo di viaggio per ricevere raccomandazioni su misura</p>
                    </div>
                    
                    <form id="profileForm" class="space-y-4">
                        <div class="bg-gray-800 rounded-xl p-4">
                            <h3 class="text-white font-medium text-sm mb-3">🎯 Preferenze di Viaggio</h3>
                            
                            <div class="space-y-3">
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Budget preferito per viaggio</label>
                                    <select name="budget_range" required 
                                            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                                        <option value="">Seleziona budget</option>
                                        <option value="low">Economico (€50-150/giorno)</option>
                                        <option value="medium">Medio (€150-300/giorno)</option>
                                        <option value="high">Alto (€300-500/giorno)</option>
                                        <option value="luxury">Lusso (€500+/giorno)</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Tipo di viaggiatore</label>
                                    <select name="traveler_type" required 
                                            class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                                        <option value="">Seleziona tipo</option>
                                        <option value="solo">Viaggiatore solitario</option>
                                        <option value="couple">In coppia</option>
                                        <option value="family">Famiglia</option>
                                        <option value="friends">Con amici</option>
                                        <option value="business">Business</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Interessi principali</label>
                                    <div class="grid grid-cols-2 gap-2 mt-2">
                                        <label class="flex items-center text-xs text-gray-300">
                                            <input type="checkbox" name="interests" value="culture" class="mr-2 text-violet-500">
                                            🏛️ Cultura
                                        </label>
                                        <label class="flex items-center text-xs text-gray-300">
                                            <input type="checkbox" name="interests" value="food" class="mr-2 text-violet-500">
                                            🍝 Gastronomia
                                        </label>
                                        <label class="flex items-center text-xs text-gray-300">
                                            <input type="checkbox" name="interests" value="nature" class="mr-2 text-violet-500">
                                            🌿 Natura
                                        </label>
                                        <label class="flex items-center text-xs text-gray-300">
                                            <input type="checkbox" name="interests" value="shopping" class="mr-2 text-violet-500">
                                            🛍️ Shopping
                                        </label>
                                        <label class="flex items-center text-xs text-gray-300">
                                            <input type="checkbox" name="interests" value="nightlife" class="mr-2 text-violet-500">
                                            🌙 Vita notturna
                                        </label>
                                        <label class="flex items-center text-xs text-gray-300">
                                            <input type="checkbox" name="interests" value="adventure" class="mr-2 text-violet-500">
                                            🏔️ Avventura
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="bg-gray-800 rounded-xl p-4">
                            <h3 class="text-white font-medium text-sm mb-3">📍 Informazioni Aggiuntive</h3>
                            
                            <div class="space-y-3">
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Città di residenza (opzionale)</label>
                                    <input type="text" name="home_city" 
                                           placeholder="es. Milano, Roma, Firenze..."
                                           class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent">
                                </div>
                                
                                <div>
                                    <label class="block text-xs font-medium text-gray-300 mb-1">Note preferenze (opzionale)</label>
                                    <textarea name="notes" rows="3" 
                                              placeholder="Aggiungi dettagli sulle tue preferenze di viaggio..."
                                              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent resize-none"></textarea>
                                </div>
                            </div>
                        </div>
                        
                        <div id="errorMessage" class="hidden text-red-400 text-xs bg-red-900/20 p-2 rounded-lg border border-red-700"></div>
                        
                        <button type="submit" 
                                class="w-full bg-gradient-to-r from-violet-600 to-purple-600 text-white py-3 rounded-lg font-medium hover:from-violet-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-violet-500">
                            Completa Profilo
                        </button>
                        
                        <div class="text-center">
                            <button type="button" onclick="skipProfile()" 
                                    class="text-xs text-gray-400 hover:text-gray-300 underline">
                                Salta per ora
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('profileForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            // Raccogli interessi selezionati
            const interests = [];
            document.querySelectorAll('input[name="interests"]:checked').forEach(checkbox => {
                interests.push(checkbox.value);
            });
            data.interests = interests;
            
            try {
                const response = await fetch('/create-profile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showSuccessPopup('Profilo creato con successo!', '/dashboard');
                } else {
                    showError(result.error || 'Errore durante la creazione del profilo');
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
            const overlay = document.createElement('div');
            overlay.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';
            
            const popup = document.createElement('div');
            popup.className = 'bg-gray-800 rounded-xl p-6 mx-4 max-w-sm w-full border border-gray-600';
            popup.innerHTML = `
                <div class="text-center">
                    <div class="text-4xl mb-4">🎉</div>
                    <h3 class="text-white font-semibold mb-2">${message}</h3>
                    <p class="text-gray-400 text-sm mb-4">Ora puoi iniziare a pianificare i tuoi viaggi</p>
                    <button onclick="proceedToDashboard()" class="w-full bg-gradient-to-r from-violet-600 to-purple-600 text-white py-2 rounded-lg font-medium hover:from-violet-700 hover:to-purple-700">
                        Vai alla Dashboard
                    </button>
                </div>
            `;
            
            overlay.appendChild(popup);
            document.body.appendChild(overlay);
            
            setTimeout(() => { window.location.href = redirectUrl; }, 3000);
            window.proceedToDashboard = function() { window.location.href = redirectUrl; };
        }
        
        function skipProfile() {
            if (confirm('Sei sicuro di voler saltare la configurazione del profilo? Potrai completarla in seguito dalle impostazioni.')) {
                window.location.href = '/dashboard';
            }
        }
    </script>
</body>
</html>
        ''')
    
    elif request.method == 'POST':
        # Processa creazione profilo
        data = request.get_json()
        db_session = get_db_session()
        
        if not db_session:
            return jsonify({'error': 'Database non disponibile'}), 500
        
        # Validazioni
        required_fields = ['budget_range', 'traveler_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo {field} obbligatorio'}), 400
        
        try:
            # Crea o aggiorna profilo utente
            profile = UserProfile.query.filter_by(user_id=current_user.id).first()
            
            if not profile:
                profile = UserProfile(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id
                )
                db_session.add(profile)
            
            # Aggiorna i dati del profilo
            profile.budget_range = data['budget_range']
            profile.traveler_type = data['traveler_type']
            profile.interests = ','.join(data.get('interests', []))
            profile.home_city = data.get('home_city', '').strip() or None
            profile.notes = data.get('notes', '').strip() or None
            
            db_session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profilo creato con successo',
                'profile_id': profile.id
            }), 201
            
        except Exception as e:
            db_session.rollback()
            return jsonify({'error': f'Errore durante la creazione profilo: {str(e)}'}), 500