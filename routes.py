from flask import session, render_template_string, request, jsonify, redirect, url_for, flash
from flask_login import current_user
from models import User, UserProfile, AdminUser
import logging

# Import app and db after initialization to avoid circular imports
def get_app_db():
    from flask_app import app, db
    return app, db

app, db = get_app_db()

# Only import auth if database is available
if db:
    from replit_auth import require_login, make_replit_blueprint
    app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")
else:
    # Mock decorators for development without auth
    def require_login(f):
        return f
    def make_replit_blueprint():
        return None

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
    if current_user.is_authenticated:
        # Home page per utenti loggati
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
                        <span>Ciao, {{ user.first_name or user.email }}</span>
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
        ''', user=current_user)
    else:
        # Landing page per utenti non loggati
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Viamigo - Pianifica i tuoi viaggi</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-b from-blue-500 to-blue-700 min-h-screen text-white">
            <div class="container mx-auto p-8 text-center">
                <h1 class="text-5xl font-bold mb-6">Viamigo</h1>
                <p class="text-xl mb-8">Il tuo assistente AI per viaggi personalizzati in Italia</p>
                
                <div class="bg-white bg-opacity-20 rounded-lg p-8 max-w-md mx-auto">
                    <h2 class="text-2xl font-semibold mb-4">Inizia il tuo viaggio</h2>
                    <p class="mb-6">Accedi per creare itinerari personalizzati basati sui tuoi interessi</p>
                    <a href="/auth/login" class="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold">Accedi</a>
                </div>
            </div>
        </body>
        </html>
        ''')

@app.route('/planner')
def planner():
    """Redirect alla pagina originale di pianificazione"""
    return redirect('/static/index.html')

# === CRUD ROUTES PER USER PROFILE ===

@app.route('/profile')
@require_login
def view_profile():
    """Visualizza il profilo dell'utente corrente"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Il Mio Profilo - Viamigo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/" class="text-xl font-bold">Viamigo</a>
                <div class="space-x-4">
                    <span>{{ user.first_name or user.email }}</span>
                    <a href="/auth/logout" class="bg-red-500 px-3 py-1 rounded">Logout</a>
                </div>
            </div>
        </nav>
        
        <div class="container mx-auto p-8">
            <div class="bg-white rounded-lg shadow-md p-6 max-w-2xl mx-auto">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold">Il Mio Profilo</h2>
                    {% if profile %}
                        <a href="/profile/edit" class="bg-blue-600 text-white px-4 py-2 rounded">Modifica</a>
                    {% else %}
                        <a href="/profile/create" class="bg-green-600 text-white px-4 py-2 rounded">Crea Profilo</a>
                    {% endif %}
                </div>
                
                <div class="space-y-4">
                    <div>
                        <h3 class="font-semibold text-gray-700">Informazioni Account</h3>
                        <p><span class="font-medium">Email:</span> {{ user.email or 'Non disponibile' }}</p>
                        <p><span class="font-medium">Nome:</span> {{ user.first_name or 'Non disponibile' }} {{ user.last_name or '' }}</p>
                    </div>
                    
                    {% if profile %}
                    <div class="border-t pt-4">
                        <h3 class="font-semibold text-gray-700 mb-2">Preferenze di Viaggio</h3>
                        <div class="grid md:grid-cols-3 gap-4">
                            <div>
                                <p class="font-medium">Interessi:</p>
                                {% if profile.get_interests() %}
                                    <div class="flex flex-wrap gap-1 mt-1">
                                        {% for interest in profile.get_interests() %}
                                            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">{{ interest }}</span>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <p class="text-gray-500 text-sm">Non specificati</p>
                                {% endif %}
                            </div>
                            
                            <div>
                                <p class="font-medium">Ritmo di Viaggio:</p>
                                <p class="text-gray-600">{{ profile.travel_pace or 'Non specificato' }}</p>
                            </div>
                            
                            <div>
                                <p class="font-medium">Budget:</p>
                                <p class="text-gray-600">{{ profile.budget or 'Non specificato' }}</p>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="border-t pt-4 text-center">
                        <p class="text-gray-500 mb-4">Non hai ancora configurato le tue preferenze di viaggio.</p>
                        <a href="/profile/create" class="bg-green-600 text-white px-6 py-2 rounded">Configura Ora</a>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', user=current_user, profile=profile)

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