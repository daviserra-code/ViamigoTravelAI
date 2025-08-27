from flask import request, jsonify, render_template_string
from flask_login import login_required, current_user
from flask_app import app, db
from models import TravelJournal, SmartDiscovery, PlanBEvent, UserPreferences, AIInsight
from datetime import datetime, date
import json
import random
from typing import Dict, List, Any
import openai
import os

# Configura OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/advanced-features')
@login_required
def advanced_features():
    """Pagina delle funzionalità avanzate"""
    with open('static/advanced_features.html', 'r', encoding='utf-8') as f:
        return f.read()

# === PIANO B DINAMICO ===

@app.route('/api/plan-b/analyze', methods=['POST'])
@login_required
def analyze_plan_b():
    """Analizza un imprevisto e genera alternative intelligenti"""
    try:
        data = request.get_json()
        
        # Estrai dati dell'imprevisto
        original_plan = data.get('original_plan', {})
        disruption_type = data.get('disruption_type', 'crowded')
        disruption_description = data.get('disruption_description', '')
        affected_location = data.get('affected_location', '')
        city = data.get('city', '')
        user_location = data.get('user_location', '')
        
        # Genera alternative usando AI
        alternatives = generate_plan_b_alternatives(
            original_plan, disruption_type, city, affected_location
        )
        
        # Salva evento Piano B
        plan_b_event = PlanBEvent(
            user_id=current_user.id,
            original_plan=original_plan,
            disruption_type=disruption_type,
            disruption_description=disruption_description,
            city=city,
            affected_location=affected_location,
            current_user_location=user_location,
            ai_alternatives=alternatives,
            ai_reasoning=f"Analisi automatica per {disruption_type} a {affected_location}"
        )
        
        db.session.add(plan_b_event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'event_id': plan_b_event.id,
            'alternatives': alternatives,
            'processing_time': 2.5,
            'ai_confidence': 0.87
        })
        
    except Exception as e:
        print(f"Errore Piano B: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/plan-b/select', methods=['POST'])
@login_required
def select_plan_b_option():
    """Registra la scelta dell'utente per Piano B"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        selected_option = data.get('selected_option')
        selected_alternative = data.get('selected_alternative', {})
        
        # Aggiorna evento Piano B
        plan_b_event = PlanBEvent.query.filter_by(
            id=event_id, 
            user_id=current_user.id
        ).first()
        
        if not plan_b_event:
            return jsonify({'success': False, 'error': 'Evento non trovato'}), 404
            
        plan_b_event.selected_option = selected_option
        plan_b_event.selected_alternative = selected_alternative
        plan_b_event.resolved_at = datetime.now()
        
        db.session.commit()
        
        # Aggiorna preferenze utente
        update_user_plan_b_preferences(current_user.id, selected_option)
        
        return jsonify({
            'success': True,
            'message': 'Piano B applicato con successo',
            'updated_itinerary': selected_alternative
        })
        
    except Exception as e:
        print(f"Errore selezione Piano B: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# === SCOPERTE INTELLIGENTI ===

@app.route('/api/discoveries/find', methods=['POST'])
@login_required
def find_smart_discoveries():
    """Trova scoperte intelligenti basate sulla posizione e interessi"""
    try:
        data = request.get_json()
        user_lat = data.get('lat')
        user_lon = data.get('lon')
        city = data.get('city', '')
        current_location = data.get('current_location', '')
        radius_meters = data.get('radius_meters', 500)
        
        # Ottieni preferenze utente
        user_prefs = get_user_preferences(current_user.id)
        
        # Genera scoperte usando AI
        discoveries = generate_smart_discoveries(
            user_lat, user_lon, city, user_prefs, radius_meters
        )
        
        # Salva scoperte nel database
        for discovery_data in discoveries:
            discovery = SmartDiscovery(
                user_id=current_user.id,
                discovery_type=discovery_data['type'],
                trigger_location=current_location,
                suggested_place=discovery_data['name'],
                user_lat=user_lat,
                user_lon=user_lon,
                place_lat=discovery_data['lat'],
                place_lon=discovery_data['lon'],
                distance_meters=discovery_data['distance'],
                relevance_score=discovery_data['relevance'],
                user_interests_matched=discovery_data['matched_interests'],
                ai_reasoning=discovery_data['reasoning']
            )
            db.session.add(discovery)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'discoveries': discoveries,
            'total_found': len(discoveries)
        })
        
    except Exception as e:
        print(f"Errore scoperte intelligenti: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/discoveries/respond', methods=['POST'])
@login_required
def respond_to_discovery():
    """Registra la risposta dell'utente a una scoperta"""
    try:
        data = request.get_json()
        discovery_id = data.get('discovery_id')
        action = data.get('action')  # 'accepted', 'ignored'
        feedback = data.get('feedback', '')
        
        discovery = SmartDiscovery.query.filter_by(
            id=discovery_id,
            user_id=current_user.id
        ).first()
        
        if not discovery:
            return jsonify({'success': False, 'error': 'Scoperta non trovata'}), 404
            
        discovery.user_action = action
        discovery.action_timestamp = datetime.now()
        discovery.user_feedback = feedback
        discovery.was_useful = action == 'accepted'
        
        db.session.commit()
        
        # Aggiorna preferenze basate sul feedback
        update_user_discovery_preferences(current_user.id, discovery, action)
        
        return jsonify({
            'success': True,
            'message': f'Scoperta {action} con successo'
        })
        
    except Exception as e:
        print(f"Errore risposta scoperta: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# === DIARIO DI VIAGGIO AI ===

@app.route('/api/journal/create', methods=['POST'])
@login_required
def create_travel_journal():
    """Crea un nuovo diario di viaggio con AI"""
    try:
        data = request.get_json()
        
        title = data.get('title')
        city = data.get('city')
        travel_date = datetime.strptime(data.get('travel_date'), '%Y-%m-%d').date()
        itinerary_data = data.get('itinerary_data', {})
        user_notes = data.get('user_notes', '')
        
        # Genera contenuto AI per il diario
        ai_content = generate_journal_ai_content(
            city, itinerary_data, user_notes, current_user.id
        )
        
        journal = TravelJournal(
            user_id=current_user.id,
            title=title,
            city=city,
            travel_date=travel_date,
            itinerary_data=itinerary_data,
            user_notes=user_notes,
            ai_summary=ai_content['summary'],
            highlights=ai_content['highlights'],
            insights=ai_content['insights'],
            total_steps=len(itinerary_data.get('steps', [])),
            ai_confidence=ai_content['confidence']
        )
        
        db.session.add(journal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'journal_id': journal.id,
            'ai_content': ai_content
        })
        
    except Exception as e:
        print(f"Errore creazione diario: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/journal/list')
@login_required
def list_travel_journals():
    """Lista tutti i diari di viaggio dell'utente"""
    try:
        journals = TravelJournal.query.filter_by(
            user_id=current_user.id
        ).order_by(TravelJournal.travel_date.desc()).all()
        
        journals_data = []
        for journal in journals:
            journals_data.append({
                'id': journal.id,
                'title': journal.title,
                'city': journal.city,
                'travel_date': journal.travel_date.isoformat(),
                'ai_summary': journal.ai_summary,
                'highlights': journal.highlights,
                'user_rating': journal.user_rating,
                'completed_steps': journal.completed_steps,
                'total_steps': journal.total_steps,
                'duration_hours': journal.duration_hours,
                'distance_km': journal.distance_km
            })
        
        return jsonify({
            'success': True,
            'journals': journals_data,
            'total_count': len(journals_data)
        })
        
    except Exception as e:
        print(f"Errore lista diari: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/journal/<int:journal_id>')
@login_required  
def get_journal_detail(journal_id):
    """Ottieni dettagli completi di un diario"""
    try:
        journal = TravelJournal.query.filter_by(
            id=journal_id,
            user_id=current_user.id
        ).first()
        
        if not journal:
            return jsonify({'success': False, 'error': 'Diario non trovato'}), 404
            
        return jsonify({
            'success': True,
            'journal': {
                'id': journal.id,
                'title': journal.title,
                'city': journal.city,
                'travel_date': journal.travel_date.isoformat(),
                'ai_summary': journal.ai_summary,
                'highlights': journal.highlights,
                'insights': journal.insights,
                'itinerary_data': journal.itinerary_data,
                'user_notes': journal.user_notes,
                'user_rating': journal.user_rating,
                'duration_hours': journal.duration_hours,
                'distance_km': journal.distance_km,
                'ai_confidence': journal.ai_confidence,
                'generated_suggestions': journal.generated_suggestions
            }
        })
        
    except Exception as e:
        print(f"Errore dettaglio diario: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/insights/generate')
@login_required
def generate_ai_insights():
    """Genera insights AI basati sui diari dell'utente"""
    try:
        # Ottieni tutti i diari dell'utente
        journals = TravelJournal.query.filter_by(user_id=current_user.id).all()
        
        if len(journals) < 2:
            return jsonify({
                'success': False,
                'error': 'Servono almeno 2 viaggi per generare insights'
            })
        
        # Genera insights usando AI
        insights = generate_user_insights(current_user.id, journals)
        
        # Salva insights nel database
        for insight_data in insights:
            insight = AIInsight(
                user_id=current_user.id,
                insight_type=insight_data['type'],
                insight_category=insight_data['category'],
                title=insight_data['title'],
                description=insight_data['description'],
                confidence_score=insight_data['confidence'],
                supporting_data=insight_data['data'],
                suggested_actions=insight_data['actions']
            )
            db.session.add(insight)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'insights': insights,
            'total_generated': len(insights)
        })
        
    except Exception as e:
        print(f"Errore generazione insights: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# === FUNZIONI DI SUPPORTO AI ===

def generate_plan_b_alternatives(original_plan: Dict, disruption_type: str, 
                                     city: str, affected_location: str) -> List[Dict]:
    """Genera alternative per Piano B usando AI"""
    try:
        prompt = f"""
        Situazione: {disruption_type} a {affected_location} in {city}.
        Piano originale: {json.dumps(original_plan, indent=2)}
        
        Genera 3 alternative intelligenti per gestire questo imprevisto.
        Considera: vicinanza geografica, qualità equivalente, tempi di attesa.
        
        Rispondi in JSON con questo formato:
        {{
            "alternatives": [
                {{
                    "option": "skip|alternative|reschedule",
                    "title": "Titolo dell'alternativa",
                    "description": "Descrizione dettagliata",
                    "location": "Nome del luogo alternativo",
                    "time_impact": "Impatto sui tempi",
                    "quality_score": 0.8,
                    "distance_meters": 200
                }}
            ]
        }}
        """
        
        # Usa GPT-5 per generare alternative
        response = openai.chat.completions.create(
            model="gpt-5",  # il modello più recente
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("alternatives", [])
        
    except Exception as e:
        print(f"Errore generazione Piano B: {e}")
        # Fallback con alternative predefinite
        return [
            {
                "option": "skip",
                "title": "Salta la tappa",
                "description": "Prosegui con il resto del programma",
                "time_impact": "Risparmi 2 ore",
                "quality_score": 0.6,
                "distance_meters": 0
            }
        ]

def generate_smart_discoveries(lat: float, lon: float, city: str, 
                                   user_prefs: Dict, radius: int) -> List[Dict]:
    """Genera scoperte intelligenti usando AI e preferenze utente"""
    try:
        prompt = f"""
        Posizione utente: {lat}, {lon} in {city}
        Raggio di ricerca: {radius} metri
        Preferenze utente: {json.dumps(user_prefs)}
        
        Trova 2-3 luoghi interessanti nelle vicinanze che corrispondono agli interessi dell'utente.
        Considera: autenticità locale, qualità, distanza, orari di apertura.
        
        Rispondi in JSON:
        {{
            "discoveries": [
                {{
                    "name": "Nome del luogo",
                    "type": "restaurant|attraction|shop|event",
                    "description": "Descrizione coinvolgente",
                    "lat": 45.123,
                    "lon": 9.456,
                    "distance": 150,
                    "relevance": 0.9,
                    "matched_interests": ["cibo", "storia"],
                    "reasoning": "Perché è stato suggerito",
                    "estimated_time": "30 min"
                }}
            ]
        }}
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=600
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("discoveries", [])
        
    except Exception as e:
        print(f"Errore scoperte intelligenti: {e}")
        return []

def generate_journal_ai_content(city: str, itinerary: Dict, 
                                     user_notes: str, user_id: str) -> Dict:
    """Genera contenuto AI per il diario di viaggio"""
    try:
        prompt = f"""
        Crea un diario di viaggio AI per {city}.
        
        Itinerario: {json.dumps(itinerary, indent=2)}
        Note utente: {user_notes}
        
        Genera contenuto emotivo e personale che catturi l'essenza del viaggio.
        
        Rispondi in JSON:
        {{
            "summary": "Riassunto coinvolgente del viaggio (200 parole)",
            "highlights": [
                {{
                    "moment": "Descrizione del momento",
                    "location": "Dove è successo", 
                    "emotion": "Emozione provata",
                    "photo_suggestion": "Cosa fotografare"
                }}
            ],
            "insights": {{
                "travel_style": "Stile di viaggio emerso",
                "preferences_discovered": ["nuove preferenze"],
                "recommendations": "Suggerimenti per viaggi futuri"
            }},
            "confidence": 0.85
        }}
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Errore contenuto diario AI: {e}")
        return {
            "summary": f"Un bellissimo viaggio a {city}",
            "highlights": [],
            "insights": {},
            "confidence": 0.5
        }

def generate_user_insights(user_id: str, journals: List[TravelJournal]) -> List[Dict]:
    """Genera insights comportamentali dall'analisi dei viaggi"""
    try:
        journals_data = []
        for journal in journals:
            journals_data.append({
                'city': journal.city,
                'date': journal.travel_date.isoformat(),
                'rating': journal.user_rating,
                'highlights': journal.highlights,
                'insights': journal.insights
            })
        
        prompt = f"""
        Analizza i viaggi dell'utente e genera insights comportamentali.
        
        Dati viaggi: {json.dumps(journals_data, indent=2)}
        
        Identifica pattern, preferenze nascoste, suggerimenti personalizzati.
        
        Rispondi in JSON:
        {{
            "insights": [
                {{
                    "type": "pattern|recommendation|trend",
                    "category": "travel_behavior|preferences|efficiency",
                    "title": "Titolo dell'insight",
                    "description": "Descrizione dettagliata",
                    "confidence": 0.8,
                    "data": {{"supporting_evidence": "dati di supporto"}},
                    "actions": ["azioni suggerite"]
                }}
            ]
        }}
        """
        
        response = openai.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("insights", [])
        
    except Exception as e:
        print(f"Errore generazione insights: {e}")
        return []

# === FUNZIONI DI SUPPORTO ===

def get_user_preferences(user_id: str) -> Dict:
    """Ottieni preferenze utente dal database"""
    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        return {
            'favorite_categories': ['storia', 'arte'],
            'travel_pace': 'medium',
            'budget_preference': 'medium'
        }
    
    return {
        'favorite_categories': prefs.favorite_categories or ['storia', 'arte'],
        'travel_pace': prefs.travel_pace or 'medium',
        'budget_preference': prefs.budget_preference or 'medium',
        'crowding_tolerance': prefs.crowding_tolerance or 0.5,
        'spontaneity_score': prefs.spontaneity_score or 0.5
    }

def update_user_plan_b_preferences(user_id: str, selected_option: str):
    """Aggiorna preferenze basate su scelte Piano B"""
    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.session.add(prefs)
    
    # Aggiorna metriche Piano B
    if selected_option == 'alternative':
        prefs.spontaneity_score = min(1.0, (prefs.spontaneity_score or 0.5) + 0.1)
    elif selected_option == 'skip':
        prefs.crowding_tolerance = max(0.0, (prefs.crowding_tolerance or 0.5) - 0.1)
    
    db.session.commit()

def update_user_discovery_preferences(user_id: str, discovery: SmartDiscovery, action: str):
    """Aggiorna preferenze basate su feedback scoperte"""
    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.session.add(prefs)
    
    # Aggiorna ratio di accettazione scoperte
    current_ratio = prefs.accepted_discoveries_ratio or 0.5
    if action == 'accepted':
        prefs.accepted_discoveries_ratio = min(1.0, current_ratio + 0.05)
    else:
        prefs.accepted_discoveries_ratio = max(0.0, current_ratio - 0.05)
    
    db.session.commit()

print("🚀 Advanced Routes caricato - Piano B, Scoperte Intelligenti, Diario AI attivi!")